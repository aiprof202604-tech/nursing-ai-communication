"""Check that data/experiment.db is the database behind data/data.csv.

Runs exactly the export query of `cmd_export` in code/experiment.py (no API
keys needed) and compares the result with data/data.csv byte for byte.
Usage: python3 code/verify_db_export.py data/experiment.db data/data.csv
"""
import csv
import io
import sqlite3
import sys

db, ref = sys.argv[1], sys.argv[2]
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("""
    SELECT s.session_id, s.scenario, s.condition, s.run, s.actor_model,
           e.ps, e.cc, e.er, e.lf, e.rc, e.total, e.rationale
    FROM sessions s
    LEFT JOIN evaluations e ON e.session_id = s.session_id
    WHERE s.status = 'completed'
    ORDER BY s.scenario, s.condition, s.run, s.actor_model
""").fetchall()
buf = io.StringIO(newline="")
w = csv.writer(buf)
w.writerow(["session_id", "scenario", "condition", "run", "actor_model",
            "PS", "CC", "ER", "LF", "RC", "total", "rationale"])
w.writerows(rows)
exported = buf.getvalue().encode("utf-8")
reference = open(ref, "rb").read()
print(f"sessions exported: {len(rows)}")
print(f"byte-identical to {ref}: {exported == reference}")
sys.exit(0 if exported == reference else 1)
