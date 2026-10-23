# National framework comparison — verified source baseline

Source: SDAIA, **الإطار الوطني لإدارة مخاطر الذكاء الاصطناعي**, SDAIA-P145, version 1, April 2026, 48 pages. [Official Arabic publication](https://sdaia.gov.sa/ar/MediaCenter/KnowledgeCenter/ResearchLibrary/ExecutiveSummaryAr.pdf). A user-supplied copy enabled source review after direct retrieval failed. Its SHA-256 and reviewed sections are recorded in [source metadata](../data/saudi_risk_source.json). Printed page and PDF page numbers agree for the cited sections. English descriptions are project translations. This is an analytical comparison, not an official SDAIA crosswalk or conformity assessment.

## Source findings and implementation decisions

| Source section | Verified finding (paraphrased) | Current implementation / remaining gap |
| --- | --- | --- |
| pp. 6–8 | Advisory guidance for government/private entities, covering organizational risk practice; not detailed model-performance standards | Keep prototype and conformity limitations; applicability of other regulations remains a separate task |
| p. 13; pp. 14–16 | Five risk-workflow stages, supported by four reference pillars: general principles, AI regulations, data regulations, sector regulations | New Saudi National Risk Method page uses the national workflow as the primary displayed workflow. NIST remains a complementary conceptual reference, not a mandated structure |
| p. 17 | System boundaries, data flows, automation/human roles, lifecycle/change planning | Intake and control forms cover parts of this context. Complete data-flow/source classification and structured change approval are not yet implemented |
| pp. 18–20 | Seven risk categories; scenario sources, intent and pre/post-launch timing support systematic identification | National risk records now require one category and retain cause/consequence fields. Multi-category coverage, intent/timing fields and completeness assessment remain gaps |
| pp. 22–23 | Four likelihood levels; evidence, exposure, preventive controls, ease of occurrence and precedents inform estimation within a time horizon | National records require an assessment horizon, likelihood rationale and evidence reference. App validates documentary presence, not factual quality |
| pp. 23–24 | Impact has four levels; catastrophic denotes extreme, severe contextual harms | Labels and impact rationale are captured. App cannot establish that a catastrophic classification is substantively justified |
| p. 25, Figures 4–5 | Each risk uses likelihood × impact; levels 1–2 Low, 3–6 Medium, 8–12 High, 16 Catastrophic | Verified matrix implemented for records explicitly saved with SDAIA-P145-v1-2026. The original eight-question screening remains separate. No scores are automatically migrated |
| p. 26 | Avoid, mitigate, transfer or accept with recorded reasoning, ownership and implementation; transfer does not remove entity responsibility | National records require a strategy; treatment/owner/date and corrective actions capture parts of execution. Selecting Accept is not an approval |
| p. 27 | Reassess residual risk consistently; compare with approved tolerance, then accept or escalate with governance documentation | Same matrix used for inherent and residual ratings; record distinguishes planned estimates from user-reported post-treatment reassessment. Approved tolerance, authenticated acceptance/escalation and decision history remain gaps |
| pp. 28–29 | Monitoring, event/periodic reviews, incidents, root causes and corrective/preventive measures feed risk updates | MON-01, INC-01 and corrective-action tracking cover documentary planning/follow-up; live monitoring and versioned risk-review history remain gaps |

## Arithmetic specification

Rows below are likelihood 1–4; columns are impact 1–4. Values and classifications were visually checked against page 25.

| Likelihood / impact | 1 Low | 2 Medium | 3 High | 4 Catastrophic |
| --- | --- | --- | --- | --- |
| 1 Rare | 1 Low | 2 Low | 3 Medium | 4 Medium |
| 2 Unlikely | 2 Low | 4 Medium | 6 Medium | 8 High |
| 3 Likely | 3 Medium | 6 Medium | 9 High | 12 High |
| 4 Almost certain | 4 Medium | 8 High | 12 High | 16 Catastrophic |

Scores 5, 7, 10, 11 and 13–15 cannot arise from integer inputs 1–4. Likelihood's annual percentage ranges on page 23 are contextual reference ranges; the framework explains that estimation is not initially based on fixed percentages. The app does not request an annual probability or invent probability thresholds.

## Migration and assurance boundaries

Existing risk records without a methodology marker remain illustrative, even though their numeric range was already 1–4. To use the national matrix, select it, review the ratings against the source definitions, document category, time horizon, rating rationales, strategy, residual basis and evidence, then explicitly save. Old case files remain supported. The displayed screening score is never relabelled as a national risk score.

Neither a low product nor a Closed action/risk authorizes deployment. The readiness workflow remains an illustrative evidence gate with a human decision; national-framework completeness and residual-risk acceptance are not automatically established. A planned residual estimate is not evidence that controls reduced risk. Selecting Post-treatment reassessment records a user's report and evidence reference, not an independently performed evaluation.
