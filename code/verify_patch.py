#!/usr/bin/env python3
"""
verify_patch.py
===============
Static (no-API) verification that the v1.2.0 patch is correctly
installed in experiment.py. Run this once after replacing the file
to confirm both bug fixes are present before kicking off the long
API run.

Usage
-----
    python code/verify_patch.py
"""

from pathlib import Path
import sys

SRC = Path(__file__).resolve().parent / "experiment.py"
if not SRC.exists():
    sys.exit("ERROR: experiment.py not found alongside verify_patch.py")

text = SRC.read_text(encoding="utf-8")

checks = [
    ("Bug 1 fix: dual canonical histories declared",
     "student_canonical : List[Dict] = []" in text
     and "nurse_canonical   : List[Dict] = []" in text),
    ("Bug 1 fix: single shared canonical removed",
     "canonical  : List[Dict] = []" not in text),
    ("Bug 1 fix: dead variable student_for_nurse removed",
     "student_for_nurse" not in text),
    ("Bug 1 fix: nurse_canonical receives bridged student message",
     'nurse_canonical.append({"speaker": "student",   "content": bridged_s2n})' in text),
    ("Bug 1 fix: student_canonical receives bridged nurse message",
     'student_canonical.append({"speaker": "nurse", "content": bridged_n2s})' in text),
    ("Bug 2 fix: normalised transcript labels (no leaky labels remain)",
     "mediator→student" not in text
     and "mediator→nurse" not in text
     and "student_raw" not in text.split('"speaker"')[0]),  # ignore audit tag mentions
    ("Bug 2 fix: Judge view filters mediator entries",
     'visible = [e for e in transcript if e["speaker"] in ("student", "nurse")]' in text),
    ("Bug 2 fix: Judge formats only the filtered list",
     "for e in visible" in text),
]

passed = sum(1 for _, ok in checks if ok)
total  = len(checks)

for label, ok in checks:
    mark = "OK  " if ok else "FAIL"
    print(f"  [{mark}] {label}")

print()
if passed == total:
    print(f"VERIFICATION PASSED: all {total} checks satisfied.")
    print("You may proceed to `python code/setup_check.py` and then the pilot.")
    sys.exit(0)
else:
    print(f"VERIFICATION FAILED: {passed}/{total} checks passed.")
    print("The patched experiment.py does not match expectations.")
    print("Restore from backup and try again.")
    sys.exit(2)
