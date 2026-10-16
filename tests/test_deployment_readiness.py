from src.governance.control_assessment import (
    DAT_01_REQUIRED_TEXT_FIELDS,
    INC_01_REQUIRED_TEXT_FIELDS,
    MON_01_REQUIRED_TEXT_FIELDS,
    VAL_01_REQUIRED_TEXT_FIELDS,
    assess_control,
)
from src.governance.deployment_readiness import evaluate_readiness


def complete_plans():
    return {
        "monitoring": {
            "plan_defined": True,
            "metrics_defined": True,
            "thresholds_defined": True,
            "responsibilities_defined": True,
        },
        "incident_response": {"plan_approved": True},
    }


def assessments(**overrides):
    result = {
        control_id: {"Applicability": "Required", "Evidence Status": "Available"}
        for control_id in (
            "GOV-01",
            "MAP-01",
            "DAT-01",
            "FAI-01",
            "SEC-01",
            "TRN-01",
            "VAL-01",
        )
    }
    result["MON-01"] = {"Applicability": "Required", "Evidence Status": "Pending"}
    result["INC-01"] = {"Applicability": "Required", "Evidence Status": "Pending"}
    result["RET-01"] = {"Applicability": "Lifecycle", "Evidence Status": "Not Due"}
    result.update(overrides)
    return result


def test_pending_mandatory_control_is_not_ready():
    control_assessments = assessments()
    control_assessments["GOV-01"] = {
        "Applicability": "Required",
        "Evidence Status": "Pending",
    }
    result = evaluate_readiness(
        control_assessments,
        complete_plans(),
        True,
    )
    assert result["status"] == "Not Ready for Deployment Approval"


def test_incomplete_monitoring_plan_is_not_ready():
    plans = complete_plans()
    plans["monitoring"]["thresholds_defined"] = False
    result = evaluate_readiness(assessments(), plans, True)
    assert result["status"] == "Not Ready for Deployment Approval"


def test_unapproved_incident_plan_is_not_ready():
    control_assessments = assessments()
    plans = complete_plans()
    plans["incident_response"]["plan_approved"] = True
    result = evaluate_readiness(control_assessments, plans, True)
    assert result["incomplete_operational_requirements"] == 5
    assert result["status"] == "Not Ready for Deployment Approval"


def test_retirement_control_does_not_block():
    result = evaluate_readiness(assessments(), complete_plans(), True)
    assert result["blocking_controls"] == []


def test_complete_requirements_are_ready_for_human_approval():
    result = evaluate_readiness(
        assessments(**{
            "MON-01": {"Applicability": "Required", "Evidence Status": "Available"},
            "INC-01": {"Applicability": "Required", "Evidence Status": "Available"},
        }),
        complete_plans(),
        True,
    )
    assert result["status"] == "Ready for Deployment Approval"


def test_missing_risk_answers_has_no_readiness_determination():
    assert evaluate_readiness(assessments(), complete_plans(), False) is None


def test_completed_dat01_evidence_reduces_blocking_controls_by_one():
    risk_answers = {
        "personal_data": True,
        "sensitive_data": False,
        "significant_decision": False,
        "vulnerable_groups": False,
        "external_users": False,
        "automated_action": False,
        "third_party_model": False,
        "security_critical": False,
    }
    pending_assessments = {
        control_id: {"Applicability": "Required", "Evidence Status": "Pending"}
        for control_id in ("GOV-01", "MAP-01", "DAT-01", "FAI-01", "SEC-01", "TRN-01", "VAL-01")
    }
    pending_result = evaluate_readiness(
        pending_assessments, complete_plans(), True
    )

    dat01_evidence = {
        field: f"Completed {field}" for field in DAT_01_REQUIRED_TEXT_FIELDS
    }
    dat01_evidence.update({
        "sensitive_data_used": False,
        "sensitive_data_details": "",
        "assessment_status": "Reviewed",
    })
    pending_assessments["DAT-01"] = assess_control(
        "DAT-01",
        {"name": "Citizen Request Prioritisation AI"},
        risk_answers,
        {"DAT-01": dat01_evidence},
    )
    completed_result = evaluate_readiness(
        pending_assessments, complete_plans(), True
    )

    assert len(completed_result["blocking_controls"]) == len(
        pending_result["blocking_controls"]
    ) - 1


def test_val01_blocks_readiness_until_saved_reviewed_validation_assessment():
    use_case = {"name": "Citizen Request Prioritisation AI"}
    risk_answers = {
        "personal_data": False,
        "sensitive_data": False,
        "significant_decision": False,
        "vulnerable_groups": False,
        "external_users": False,
        "automated_action": False,
        "third_party_model": False,
        "security_critical": False,
    }
    control_assessments = assessments()
    control_assessments["VAL-01"] = assess_control(
        "VAL-01",
        use_case,
        risk_answers,
        {},
    )
    pending = evaluate_readiness(control_assessments, complete_plans(), True)
    assert "VAL-01" in pending["blocking_controls"]

    evidence = {
        field: f"Documented {field}" for field in VAL_01_REQUIRED_TEXT_FIELDS
    }
    evidence["assessment_status"] = "Reviewed"
    control_assessments["VAL-01"] = assess_control(
        "VAL-01",
        use_case,
        risk_answers,
        {"VAL-01": evidence},
    )
    available = evaluate_readiness(control_assessments, complete_plans(), True)
    assert control_assessments["VAL-01"]["Evidence Status"] == "Available"
    assert "VAL-01" not in available["blocking_controls"]


def test_monitoring_readiness_is_derived_from_complete_reviewed_mon01_evidence():
    use_case = {"name": "Citizen Request Prioritisation AI"}
    risk_answers = {
        "personal_data": False,
        "sensitive_data": False,
        "significant_decision": False,
        "vulnerable_groups": False,
        "external_users": False,
        "automated_action": False,
        "third_party_model": False,
        "security_critical": False,
    }
    control_assessments = assessments()
    control_assessments["MON-01"] = assess_control(
        "MON-01",
        use_case,
        risk_answers,
        {},
    )
    plans = complete_plans()
    plans["incident_response"]["plan_approved"] = False
    for requirement in (
        "plan_defined",
        "metrics_defined",
        "thresholds_defined",
        "responsibilities_defined",
    ):
        plans["monitoring"][requirement] = True

    pending = evaluate_readiness(control_assessments, plans, True)
    assert pending["incomplete_operational_requirements"] == 5

    mon01_evidence = {
        field: f"Planned {field}" for field in MON_01_REQUIRED_TEXT_FIELDS
    }
    mon01_evidence["assessment_status"] = "Reviewed"
    control_assessments["MON-01"] = assess_control(
        "MON-01",
        use_case,
        risk_answers,
        {"MON-01": mon01_evidence},
    )
    after_mon01 = evaluate_readiness(control_assessments, plans, True)
    assert after_mon01["incomplete_operational_requirements"] == 1
    assert after_mon01["status"] == "Not Ready for Deployment Approval"

    for requirement in (
        "plan_defined",
        "metrics_defined",
        "thresholds_defined",
        "responsibilities_defined",
    ):
        plans["monitoring"][requirement] = False
    still_complete = evaluate_readiness(control_assessments, plans, True)
    assert still_complete["incomplete_operational_requirements"] == 1


def test_mon01_alone_never_completes_incident_response_requirement():
    use_case = {"name": "Citizen Request Prioritisation AI"}
    risk_answers = {
        "personal_data": False,
        "sensitive_data": False,
        "significant_decision": False,
        "vulnerable_groups": False,
        "external_users": False,
        "automated_action": False,
        "third_party_model": False,
        "security_critical": False,
    }
    mon01_evidence = {
        field: f"Planned {field}" for field in MON_01_REQUIRED_TEXT_FIELDS
    }
    mon01_evidence["assessment_status"] = "Reviewed"
    control_assessments = assessments(
        **{"MON-01": assess_control(
            "MON-01",
            use_case,
            risk_answers,
            {"MON-01": mon01_evidence},
        )}
    )
    plans = complete_plans()
    plans["incident_response"]["plan_approved"] = False

    result = evaluate_readiness(control_assessments, plans, True)
    assert result["incomplete_operational_requirements"] == 1
    assert result["status"] == "Not Ready for Deployment Approval"


def test_mon01_available_and_inc01_pending_leaves_one_requirement_incomplete():
    control_assessments = assessments(**{
        "MON-01": {"Applicability": "Required", "Evidence Status": "Available"},
        "INC-01": {"Applicability": "Required", "Evidence Status": "Pending"},
    })
    result = evaluate_readiness(control_assessments, complete_plans(), True)
    assert result["incomplete_operational_requirements"] == 1
    assert result["status"] == "Not Ready for Deployment Approval"


def test_ready_for_approval_requires_saved_inc01_not_manual_plan_boolean():
    control_assessments = assessments(**{
        "MON-01": {"Applicability": "Required", "Evidence Status": "Available"},
        "INC-01": {"Applicability": "Required", "Evidence Status": "Pending"},
    })
    plans = complete_plans()
    plans["incident_response"]["plan_approved"] = True
    result = evaluate_readiness(control_assessments, plans, True)
    assert result["incomplete_operational_requirements"] == 1
    assert result["status"] == "Not Ready for Deployment Approval"


def test_complete_inc01_evidence_is_required_for_incident_readiness():
    use_case = {"name": "Citizen Request Prioritisation AI"}
    risk_answers = {key: False for key in (
        "personal_data",
        "sensitive_data",
        "significant_decision",
        "vulnerable_groups",
        "external_users",
        "automated_action",
        "third_party_model",
        "security_critical",
    )}
    evidence = {
        field: f"Planned {field}" for field in INC_01_REQUIRED_TEXT_FIELDS
    }
    evidence["assessment_status"] = "Reviewed"
    incident_assessment = assess_control(
        "INC-01",
        use_case,
        risk_answers,
        {"INC-01": evidence},
    )
    assert incident_assessment["Evidence Status"] == "Available"
    control_assessments = assessments(**{
        "MON-01": {"Applicability": "Required", "Evidence Status": "Available"},
        "INC-01": incident_assessment,
    })
    result = evaluate_readiness(control_assessments, complete_plans(), True)
    assert result["incomplete_operational_requirements"] == 0
    assert result["status"] == "Ready for Deployment Approval"
    assert result["status"] != "Approved for Deployment"
