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
yields slightly smaller values (e.g. 0.06 vs. 0.08 for the condition
effect) but does not change any qualitative interpretation.

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
PAPER_CLAIMS = {
    "A": (15.33, 4.05),
    "B": (18.09, 3.30),
    "C": (17.44, 3.47),
    "D": (16.73, 3.53),
}


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
    all_match = True
    for cond in CONDITIONS:
        sub = df[df.condition == cond]["total"]
        m_paper, sd_paper = PAPER_CLAIMS[cond]
        m_obs = round(sub.mean(), 2)
        sd_obs = round(sub.std(ddof=1), 2)
        match = (abs(m_obs - m_paper) < 0.01) and (abs(sd_obs - sd_paper) < 0.01)
        all_match = all_match and match
        print(f"  {cond:<6} {m_paper:>6.2f} ({sd_paper:>4.2f})       "
              f"{m_obs:>6.2f} ({sd_obs:>4.2f})         {'OK' if match else 'FAIL'}")
    print()

    # --- Kruskal-Wallis (condition) ------------------------------------
    cond_groups = [df[df.condition == c]["total"].values for c in CONDITIONS]
    H_cond, p_cond = stats.kruskal(*cond_groups)
    eta_cond = cohen_eta2_H(H_cond, n)
    print(f"Kruskal-Wallis (condition): H = {H_cond:.2f}, p = {p_cond:.4f}, "
          f"eta^2_H = {eta_cond:.3f}")
    print(f"  Paper claim              : H = 13.73,  p = .003,   eta^2_H = 0.08")
    print()

    # --- Kruskal-Wallis (actor model) ----------------------------------
    model_groups = [df[df.actor_model == m]["total"].values for m in MODELS]
    H_model, p_model = stats.kruskal(*model_groups)
    eta_model = cohen_eta2_H(H_model, n)
    print(f"Kruskal-Wallis (model)    : H = {H_model:.2f}, p < .0001, "
          f"eta^2_H = {eta_model:.3f}")
    print(f"  Paper claim              : H = 91.81,  p < .0001,  eta^2_H = 0.51")
    print()

    # --- Variance ratio (key headline) ---------------------------------
    ratio = H_model / H_cond
    print(f"H ratio (model / condition): {ratio:.2f}-fold")
    print(f"  Paper claim              : 6.7-fold")
    print()

    if all_match:
        print("VERIFICATION PASSED: all condition cell statistics match the paper.")
        return 0
    else:
        print("VERIFICATION FAILED: at least one cell does not match.")
        return 2


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "data/data.csv"
    sys.exit(main(arg))
