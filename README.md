# Multi-LLM In-Silico Evaluation of Generative AI for Student–Nurse Communication

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.1.0-brightgreen.svg)](./CHANGELOG.md)

Reproducibility package for the paper:

> Tajima, H. (2027). *Generative AI in Student–Nurse Clinical Communication: A Multi-LLM In-Silico Evaluation and Five Walls to 2027.* Journal of Information Processing, Vol.35. (Accepted to IPSJ Transactions on Digital Practices Vol.8 No.1 Special Issue; English papers are published as a preprint in TDP and as the version of record in JIP.)

This repository contains the complete experimental code, all prompts, and the full session-level dataset (180 sessions) required to reproduce every quantitative result reported in the paper.

---

## ⚠️ Important: Version 2.0.0 supersedes Version 1.0.0

The current release (**v2.0.0**) fixes two methodological bugs discovered during manuscript re-review on 2026-05-18. Both fixes materially change the headline results. See [`CHANGELOG.md`](./CHANGELOG.md) for the full account.

The submitted manuscript reflects **v2.0.0** numbers exclusively. The v1.0.0 dataset is retained as `data/data_v1.1.0.csv` for full transparency.

---

## 1. Study at a Glance

- **Design**: 3 scenarios × 4 conditions × 3 actor LLMs × 5 runs = **180 sessions**
- **Scenarios**: S1 Question Inhibition, S2 Error Feedback, S3 SBAR Under Pressure
- **Conditions**: A Control, B Student Support, C Mediation, D Nurse Support
- **Actor LLMs**: Claude Sonnet 4.6 (Anthropic), GPT-4.1 mini (OpenAI), Gemini 2.5 Flash (Google)
- **Independent Judge**: GPT-4.1 (blinded; transcript filtered to only `student` and `nurse` turns)
- **Evaluation**: 5 dimensions (PS, CC, ER, LF, RC), 1–5 each, total 5–25
- **Ethics**: No human participants. All interactions are between LLM agents. No IRB review required.

Headline result (condition means across all actors and scenarios, v2.0.0 dataset):

| Condition | Mean Total | SD | Δ vs. Control | p (Dunn, Bonferroni) |
|---|---:|---:|---:|---:|
| A Control | 14.96 | 4.01 | — | — |
| B Student Support | 15.47 | 4.14 | +0.51 | n.s. |
| C Mediation | 18.18 | 2.95 | +3.22 | **.002** |
| D Nurse Support | 17.80 | 3.44 | +2.84 | **.005** |

The dominant source of variance is **actor model identity**, not intervention condition (H = 87.13 model vs. 21.00 condition; η²_H = 0.49 vs. 0.12; ~4-fold ratio). See the paper for the "Five Walls to 2027" framework discussion.

To independently verify all the numbers above against the bundled data:

```bash
python code/verify_paper_claims.py
# Expected output: "VERIFICATION PASSED"
```

---

## 2. Repository Layout

```
.
├── README.md                  This file
├── CHANGELOG.md               Version history (v1.0.0 → v2.1.0)
├── CITATION.cff               Citation metadata
├── LICENSE                    MIT
├── REFERENCES.md              Bibliography (matches manuscript references.bib)
├── requirements.txt
│
├── code/
│   ├── experiment.py          Main orchestrator (180-session async runner)
│   ├── pilot.py               6-session smoke test (~5 min, ~$0.50)
│   ├── analyze.py             Statistical analysis (Kruskal-Wallis, Dunn)
│   ├── generate_figures_mono.py   Greyscale-safe figure generation
│   ├── setup_check.py         API connectivity probe
│   ├── verify_patch.py        Static check of v2.0.0 bug fixes
│   ├── verify_paper_claims.py Reproduce manuscript Table 2 from data.csv
│   ├── factorial_art_srh.py   ART + Scheirer–Ray–Hare factorial analysis (Section 4.3)
│   ├── supplementary_stats.py Cronbach's alpha / McDonald's omega; BH-FDR sensitivity (Sections 3.5–3.6)
│   ├── preservation_audit.py  Clinical information preservation audit of the 540 rewritten pairs (Section 4.6)
│   ├── export_transcripts.py  Export data/experiment.db to data/transcripts.jsonl
│   └── verify_db_export.py    Confirm data/experiment.db reproduces data/data.csv byte for byte
│
├── data/
│   ├── experiment.db          SQLite session database of the published run (2026-05-18): every
│   │                          dialogue turn, incl. raw and rewritten utterances; Judge scores
│   ├── transcripts.jsonl      The same 180 sessions as JSON Lines (no SQLite needed)
│   ├── data.csv               v2.0.0 dataset (180 sessions, matches paper; = export of experiment.db)
│   ├── data_v1.1.0.csv        Historical v1.0.0 dataset (retained for transparency)
│   ├── stats_summary.csv      v2.0.0 statistical summary
│   └── stats_summary_v1.1.0.csv  Historical
│
└── results/
    ├── data.csv               Copy of data/data.csv as produced by export
    ├── kruskal_results.csv    KW test outputs (all dimensions, both factors)
    ├── dunn_results.csv       Post-hoc pairwise comparisons (Bonferroni)
    ├── stats_summary.csv      Cell-level descriptives
    ├── S1_internal_consistency.csv          alpha / omega (Section 3.5)
    ├── S2_FDR_sensitivity_54_comparisons.csv BH-FDR sensitivity analysis (Section 3.6)
    ├── S3_factorial_ART_SRH.csv             ART and SRH results (Section 4.3)
    ├── preservation_audit_summary.csv       Section 4.6 totals by direction / scenario / actor
    └── preservation_audit_flagged.csv       Every lost or newly appearing item, with source and rewrite text

docs/
├── deployment_checklist.md    Five Walls Deployment Checklist, 42 items (26 Critical, 16 Recommended) — English
└── deployment_checklist_ja.md The same checklist — Japanese original
```

---

## 3. Quick Verification (No API Calls Required)

The pre-computed dataset is bundled. To reproduce the headline statistics:

```bash
pip install -r requirements.txt
python code/verify_paper_claims.py
```

Expected output: condition cells match paper Table 2; H_condition = 21.00, H_model = 87.13.

---

## 3b. Supplementary Analyses and Audit (v2.1.0, no API calls)

```bash
python code/factorial_art_srh.py   data/data.csv       results/   # Section 4.3 (asserts the paper's values)
python code/supplementary_stats.py data/data.csv       results/   # Sections 3.5-3.6
python code/preservation_audit.py  data/experiment.db  results/   # Section 4.6 (asserts the paper's numeral results)
python code/export_transcripts.py  data/experiment.db  data/transcripts.jsonl
python code/verify_db_export.py    data/experiment.db  data/data.csv
```

`data/experiment.db` is the database written by `code/experiment.py` during the published run (2026-05-18). `python code/verify_db_export.py data/experiment.db data/data.csv` runs the export query of `experiment.py` on it (no API keys needed) and confirms that it reproduces `data/data.csv` byte for byte. (`experiment.py` itself expects its database at `results/experiment.db` and the three API-key variables to be set.)

---

## 4. Full Replication (Requires API Access)

To rerun the experiment from scratch:

### Prerequisites

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIza..."
pip install -r requirements.txt
python code/setup_check.py   # confirm all three APIs respond
```

### Optional: Static patch verification

```bash
python code/verify_patch.py  # confirms v2.0.0 bug fixes present in experiment.py
```

### Smoke test (6 sessions, ~5 min, ~$0.50)

```bash
python code/pilot.py
```

### Full run (180 sessions, ~1–1.5 hours, ~$5–8)

```bash
python code/experiment.py run     # actor phase
python code/experiment.py judge   # judge phase
python code/experiment.py export  # writes results/data.csv
cp results/data.csv data/data.csv
python code/analyze.py            # writes results/kruskal_results.csv etc.
python code/generate_figures_mono.py
python code/verify_paper_claims.py
```

The run is resume-safe via SQLite (`results/experiment.db`). Interrupting and re-running picks up where it left off.

---

## 5. Reproducibility Notes

- **Determinism**: LLM outputs are non-deterministic. We use `temperature = 0.8` for the actor and Mediator agents and `temperature = 0.2` for the judge (as set in `code/experiment.py` and reported in the paper) to balance ecological validity with judgment stability. Cell means typically reproduce within ±0.5 across independent runs; significance directions are stable.
- **Model versions used in the published run** (frozen 2026-05-18):
  - `claude-sonnet-4-6` (Anthropic)
  - `gpt-4.1-mini-2025-04-14` (OpenAI, actor)
  - `gpt-4.1-2025-04-14` (OpenAI, judge)
  - `gemini-2.5-flash` (Google)
- **Provider note**: One of the actor models discontinued between protocol design and execution; see manuscript Section 5.6 Practice 1.

---

## 6. Citation

If you use this code or data, please cite:

```bibtex
@article{tajima2026genai,
  author  = {Tajima, Hiroyuki},
  title   = {Generative {AI} in Student--Nurse Clinical Communication:
             A Multi-{LLM} In-Silico Evaluation and Five Walls to 2027},
  journal = {Journal of Information Processing},
  volume  = {35},
  year    = {2027},
  note    = {Accepted to IPSJ Transactions on Digital Practices Vol.8 No.1 Special Issue}
}
```

Software archive (this release): see `CITATION.cff` for the latest Zenodo DOI.

---

## 7. License

MIT License. See [`LICENSE`](./LICENSE).

---

## 8. Contact

Hiroyuki Tajima
Faculty of Nursing, Shumei University
1-1 Daigaku-cho, Yachiyo, Chiba 276-0003, Japan
Email: tajima@mailg.shumei-u.ac.jp
ORCID: [0000-0003-3817-4455](https://orcid.org/0000-0003-3817-4455)
