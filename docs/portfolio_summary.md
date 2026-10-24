# Portfolio Summary

## Saudi Public Sector AI Governance Lab

**A self-directed portfolio prototype demonstrating AI Governance, Responsible AI, AI Risk and GRC workflow design.**

The project explores a practical governance question: how can teams make use-case context, accountability, evidence expectations and readiness blockers visible across an AI system lifecycle? It uses a fictional Citizen Request Prioritisation AI scenario set in an imagined public-sector service context. It is not a client engagement, government partnership, deployed model or production governance system.

## What the prototype demonstrates

- Streamlit intake for use-case purpose, users, affected people, data categories, AI role and human oversight.
- Separate illustrative intake screening and source-referenced national per-risk assessments, treatment plans and residual-risk decisions.
- A CSV-backed AI inventory and RACI matrix. The inventory reflects the current session risk tier when the case name matches; Validated RACI changes saved to the case are included in downloaded case JSON.
- A control library with shared applicability/evidence-status logic and structured DAT-01, FAI-01, SEC-01, TRN-01, VAL-01, MON-01 and INC-01 assessments.
- Optional structured SDAIA impact, fairness, validation and explainability documentation, including Planned/Performed distinctions where supported.
- Deployment-readiness blockers derived from control evidence, operational plans, corrective actions and residual-risk review.
- A read-only executive dashboard using shared control and readiness calculations.
- Local case save/load and restoration, plus automated tests and a GitHub Actions workflow.

## Saudi reference model

The current workflow uses SDAIA-P145 v1 (April 2026), including its page-25 likelihood × impact matrix, national risk categories, treatment options and a documented residual-risk decision gate. The seven-principle SDAIA AI Ethics mapping describes documentary coverage and gaps. Saudi PDPL/NDMO/NCA/DGA sources are listed with verification and applicability limitations.

## Design contributions

- Per-risk methodology and explicit legacy reassessment preserve the meaning of earlier records.
- Corrective-action tracking connects findings, owners, evidence and readiness blockers.
- Residual-risk decisions are bound to the reviewed risk/context and expire at the next review date.
- The dashboard and deployment page share one readiness calculation.

## Run and demonstrate safely

Install the dependencies from `requirements.txt`, start Streamlit with `python -m streamlit run app.py`, and use only invented synthetic information. See [the five-minute demo script](demo_script.md), [the synthetic case study](synthetic_case_study.md) and [design decisions](design_decisions.md).

Default snapshots are isolated to the visitor session. Download case JSON before refreshing; import it to resume. Saved RACI edits are included. No authenticated roles, verified approvals or production storage are provided. The optional filesystem mode is for private local use only.

## Important limitations

The eight-factor screening is an educational heuristic. National-method records use the verified SDAIA matrix, but ratings and review decisions are user-entered; this does not establish full-framework or legal conformity. No AI model, model test results, live monitoring, operational incident response or deployment is provided. Saved assessments and evidence references are user-reported and are not independently authenticated. “Available” and “Ready for Deployment Approval” are prototype workflow states—not proof of operational activity or actual approval.
