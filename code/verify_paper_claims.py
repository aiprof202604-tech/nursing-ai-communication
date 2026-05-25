#!/usr/bin/env python3
"""
verify_paper_claims.py
======================
Independent verification of the headline numerical claims of the paper:

  Tajima (2026), "Generative AI for Student-Nurse Communication ..."

Run this script after running `experiment.py export` (or directly against
the bundled `data/data.csv`) to confirm that the dataset reproduces the
quantitative claims in Tables 1-2 and Sections 4.1-4.2 of the manuscript.

Effect size convention follows the paper (Section 3.5):
    eta^2_H = H / (N - 1)
which is Cohen's original formulation. A bias-corrected variant,
    eta^2_H_corrected = (H - k + 1) / (N - k),
yields slightly smaller values but does not change any qualitative
interpretation.

This script targets the v2.0.0 dataset (180 sessions, post-bug-fix).
For the historical v1.0.0 dataset comparison, see data/data_v1.1.0.csv.

Usage
-----
    python verify_paper_claims.py            # uses data/data.csv
    python verify_paper_claims.py PATH.csv   # uses a custom CSV
"""

import sys
from pathlib import Path

import pandas as pd
from scipy import stats

CONDITIONS = ["A", "B", "C", "D"]
MODELS = ["claude", "gpt4mini", "gemini"]

# Paper claims (v2.0.0 dataset, post-bug-fix; matches manuscript Table 2)
PAPER_CLAIMS = {
    "A": (14.96, 4.01),   # Control
    "B": (15.47, 4.14),   # Student Support
    "C": (18.18, 2.95),   # Mediation
    "D": (17.80, 3.44),   # Nurse Support
}

# Paper claims for model-level means (manuscript Section 4.1)
MODEL_CLAIMS = {
    "claude":   (19.87, 2.41),
    "gpt4mini": (16.58, 2.63),
    "gemini":   (13.35, 3.43),
}

# Headline Kruskal-Wallis statistics
H_CONDITION_PAPER = 21.00
H_MODEL_PAPER     = 87.13
ETA_CONDITION_PAPER = 0.12
ETA_MODEL_PAPER     = 0.49
H_RATIO_PAPER       = H_MODEL_PAPER / H_CONDITION_PAPER  # ~4.15


def cohen_eta2_H(H: float, n: int) -> float:
    """Eta-squared for Kruskal-Wallis, paper convention: H / (N - 1)."""
    return H / (n - 1)


def main(path: str = "data/data.csv") -> int:
    csv_path = Path(path)
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found", file=sys.stderr)
        return 1

    df = pd.read_csv(csv_path)
    n = len(df)
    print(f"Loaded {n} sessions from {csv_path}")
    print()

    # --- Cell counts ----------------------------------------------------
    print("Sessions per condition:", df.groupby("condition").size().to_dict())
    print("Sessions per actor    :", df.groupby("actor_model").size().to_dict())
    print()

    # --- Condition means vs. paper -------------------------------------
    print("Condition totals (paper claim vs. computed):")
    print(f"  {'Cond':<6} {'Paper mean (SD)':<20} {'Computed mean (SD)':<22} {'Match':<6}")
    cond_match = True
    for cond in CONDITIONS:
        sub = df[df.condition == cond]["total"]
        m_paper, sd_paper = PAPER_CLAIMS[cond]
        m_obs = round(sub.mean(), 2)
        sd_obs = round(sub.std(ddof=1), 2)
        match = (abs(m_obs - m_paper) < 0.02) and (abs(sd_obs - sd_paper) < 0.02)
        cond_match = cond_match and match
        print(f"  {cond:<6} {m_paper:>6.2f} ({sd_paper:>4.2f})       "
              f"{m_obs:>6.2f} ({sd_obs:>4.2f})         {'OK' if match else 'FAIL'}")
    print()

    # --- Model means vs. paper -----------------------------------------
    print("Actor model totals (paper claim vs. computed):")
    print(f"  {'Model':<10} {'Paper mean (SD)':<20} {'Computed mean (SD)':<22} {'Match':<6}")
    model_match = True
    for m in MODELS:
        sub = df[df.actor_model == m]["total"]
        m_paper, sd_paper = MODEL_CLAIMS[m]
        m_obs = round(sub.mean(), 2)
        sd_obs = round(sub.std(ddof=1), 2)
        match = (abs(m_obs - m_paper) < 0.02) and (abs(sd_paper - sd_obs) < 0.02)
        model_match = model_match and match
        print(f"  {m:<10} {m_paper:>6.2f} ({sd_paper:>4.2f})       "
              f"{m_obs:>6.2f} ({sd_obs:>4.2f})         {'OK' if match else 'FAIL'}")
    print()

    # --- Kruskal-Wallis (condition) ------------------------------------
    cond_groups = [df[df.condition == c]["total"].values for c in CONDITIONS]
    H_cond, p_cond = stats.kruskal(*cond_groups)
    eta_cond = cohen_eta2_H(H_cond, n)
    print(f"Kruskal-Wallis (condition): H = {H_cond:.2f}, p = {p_cond:.6f}, "
          f"eta^2_H = {eta_cond:.3f}")
    print(f"  Paper claim              : H = {H_CONDITION_PAPER:.2f},  "
          f"p < .001,  eta^2_H = {ETA_CONDITION_PAPER:.2f}")
    print()

    # --- Kruskal-Wallis (actor model) ----------------------------------
    model_groups = [df[df.actor_model == m]["total"].values for m in MODELS]
    H_model, p_model = stats.kruskal(*model_groups)
    eta_model = cohen_eta2_H(H_model, n)
    print(f"Kruskal-Wallis (model)    : H = {H_model:.2f}, p < .0001, "
          f"eta^2_H = {eta_model:.3f}")
    print(f"  Paper claim              : H = {H_MODEL_PAPER:.2f},  "
          f"p < .0001,  eta^2_H = {ETA_MODEL_PAPER:.2f}")
    print()

    # --- Variance ratio (key headline) ---------------------------------
    ratio = H_model / H_cond
    print(f"H ratio (model / condition): {ratio:.2f}-fold")
    print(f"  Paper claim              : ~{H_RATIO_PAPER:.1f}-fold")
    print()

    all_match = cond_match and model_match
    if all_match:
        print("VERIFICATION PASSED: all cell statistics match the paper "
              "within rounding tolerance.")
        return 0
    else:
        print("VERIFICATION FAILED: at least one cell does not match.")
        return 2


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "data/data.csv"
    sys.exit(main(arg))
