from .constants import PRE_DEPLOYMENT_CONTROL_IDS

SCREENING_KEYS = (
    "personal_data",
    "sensitive_data",
    "significant_decision",
    "vulnerable_groups",
    "external_users",
    "automated_action",
    "third_party_model",
    "security_critical",
)


DAT_01_REQUIRED_TEXT_FIELDS = (
    "personal_data_categories",
    "purpose_necessity",
    "data_minimisation",
    "data_access",
    "responsible_owner",
    "retention_deletion",
    "privacy_risks",
    "mitigations",
    "privacy_reviewer",
)

FAI_01_REQUIRED_TEXT_FIELDS = (
    "affected_groups",
    "fairness_risk",
    "evaluation_approach",
    "data_evaluation_limitations",
    "findings_observations",
    "mitigation_actions",
    "responsible_owner",
    "fairness_reviewer",
)

SEC_01_REQUIRED_TEXT_FIELDS = (
    "security_scope",
    "key_security_risks",
    "access_control_approach",
    "data_protection_measures",
    "third_party_considerations",
    "security_monitoring_approach",
    "incident_escalation_approach",
    "security_limitations_actions",
    "responsible_owner",
    "security_reviewer",
)

TRN_01_REQUIRED_TEXT_FIELDS = (
    "ai_system_purpose",
    "ai_decision_role",
    "intended_users_stakeholders",
    "key_system_limitations",
    "human_oversight_approach",
    "information_to_communicate",
    "communication_disclosure_approach",
    "transparency_limitations_actions",
    "responsible_owner",
    "transparency_reviewer",
)

VAL_01_REQUIRED_TEXT_FIELDS = (
    "validation_scope",
    "acceptance_criteria",
    "validation_approach",
    "data_test_set_considerations",
    "human_oversight_validation",
    "validation_findings_evidence",
    "validation_limitations_actions",
    "responsible_owner",
    "validation_reviewer",
)

MON_01_REQUIRED_TEXT_FIELDS = (
    "monitoring_objectives",
    "performance_metrics",
    "fairness_disparity_monitoring",
    "human_override_review_monitoring",
    "incident_complaint_indicators",
    "data_model_drift_indicators",
    "monitoring_thresholds",
    "monitoring_frequency",
    "monitoring_responsibilities",
    "threshold_breach_escalation",
    "monitoring_limitations_actions",
    "responsible_owner",
    "monitoring_reviewer",
)

INC_01_REQUIRED_TEXT_FIELDS = (
    "incident_definition_scope",
    "detection_reporting_channels",
    "initial_assessment_triage",
    "severity_impact_classification",
    "immediate_containment_actions",
    "human_review_decision_correction",
    "escalation_criteria",
    "escalation_roles_notifications",
    "investigation_root_cause_approach",
    "corrective_preventive_actions",
    "recovery_return_to_service",
    "incident_documentation_records",
    "post_incident_review_lessons",
    "incident_limitations_actions",
    "responsible_owner",
    "incident_response_reviewer",
)


def has_complete_risk_answers(risk_answers):
    return isinstance(risk_answers, dict) and all(
        key in risk_answers for key in SCREENING_KEYS
    )


def has_complete_dat01_evidence(evidence):
    if not isinstance(evidence, dict):
        return False
    if evidence.get("assessment_status") != "Reviewed":
        return False
    if any(
        not isinstance(evidence.get(field), str) or not evidence[field].strip()
        for field in DAT_01_REQUIRED_TEXT_FIELDS
    ):
        return False
    if not isinstance(evidence.get("sensitive_data_used"), bool):
        return False
    if evidence["sensitive_data_used"] and not (
        isinstance(evidence.get("sensitive_data_details"), str)
        and evidence["sensitive_data_details"].strip()
    ):
        return False
    return True


def has_complete_fai01_evidence(evidence):
    if not isinstance(evidence, dict):
        return False
    if evidence.get("assessment_status") != "Reviewed":
        return False
    return all(
        isinstance(evidence.get(field), str) and evidence[field].strip()
        for field in FAI_01_REQUIRED_TEXT_FIELDS
    )


def has_complete_sec01_evidence(evidence):
    if not isinstance(evidence, dict):
        return False
    if evidence.get("assessment_status") != "Reviewed":
        return False
    return all(
        isinstance(evidence.get(field), str) and evidence[field].strip()
        for field in SEC_01_REQUIRED_TEXT_FIELDS
    )


def has_complete_trn01_evidence(evidence):
    if not isinstance(evidence, dict):
        return False
    if evidence.get("assessment_status") != "Reviewed":
        return False
    return all(
        isinstance(evidence.get(field), str) and evidence[field].strip()
        for field in TRN_01_REQUIRED_TEXT_FIELDS
    )


def has_complete_val01_evidence(evidence):
    if not isinstance(evidence, dict):
        return False
    if evidence.get("assessment_status") != "Reviewed":
        return False
    return all(
        isinstance(evidence.get(field), str) and evidence[field].strip()
        for field in VAL_01_REQUIRED_TEXT_FIELDS
    )


def has_complete_mon01_evidence(evidence):
    if not isinstance(evidence, dict):
        return False
    if evidence.get("assessment_status") != "Reviewed":
        return False
    return all(
        isinstance(evidence.get(field), str) and evidence[field].strip()
        for field in MON_01_REQUIRED_TEXT_FIELDS
    )


def has_complete_inc01_evidence(evidence):
    if not isinstance(evidence, dict):
        return False
    if evidence.get("assessment_status") != "Reviewed":
        return False
    return all(
        isinstance(evidence.get(field), str) and evidence[field].strip()
        for field in INC_01_REQUIRED_TEXT_FIELDS
    )


def control_is_required(control_id, risk_answers):
    if control_id == "DAT-01":
        return risk_answers["personal_data"] or risk_answers["sensitive_data"]
    if control_id == "FAI-01":
        return risk_answers["vulnerable_groups"] or risk_answers["significant_decision"]
    return True


def assess_control(
    control_id,
    use_case,
    risk_answers,
    explicit_evidence,
    inventory_available=True,
    raci_available=True,
):
    has_use_case = bool(use_case)
    human_oversight = use_case.get("human_oversight")
    ai_role = use_case.get("ai_role")

    if control_id == "GOV-01":
        applicability = "Required"
        reason = "AI system is registered and requires accountable ownership"
        default_evidence = (
            "Available"
            if has_use_case and raci_available and inventory_available
            else "Pending"
        )
    elif control_id == "MAP-01":
        applicability = "Required"
        reason = "AI use-case context must be documented"
        default_evidence = "Available" if has_use_case else "Pending"
    elif control_id == "DAT-01":
        required = control_is_required(control_id, risk_answers)
        applicability = "Required" if required else "Not required"
        reason = "Personal/sensitive data identified"
        default_evidence = "Pending" if required else "Not Due"
    elif control_id == "FAI-01":
        required = control_is_required(control_id, risk_answers)
        applicability = "Required" if required else "Not required"
        reason = "Potential fairness or differential-impact risk"
        default_evidence = "Pending" if required else "Not Due"
    elif control_id == "SEC-01":
        applicability = "Required" if has_use_case else "Not required"
        reason = "Security review required before deployment"
        default_evidence = "Pending" if has_use_case else "Not Due"
    elif control_id == "TRN-01":
        applicability = "Required" if has_use_case else "Not required"
        reason = "AI role and limitations must be communicated"
        default_evidence = "Pending" if has_use_case else "Not Due"
    elif control_id == "VAL-01":
        applicability = "Required" if has_use_case else "Not required"
        reason = "Define acceptance criteria and validate performance against intended use"
        default_evidence = "Pending" if has_use_case else "Not Due"
    elif control_id == "MON-01":
        applicability = "Required" if has_use_case else "Not required"
        reason = "Ongoing monitoring requirement"
        default_evidence = "Pending" if has_use_case else "Not Due"
    elif control_id == "INC-01":
        applicability = "Required" if has_use_case else "Not required"
        reason = "Incident response and escalation capability required"
        default_evidence = "Pending" if has_use_case else "Not Due"
    elif control_id == "HUM-01":
        required = human_oversight == "Required before action" or ai_role in {
            "Recommendation only",
            "Decision support",
        }
        applicability = "Required" if required else "Not required"
        reason = "Meaningful human oversight requirement"
        default_evidence = "Pending" if required else "Not Due"
    elif control_id == "RET-01":
        applicability = "Lifecycle"
        reason = "Applies when the AI system is retired/decommissioned"
        default_evidence = "Not Due"
    else:
        applicability = "Required"
        reason = "Control applies to the governed AI use case"
        default_evidence = "Pending"

    if control_id == "DAT-01":
        evidence_status = (
            "Available"
            if has_complete_dat01_evidence(explicit_evidence.get(control_id))
            else default_evidence
        )
    elif control_id == "FAI-01":
        evidence_status = (
            "Available"
            if applicability == "Required"
            and has_complete_fai01_evidence(explicit_evidence.get(control_id))
            else default_evidence
        )
    elif control_id == "SEC-01":
        evidence_status = (
            "Available"
            if applicability == "Required"
            and has_complete_sec01_evidence(explicit_evidence.get(control_id))
            else default_evidence
        )
    elif control_id == "TRN-01":
        evidence_status = (
            "Available"
            if applicability == "Required"
            and has_complete_trn01_evidence(explicit_evidence.get(control_id))
            else default_evidence
        )
    elif control_id == "VAL-01":
        evidence_status = (
            "Available"
            if applicability == "Required"
            and has_complete_val01_evidence(explicit_evidence.get(control_id))
            else default_evidence
        )
    elif control_id == "MON-01":
        evidence_status = (
            "Available"
            if applicability == "Required"
            and has_complete_mon01_evidence(explicit_evidence.get(control_id))
            else default_evidence
        )
    elif control_id == "INC-01":
        evidence_status = (
            "Available"
            if applicability == "Required"
            and has_complete_inc01_evidence(explicit_evidence.get(control_id))
            else default_evidence
        )
    else:
        evidence_status = "Available" if explicit_evidence.get(control_id) else default_evidence
    return {
        "Applicability": applicability,
        "Trigger / Reason": reason,
        "Evidence Status": evidence_status,
    }
