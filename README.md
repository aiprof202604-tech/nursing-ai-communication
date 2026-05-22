# Multi-LLM In-Silico Evaluation of Generative AI for Student–Nurse Communication

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Reproducibility package for the paper:

>Tajima, H. (2026). Generative AI in Student–Nurse Clinical 
Communication: A Multi-LLM In-Silico Evaluation and Five Walls 
to 2027.* Under review, IPSJ Transactions on Digital Practices (TDP) Special Issue.

This repository contains the complete experimental code, all prompts, and the full session-level dataset (180 sessions) required to reproduce every quantitative result reported in the paper.

---

## 1. Study at a Glance

- **Design**: 3 scenarios × 4 conditions × 3 actor LLMs × 5 runs = **180 sessions**
- **Scenarios**: S1 Question Inhibition, S2 Error Feedback, S3 SBAR Under Pressure
- **Conditions**: A Control, B Student Support, C Mediation, D Nurse Support
- **Actor LLMs**: Claude Sonnet 4 (Anthropic), GPT-4.1 mini (OpenAI), Gemini 2.5 Flash (Google)
- **Independent Judge**: GPT-4.1 (blinded; different family from two of three actors)
- **Evaluation**: 5 dimensions (PS, CC, ER, LF, RC), 1–5 each, total 5–25
- **Ethics**: No human participants. All interactions are between LLM agents.

Headline result (condition means across all actors and scenarios):

| Condition | Mean Total | SD | Δ vs. Control | p (Dunn, Bonferroni) |
|---|---:|---:|---:|---:|
| A Control | 15.33 | 4.05 | — | — |
| B Student Support | 18.09 | 3.30 | +2.76 | **.003** |
| C Mediation | 17.44 | 3.47 | +2.11 | **.039** |
| D Nurse Support | 16.73 | 3.53 | +1.40 | .538 |

The dominant source of variance is **actor model identity**, not intervention condition (H ratio ≈ 6.7-fold; η²_H model = 0.51, condition = 0.08). See the paper for full discussion of the "Five Walls to 2027" framework.

---

## 2. Repository Layout

```
.
├── code/
│   ├── experiment.py            # main runner: sessions + judge evaluation
│   ├── analyze.py               # statistics (Kruskal-Wallis, Dunn) + figures
│   ├── verify_paper_claims.py   # one-line verification of headline numbers
│   ├── pilot.py                 # 6-session pilot for prompt validation
│   └── setup_check.py           # API connectivity + dependency check
├── data/
│   ├── data.csv                 # 180 session-level scores + judge rationales
│   └── stats_summary.csv        # descriptive statistics per cell
├── LICENSE                      # MIT
├── CITATION.cff                 # citation metadata
├── REFERENCES.md                # full verification of cited literature
├── requirements.txt
└── README.md                    # this file
```

---

## 3. Reproducing the Results

### 3.1 One-line verification of the headline claims (~3 seconds)

To confirm that the bundled dataset reproduces every numerical claim in Tables 1–2 and Sections 4.1–4.2 of the paper:

```bash
pip install pandas scipy
python code/verify_paper_claims.py
# Expected: "VERIFICATION PASSED: all condition cell statistics match the paper."
```

### 3.2 Reproducing the full analysis (no API calls, free, ~10 seconds)

The published statistical results and figures can be regenerated directly from `data/data.csv` — no API keys required.

```bash
pip install pandas scipy scikit-posthocs matplotlib seaborn
mkdir -p results
cp data/data.csv results/
python code/analyze.py
# Outputs appear in results/: stats_summary.csv, kruskal_results.csv,
# dunn_results.csv, and figures/*.png
```

### 3.3 Re-running the full experiment (API calls, ~$5–8 USD, ~2 hours)

> **Warning**: Re-running the experiment will produce numerically different scores. LLM outputs are stochastic; the seed/temperature controls available in commercial APIs do not guarantee bit-exact replication across runs or across model version updates. Use this path to validate the *qualitative* pattern (model > condition variance, B and C above A), not to reproduce specific cell means.

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIza..."

# Optional: confirm all three APIs respond
python code/setup_check.py

# Optional: 6-session smoke test (~5 min, ~$0.50)
python code/pilot.py

# Full run (auto-resumes from SQLite if interrupted)
python code/experiment.py run
python code/experiment.py judge
python code/experiment.py export   # writes results/data.csv
python code/analyze.py             # statistics and figures
```

---

## 4. Data Schema

`data/data.csv` — one row per session (n = 180):

| Column | Description |
|---|---|
| `session_id` | e.g. `S1_A_r01_claude` (scenario_condition_run_actorModel) |
| `scenario` | S1 / S2 / S3 |
| `condition` | A / B / C / D |
| `run` | 1–5 |
| `actor_model` | claude / gpt4mini / gemini |
| `PS` | Psychological Safety, 1–5 |
| `CC` | Communication Clarity, 1–5 |
| `ER` | Empathic Response, 1–5 |
| `LF` | Learning Facilitation, 1–5 |
| `RC` | Relationship Continuity, 1–5 |
| `total` | Sum of the five dimensions, 5–25 |
| `rationale` | Free-text rationale produced by the blinded GPT-4.1 judge |

`data/stats_summary.csv` — descriptive statistics by dimension × condition × actor_model.

---

## 5. Prompt Specifications

All experimental prompts are embedded as string constants in `code/experiment.py` and are reproduced unmodified from the live study:

- `STUDENT_BASE` — second-year nursing student persona (belongingness framework: Levett-Jones & Lathlean, 2009)
- `NURSE_BASE` — experienced preceptor under time pressure
- `MEDIATOR_COACH_STUDENT` — Condition B: AI coach visible to student only
- `MEDIATOR_BRIDGE` — Condition C: AI rewriter visible to both
- `MEDIATOR_COACH_NURSE` — Condition D: AI coach visible to nurse only
- `JUDGE_SYSTEM` — blinded GPT-4.1 evaluator with full rubric
- `SCENARIOS_TEXT` — S1 / S2 / S3 framings for student and nurse

Mediator and judge prompts are held identical across all conditions to avoid prompt-engineering confounds.

---

## 6. Ethics

This study involved **no human participants**. All sessions are between LLM agents. Institutional review board approval was not required and was not sought.

The repository contains no personally identifying information of any kind.

---

## 7. Citation

If you use this code or data, please cite both the article and this repository. Citation metadata in machine-readable form is available in `CITATION.cff`.

```bibtex
@article{tajima2026genai_nursing,
  author  = {Tajima, Hiroyuki},
  title   = {Generative {AI} for Student--Nurse Communication in
             Clinical Nursing Education: A Multi-{LLM} In-Silico
             Evaluation and Five Walls to Overcome by 2027},
  journal = {Journal of Information Processing},
  year    = {2026},
  note    = {Under review, IPSJ TDP Special Issue}
}
```

---

## 8. Contact

Hiroyuki Tajima, PhD
Faculty of Nursing, Shumei University
ORCID: [0000-0003-3817-4455](https://orcid.org/0000-0003-3817-4455)
Email: tajima [at] mailg.shumei-u.ac.jp

Issues and pull requests are welcome.

---

## 9. License

Code and data are released under the MIT License (see `LICENSE`).
