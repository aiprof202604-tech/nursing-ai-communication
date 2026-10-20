"""Export every session of data/experiment.db to JSON Lines, so that the full
dialogues (including the Mediator's raw and rewritten turns in Condition C,
and the private coaching turns in Conditions B and D) can be read without
SQLite. One line per session; Judge scores and rationale are attached.

Speaker labels in `transcript`:
  student / nurse                  text delivered to the counterpart
                                   (in Condition C: the rewritten text)
  mediator_coach_student           Condition B private coaching (hidden from nurse and Judge)
  mediator_coach_nurse             Condition D private coaching (hidden from student and Judge)
  mediator_internal_student_raw    Condition C: student's original utterance
  mediator_internal_bridge_s2n     Condition C: rewrite delivered to the nurse
  mediator_internal_nurse_raw      Condition C: nurse's original utterance
  mediator_internal_bridge_n2s     Condition C: rewrite delivered to the student
Only `student` / `nurse` turns were shown to the Judge.

Usage: python3 code/export_transcripts.py data/experiment.db data/transcripts.jsonl
"""
import json
import sqlite3
import sys

db, out = sys.argv[1], sys.argv[2]
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("""
    SELECT s.session_id, s.scenario, s.condition, s.run, s.actor_model, s.transcript,
           s.completed_at, e.judge_model, e.ps, e.cc, e.er, e.lf, e.rc, e.total, e.rationale
    FROM sessions s JOIN evaluations e ON e.session_id = s.session_id
    WHERE s.status = 'completed'
    ORDER BY s.scenario, s.condition, s.run, s.actor_model""").fetchall()
with open(out, "w", encoding="utf-8") as f:
    for (sid, scen, cond, run, actor, tr, done, judge, ps, cc, er, lf, rc, total, why) in rows:
        f.write(json.dumps({
            "session_id": sid, "scenario": scen, "condition": cond, "run": run,
            "actor_model": actor, "completed_at": done,
            "transcript": json.loads(tr),
            "judge": {"model": judge, "PS": ps, "CC": cc, "ER": er, "LF": lf, "RC": rc,
                      "total": total, "rationale": why},
        }, ensure_ascii=False) + "\n")
print(f"wrote {len(rows)} sessions -> {out}")
