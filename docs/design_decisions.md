# Governance Design Decisions

This portfolio implements a synthetic Saudi public-sector governance workflow, not a production AI model or a client engagement.

## Separate screening from per-risk assessment

The eight-question heuristic identifies intake characteristics. It is not the national matrix. Records explicitly using SDAIA-P145-v1-2026 apply the source-defined likelihood × impact calculation and labels, with an assessment horizon, category, reasoning and evidence references. Legacy records require explicit reassessment.

## Separate evidence presence, review and approval

Available control evidence means the configured documentary fields are complete and user-recorded as Reviewed. This does not authenticate the evidence or demonstrate effectiveness. Corrective actions and residual-risk decisions are separately documented; neither is inferred from Available status.

## Bind residual-risk decisions to the assessed state

A decision records authority, tolerance reference, rationale, evidence, decision date and next review. The readiness gate requires current acceptance records after reported post-treatment reassessment. A change to a risk or use-case context invalidates the preceding decision for readiness. Escalation, rejection, expiry, missing decisions and legacy records remain blockers. These are prototype document controls, not identity-authenticated approvals.

## Keep one readiness calculation

The deployment page and dashboard use the same control, corrective-action and residual-risk review rules. Missing mandatory control assessments block readiness. Ready for Deployment Approval means the configured documentary gates are satisfied; final approval remains a human governance decision.

## Preserve traceability and scope

Records are version-labelled and saved with their case. Default snapshots are session-isolated; downloaded/imported JSON supports resumption after refresh. Saved RACI is case-specific. Evidence and decisions remain user-reported without authentication or verified authorization. The [national framework comparison](saudi_national_framework_comparison.md) distinguishes selected implemented components from remaining framework and regulatory gaps. The [design background](design_background.md) attributes the earlier prototype's conceptual sources.
