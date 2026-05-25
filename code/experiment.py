#!/usr/bin/env python3
"""
Nursing Education In-Silico Experiment
=======================================
Multi-LLM simulation of nursing student–clinical nurse interactions.

Features
--------
- Resume-safe  : each session saved to SQLite immediately on completion
- Parallel     : asyncio + per-provider semaphores (no rate-limit crashes)
- Three actor models  : Claude Sonnet / GPT-4.1 mini / Gemini 2.5 Flash
- Independent judge   : GPT-4.1 (different provider from some actors)

Requirements
------------
pip install anthropic openai google-genai aiosqlite

Environment variables
---------------------
ANTHROPIC_API_KEY   OPENAI_API_KEY   GOOGLE_API_KEY

Usage
-----
python experiment.py run      # run all sessions (auto-resumes if interrupted)
python experiment.py judge    # evaluate completed sessions with Judge Agent
python experiment.py status   # show progress table
python experiment.py export   # write results/data.csv
"""

# ── Imports ───────────────────────────────────────────────────────────────────
import argparse
import asyncio
import csv
import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite
import anthropic
from openai import AsyncOpenAI
from google import genai as gai

# ── Configuration ─────────────────────────────────────────────────────────────
SCENARIOS    = ["S1", "S2", "S3"]
CONDITIONS   = ["A", "B", "C", "D"]
RUNS         = 5
ACTOR_MODELS = ["claude", "gpt4mini", "gemini"]
MAX_TURNS    = 6          # exchange pairs (student + nurse = 1 turn)

MODEL_IDS = {
    "claude"   : "claude-sonnet-4-6",
    "gpt4mini" : "gpt-4.1-mini",
    "gemini"   : "gemini-2.5-flash",
    "judge"    : "gpt-4.1",
}

# Concurrent API calls per provider (tune to your tier)
SEM_LIMITS = {
    "claude"   : 3,
    "gpt4mini" : 5,
    "gemini"   : 5,
    "judge"    : 3,
}

RESULTS_DIR  = Path("results")
DB_PATH      = RESULTS_DIR / "experiment.db"
LOG_PATH     = RESULTS_DIR / "experiment.log"

MAX_RETRIES  = 4
RETRY_BASE   = 2.0   # seconds (exponential backoff)
ACTOR_TOKENS = 300
JUDGE_TOKENS = 450
TEMPERATURE  = 0.8

# ── Logging ───────────────────────────────────────────────────────────────────
RESULTS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── System Prompts ────────────────────────────────────────────────────────────
STUDENT_BASE = """You are a second-year nursing student in clinical practice on an internal medicine ward.

PERSONA:
- Age 20, female, first clinical rotation; conscientious but low confidence
- High anxiety about making mistakes; strong need to be accepted by clinical staff
  (belongingness need; Levett-Jones & Lathlean, 2009)
- Tendency to self-censor, avoid initiating with busy nurses, hedge when stressed

BEHAVIOURAL RULES:
1. Feel more anxious when the nurse appears rushed or irritated
2. Under stress, prioritise avoiding conflict over raising concerns
3. Respond to warmth with greater openness and longer sentences
4. Respond to criticism with shorter, more defensive replies
5. Never fabricate clinical knowledge you do not possess
6. Convey uncertainty with hedging ("I think...", "Maybe...", "I'm not sure but...")

CURRENT SCENARIO:
{scenario}

Respond as this student would. Express emotion through word choice and sentence
length — do NOT label your feelings explicitly. 2–4 sentences per turn."""

NURSE_BASE = """You are an experienced clinical nurse supervising nursing students on a busy internal medicine ward.

PERSONA:
- Age 34; 10 years clinical experience, 5 years supervising students
- Today: managing 8 patients, short-staffed, behind on charting
- Teaching philosophy: students learn by doing; hand-holding is counterproductive
- Style: direct, efficient; brusque under pressure; genuinely cares but rarely shows it

BEHAVIOURAL RULES:
1. Response length is inversely proportional to perceived busyness
2. Use clipped sentences when stressed; avoid unsolicited encouragement
3. Show patience and detail only during low-pressure moments
4. Notice student hesitation but do not always address it when pressed for time
5. Never provide incorrect clinical information
6. Show occasional genuine mentorship even when rushed

CURRENT SCENARIO:
{scenario}

Respond as this nurse would. Convey time pressure through sentence structure —
do NOT write "I am busy". 2–4 sentences per turn."""

MEDIATOR_COACH_STUDENT = """You are a generative AI support system visible ONLY to the nursing student.
Your role: coach the student BEFORE she speaks to the nurse this turn.
- 1–2 concrete, non-patronising sentence suggestions
- Briefly validate her emotion, then redirect to action
- Use SBAR structure where relevant
- Never act on her behalf
- Maximum 50 words."""

MEDIATOR_BRIDGE = """You are a generative AI communication intermediary, visible to BOTH parties.
You receive a raw message and rewrite it for the intended recipient.

Rules:
- Preserve ALL clinical content exactly — never omit or alter facts
- Improve clarity and professional register
- Flag patient-safety concerns explicitly if present
- Output ONLY the rewritten message, no preamble or commentary
- Maximum 80 words."""

MEDIATOR_COACH_NURSE = """You are a generative AI support system visible ONLY to the supervising nurse.
Your role: provide one brief, evidence-based supervisory suggestion before the nurse responds.
- Alert the nurse to the student's apparent cognitive/emotional state
- Suggest a specific verbal approach that promotes psychological safety
- Frame as an option, not a correction
- Maximum 40 words."""

JUDGE_SYSTEM = """You are a blinded evaluator assessing clinical communication quality.
You do NOT know which experimental condition produced the transcript.

Score five dimensions 1–5:

PS – Psychological Safety
1 student shut down | 2 minimal/stressed | 3 moderate hesitation
4 reasonable confidence | 5 open; mutual respect

CC – Communication Clarity (accuracy & completeness)
1 critical gaps | 2 significant gaps | 3 minor omissions
4 complete/structured | 5 complete + confirmed (e.g. SBAR)

ER – Empathic Response (emotional acknowledgement)
1 ignored/negative | 2 noticed not addressed | 3 brief acknowledgement
4 addressed | 5 sustained attunement

LF – Learning Facilitation (educational value)
1 harmful/neutral | 2 minimal | 3 some learning
4 clear learning moment | 5 deep learning / insight demonstrated

RC – Relationship Continuity (post-dialogue relationship health)
1 damaged/avoidant | 2 tension unresolved | 3 neutral
4 slightly strengthened | 5 meaningfully strengthened

OUTPUT — JSON only, no markdown, no preamble:
{"PS":N,"CC":N,"ER":N,"LF":N,"RC":N,"total":N,"rationale":"2-3 sentences"}"""

# ── Scenario Descriptions ─────────────────────────────────────────────────────
SCENARIOS_TEXT = {
    "S1": {
        "name"   : "Question Inhibition",
        "student": (
            "You are reviewing a medication order for a patient in room 302 and notice the prescribed "
            "dose appears higher than what you studied. The supervising nurse is nearby but appears "
            "absorbed in her work. You are afraid of interrupting and of appearing incompetent. "
            "You must decide whether and how to raise your concern."
        ),
        "nurse": (
            "You are updating medication charts for multiple patients. A nursing student has been "
            "hovering nearby for several minutes. You are aware of her presence but deeply focused "
            "on your documentation."
        ),
    },
    "S2": {
        "name"   : "Error Feedback",
        "student": (
            "The supervising nurse has just told you, curtly, that your SOAP note for room 304 "
            "contains a documentation error — you recorded an incorrect assessment finding. "
            "You feel embarrassed and unsure how to respond or correct the mistake."
        ),
        "nurse": (
            "You discovered that the nursing student's SOAP note for room 304 contains an incorrect "
            "assessment entry that could cause a handover problem. You corrected the student directly "
            "and are now waiting for her response."
        ),
    },
    "S3": {
        "name"   : "SBAR Reporting Under Pressure",
        "student": (
            "A patient in room 307 is deteriorating: increased respiratory rate, new onset pallor, "
            "and confusion. You need to report this to the supervising nurse using SBAR. "
            "The nurse looks visibly pressed for time. You are nervous and struggling to organise "
            "your thoughts into a structured format."
        ),
        "nurse": (
            "You are preparing an urgent procedure when the nursing student approaches looking "
            "flustered. You have very limited time. You know student reports must be heard, "
            "but your impatience is difficult to conceal."
        ),
    },
}

# ── Database Layer ────────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id   TEXT PRIMARY KEY,
    scenario     TEXT NOT NULL,
    condition    TEXT NOT NULL,
    run          INTEGER NOT NULL,
    actor_model  TEXT NOT NULL,
    transcript   TEXT,          -- JSON
    canonical    TEXT,          -- JSON (student/nurse turns only)
    status       TEXT NOT NULL DEFAULT 'pending',
    error_msg    TEXT,
    started_at   TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS evaluations (
    eval_id      TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL,
    judge_model  TEXT NOT NULL,
    ps           INTEGER,
    cc           INTEGER,
    er           INTEGER,
    lf           INTEGER,
    rc           INTEGER,
    total        INTEGER,
    rationale    TEXT,
    status       TEXT NOT NULL DEFAULT 'pending',
    completed_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
"""

async def init_db(db: aiosqlite.Connection) -> None:
    await db.executescript(SCHEMA)
    await db.commit()


async def is_session_done(db: aiosqlite.Connection, sid: str) -> bool:
    cur = await db.execute(
        "SELECT 1 FROM sessions WHERE session_id=? AND status='completed'", (sid,)
    )
    return await cur.fetchone() is not None


async def save_session(
    db: aiosqlite.Connection,
    sid: str,
    scenario: str,
    condition: str,
    run: int,
    model: str,
    transcript: List[Dict],
    canonical: List[Dict],
) -> None:
    now = datetime.utcnow().isoformat()
    await db.execute(
        """INSERT OR REPLACE INTO sessions
           (session_id,scenario,condition,run,actor_model,
            transcript,canonical,status,completed_at)
           VALUES (?,?,?,?,?,?,?,'completed',?)""",
        (sid, scenario, condition, run, model,
         json.dumps(transcript, ensure_ascii=False),
         json.dumps(canonical, ensure_ascii=False), now),
    )
    await db.commit()


async def save_session_error(
    db: aiosqlite.Connection, sid: str, scenario: str,
    condition: str, run: int, model: str, error: str,
) -> None:
    now = datetime.utcnow().isoformat()
    await db.execute(
        """INSERT OR REPLACE INTO sessions
           (session_id,scenario,condition,run,actor_model,
            status,error_msg,completed_at)
           VALUES (?,?,?,?,?,'error',?,?)""",
        (sid, scenario, condition, run, model, error, now),
    )
    await db.commit()


async def is_eval_done(db: aiosqlite.Connection, eid: str) -> bool:
    cur = await db.execute(
        "SELECT 1 FROM evaluations WHERE eval_id=? AND status='completed'", (eid,)
    )
    return await cur.fetchone() is not None


async def save_eval(
    db: aiosqlite.Connection,
    eid: str, sid: str,
    scores: Dict[str, Any],
) -> None:
    now = datetime.utcnow().isoformat()
    await db.execute(
        """INSERT OR REPLACE INTO evaluations
           (eval_id,session_id,judge_model,ps,cc,er,lf,rc,total,
            rationale,status,completed_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,'completed',?)""",
        (eid, sid, MODEL_IDS["judge"],
         scores["PS"], scores["CC"], scores["ER"],
         scores["LF"], scores["RC"], scores["total"],
         scores.get("rationale", ""), now),
    )
    await db.commit()


async def get_completed_sessions(db: aiosqlite.Connection) -> List[Dict]:
    cur = await db.execute(
        "SELECT session_id, transcript FROM sessions WHERE status='completed'"
    )
    rows = await cur.fetchall()
    return [{"session_id": r[0], "transcript": r[1]} for r in rows]

# ── API Clients (initialised in main) ────────────────────────────────────────
_claude_client : Optional[anthropic.AsyncAnthropic] = None
_openai_client : Optional[AsyncOpenAI]               = None
_gemini_client : Optional[gai.Client]                = None
_sems          : Dict[str, asyncio.Semaphore]        = {}


def init_clients() -> None:
    global _claude_client, _openai_client, _gemini_client, _sems
    _claude_client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    _openai_client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    _gemini_client = gai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    _sems = {k: asyncio.Semaphore(v) for k, v in SEM_LIMITS.items()}

# ── Low-level API Wrappers (with retry) ───────────────────────────────────────
async def _call_claude(system: str, messages: List[Dict], max_tokens: int) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            async with _sems["claude"]:
                resp = await _claude_client.messages.create(
                    model=MODEL_IDS["claude"],
                    max_tokens=max_tokens,
                    temperature=TEMPERATURE,
                    system=system,
                    messages=messages,
                )
            return resp.content[0].text.strip()
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = RETRY_BASE ** attempt + random.uniform(0, 1)
            log.warning("Claude error (attempt %d): %s — retrying in %.1fs", attempt + 1, e, wait)
            await asyncio.sleep(wait)


async def _call_openai(system: str, messages: List[Dict], max_tokens: int,
                       model_key: str = "gpt4mini") -> str:
    sem_key = "judge" if model_key == "judge" else "gpt4mini"
    for attempt in range(MAX_RETRIES):
        try:
            async with _sems[sem_key]:
                resp = await _openai_client.chat.completions.create(
                    model=MODEL_IDS[model_key],
                    max_tokens=max_tokens,
                    temperature=TEMPERATURE if model_key != "judge" else 0.2,
                    messages=[{"role": "system", "content": system}] + messages,
                )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = RETRY_BASE ** attempt + random.uniform(0, 1)
            log.warning("OpenAI error (attempt %d): %s — retrying in %.1fs", attempt + 1, e, wait)
            await asyncio.sleep(wait)


async def _call_gemini(system: str, messages: List[Dict], max_tokens: int) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            async with _sems["gemini"]:
                # Convert to Gemini role format ("user"/"model")
                contents = []
                for m in messages:
                    g_role = "model" if m["role"] == "assistant" else "user"
                    contents.append({"role": g_role, "parts": [{"text": m["content"]}]})
                resp = await _gemini_client.aio.models.generate_content(
                    model=MODEL_IDS["gemini"],
                    contents=contents,
                    config=gai.types.GenerateContentConfig(
                        system_instruction=system,
                        max_output_tokens=max_tokens,
                        temperature=TEMPERATURE,
                    ),
                )
            return resp.text.strip()
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = RETRY_BASE ** attempt + random.uniform(0, 1)
            log.warning("Gemini error (attempt %d): %s — retrying in %.1fs", attempt + 1, e, wait)
            await asyncio.sleep(wait)

# ── Unified Actor/Mediator/Judge Dispatcher ───────────────────────────────────
async def call_llm(model_key: str, system: str,
                   messages: List[Dict], max_tokens: int) -> str:
    if model_key == "claude":
        return await _call_claude(system, messages, max_tokens)
    elif model_key in ("gpt4mini", "judge"):
        return await _call_openai(system, messages, max_tokens, model_key)
    elif model_key == "gemini":
        return await _call_gemini(system, messages, max_tokens)
    else:
        raise ValueError(f"Unknown model key: {model_key}")

# ── Conversation Utilities ────────────────────────────────────────────────────
def build_api_messages(canonical: List[Dict], perspective: str) -> List[Dict]:
    """
    Convert canonical history to API messages from a given perspective.
    From agent's perspective: own turns → 'assistant', other party → 'user'.
    The last entry in canonical is what the OTHER party just said,
    so it naturally ends as a 'user' message for the next assistant reply.
    """
    msgs = []
    for entry in canonical:
        role = "assistant" if entry["speaker"] == perspective else "user"
        msgs.append({"role": role, "content": entry["content"]})
    return msgs


def make_session_id(scenario: str, condition: str, run: int, model: str) -> str:
    return f"{scenario}_{condition}_r{run:02d}_{model}"


def make_eval_id(session_id: str) -> str:
    return f"eval_{session_id}"

# ── Session Runner ────────────────────────────────────────────────────────────
async def run_one_session(
    scenario: str, condition: str, run: int, model: str, db: aiosqlite.Connection
) -> None:
    sid = make_session_id(scenario, condition, run, model)

    if await is_session_done(db, sid):
        log.info("SKIP  %s (already completed)", sid)
        return

    log.info("START %s", sid)
    sc    = SCENARIOS_TEXT[scenario]
    s_sys = STUDENT_BASE.format(scenario=sc["student"])
    n_sys = NURSE_BASE.format(scenario=sc["nurse"])

    # Two perception histories (Bug 1 fix).
    # In Conditions A, B, D: identical contents (no bridging).
    # In Condition C: each agent sees the OTHER party's bridged version,
    # and remembers her OWN raw utterance.
    student_canonical : List[Dict] = []   # what the student perceives
    nurse_canonical   : List[Dict] = []   # what the nurse perceives
    transcript        : List[Dict] = []   # full record for Judge

    try:
        for turn_idx in range(MAX_TURNS):
            # ── Student turn ──────────────────────────────────────────────────
            s_msgs = build_api_messages(student_canonical, "student")
            if not s_msgs:                        # first turn: prompt the student
                s_msgs = [{"role": "user",
                            "content": "Please begin the interaction based on your scenario."}]

            if condition == "B":
                # Mediator coaches student; inject coaching as final system addendum
                coach = await call_llm(
                    "gpt4mini", MEDIATOR_COACH_STUDENT,
                    [{"role": "user",
                      "content": f"Conversation so far:\n{_fmt_canonical(student_canonical)}\n"
                                 f"Please coach the student for her next turn."}],
                    60,
                )
                s_sys_turn = s_sys + f"\n\n[AI SUPPORT — this turn only]: {coach}"
                transcript.append({"speaker": "mediator_coach_student", "content": coach})
            else:
                s_sys_turn = s_sys
                coach = None

            student_raw = await call_llm(model, s_sys_turn, s_msgs, ACTOR_TOKENS)

            if condition == "C":
                # Mediator bridges student → nurse
                bridged_s2n = await call_llm(
                    "gpt4mini", MEDIATOR_BRIDGE,
                    [{"role": "user",
                      "content": f"Rewrite for the nurse:\n{student_raw}"}],
                    ACTOR_TOKENS,
                )
                # Transcript: clean "student" label with the delivered (bridged) content
                # for the Judge (Bug 2 fix), plus an internal record of the raw and
                # bridge action for audit (excluded from the Judge view).
                transcript.append({"speaker": "student", "content": bridged_s2n})
                transcript.append({"speaker": "mediator_internal_student_raw",
                                   "content": student_raw})
                transcript.append({"speaker": "mediator_internal_bridge_s2n",
                                   "content": bridged_s2n})
                # Bug 1 fix: student remembers her OWN raw; nurse sees BRIDGED.
                student_canonical.append({"speaker": "student", "content": student_raw})
                nurse_canonical.append({"speaker": "student",   "content": bridged_s2n})
            else:
                transcript.append({"speaker": "student", "content": student_raw})
                student_canonical.append({"speaker": "student", "content": student_raw})
                nurse_canonical.append({"speaker": "student",   "content": student_raw})

            # ── Nurse turn ────────────────────────────────────────────────────
            n_msgs = build_api_messages(nurse_canonical, "nurse")

            if condition == "D":
                # Mediator coaches nurse
                coach_n = await call_llm(
                    "gpt4mini", MEDIATOR_COACH_NURSE,
                    [{"role": "user",
                      "content": f"Conversation so far:\n{_fmt_canonical(nurse_canonical)}\n"
                                 f"Please coach the nurse for her next turn."}],
                    50,
                )
                n_sys_turn = n_sys + f"\n\n[AI SUPPORT — this turn only]: {coach_n}"
                transcript.append({"speaker": "mediator_coach_nurse", "content": coach_n})
            else:
                n_sys_turn = n_sys

            nurse_raw = await call_llm(model, n_sys_turn, n_msgs, ACTOR_TOKENS)

            if condition == "C":
                # Mediator bridges nurse → student
                bridged_n2s = await call_llm(
                    "gpt4mini", MEDIATOR_BRIDGE,
                    [{"role": "user",
                      "content": f"Rewrite for the student:\n{nurse_raw}"}],
                    ACTOR_TOKENS,
                )
                transcript.append({"speaker": "nurse", "content": bridged_n2s})
                transcript.append({"speaker": "mediator_internal_nurse_raw",
                                   "content": nurse_raw})
                transcript.append({"speaker": "mediator_internal_bridge_n2s",
                                   "content": bridged_n2s})
                # Bug 1 fix: nurse remembers her OWN raw; student sees BRIDGED.
                nurse_canonical.append({"speaker": "nurse",   "content": nurse_raw})
                student_canonical.append({"speaker": "nurse", "content": bridged_n2s})
            else:
                transcript.append({"speaker": "nurse", "content": nurse_raw})
                nurse_canonical.append({"speaker": "nurse",   "content": nurse_raw})
                student_canonical.append({"speaker": "nurse", "content": nurse_raw})

        # We persist the student perception history as the "canonical" record;
        # it equals nurse_canonical in Conditions A, B, D and differs only in C.
        await save_session(db, sid, scenario, condition, run, model,
                           transcript, student_canonical)
        log.info("DONE  %s", sid)

    except Exception as e:
        err = str(e)
        log.error("ERROR %s : %s", sid, err)
        await save_session_error(db, sid, scenario, condition, run, model, err)


def _fmt_canonical(canonical: List[Dict]) -> str:
    return "\n".join(f"{e['speaker'].upper()}: {e['content']}" for e in canonical) or "(empty)"

# ── Judge Runner ──────────────────────────────────────────────────────────────
async def run_one_eval(session: Dict, db: aiosqlite.Connection) -> None:
    sid  = session["session_id"]
    eid  = make_eval_id(sid)

    if await is_eval_done(db, eid):
        log.info("SKIP  eval %s (already done)", sid)
        return

    log.info("JUDGE %s", sid)
    transcript = json.loads(session["transcript"])

    # Bug 2 fix: filter out mediator-internal and coach entries before sending
    # to the Judge. The Judge sees only the dialogue as it was actually
    # delivered: "student" and "nurse" turns. In Condition C these are the
    # bridged versions (what each recipient experienced); in A, B, D these
    # are the raw turns (no bridging). The mediator-coach messages in B and D
    # influenced the agent outputs but are not directly visible to the
    # recipient or the Judge, mirroring real deployment.
    visible = [e for e in transcript if e["speaker"] in ("student", "nurse")]
    fmt = "\n".join(
        f"[{e['speaker'].upper()}] {e['content']}" for e in visible
    )

    try:
        raw = await call_llm(
            "judge", JUDGE_SYSTEM,
            [{"role": "user", "content": f"TRANSCRIPT:\n{fmt}"}],
            JUDGE_TOKENS,
        )
        # Strip markdown fences if present
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        scores = json.loads(raw)
        await save_eval(db, eid, sid, scores)
        log.info("EVAL  %s → total=%d", sid, scores.get("total", "?"))
    except Exception as e:
        log.error("EVAL ERROR %s : %s", sid, e)

# ── Orchestrators ─────────────────────────────────────────────────────────────
async def run_experiment(db: aiosqlite.Connection) -> None:
    """Create all session tasks and execute in parallel (semaphore-controlled)."""
    tasks = []
    for scenario in SCENARIOS:
        for condition in CONDITIONS:
            for run in range(1, RUNS + 1):
                for model in ACTOR_MODELS:
                    tasks.append(
                        run_one_session(scenario, condition, run, model, db)
                    )
    log.info("Total sessions: %d  (parallel, resume-safe)", len(tasks))
    await asyncio.gather(*tasks)


async def run_judge_all(db: aiosqlite.Connection) -> None:
    """Evaluate all completed sessions that have not yet been judged."""
    sessions = await get_completed_sessions(db)
    tasks = [run_one_eval(s, db) for s in sessions]
    log.info("Pending evaluations: %d", len(tasks))
    await asyncio.gather(*tasks)

# ── CLI Commands ──────────────────────────────────────────────────────────────
async def cmd_status(db: aiosqlite.Connection) -> None:
    cur = await db.execute(
        "SELECT status, COUNT(*) FROM sessions GROUP BY status"
    )
    rows = await cur.fetchall()
    total = RUNS * len(CONDITIONS) * len(SCENARIOS) * len(ACTOR_MODELS)
    print(f"\n{'Status':12}  {'Count':>6}")
    print("-" * 22)
    for status, count in rows:
        print(f"{status:12}  {count:>6}")
    cur2 = await db.execute("SELECT COUNT(*) FROM sessions")
    done = (await cur2.fetchone())[0]
    print(f"{'(total)':12}  {done:>6} / {total}")
    cur3 = await db.execute(
        "SELECT COUNT(*) FROM evaluations WHERE status='completed'"
    )
    evaled = (await cur3.fetchone())[0]
    print(f"\nEvaluations completed: {evaled} / {done}\n")


async def cmd_export(db: aiosqlite.Connection) -> None:
    cur = await db.execute("""
        SELECT s.session_id, s.scenario, s.condition, s.run, s.actor_model,
               e.ps, e.cc, e.er, e.lf, e.rc, e.total, e.rationale
        FROM sessions s
        LEFT JOIN evaluations e ON e.session_id = s.session_id
        WHERE s.status = 'completed'
        ORDER BY s.scenario, s.condition, s.run, s.actor_model
    """)
    rows = await cur.fetchall()
    out = RESULTS_DIR / "data.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "session_id", "scenario", "condition", "run", "actor_model",
            "PS", "CC", "ER", "LF", "RC", "total", "rationale"
        ])
        writer.writerows(rows)
    print(f"Exported {len(rows)} rows → {out}")

# ── Main ──────────────────────────────────────────────────────────────────────
async def main() -> None:
    parser = argparse.ArgumentParser(description="Nursing In-Silico Experiment")
    parser.add_argument(
        "command",
        choices=["run", "judge", "status", "export"],
        help="run | judge | status | export",
    )
    args = parser.parse_args()

    init_clients()

    async with aiosqlite.connect(DB_PATH) as db:
        await init_db(db)

        if args.command == "run":
            await run_experiment(db)
            log.info("All sessions complete. Run 'python experiment.py judge' next.")

        elif args.command == "judge":
            await run_judge_all(db)
            log.info("All evaluations complete. Run 'python experiment.py export' next.")

        elif args.command == "status":
            await cmd_status(db)

        elif args.command == "export":
            await cmd_export(db)


if __name__ == "__main__":
    asyncio.run(main())
