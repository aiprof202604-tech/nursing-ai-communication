# Five Walls Deployment Checklist for 2027

**Supplementary material to**: Tajima, H.: Generative AI in Student–Nurse Clinical Communication: A Multi-LLM In-Silico Evaluation and Five Walls to 2027, *Journal of Information Processing*, Vol.35 (2027).

**Intended users**: IT departments, clinical-safety committees, and nurse educators in hospitals and nursing-education institutions.

**Purpose**: The Five Walls framework of the paper, recast as a checklist for an institution's decision on deploying generative AI. Each item is answered Yes / No / N/A. Deployment is not recommended until every **Critical** item is answered Yes.

**Composition**: 42 items — 26 Critical and 16 Recommended (Table 3 of the paper). The Japanese original is `deployment_checklist_ja.md`; this English text is a faithful translation. Items marked † correspond to the representative Critical item quoted for each Wall in Table 3.

**Version**: 1.1

---

## Wall 1: Trust

Are the conditions in place for students, nurses, and patients to accept AI involvement?

### Critical

- [ ] 1.C1 † Students are informed in advance that AI will intervene in the conversation. *(Table 3: “Students are explicitly informed when AI mediation is active”)*
- [ ] 1.C2 Students' right to decline AI intervention is guaranteed in writing.
- [ ] 1.C3 The institution's arrangements ensure that students who decline AI intervention suffer no educational or assessment disadvantage.
- [ ] 1.C4 Preceptors are informed that the AI may edit students' messages.
- [ ] 1.C5 (Clinical application) A procedure exists for informing patients that the student caring for them is working under AI mediation.

### Recommended

- [ ] 1.R1 A user interface allows students to choose, session by session, whether AI mediation is active.
- [ ] 1.R2 Students can review the mediation log (whose utterances the AI edited, and how).
- [ ] 1.R3 Students' subjective acceptance of AI mediation (e.g. the extent to which they feel heard) is measured periodically.

**Rationale**: Yin et al. (2024) showed that recipients who knew a message was AI-generated rated it as making them feel less heard. See Section 5.1 of the paper.

---

## Wall 2: Privacy

Is communication that contains clinical information legally protected?

### Critical

- [ ] 2.C1 The AI vendor (API provider) is legally positioned as the institution's **data processor**.
- [ ] 2.C2 The requirements of Japan's Act on the Protection of Personal Information (APPI) for **special care-required personal information** are met.
- [ ] 2.C3 For international sites, a route to compliance with GDPR Article 9 (special categories of personal data) is established.
- [ ] 2.C4 For HIPAA-covered sites, a Business Associate Agreement (BAA) has been executed with the AI vendor.
- [ ] 2.C5 † Where patient information is sent to an API, the de-identification procedure is documented. *(Table 3: “No identifiable patient data is sent to external APIs without approval”)*
- [ ] 2.C6 The retention period and disposal procedure for API call logs are documented.

### Recommended

- [ ] 2.R1 The vendor contract states that data will not be used for model training (offered as standard by enterprise offerings such as those of Anthropic, OpenAI Enterprise, and Google Vertex AI).
- [ ] 2.R2 The status of consideration of on-premise or private-cloud deployment is recorded.
- [ ] 2.R3 A procedure exists for deleting past AI session logs when a patient withdraws consent.

**Rationale**: In the study (Section 5.2), only synthetic research data were sent to three commercial APIs. Clinical application requires a fundamentally different legal structure.

---

## Wall 3: Over-reliance

Can students and nurses develop their own abilities without becoming over-dependent on the AI?

### Critical

- [ ] 3.C1 The curriculum incorporates a scaffolding design in which AI intervention is **progressively withdrawn**.
- [ ] 3.C2 † Students' ability to communicate clinically **without AI** is assessed regularly (formative and summative). *(Table 3: “AI-free assessment intervals are preserved”)*
- [ ] 3.C3 An indicator exists for judging whether AI intervention is producing *facilitation* of learning rather than *displacement* of it.
- [ ] 3.C4 Nurses are trained to evaluate AI alerts and suggestions critically rather than accepting them automatically.

### Recommended

- [ ] 3.R1 Students complete reflection tasks in which they appraise the quality of the AI's output themselves.
- [ ] 3.R2 Scaffolding criteria exist (e.g. “move to the next stage after X consecutive high-quality SBAR reports without AI”).
- [ ] 3.R3 The frequency of AI intervention is monitored longitudinally (per student, per term).

**Rationale**: In the study (Section 5.3), Student Support (turn-by-turn coaching of the student) produced no appreciable benefit for any of the three actor LLMs — a structural finding consistent with scaffolding theory.

---

## Wall 4: Competency

Does AI intervention remain within clinically safe limits?

### Critical

- [ ] 4.C1 † A process for **independent adjudication of clinical content** in AI output is defined. *(Table 3: “Clinical content accuracy is independently adjudicated”)*
- [ ] 4.C2 The **clinical accuracy** of AI output on dose ranges, symptom interpretation, SBAR content, and escalation decisions is verified periodically by in-house experts.
- [ ] 4.C3 Detection criteria and a response protocol for hallucination (generation of factual errors) exist.
- [ ] 4.C4 In acute handover (corresponding to scenario S3 of the paper), the latency of AI intervention is within acceptable limits.
- [ ] 4.C5 The AI is designed to **preserve, not smooth away,** uncertainty markers (indicators of hesitation or doubt) in students' and nurses' utterances.

### Recommended

- [ ] 4.R1 A committee monitors the quality of AI output (e.g. quarterly review).
- [ ] 4.R2 A mechanism pauses AI intervention when critical clinical decisions (such as escalation) are involved.
- [ ] 4.R3 A recording system exists for near misses and adverse events occurring under AI intervention.

**Rationale**: In the study (Section 5.4), the LLM Judge evaluated communication quality; **clinical accuracy was not measured**. It must be evaluated independently before deployment.

---

## Wall 5: Governance

Are accountability and the management of model changes clearly defined?

### Critical

- [ ] 5.C1 The **allocation of responsibility** is documented for cases in which an error under AI intervention harms a patient (division between nurse, institution, and AI vendor).
- [ ] 5.C2 † A **re-evaluation protocol** applies when the AI model is updated (version change or deprecation). *(Table 3: “Model changes trigger re-validation before continued use”)*
- [ ] 5.C3 Where several LLMs are used, the rationale for the choice of each model is documented.
- [ ] 5.C4 LLM selection is decided **jointly by the clinical-safety committee and the education lead**, not by a single IT officer.
- [ ] 5.C5 The principal finding of the paper (actor-model variance, ε² = 0.49, exceeding intervention-condition variance, ε² = 0.12) is reflected in the institution's evaluation of LLMs.
- [ ] 5.C6 Approval of an Institutional Review Board (or equivalent ethics committee) has been obtained for the deployment phase.

### Recommended

- [ ] 5.R1 Compliance with the latest AI-related guidance of the Japanese Nursing Association has been confirmed.
- [ ] 5.R2 The route to compliance with international medical-AI regulation (EU AI Act, FDA SaMD, etc.) is recorded.
- [ ] 5.R3 The AI vendor's Service Level Agreement includes the availability and response-time requirements needed for healthcare use.
- [ ] 5.R4 A standing forum exists in which the leads of the education, IT, and clinical departments review AI deployment regularly.

**Rationale**: See Section 5.5 of the paper. During the study itself, a major actor LLM was retired by its provider (Section 5.6, Practice 1), demonstrating temporal instability. Practice 4 of the paper further recommends a deterministic integrity check of numerals, units, and patient identifiers for any intervention that rewrites clinical utterances; adopters may add it to this Wall.

---

## Summary: deployment decision

| Wall | Critical items | Achieved | Rate |
|------|---------------:|---------:|-----:|
| 1. Trust | 5 | __/5 | __% |
| 2. Privacy | 6 | __/6 | __% |
| 3. Over-reliance | 4 | __/4 | __% |
| 4. Competency | 5 | __/5 | __% |
| 5. Governance | 6 | __/6 | __% |
| **Total** | **26** | __/26 | __% |

### Decision criteria

| Critical items achieved | Decision | Action |
|---|---|---|
| 100% | **GO**: deployment may begin | Proceed to a pilot phase |
| 80–99% | **CONDITIONAL**: mitigation plan required for unmet items | Case-by-case review by the institutional ethics committee |
| 50–79% | **HOLD**: major preparation required | Plan to resolve unmet items within three months |
| 0–49% | **NO-GO**: deployment not permitted | Return to the system-design stage |

---

## Revision history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-05-20 | First edition (Japanese; supplementary material to the paper) |
| 1.1 | release | Effect-size symbol aligned with the paper (η² → ε², rank epsilon-squared); licence aligned with the repository (MIT); English translation added |

## Licence

Released under the MIT License, as is the rest of this repository (see `LICENSE`). Please cite the paper when reusing the checklist.

## Contact

Hiroyuki Tajima, Faculty of Nursing, Shumei University — tajima@mailg.shumei-u.ac.jp
