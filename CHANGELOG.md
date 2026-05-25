# Changelog

All notable changes to this reproducibility package are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [2.0.0] — 2026-05-25

This is a **major release** because two methodological bug fixes
materially change the headline numerical results reported in the
manuscript. The submitted manuscript reflects v2.0.0 numbers
exclusively. The v1.0.0 dataset is retained as `data/data_v1.1.0.csv`
for full transparency and to allow side-by-side comparison.

### Why v2.0.0 (not v1.1.0 or v1.0.1)

Per Semantic Versioning, MAJOR is appropriate when changes alter the
meaning of previously reported results. Both fixes below change the
direction and magnitude of the headline findings (which intervention
condition is most effective; the variance ratio between model and
condition factors). A minor- or patch-level bump would understate
the significance of these corrections.

### Fixed

#### Bug 1 — Mediation propagation failure (Condition C)

**Symptom.** In v1.0.0, the variable `student_for_nurse = bridged_s2n`
was computed but never used elsewhere in the codebase. The agents'
shared conversational history (`canonical`) always received the *raw*
student/nurse utterances, even in Condition C (Mediation). The bridged
versions were generated and written to the transcript, but neither the
student agent nor the nurse agent ever saw them on subsequent turns.

**Implication for v1.0.0 data.** The Mediation condition's measured
effect in v1.0.0 (Δ +2.11 on total score, p = .039) was almost
entirely a *Judge-side perception artifact*: the Judge saw a transcript
containing both raw and bridged turns and rated that combination more
favourably, while the agents themselves continued interacting as if
no mediation had taken place. The paper's claim that "both agents
respond to the bridged version in subsequent turns" was therefore
inconsistent with the v1.0.0 implementation.

**Fix.** Replaced the single shared `canonical` history with two
perception histories, `student_canonical` and `nurse_canonical`. In
Condition C the student records what she said; the nurse records the
bridged version she actually received. Conditions A, B, D are
unchanged in behaviour (the two histories remain identical there).

#### Bug 2 — Judge blinding leak via speaker labels

**Symptom.** In v1.0.0, the Judge prompt was constructed by formatting
the full transcript with explicit speaker labels including
`[STUDENT_RAW]`, `[NURSE_RAW]`, `[MEDIATOR→STUDENT]`, and
`[MEDIATOR→NURSE]`. These labels were a one-to-one fingerprint of the
experimental condition. The Judge prompt nominally claimed
"You do NOT know which experimental condition produced the transcript",
and Section 3.5 of the manuscript claimed "all condition identifiers
were stripped from the transcript before submission". Both statements
were inconsistent with the implementation: the Judge could
unambiguously identify every condition from label patterns alone.
An unknown amount of upward bias toward mediated conditions cannot
be ruled out for the v1.0.0 data.

**Fix.** Normalised transcript labels so that all utterances visible
to the Judge use only `student` or `nurse` tags. Mediator coaching
messages (Conditions B/D) and bridge actions (Condition C) are
retained in the database as `mediator_coach_*` and
`mediator_internal_*` entries for audit, but are filtered out before
the transcript reaches the Judge. The structural shape of the
transcript seen by the Judge is now identical across all four
conditions; only the textual content differs (because coaching and
bridging affect what the agents say).

### Changed — headline numbers

Side-by-side comparison of the condition means (v1.0.0 vs. v2.0.0):

| Condition | v1.0.0 Mean (SD) | v2.0.0 Mean (SD) | Direction of change |
|---|---:|---:|---|
| A Control | 15.33 (4.05) | 14.96 (4.01) | similar |
| B Student Support | 18.09 (3.30) | 15.47 (4.14) | **substantially lower** |
| C Mediation | 17.44 (3.47) | 18.18 (2.95) | slightly higher |
| D Nurse Support | 16.73 (3.53) | 17.80 (3.44) | slightly higher |

Side-by-side comparison of model means:

| Model | v1.0.0 Mean (SD) | v2.0.0 Mean (SD) |
|---|---:|---:|
| Claude Sonnet 4.6 | 20.20 (2.48) | 19.87 (2.41) |
| GPT-4.1 mini | 16.67 (2.38) | 16.58 (2.63) |
| Gemini 2.5 Flash | 13.83 (3.04) | 13.35 (3.43) |

Side-by-side comparison of Kruskal-Wallis statistics:

| Factor | v1.0.0 H | v2.0.0 H | v1.0.0 η²_H | v2.0.0 η²_H |
|---|---:|---:|---:|---:|
| Actor model | 91.81 | 87.13 | 0.51 | 0.49 |
| Intervention | 13.73 | 21.00 | 0.08 | 0.12 |
| H ratio (model/condition) | 6.7-fold | 4.15-fold | — | — |

### Interpretation of the change

- The model-vs-condition variance asymmetry — the central qualitative
  finding of the paper — **survives the bug fixes**. Actor model
  identity still dominates intervention condition by a wide margin
  (~4-fold rather than ~7-fold).
- The relative effectiveness of the four intervention conditions
  changes meaningfully:
  - In v1.0.0, **Student Support (B)** appeared to be the strongest
    intervention (Δ +2.76, p = .003). Under the corrected v2.0.0
    code this was an artefact of the bug; in v2.0.0 Student Support
    is not significantly different from Control.
  - In v2.0.0, **Mediation (C) and Nurse Support (D)** are the two
    interventions with significant positive effects. These two share
    the property that they operate on the nurse/instructor side or on
    the structural channel between speakers, rather than on the
    student in isolation. This sharpens, rather than weakens, the
    paper's argument about structural vs. individual interventions.

### Added

- `code/verify_patch.py` — static, no-API check that v2.0.0 fixes are
  present in `experiment.py`.
- `data/data_v1.1.0.csv`, `data/stats_summary_v1.1.0.csv` — historical
  v1.0.0 outputs retained for transparency and side-by-side comparison.
- `results/kruskal_results.csv`, `results/dunn_results.csv` —
  detailed per-dimension statistical outputs.

### Updated

- `code/verify_paper_claims.py` — `PAPER_CLAIMS` and reference values
  updated from v1.0.0 (paper preprint) to v2.0.0 (submitted manuscript).
  Now also checks model-level means.
- `README.md` — headline table, layout description, replication
  instructions, model identifiers.

### Removed

- Dead variable `student_for_nurse` in `experiment.py`.
- Leaky speaker labels `[STUDENT_RAW]`, `[NURSE_RAW]`,
  `[MEDIATOR→STUDENT]`, `[MEDIATOR→NURSE]` in transcript records
  visible to the Judge (retained internally for audit).

### Schema

The SQLite schema is unchanged. The `canonical` column now stores
the student's perception history (equivalent to the nurse's in
Conditions A/B/D, and to the v1.0.0 history in those conditions).

---

## [1.0.0] — 2026-05-17

Initial public release accompanying preliminary preparation for IPSJ
Transactions on Digital Practices (TDP) Special Issue 2027.

### Included

- Complete experimental code (`experiment.py`, `analyze.py`, `pilot.py`)
- All prompts: Student / Nurse / 3 Mediator variants / Judge
- Session-level dataset: 180 sessions, 5 dimensions, judge rationales
- One-script verification of headline statistical claims

### Known issues (corrected in 2.0.0)

The two bugs documented in the v2.0.0 entry above were present in
v1.0.0. The v1.0.0 dataset (`data/data.csv` of that release; preserved
in v2.0.0 as `data/data_v1.1.0.csv`) reflects those bugs and **should
not be used to evaluate the interventions reported in the submitted
manuscript**. It is retained only as a historical record.
