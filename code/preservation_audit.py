"""Clinical information preservation audit for Condition C (Mediation),
Section 4.6 of Tajima (TDP-315 / JIP).

Every utterance that the Mediator rewrote is compared with its source:
  student raw  -> bridged text delivered to the nurse   (direction S2N)
  nurse raw    -> bridged text delivered to the student (direction N2S)
45 sessions x 6 turns x 2 directions = 540 pairs. The procedure is purely
rule-based (no LLM is involved), so the audit of an LLM evaluation does not
itself rest on an LLM.

Extraction rules (applied to source and rewrite alike)
  * stage directions written as *...* are removed first;
  * chemical / device symbols whose digits are not quantities (O2, SpO2,
    CO2, ...) are removed before numerals are extracted;
  * clock times (e.g. 19:42) are kept whole as one value;
  * values are compared as DISTINCT sets per utterance, so a speaker's
    redundant repetition of a value is not scored as a loss.

Numerals    : every digit string (incl. decimals) after the rules above.
Concepts    : canonical clinical concepts from the lexicon below; synonyms
              map to one concept (e.g. "BP" and "blood pressure"), so a
              faithful paraphrase is not scored as a loss.

Outputs
  results/preservation_audit_summary.csv   totals by direction / scenario / actor
  results/preservation_audit_flagged.csv   every lost or newly appearing item,
                                           with the source and rewrite text
Usage
  python3 code/preservation_audit.py data/experiment.db results/
"""
import csv
import json
import re
import sqlite3
import sys
from collections import defaultdict

STAGE = re.compile(r"\*[^*]*\*")
CHEM = re.compile(r"\b(?:Sp?O2|SaO2|CO2|O2|PaO2|PaCO2|EtCO2|H2O|B12)\b", re.I)
TIME = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b")
NUM = re.compile(r"\d+(?:\.\d+)?")

# Canonical clinical concepts. Fixed before the audit was run; not tuned to
# any target value.
LEXICON = {
    # Acronyms are matched case-sensitively (so "met" or "good news" do not
    # count as MET or NEWS); ordinary words are matched case-insensitively.
    # medication
    "metoprolol": r"(?i:\bmetoprolol\b)",
    "beta-blocker": r"(?i:\bbeta[- ]?blockers?\b)",
    "formulation": r"(?i:\b(?:succinate|tartrate|extended[- ]release|immediate[- ]release)\b)",
    "medication": r"(?i:\b(?:medications?|meds|drugs?)\b)",
    "dose": r"(?i:\b(?:doses?|dosage|dosing)\b)",
    "milligram": r"(?<![A-Za-z])mg\b|(?i:\bmilligrams?\b)",
    "medication order": r"(?i:\b(?:orders?|ordered|prescription|prescribed|prescriber)\b)",
    "administration": r"(?i:\badminist\w*)",
    "indication": r"(?i:\bindications?\b)",
    "titration": r"(?i:\btitrat\w*)",
    "allergy": r"(?i:\ballerg\w*)",
    "intravenous": r"\bIV\b|(?i:\bintravenous\w*)",
    "fluids": r"(?i:\b(?:fluids?|bolus|saline)\b)",
    "pharmacy": r"(?i:\bpharmac\w*)",
    # observations
    "vital signs": r"(?i:\bvitals?\b|\bvital signs?\b|\bobs\b|\bobservations?\b)",
    "blood pressure": r"\bBP\b|(?i:\bblood pressures?\b|\bsystolic\b|\bdiastolic\b)",
    "hypotension": r"(?i:\bhypotens\w*)",
    "hypertension": r"(?i:\bhypertens\w*)",
    "heart rate": r"\bHR\b|(?i:\bheart rates?\b|\bpulse\b|\bbpm\b)",
    "tachycardia": r"(?i:\btachycard\w*)",
    "respiratory rate": r"\bRR\b|(?i:\brespiratory rates?\b|\bresp rate\b|\bbreaths\b)",
    "oxygen saturation": r"\bSpO2\b|\bO2 sats?\b|(?i:\bsats?\b|\bsaturations?\b|\bpulse ox\w*)",
    "oxygen therapy": r"\bO2\b(?! sat)|(?i:\boxygen\b|\bnon[- ]?rebreather\b|\bmask\b|\bnasal cannula\b|\blitres?\b|\bliters?\b)",
    "temperature": r"(?i:\btemp\b|\btemperatures?\b|\bfebrile\b|\bfever\b|\bpyrexi\w*)",
    "early warning score": r"\bNEWS2?\b|\bMEWS\b|(?i:\bearly warning\b)",
    "mental status": r"\bGCS\b|(?i:\bconfus\w*|\bmental status\b|\bdisorient\w*|\bdrows\w*)",
    "pallor": r"(?i:\bpale\b|\bpallor\b)",
    "diaphoresis": r"(?i:\bclammy\b|\bdiaphore\w*|\bsweat\w*)",
    "breath sounds": r"(?i:\bcrackles?\b|\bwheez\w*)",
    "chest pain": r"(?i:\bchest pain\b)",
    "urine output": r"(?i:\burine\b|\burinary\b|\boliguri\w*|\bcatheter\b)",
    "lactate": r"(?i:\blactate\b|\blactic\b)",
    "blood cultures": r"(?i:\bcultures?\b)",
    "sepsis": r"(?i:\bseps\w*|\bseptic\b)",
    "shock": r"(?i:\bshock\b)",
    "heart failure": r"\bCHF\b|(?i:\bheart failure\b)",
    "cardiac": r"(?i:\bcardiac\b)",
    "deterioration": r"(?i:\bdeteriorat\w*|\bworsening\b)",
    "baseline": r"(?i:\bbaseline\b)",
    # escalation and roles
    "physician": r"\bDr\b\.?|(?i:\bdoctors?\b|\bphysicians?\b|\bregistrar\b|\bmedical team\b|\bconsultant\b)",
    "rapid response": r"\bRRT\b|\bMET\b|(?i:\brapid response\b)",
    "escalation": r"(?i:\bescalat\w*)",
    # structured communication and documentation
    "SBAR": r"\bI?SBAR\b",
    "SOAP": r"\bSOAP\b",
    "assessment": r"(?i:\bassess\w*)",
    "recommendation": r"(?i:\brecommend\w*)",
    "subjective": r"(?i:\bsubjective\b)",
    "objective": r"(?i:\bobjective\b)",
    "care plan": r"(?i:\bplan\b)",
    "documentation": r"(?i:\bdocument\w*|\bchart(?:s|ing|ed)?\b|\bnotes?\b|\bentry\b|\bentries\b)",
    "handover": r"(?i:\bhandover\b|\bhand-?off\b|\bhand over\b)",
    "timestamp": r"(?i:\btimestamps?\b|\btime[- ]stamp\w*)",
    "specimen": r"(?i:\bspecimens?\b)",
    "label": r"(?i:\blabel\w*)",
    "protocol": r"(?i:\bprotocols?\b)",
    "patient location": r"(?i:\broom\b|\bbed\b)",
}
LEX = {k: re.compile(v) for k, v in LEXICON.items()}


def clean(text):
    return STAGE.sub(" ", text or "")


def numerals(text):
    t = CHEM.sub(" ", clean(text))
    found = set(TIME.findall(t))
    return found | set(NUM.findall(TIME.sub(" ", t)))


def concepts(text):
    t = clean(text)
    return {k for k, rx in LEX.items() if rx.search(t)}


def load_pairs(db):
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT session_id, scenario, actor_model, transcript FROM sessions "
        "WHERE condition='C' AND status='completed' ORDER BY session_id").fetchall()
    pairs = []
    for sid, scen, actor, tr in rows:
        raw = {}
        turn = {"S2N": 0, "N2S": 0}
        for rec in json.loads(tr):
            sp, c = rec["speaker"], rec["content"]
            if sp == "mediator_internal_student_raw":
                raw["S2N"] = c
            elif sp == "mediator_internal_nurse_raw":
                raw["N2S"] = c
            elif sp in ("mediator_internal_bridge_s2n", "mediator_internal_bridge_n2s"):
                d = "S2N" if sp.endswith("s2n") else "N2S"
                turn[d] += 1
                pairs.append(dict(session_id=sid, scenario=scen, actor=actor, direction=d,
                                  turn=turn[d], source=raw[d], rewrite=c))
    return pairs


def main(db, outdir):
    pairs = load_pairs(db)
    assert len(pairs) == 540, len(pairs)
    tally = defaultdict(lambda: [0, 0, 0, 0, 0])  # num_src, num_kept, num_new, con_src, con_kept
    flagged = []
    for p in pairs:
        ns, nr = numerals(p["source"]), numerals(p["rewrite"])
        cs, cr = concepts(p["source"]), concepts(p["rewrite"])
        for key in ("ALL", f"direction={p['direction']}", f"scenario={p['scenario']}", f"actor={p['actor']}"):
            t = tally[key]
            t[0] += len(ns); t[1] += len(ns & nr); t[2] += len(nr - ns)
            t[3] += len(cs); t[4] += len(cs & cr)
        for kind, items in (("numeral_lost", ns - nr), ("numeral_new_in_rewrite", nr - ns),
                            ("concept_lost", cs - cr)):
            for it in sorted(items):
                flagged.append(dict(kind=kind, item=it, session_id=p["session_id"],
                                    direction=p["direction"], turn=p["turn"],
                                    source=" ".join(p["source"].split()),
                                    rewrite=" ".join(p["rewrite"].split())))

    with open(f"{outdir}/preservation_audit_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["subset", "numerals_in_source", "numerals_preserved", "numeral_preservation",
                    "numerals_new_in_rewrite", "concepts_in_source", "concepts_preserved",
                    "concept_preservation"])
        for key in sorted(tally, key=lambda k: (k != "ALL", k)):
            a, b, c, d, e = tally[key]
            w.writerow([key, a, b, f"{b / a:.3f}" if a else "", c, d, e, f"{e / d:.3f}" if d else ""])
    with open(f"{outdir}/preservation_audit_flagged.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(flagged[0]))
        w.writeheader()
        w.writerows(flagged)

    a, b, c, d, e = tally["ALL"]
    print(f"pairs: {len(pairs)}")
    print(f"numerals: {b}/{a} preserved ({b / a:.1%}); {c} appear only in a rewrite")
    print(f"concepts: {e}/{d} preserved ({e / d:.1%})")
    for key in ("direction=S2N", "direction=N2S", "scenario=S1", "scenario=S2", "scenario=S3"):
        t = tally[key]
        print(f"  {key}: numerals {t[1]}/{t[0]} ({t[1] / t[0]:.1%}), concepts {t[4]}/{t[3]} ({t[4] / t[3]:.1%})")
    # numeral results reported in Section 4.6
    assert (a, b, c) == (271, 267, 19)
    assert tally["scenario=S1"][:2] == [73, 73]
    assert tally["direction=S2N"][:2] == [185, 184]
    assert (d, e) == (985, 954)
    print("Section 4.6 reproduced: numerals 267/271 (19 new; S1 100%, S2N 99.5%), "
          "clinical concepts 954/985 (96.9%).")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
