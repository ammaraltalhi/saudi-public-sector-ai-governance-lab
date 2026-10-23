# Saudi reference transition: implementation baseline

This is a developer gap analysis, not a completed regulatory assessment. The existing app is a synthetic portfolio and its screening score is not an official SDAIA classification.

| Area | Baseline | Change / next evidence |
| --- | --- | --- |
| Risk method | Eight weighted screening flags | Keep screening separate; add individual risk records, causes, consequences, owner, treatment, dates and residual estimates |
| Saudi references | SDAIA AI Ethics crosswalk | National matrix/scales now checked against supplied PDF; see the source-based comparison. PDPL/NDMO/NCA/DGA applicability and detailed mappings remain pending |
| Evidence | Reviewed forms and supplementary planned/performed records | Add substantive acceptance decisions and corrective-action verification |
| Readiness | Evidence availability and operational plans | Open corrective actions marked as blockers now prevent readiness; residual-risk acceptance decisions remain future work |
| Responsibility | RACI editor is not saved | Future change: persist case-specific ownership |
| Privacy | DAT-01 documentation | Future change: processing records and impact-assessment applicability, followed by a documented assessment where relevant |

## First increment (historical baseline)

A case-linked register records individual risks and treatment plans. Closure requires an evidence reference, reviewer and review date. These are user attestations, not authentication or independent verification. A 1–4 illustrative likelihood/impact scale generates products without regulatory tier labels. No claim is made that these values reproduce SDAIA's matrix. Closed treatment records do not imply formal acceptance of residual risk.

Old schema-version-1 cases remain loadable. The optional register is validated before saving/loading and resets to empty when loading a legacy case. The risk register alone does not affect deployment readiness. Linked corrective actions explicitly marked as readiness blockers do affect the readiness calculation.

## Sources for the next comparison

- [SDAIA publications](https://sdaia.gov.sa/en/MediaCenter/KnowledgeCenter/Pages/SDAIAPublications.aspx): obtain and verify the full National AI Risk Management Framework, including edition, scales and matrix bands.
- [Official framework announcement](https://www.spa.gov.sa/en/N2633781): context, assessment, treatment, monitoring; likelihood and impact.
- [PDPL Implementing Regulations](https://dgp.sdaia.gov.sa/wps/portal/pdp/knowledgecenter/details/PDPL2): Articles 25 and 33, subject to applicability and full-text review.

## Demonstration acceptance scenario

Using synthetic data only, document the risk of unjustified retention of citizen requests; assign a privacy owner, treatment and due date; record inherent and estimated residual likelihood/impact; attempt closure without evidence (must fail); add review evidence and close; save and reload the case; export the register. Do not describe this scenario as work performed for a real municipality.

## Second increment: corrective-action verification

The Corrective Actions page links each finding to an existing risk or catalogue control. It records ownership, action plan, due date, readiness impact/rationale and closure evidence, reviewer, date and verification notes. Open blocking actions and invalid action records prevent readiness. A nonblocking finding remains visible and can be overdue; its rationale is recorded rather than inferred from a score. The dashboard and readiness page use the same calculation.

The export contains the case name, report date, action records and open/overdue/blocking counts. Old cases load with an empty action list. References to missing risks and unknown controls are rejected before saving or restoring a case. Closure is a user attestation, not authenticated sign-off, evidence-content verification or acceptance of residual risk. Empty action lists do not demonstrate that a review occurred.

The Humanity and Social & Environmental Benefits crosswalk descriptions were corrected to acknowledge the dedicated assessment forms already present. No official checklist IDs or page references were added or changed.

### National framework source status (superseded by supplied PDF)

The official Arabic publication was located at https://sdaia.gov.sa/ar/MediaCenter/KnowledgeCenter/ResearchLibrary/ExecutiveSummaryAr.pdf and its English summary at https://sdaia.gov.sa/en/MediaCenter/KnowledgeCenter/ResearchLibrary/ExecutiveSummaryEn.pdf. Direct reading/download was blocked during this increment. Neither document's full text, scale definitions nor matrix bands were verified. The project retains illustrative scales and does not claim national-framework conformity. Clause-level comparison remains pending full-text access.

### Synthetic walkthrough

1. Create a synthetic intake and complete screening.
2. Record a retention risk in Risk Register & Treatment.
3. Create a corrective action linked to that risk and DAT-01; document a retention-schedule review, owner, due date and readiness-blocking rationale.
4. Attempt Closed with no evidence: validation must reject it.
5. Record a synthetic evidence reference, reviewer, review date and specific verification findings; save Closed.
6. Confirm that the action blocker clears in both readiness and dashboard. Other missing control evidence continues to block readiness.
7. Reopen the action: the blocker returns. Save Case, reload and export the corrective-action report.

## Third increment: source-verified national assessment

The supplied 48-page Arabic PDF resolved the previous direct-access limitation. Source metadata, page references, a gap comparison, national-method UI and per-risk methodology markers are now implemented; see [verified comparison](saudi_national_framework_comparison.md). The original access-failure notes above describe the earlier increment only. Existing illustrative records and the eight-factor screening retain their original meaning. The national method implements selected components, not full-framework conformity, regulatory applicability or residual-risk approval.
