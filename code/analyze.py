#!/usr/bin/env python3
"""
Analyze In-Silico Experiment Results
=====================================
Reads results/data.csv produced by experiment.py export.

Outputs
-------
results/stats_summary.csv    descriptive statistics per condition × model
results/kruskal_results.csv  Kruskal-Wallis H and p-values per dimension
results/dunn_results.csv     Dunn post-hoc pairwise comparisons (Bonferroni)
results/figures/             PNG box-plots (one per dimension)

Requirements
------------
pip install pandas scipy scikit-posthocs matplotlib seaborn
"""

import csv
import warnings
from pathlib import Path

import pandas as pd
import scipy.stats as stats
import scikit_posthocs as sp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# ── Config ────────────────────────────────────────────────────────────────────
DATA_PATH   = Path("results/data.csv")
OUT_DIR     = Path("results")
FIG_DIR     = OUT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

DIMENSIONS  = ["PS", "CC", "ER", "LF", "RC", "total"]
CONDITIONS  = ["A", "B", "C", "D"]
MODELS      = ["claude", "gpt4mini", "gemini"]
SCENARIOS   = ["S1", "S2", "S3"]

COND_LABELS = {
    "A": "Control",
    "B": "Student\nSupport",
    "C": "Mediation",
    "D": "Nurse\nSupport",
}
MODEL_LABELS = {
    "claude"  : "Claude\nSonnet",
    "gpt4mini": "GPT-4.1\nmini",
    "gemini"  : "Gemini\n2.5 Flash",
}
DIM_LABELS = {
    "PS": "Psychological Safety",
    "CC": "Communication Clarity",
    "ER": "Empathic Response",
    "LF": "Learning Facilitation",
    "RC": "Relationship Continuity",
    "total": "Total Score",
}

# ── Load Data ─────────────────────────────────────────────────────────────────
def load() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    for dim in DIMENSIONS:
        df[dim] = pd.to_numeric(df[dim], errors="coerce")
    df = df.dropna(subset=DIMENSIONS)
    print(f"Loaded {len(df)} evaluated sessions.")
    return df

# ── Descriptive Statistics ────────────────────────────────────────────────────
def descriptive(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dim in DIMENSIONS:
        for cond in CONDITIONS:
            for model in MODELS:
                sub = df[(df["condition"] == cond) & (df["actor_model"] == model)][dim]
                rows.append({
                    "dimension" : dim,
                    "condition" : cond,
                    "actor_model": model,
                    "n"         : len(sub),
                    "mean"      : round(sub.mean(), 3),
                    "sd"        : round(sub.std(ddof=1), 3),
                    "median"    : round(sub.median(), 3),
                    "min"       : sub.min(),
                    "max"       : sub.max(),
                })
    result = pd.DataFrame(rows)
    out = OUT_DIR / "stats_summary.csv"
    result.to_csv(out, index=False)
    print(f"Descriptive stats → {out}")
    return result

# ── Kruskal-Wallis Test ───────────────────────────────────────────────────────
def kruskal_by_condition(df: pd.DataFrame) -> pd.DataFrame:
    """Test whether scores differ across conditions (A/B/C/D), per dimension."""
    rows = []
    for dim in DIMENSIONS:
        groups = [df[df["condition"] == c][dim].dropna().values for c in CONDITIONS]
        h, p = stats.kruskal(*groups)
        rows.append({
            "dimension": dim,
            "factor"   : "condition",
            "H_stat"   : round(h, 4),
            "p_value"  : round(p, 6),
            "sig"      : "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns",
        })

    for dim in DIMENSIONS:
        groups = [df[df["actor_model"] == m][dim].dropna().values for m in MODELS]
        h, p = stats.kruskal(*groups)
        rows.append({
            "dimension": dim,
            "factor"   : "actor_model",
            "H_stat"   : round(h, 4),
            "p_value"  : round(p, 6),
            "sig"      : "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns",
        })

    result = pd.DataFrame(rows)
    out = OUT_DIR / "kruskal_results.csv"
    result.to_csv(out, index=False)
    print(f"Kruskal-Wallis → {out}")
    return result

# ── Dunn Post-hoc ─────────────────────────────────────────────────────────────
def dunn_posthoc(df: pd.DataFrame) -> None:
    rows = []
    for dim in DIMENSIONS:
        # By condition
        p_matrix = sp.posthoc_dunn(
            df, val_col=dim, group_col="condition", p_adjust="bonferroni"
        )
        for c1 in CONDITIONS:
            for c2 in CONDITIONS:
                if c1 < c2:
                    p = p_matrix.loc[c1, c2]
                    rows.append({
                        "dimension": dim, "factor": "condition",
                        "group1": c1, "group2": c2,
                        "p_adj": round(p, 6),
                        "sig": "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns",
                    })

        # By model
        p_matrix_m = sp.posthoc_dunn(
            df, val_col=dim, group_col="actor_model", p_adjust="bonferroni"
        )
        for m1 in MODELS:
            for m2 in MODELS:
                if m1 < m2:
                    p = p_matrix_m.loc[m1, m2]
                    rows.append({
                        "dimension": dim, "factor": "actor_model",
                        "group1": m1, "group2": m2,
                        "p_adj": round(p, 6),
                        "sig": "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns",
                    })

    out = OUT_DIR / "dunn_results.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Dunn post-hoc → {out}")

# ── Box Plots ─────────────────────────────────────────────────────────────────
def plot_by_condition(df: pd.DataFrame) -> None:
    """One figure per dimension, x=condition, hue=actor_model."""
    palette = {"claude": "#2563eb", "gpt4mini": "#16a34a", "gemini": "#dc2626"}

    for dim in DIMENSIONS:
        fig, ax = plt.subplots(figsize=(8, 5))
        data_plot = df[["condition", "actor_model", dim]].copy()
        data_plot["Condition"] = data_plot["condition"].map(COND_LABELS)
        data_plot["Model"] = data_plot["actor_model"].map(MODEL_LABELS)

        sns.boxplot(
            data=data_plot,
            x="Condition", y=dim, hue="Model",
            palette=list(palette.values()),
            order=[COND_LABELS[c] for c in CONDITIONS],
            flierprops=dict(marker="o", markersize=4, alpha=0.5),
            ax=ax,
        )
        ax.set_ylim(0.5, 5.5 if dim != "total" else 25.5)
        ax.set_xlabel("Condition", fontsize=12)
        ax.set_ylabel(DIM_LABELS[dim], fontsize=12)
        ax.set_title(f"{DIM_LABELS[dim]} by Condition and Actor Model", fontsize=13)
        ax.legend(title="Actor Model", fontsize=9, title_fontsize=9)
        sns.despine()
        plt.tight_layout()
        path = FIG_DIR / f"box_{dim}_by_condition.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"Figure → {path}")


def plot_by_scenario(df: pd.DataFrame) -> None:
    """One figure per dimension, x=scenario, hue=condition."""
    for dim in DIMENSIONS:
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.boxplot(
            data=df, x="scenario", y=dim, hue="condition",
            order=SCENARIOS, hue_order=CONDITIONS,
            flierprops=dict(marker="o", markersize=4, alpha=0.5),
            ax=ax,
        )
        ax.set_ylim(0.5, 5.5 if dim != "total" else 25.5)
        ax.set_xlabel("Scenario", fontsize=12)
        ax.set_ylabel(DIM_LABELS[dim], fontsize=12)
        ax.set_title(f"{DIM_LABELS[dim]} by Scenario and Condition", fontsize=13)
        ax.legend(title="Condition", fontsize=9, title_fontsize=9)
        sns.despine()
        plt.tight_layout()
        path = FIG_DIR / f"box_{dim}_by_scenario.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"Figure → {path}")


def plot_heatmap(df: pd.DataFrame) -> None:
    """Mean score heatmap: condition × dimension, per model."""
    for model in MODELS:
        sub = df[df["actor_model"] == model]
        pivot = sub.groupby("condition")[DIMENSIONS].mean().round(2)
        pivot.index = [COND_LABELS[c].replace("\n", " ") for c in pivot.index]
        pivot.columns = [DIM_LABELS[d] for d in pivot.columns]

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.heatmap(
            pivot, annot=True, fmt=".2f", cmap="YlGnBu",
            vmin=1, vmax=5, ax=ax,
            linewidths=0.5, cbar_kws={"label": "Mean Score"},
        )
        ax.set_title(f"Mean Scores by Condition — {MODEL_LABELS[model].replace(chr(10),' ')}", fontsize=13)
        ax.set_ylabel("")
        plt.tight_layout()
        path = FIG_DIR / f"heatmap_{model}.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"Heatmap → {path}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    warnings.filterwarnings("ignore")
    if not DATA_PATH.exists():
        print(f"ERROR: {DATA_PATH} not found. Run 'python experiment.py export' first.")
        return

    df = load()
    if len(df) == 0:
        print("No evaluated data found. Exiting.")
        return

    print("\n── Descriptive Statistics ──────────────────────")
    desc = descriptive(df)
    print(desc.groupby(["dimension", "condition"])["mean"].mean().round(3).to_string())

    print("\n── Kruskal-Wallis Tests ────────────────────────")
    kw = kruskal_by_condition(df)
    print(kw.to_string(index=False))

    print("\n── Dunn Post-hoc (Bonferroni) ──────────────────")
    dunn_posthoc(df)

    print("\n── Generating Figures ──────────────────────────")
    plot_by_condition(df)
    plot_by_scenario(df)
    plot_heatmap(df)

    print("\nAnalysis complete. All outputs in results/")


if __name__ == "__main__":
    main()
