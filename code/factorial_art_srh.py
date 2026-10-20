"""Factorial analysis of the 3 (scenario) x 4 (condition) x 3 (actor model)
design reported in Section 4.3 of Tajima (TDP-315 / JIP).

* Aligned Rank Transform (ART; Wobbrock et al., CHI 2011): for every effect
  the response is aligned (cell residual + estimated effect), mid-ranked, and
  a full-factorial ANOVA with sum-to-zero contrasts is fitted; only the
  aligned effect's F is read off. Partial eta^2 = SS_effect/(SS_effect+SS_res).
* Scheirer-Ray-Hare (SRH): full-factorial ANOVA on ranks of the raw response;
  H = SS_effect / MS_total, referred to chi^2(df_effect).

Usage:  python3 code/factorial_art_srh.py data/data.csv results/
Writes: results/S3_factorial_ART_SRH.csv
"""
import sys
import itertools
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm

FACTORS = ["scenario", "condition", "actor_model"]


def art(df, y):
    cell = df.groupby(FACTORS)[y].transform("mean")
    resid = df[y] - cell
    grand = df[y].mean()
    effects = [e for r in range(1, 4) for e in itertools.combinations(FACTORS, r)]
    rows = []
    for eff in effects:
        est = 0.0
        for r in range(len(eff) + 1):  # inclusion-exclusion of marginal means
            for sub in itertools.combinations(eff, r):
                sign = (-1) ** (len(eff) - len(sub))
                est = est + sign * (df.groupby(list(sub))[y].transform("mean") if sub else grand)
        # round before ranking: floating-point noise (~1e-15) must not break exact ties
        d = df.assign(_ar=stats.rankdata(np.round(resid + est, 9)))  # mid-ranks for ties
        fit = smf.ols("_ar ~ " + " * ".join(f"C({f}, Sum)" for f in FACTORS), data=d).fit()
        tab = anova_lm(fit, typ=3)
        term = ":".join(f"C({f}, Sum)" for f in eff)
        ss_e, ss_r = tab.loc[term, "sum_sq"], tab.loc["Residual", "sum_sq"]
        rows.append(dict(method="ART", outcome=y, effect=" x ".join(eff),
                         df1=int(tab.loc[term, "df"]), df2=int(tab.loc["Residual", "df"]),
                         stat=round(tab.loc[term, "F"], 2), p=tab.loc[term, "PR(>F)"],
                         partial_eta2=round(ss_e / (ss_e + ss_r), 2)))
    return rows


def srh(df, y):
    d = df.assign(_r=stats.rankdata(df[y]))
    fit = smf.ols("_r ~ " + " * ".join(f"C({f}, Sum)" for f in FACTORS), data=d).fit()
    tab = anova_lm(fit, typ=2)
    ms_total = d["_r"].var(ddof=1)
    rows = []
    for term in tab.index[:-1]:
        H = tab.loc[term, "sum_sq"] / ms_total
        eff = " x ".join(t.split("(")[1].split(",")[0] for t in term.split(":"))
        rows.append(dict(method="SRH", outcome=y, effect=eff, df1=int(tab.loc[term, "df"]), df2=None,
                         stat=round(H, 2), p=stats.chi2.sf(H, tab.loc[term, "df"]), partial_eta2=None))
    return rows


if __name__ == "__main__":
    data = pd.read_csv(sys.argv[1])
    out = pd.DataFrame(art(data, "total") + srh(data, "total"))
    out["p"] = out["p"].map(lambda v: float(f"{v:.4g}"))
    out.to_csv(f"{sys.argv[2]}/S3_factorial_ART_SRH.csv", index=False)
    print(out.to_string(index=False))
    # values quoted in Section 4.3 of the paper
    get = lambda m, e: out[(out.method == m) & (out.effect == e)].iloc[0]
    assert get("ART", "actor_model").stat == 170.44
    assert get("ART", "condition").stat == 27.89
    assert get("ART", "scenario").stat == 1.27
    assert get("ART", "condition x actor_model").stat == 5.26
    assert get("SRH", "actor_model").stat == 87.13 and get("SRH", "condition").stat == 21.00
    assert get("SRH", "scenario").stat == 0.56
    print("\nAll factorial values quoted in Section 4.3 reproduced.")
