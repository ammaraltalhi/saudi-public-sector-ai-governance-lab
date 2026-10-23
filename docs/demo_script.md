# Five-Minute Local Demonstration Script

## Preparation

- Run the application from an isolated source copy that excludes existing saved-case storage.
- Use only the fictional Citizen Request Prioritisation AI scenario and invented text.
- An introductory walkthrough can start in an empty session and show the available pages and Missing evidence states.
- To show Planned and Performed evidence statuses within five minutes, prepare synthetic evidence in that isolated copy ahead of time and start the presentation with its pre-prepared synthetic session or case. Do not author all structured evidence live.
- Never load or inspect existing saved case files. If demonstrating case persistence, use an isolated application copy and temporary case storage containing only synthetic data.
- Do not display or use real citizen, organizational or operational data. Case saves write JSON under `data/cases/` in the isolated copy.
- Prefer a private local walkthrough or a recording. Do not expose the current shared, writable local-case implementation as a public demo.

## Timed walkthrough

| Time | Where to click / show | Governance concept | Limitation to state |
|---|---|---|---|
| **0:00–0:30** | Open **Overview**. Introduce the lab and its fictional scenario. | A governance workflow can make purpose, accountability, evidence and review gates visible. | This is a self-directed portfolio prototype, not a client or government implementation. |
| **0:30–1:05** | Open **AI Use Case Intake**. Show the sample purpose, users, broad input categories, recommendation-only role and human oversight. | Define context and the role of AI before assessing risk. | No model, real dataset or actual agency decision is included. |
| **1:05–1:35** | Open **Risk Screening**, then **Saudi National Risk Method**. Contrast the eight-question screening with a prepared national per-risk matrix assessment. | Screening can organize follow-up questions and governance gates. | The weighted score is an educational heuristic, not an official or legal risk classification. |
| **1:35–2:00** | Open **AI Inventory**, then **RACI Matrix**. | Inventory and role accountability are distinct governance artefacts. | The inventory is a CSV baseline; RACI editor changes are not persisted. |
| **2:00–3:15** | Open **Control Library**. Point out base assessments, then optionally show the supplementary SDAIA impact, fairness, validation or explainability sections. | Structured evidence, explicit save actions, Planned versus Performed distinction, and specific owners/reviewers support traceability. | These are user-reported records. A complete or Reviewed form does not prove independent testing, evidence authenticity, effectiveness or compliance. Use synthetic rows only. |
| **3:15–3:45** | Open **SDAIA Framework Alignment**. Show the seven-principle analytical crosswalk and Missing/Planned/Performed/Invalid supplemental statuses. | A crosswalk can expose documented coverage and gaps for review. | The ethics crosswalk is documentary; national matrix calculation is separate and neither establishes complete conformity. |
| **3:45–4:20** | Open **Deployment Readiness**. Show pending controls, corrective actions, operational plans and a residual-risk decision; change the risk and show that a fresh review is required. | Readiness can be tied to shared evidence rules rather than a separate unchecked approval flag. | **Ready for Deployment Approval** is not **Approved for Deployment**. It is only a result under this prototype's configured gates. |
| **4:20–5:00** | Open **Governance Dashboard**. Summarize risk, control evidence, readiness and outstanding actions. | Executive reporting should reuse the same risk, control and readiness calculations shown elsewhere. | No live monitoring, deployed AI system, verified performance or production approval is represented. |

## Optional persistence close

If time permits, save and restore the fictional case only in the isolated application copy and temporary case storage. Make clear that the prototype's local JSON storage has no authentication, encryption or per-user isolation. Do not load existing saved cases or use a shared writable hosted instance.
