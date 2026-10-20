"""Supplementary analyses promised in Sections 3.5-3.6 of TDP-315:
(1) internal consistency (Cronbach's alpha, McDonald's omega) of the five
    Judge dimensions from session-level scores;
(2) Benjamini-Hochberg FDR sensitivity analysis across the 54 pairwise
    Dunn comparisons (6 outcomes x [6 condition pairs + 3 actor pairs]).
Usage: python3 -I supplementary_stats.py <data.csv> <outdir>
"""
import sys
import itertools
import numpy as np
import pandas as pd
import scikit_posthocs as sp
from statsmodels.stats.multitest import multipletests

d = pd.read_csv(sys.argv[1])
out = sys.argv[2]
ITEMS = ["PS", "CC", "ER", "LF", "RC"]
X = d[ITEMS].to_numpy(float)


def cronbach_alpha(x):
    k = x.shape[1]
    return k / (k - 1) * (1 - x.var(axis=0, ddof=1).sum() / x.sum(axis=1).var(ddof=1))


def mcdonald_omega(x):
    """Omega-total from a one-factor model fitted by principal-axis
    factoring on the item correlation matrix (standardised items)."""
    r = np.corrcoef(x, rowvar=False)
    h2 = 1 - 1 / np.diag(np.linalg.inv(r))  # SMC starting communalities
    for _ in range(500):
        rr = r.copy()
        np.fill_diagonal(rr, h2)
        w, v = np.linalg.eigh(rr)
        lam = v[:, -1] * np.sqrt(w[-1])
        new = lam ** 2
        if np.max(np.abs(new - h2)) < 1e-8:
            break
        h2 = new
    lam = np.abs(lam)
    return lam.sum() ** 2 / (lam.sum() ** 2 + (1 - lam ** 2).sum()), lam


def boot_ci(fn, x, B=2000, seed=20261020):
    rng = np.random.default_rng(seed)
    n = len(x)
    vals = [fn(x[rng.integers(0, n, n)]) for _ in range(B)]
    return np.percentile(vals, [2.5, 97.5])


a = cronbach_alpha(X)
o, lam = mcdonald_omega(X)
a_ci = boot_ci(cronbach_alpha, X)
o_ci = boot_ci(lambda z: mcdonald_omega(z)[0], X)
rel = pd.DataFrame(
    {
        "statistic": ["cronbach_alpha", "mcdonald_omega_total"],
        "estimate": [round(a, 3), round(o, 3)],
        "boot95_low": [round(a_ci[0], 3), round(o_ci[0], 3)],
        "boot95_high": [round(a_ci[1], 3), round(o_ci[1], 3)],
        "n_sessions": [len(d)] * 2,
    }
)
rel.to_csv(f"{out}/S1_internal_consistency.csv", index=False)
print(rel.to_string(index=False))
print("one-factor loadings:", dict(zip(ITEMS, lam.round(3))))
print("inter-item r:\n", pd.DataFrame(np.corrcoef(X, rowvar=False), index=ITEMS, columns=ITEMS).round(2))

rows = []
for outcome in ITEMS + ["total"]:
    for factor, levels in (("condition", "ABCD"), ("actor_model", ["claude", "gemini", "gpt4mini"])):
        raw = sp.posthoc_dunn(d, val_col=outcome, group_col=factor, p_adjust=None)
        bon = sp.posthoc_dunn(d, val_col=outcome, group_col=factor, p_adjust="bonferroni")
        for g1, g2 in itertools.combinations(levels, 2):
            rows.append(dict(outcome=outcome, factor=factor, group1=g1, group2=g2,
                             p_unadjusted=raw.loc[g1, g2], p_bonferroni_within=bon.loc[g1, g2]))
t = pd.DataFrame(rows)
assert len(t) == 54, len(t)
t["q_BH_across54"] = multipletests(t.p_unadjusted, method="fdr_bh")[1]
t["sig_bonferroni_within"] = t.p_bonferroni_within < 0.05
t["sig_BH_across54"] = t.q_BH_across54 < 0.05
t["agree"] = t.sig_bonferroni_within == t.sig_BH_across54
for c in ("p_unadjusted", "p_bonferroni_within", "q_BH_across54"):
    t[c] = t[c].map(lambda v: float(f"{v:.6g}"))
t.to_csv(f"{out}/S2_FDR_sensitivity_54_comparisons.csv", index=False)
print("\nBH vs within-dimension Bonferroni: agree on", int(t.agree.sum()), "of 54")
print(t[~t.agree].to_string(index=False))
