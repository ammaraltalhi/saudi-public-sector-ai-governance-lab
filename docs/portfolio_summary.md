# Portfolio Summary

## Saudi Public Sector AI Governance Lab

**A self-directed portfolio prototype demonstrating AI Governance, Responsible AI, AI Risk and GRC workflow design.**

The project explores a practical governance question: how can teams make use-case context, accountability, evidence expectations and readiness blockers visible across an AI system lifecycle? It uses a fictional Citizen Request Prioritisation AI scenario set in an imagined public-sector service context. It is not a client engagement, government partnership, deployed model or production governance system.

## What the prototype demonstrates

- Streamlit intake for use-case purpose, users, affected people, data categories, AI role and human oversight.
- An eight-question illustrative risk heuristic with a score, tier and governance gates.
- A CSV-backed AI inventory and RACI matrix. The inventory reflects the current session risk tier when the case name matches; RACI editor changes are **not persisted**.
- A control library with shared applicability/evidence-status logic and structured DAT-01, FAI-01, SEC-01, TRN-01, VAL-01, MON-01 and INC-01 assessments.
- Optional structured SDAIA impact, fairness, validation and explainability documentation, including Planned/Performed distinctions where supported.
- Deployment-readiness blockers derived from required control evidence and MON-01/INC-01 planning.
- A read-only executive dashboard using shared control and readiness calculations.
- Local case save/load and restoration, plus automated tests and a GitHub Actions workflow.

## Framework positioning

NIST AI RMF's GOVERN, MAP, MEASURE and MANAGE functions provide a **conceptual organizing structure**, not a formal subcategory mapping or certified conformity claim. The SDAIA page is an analytical seven-principle crosswalk to selected controls and references; it is not an official SDAIA assessment, score, certification or compliance conclusion.

## Interview description

> I built a self-directed AI governance portfolio prototype around a fictional public-sector service scenario. It demonstrates how intake, illustrative risk screening, accountability roles, structured control documentation and evidence-derived readiness reporting can fit together in a Streamlit workflow. I used NIST AI RMF as a conceptual organizing reference and documented an analytical SDAIA principles crosswalk. The project is synthetic, local-only and not a client implementation or deployed AI system.

## Run and demonstrate safely

Install the dependencies from `requirements.txt`, start Streamlit with `python -m streamlit run app.py`, and use only invented synthetic information. See [the five-minute demo script](demo_script.md), [the synthetic case study](synthetic_case_study.md) and [interview talking points](interview_talking_points.md).

Cases are local JSON files without application-level encryption, authentication, role-based access or per-user isolation. Use a private local walkthrough or a recording; do not expose a shared writable instance. RACI edits are session-only and do not persist.

## Important limitations

The risk score is an educational heuristic, not an official NIST, SDAIA, government or legal classification. No AI model, model test results, live monitoring, operational incident response or deployment is provided. Saved assessments and evidence references are user-reported and are not independently authenticated. “Available” and “Ready for Deployment Approval” are prototype workflow states—not proof of operational activity or actual approval.
