# Saudi reference transition: implementation baseline

This is a developer gap analysis, not a completed regulatory assessment. The existing app is a synthetic portfolio and its screening score is not an official SDAIA classification.

| Area | Baseline | Change / next evidence |
| --- | --- | --- |
| Risk method | Eight weighted screening flags | Keep screening separate; add individual risk records, causes, consequences, owner, treatment, dates and residual estimates |
| Saudi references | SDAIA AI Ethics crosswalk | Verify full national framework and applicable PDPL/NDMO/NCA/DGA provisions before adding clause-level mappings |
| Evidence | Reviewed forms and supplementary planned/performed records | Add substantive acceptance decisions and corrective-action verification |
| Readiness | Evidence availability and operational plans | Future change: include open findings and residual-risk decisions; this release does not alter deployment approval logic |
| Responsibility | RACI editor is not saved | Future change: persist case-specific ownership |
| Privacy | DAT-01 documentation | Future change: processing records and impact-assessment applicability, followed by a documented assessment where relevant |

## First increment

A case-linked register records individual risks and treatment plans. Closure requires an evidence reference, reviewer and review date. These are user attestations, not authentication or independent verification. A 1–4 illustrative likelihood/impact scale generates products without regulatory tier labels. No claim is made that these values reproduce SDAIA's matrix. Closed treatment records do not imply formal acceptance of residual risk.

Old schema-version-1 cases remain loadable. The optional register is validated before saving/loading and resets to empty when loading a legacy case. The register does not yet affect existing deployment readiness.

## Sources for the next comparison

- [SDAIA publications](https://sdaia.gov.sa/en/MediaCenter/KnowledgeCenter/Pages/SDAIAPublications.aspx): obtain and verify the full National AI Risk Management Framework, including edition, scales and matrix bands.
- [Official framework announcement](https://www.spa.gov.sa/en/N2633781): context, assessment, treatment, monitoring; likelihood and impact.
- [PDPL Implementing Regulations](https://dgp.sdaia.gov.sa/wps/portal/pdp/knowledgecenter/details/PDPL2): Articles 25 and 33, subject to applicability and full-text review.

## Demonstration acceptance scenario

Using synthetic data only, document the risk of unjustified retention of citizen requests; assign a privacy owner, treatment and due date; record inherent and estimated residual likelihood/impact; attempt closure without evidence (must fail); add review evidence and close; save and reload the case; export the register. Do not describe this scenario as work performed for a real municipality.
