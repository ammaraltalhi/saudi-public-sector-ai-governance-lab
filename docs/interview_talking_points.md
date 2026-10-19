# Interview Talking Points

## 60-second introduction

> I built the Saudi Public Sector AI Governance Lab as a self-directed portfolio prototype to explore how AI Governance, Responsible AI and GRC responsibilities could be organized around a fictional Citizen Request Prioritisation AI scenario. The Streamlit application connects use-case intake, an illustrative risk-screening heuristic, inventory and accountability views, structured control documentation, SDAIA evidence records and readiness reporting. I focused on making evidence states and review boundaries explicit—for example, distinguishing Planned from user-reported Performed documentation and deployment readiness from approval. NIST AI RMF provides a conceptual organizing structure, and the SDAIA page is an analytical crosswalk, not a conformity claim. There is no deployed model or real agency data, and local case storage is not suitable for public shared use.

## Three governance-design contributions

1. **Connected workflow design:** represented the relationship between use-case context, risk screening, control applicability, evidence status, operational planning and dashboard reporting through shared governance calculations.
2. **Evidence-state boundaries:** designed structured, explicitly saved supplementary records for impact, fairness, validation and explainability, with Planned/Performed distinctions and Invalid handling where supported. These records remain user-reported; completeness is not independent verification.
3. **Readiness and communication:** made blockers and operational requirements visible while keeping “Ready for Deployment Approval” distinct from actual human approval, and presented NIST as conceptual organization and SDAIA as an analytical crosswalk.

## Likely interview questions

### 1. How did you approach AI risk assessment?

I implemented an eight-question weighted heuristic to demonstrate a screening flow and governance gates. It is educational, not an official NIST, SDAIA, government or legal risk classification. A real organization would need to approve its own method, thresholds, ownership and escalation rules.

### 2. What does an “Available” control status mean?

It means the prototype's configured evidence requirements are satisfied—typically complete fields, Reviewed status and an explicit save. It does not establish that a real test, operational activity or control is effective.

### 3. How did you connect readiness to evidence?

The same control assessment logic is used by the Control Library, Deployment Readiness and dashboard. MON-01 and INC-01 documentation drive the prototype's operational readiness checks. “Ready for Deployment Approval” means no configured blockers remain; it is not a deployment approval.

### 4. What are the main limitations of the SDAIA and NIST mappings?

NIST AI RMF GOVERN, MAP, MEASURE and MANAGE are used as conceptual organization, not as a formal subcategory mapping or certified conformity assessment. The SDAIA page is an analytical crosswalk across seven principles and selected references. Neither establishes legal compliance, SDAIA conformity or implementation.

### 5. What would you address before broader use?

First, replace local JSON with an appropriately secured and access-controlled storage design, including per-user isolation, auditability and retention controls. I would also make RACI edits persist safely, agree organization-specific risk and evidence methods, and review any framework mapping with qualified stakeholders. The current app is intended for synthetic local demonstrations only.

## Short descriptions

**GitHub:** Self-directed Streamlit portfolio prototype connecting AI use-case intake, illustrative risk screening, structured governance evidence and readiness reporting for a fictional public-sector scenario.

**LinkedIn:** Built a synthetic AI Governance / Responsible AI portfolio lab exploring risk screening, accountability, control evidence and readiness workflows, with NIST AI RMF used conceptually and an analytical SDAIA principles crosswalk.

**CV:** Designed a self-directed AI Governance and GRC workflow prototype in Streamlit, including illustrative risk screening, structured control/evidence records, local case restoration and evidence-derived readiness reporting.

## Accuracy guardrails

Describe this as a **self-directed portfolio prototype**. Do not imply an employer, client, government partnership, stakeholder approval, production deployment, real model evaluation, measured performance, SDAIA/NIST compliance or verified operational outcome.
