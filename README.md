# Saudi Public Sector AI Governance Lab

A **self-directed portfolio project** that demonstrates how AI governance principles can be translated into a practical operating model for a **simulated Saudi public-sector AI use case**.

> **Transparency:** This is a case study / prototype, not a live client implementation and not legal advice.

## Why this project

The project bridges academic knowledge of AI governance with practical implementation artefacts. It uses the NIST AI Risk Management Framework (AI RMF) functions — **GOVERN, MAP, MEASURE and MANAGE** — as the primary organising reference.

## What is included

- AI Use Case Intake
- AI Inventory
- Illustrative AI Risk Assessment
- RACI Accountability Matrix
- Governance Lifecycle Gates
- AI Governance Control Library
- Governance Dashboard
- Unit tests + GitHub Actions CI

## Architecture

```mermaid
flowchart LR
    A[AI Use Case Intake] --> B[Context & Risk Screening]
    B --> C[Risk Tier]
    C --> D[Governance Gates]
    D --> E[RACI & Control Assignment]
    E --> F[Validation & Approval]
    F --> G[Deployment]
    G --> H[Monitoring & Incident Management]
    H --> I[Review / Improve / Retire]
```

## NIST AI RMF mapping

| Function | Prototype implementation |
|---|---|
| GOVERN | RACI, governance roles, control library, documentation |
| MAP | Use-case intake, purpose, users, data, impact context |
| MEASURE | Risk screening, validation, fairness/security/privacy controls |
| MANAGE | Approval gates, mitigation, monitoring, escalation and retirement |

## Tech stack

- Python
- Streamlit
- Pandas
- Pytest
- GitHub Actions

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Run tests

```bash
pytest -q
```

## Deployment

A simple portfolio deployment option is **Streamlit Community Cloud** connected to the public GitHub repository.

## Repository structure

```text
.
├── app.py
├── views/
├── src/governance/
├── data/
├── docs/
├── tests/
└── .github/workflows/
```

## Risk-model disclaimer

The score in `src/governance/risk.py` is an **illustrative portfolio heuristic**. NIST AI RMF does not prescribe this scoring method. A real organisation should use an approved methodology reflecting applicable law, regulation, organisational risk appetite and system context.

## Reference sources

- NIST, *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*: https://www.nist.gov/itl/ai-risk-management-framework
- NIST AI RMF Playbook: https://airc.nist.gov/airmf-resources/playbook/
- OECD AI Principles: https://www.oecd.org/en/topics/ai-principles.html

## Portfolio positioning

Recommended CV wording:

**AI Governance Portfolio Project — Saudi Public Sector AI Governance Lab**  
Designed and built a technical AI governance prototype for a simulated public-sector use case, including AI inventory, risk screening, RACI accountability, lifecycle approval gates, governance controls, evidence requirements and monitoring dashboard, using NIST AI RMF as a reference model.
