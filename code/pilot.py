#!/usr/bin/env python3
"""
Pilot Experiment Runner
=======================
Validates prompts and pipeline before the full 180-session run.

Pilot configuration:
- Scenarios : S1 only (Question Inhibition - simplest)
- Conditions: A (Control) and C (Mediation - most complex intervention)
- Runs      : 1 per cell
- Models    : Claude / GPT-4.1 mini / Gemini
- Total     : 1 x 2 x 1 x 3 = 6 sessions + 6 evaluations

Results are saved to the SAME database as the full experiment.
After validating the pilot, simply run `python experiment.py run` and the
remaining 174 sessions will execute (the 6 pilot sessions will be skipped).

Estimated time: 5-10 minutes
Estimated cost: ~$0.50 USD (~75 yen)

Usage
-----
python pilot.py
"""

import asyncio
import aiosqlite

import experiment
from experiment import (
    init_clients,
    init_db,
    run_one_session,
    run_judge_all,
    cmd_status,
    get_completed_sessions,
    ACTOR_MODELS,
    DB_PATH,
    log,
)

# ── Pilot Configuration ───────────────────────────────────────────────────────
PILOT_SCENARIOS  = ["S1"]
PILOT_CONDITIONS = ["A", "C"]
PILOT_RUNS       = 1


async def run_pilot(db: aiosqlite.Connection) -> None:
    tasks = []
    for scenario in PILOT_SCENARIOS:
        for condition in PILOT_CONDITIONS:
            for run in range(1, PILOT_RUNS + 1):
                for model in ACTOR_MODELS:
                    tasks.append(
                        run_one_session(scenario, condition, run, model, db)
                    )
    log.info("=== PILOT RUN: %d sessions ===", len(tasks))
    await asyncio.gather(*tasks)


async def show_pilot_results(db: aiosqlite.Connection) -> None:
    """Print pilot transcripts and scores for manual inspection."""
    print("\n" + "=" * 78)
    print("PILOT RESULTS - MANUAL INSPECTION")
    print("=" * 78)

    cur = await db.execute("""
        SELECT s.session_id, s.scenario, s.condition, s.actor_model,
               s.transcript,
               e.ps, e.cc, e.er, e.lf, e.rc, e.total, e.rationale
        FROM sessions s
        LEFT JOIN evaluations e ON e.session_id = s.session_id
        WHERE s.status = 'completed'
        ORDER BY s.scenario, s.condition, s.actor_model
    """)
    rows = await cur.fetchall()

    import json
    for row in rows:
        sid, sc, cond, model, transcript_json, ps, cc, er, lf, rc, total, rat = row
        print(f"\n{'─' * 78}")
        print(f"  SESSION : {sid}")
        print(f"  SCORES  : PS={ps}  CC={cc}  ER={er}  LF={lf}  RC={rc}  TOTAL={total}")
        print(f"  JUDGE   : {rat or '(not evaluated)'}")
        print(f"{'─' * 78}")

        if transcript_json:
            transcript = json.loads(transcript_json)
            for entry in transcript:
                speaker = entry["speaker"]
                content = entry["content"]
                # Truncate very long messages for readability
                if len(content) > 240:
                    content = content[:237] + "..."
                print(f"\n  [{speaker.upper()}]")
                print(f"  {content}")

    print("\n" + "=" * 78)
    print("END OF PILOT RESULTS - review pilot_checklist.md to evaluate quality")
    print("=" * 78 + "\n")


async def main() -> None:
    init_clients()
    async with aiosqlite.connect(DB_PATH) as db:
        await init_db(db)
        await run_pilot(db)
        log.info("Pilot sessions complete. Running judge...")
        await run_judge_all(db)
        await cmd_status(db)
        await show_pilot_results(db)


if __name__ == "__main__":
    asyncio.run(main())
