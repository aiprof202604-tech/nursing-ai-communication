#!/usr/bin/env python3
"""
Monotone (grayscale) versions of figures — IPSJ print-safe.

Strategy:
- Figure 1 (heatmap): use 'Greys' colormap; same data, same layout.
- Figure 2 (boxplot): distinguish models by hatch patterns + grey shades
  (no chromatic information needed). Patterns: //// (claude), \\\\ (gpt), .... (gemini)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path

mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8.5,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7,
    "legend.title_fontsize": 7.5,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.unicode_minus": True,
    "hatch.linewidth": 0.5,
})

MODEL_ORDER = ["claude", "gpt4mini", "gemini"]
MODEL_LABEL = {
    "claude":   "Claude Sonnet 4",
    "gpt4mini": "GPT-4.1 mini",
    "gemini":   "Gemini 2.5 Flash",
}
# Grayscale shades — dark/medium/light
MODEL_GRAY = {
    "claude":   "#2D2D2D",  # dark
    "gpt4mini": "#7F7F7F",  # medium
    "gemini":   "#CCCCCC",  # light
}
MODEL_HATCH = {
    "claude":   "",        # solid dark — no hatch needed for darkest
    "gpt4mini": "////",    # diagonal — distinguishes from solid dark
    "gemini":   "....",    # dots — distinguishes lightest from white
}
COND_ORDER = ["A", "B", "C", "D"]
COND_LABEL_FULL = {
    "A": "Control",
    "B": "Student Support",
    "C": "Mediation",
    "D": "Nurse Support",
}
DIM_ORDER = ["PS", "CC", "ER", "LF", "RC"]

df = pd.read_csv("/home/claude/figures/data.csv")
OUTDIR = Path("/home/claude/figures/output")

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 2 (heatmap) — Greyscale
# ════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.5),
                        gridspec_kw={"wspace": 0.10, "left": 0.13, "right": 0.90,
                                     "bottom": 0.22, "top": 0.82})

pivots = {}
for model in MODEL_ORDER:
    sub = df[df["actor_model"] == model]
    p = sub.groupby("condition")[DIM_ORDER].mean()
    p = p.reindex(COND_ORDER)
    pivots[model] = p

vmin, vmax = 1.0, 5.0
# 'Greys' colormap: low=white, high=black. Inverted because higher score 
# means better — we want higher=darker for stronger visual presence.
# But IPSJ-style typically uses light=low, dark=high for monochrome heatmaps.
cmap = plt.cm.Greys

for idx, model in enumerate(MODEL_ORDER):
    ax = axes[idx]
    pivot = pivots[model]
    im = ax.imshow(pivot.values, aspect="auto", cmap=cmap,
                   vmin=vmin, vmax=vmax, interpolation="nearest")

    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            # Background grayscale level: normalized 0..1
            bg = (val - vmin) / (vmax - vmin)
            # In Greys colormap, bg=0 is white, bg=1 is black
            # Switch text color at bg=0.55
            txt_color = "white" if bg > 0.55 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    color=txt_color, fontsize=7.5)

    ax.set_xticks(range(len(DIM_ORDER)))
    ax.set_xticklabels(DIM_ORDER, fontsize=7.5)
    ax.set_yticks(range(len(COND_ORDER)))
    if idx == 0:
        ax.set_yticklabels([COND_LABEL_FULL[c] for c in COND_ORDER], fontsize=7.5)
    else:
        ax.set_yticklabels([])
    ax.tick_params(axis="both", which="both", length=0)
    ax.set_title(MODEL_LABEL[model], fontsize=8.5, pad=6)

    ax.text(-0.55 if idx == 0 else -0.05, 1.16, chr(ord("a")+idx),
            transform=ax.transAxes, fontsize=10, fontweight="bold",
            va="top", ha="left")

    for spine in ax.spines.values():
        spine.set_visible(False)

fig.text(0.5, 0.04, "Evaluation dimension", ha="center", fontsize=8)
axes[0].set_ylabel("Intervention condition", fontsize=8, labelpad=3)

cbar_ax = fig.add_axes([0.92, 0.22, 0.012, 0.60])
cbar = fig.colorbar(im, cax=cbar_ax)
cbar.set_label("Mean score (1–5)", fontsize=7.5, labelpad=4)
cbar.ax.tick_params(labelsize=7, length=2)
cbar.outline.set_linewidth(0.4)

fig.savefig(OUTDIR / "figure1_v4_mono.pdf", dpi=600, bbox_inches="tight", pad_inches=0.02)
fig.savefig(OUTDIR / "figure1_v4_mono.png", dpi=300, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
print("Figure 1 (heatmap) monotone saved")

# ════════════════════════════════════════════════════════════════════════════
# FIGURE 1 (boxplot) — Greyscale with hatches
# ════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7.0, 3.3),
                       gridspec_kw={"left": 0.09, "right": 0.99, "top": 0.92, "bottom": 0.13})

n_cond = len(COND_ORDER)
n_model = len(MODEL_ORDER)
box_w = 0.22
sep = 0.04
group_w = n_model * box_w + (n_model - 1) * sep
cond_x = np.arange(n_cond)

rng = np.random.default_rng(42)

for ci, cond in enumerate(COND_ORDER):
    for mi, model in enumerate(MODEL_ORDER):
        sub = df[(df["condition"] == cond) & (df["actor_model"] == model)]["total"].values
        x_offset = -group_w/2 + box_w/2 + mi * (box_w + sep)
        x = cond_x[ci] + x_offset

        bp = ax.boxplot([sub], positions=[x], widths=box_w,
                        patch_artist=True, showfliers=False,
                        medianprops=dict(color="black", linewidth=1.0),
                        whiskerprops=dict(color="black", linewidth=0.7),
                        capprops=dict(color="black", linewidth=0.7),
                        boxprops=dict(linewidth=0.6))
        for patch in bp["boxes"]:
            patch.set_facecolor(MODEL_GRAY[model])
            patch.set_edgecolor("black")
            if MODEL_HATCH[model]:
                patch.set_hatch(MODEL_HATCH[model])

        # Mean diamond (white-filled, black edge) — visible on any grey
        ax.scatter([x], [np.mean(sub)], marker="D", s=18,
                  facecolor="white", edgecolor="black", linewidth=0.7,
                  zorder=4)

        # Strip overlay — black points with white edge so visible on any grey
        jitter = rng.uniform(-box_w*0.30, box_w*0.30, size=len(sub))
        ax.scatter(np.full(len(sub), x) + jitter, sub,
                  s=7, facecolor="black", edgecolor="white",
                  linewidth=0.25, alpha=0.85, zorder=3)

ax.set_xticks(cond_x)
ax.set_xticklabels([COND_LABEL_FULL[c] for c in COND_ORDER], fontsize=8)
ax.set_xlim(-0.55, n_cond - 0.45)
ax.set_ylim(4, 29)
ax.set_yticks(range(5, 26, 5))
ax.set_ylabel("Total communication score (range 5–25)", fontsize=8)
ax.set_xlabel("Intervention condition", fontsize=8, labelpad=4)

ax.grid(axis="y", linestyle=":", linewidth=0.4, alpha=0.5, zorder=0)
ax.set_axisbelow(True)

def sig_bracket(ax, x1, x2, y, label, lift=0.5):
    ax.plot([x1, x1, x2, x2], [y, y+lift, y+lift, y],
            lw=0.7, color="black", clip_on=False)
    ax.text((x1+x2)/2, y+lift+0.05, label, ha="center", va="bottom",
            fontsize=9)

sig_bracket(ax, cond_x[0], cond_x[1], 26.2, "**", lift=0.5)
sig_bracket(ax, cond_x[0], cond_x[2], 27.7, "*",  lift=0.5)

from matplotlib.patches import Patch
legend_handles = []
for m in MODEL_ORDER:
    p = Patch(facecolor=MODEL_GRAY[m], edgecolor="black", linewidth=0.6,
              hatch=MODEL_HATCH[m] if MODEL_HATCH[m] else None,
              label=MODEL_LABEL[m])
    legend_handles.append(p)
legend_handles.append(
    plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="white",
               markeredgecolor="black", markersize=6, label="Mean")
)

ax.legend(handles=legend_handles, loc="upper right",
         bbox_to_anchor=(0.99, 0.985),
         frameon=True, framealpha=0.95, edgecolor="lightgrey",
         ncol=1, columnspacing=0.6, handletextpad=0.5,
         fontsize=7, borderpad=0.4)

fig.savefig(OUTDIR / "figure2_v4_mono.pdf", dpi=600, bbox_inches="tight", pad_inches=0.02)
fig.savefig(OUTDIR / "figure2_v4_mono.png", dpi=300, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
print("Figure 2 (boxplot) monotone saved")
