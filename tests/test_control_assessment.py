from src.governance.control_assessment import (
    DAT_01_REQUIRED_TEXT_FIELDS,
    INC_01_REQUIRED_TEXT_FIELDS,
    FAI_01_REQUIRED_TEXT_FIELDS,
    MON_01_REQUIRED_TEXT_FIELDS,
    SEC_01_REQUIRED_TEXT_FIELDS,
    TRN_01_REQUIRED_TEXT_FIELDS,
    VAL_01_REQUIRED_TEXT_FIELDS,
    SCREENING_KEYS,
    assess_control,
    control_is_required,
    has_complete_risk_answers,
)


def answers(**overrides):
    result = {key: False for key in SCREENING_KEYS}
    result.update(overrides)
    return result


def test_personal_data_requires_data_control():
    assert control_is_required("DAT-01", answers(personal_data=True))


def test_vulnerable_groups_requires_fairness_control():
    assert control_is_required("FAI-01", answers(vulnerable_groups=True))


def test_significant_decision_requires_fairness_control():
    assert control_is_required("FAI-01", answers(significant_decision=True))


def test_missing_risk_answers_are_incomplete():
    assert not has_complete_risk_answers({})


def complete_dat01_assessment(**overrides):
    record = {field: f"Completed {field}" for field in DAT_01_REQUIRED_TEXT_FIELDS}
    record.update({
        "sensitive_data_used": False,
        "sensitive_data_details": "",
        "assessment_status": "Reviewed",
    })
    record.update(overrides)
    return record


def dat01_evidence_status(evidence):
    return assess_control(
        "DAT-01",
        {"name": "Citizen Request Prioritisation AI"},
        answers(personal_data=True),
        {"DAT-01": evidence} if evidence is not None else {},
    )["Evidence Status"]


def test_dat01_without_evidence_is_pending():
    assert dat01_evidence_status(None) == "Pending"


def test_dat01_incomplete_structured_assessment_is_pending():
    assert dat01_evidence_status({"assessment_status": "Reviewed"}) == "Pending"


def test_dat01_draft_assessment_is_pending():
    assert dat01_evidence_status(
        complete_dat01_assessment(assessment_status="Draft")
    ) == "Pending"


def test_dat01_reviewed_assessment_missing_required_field_is_pending():
    evidence = complete_dat01_assessment()
    evidence["privacy_risks"] = ""
    assert dat01_evidence_status(evidence) == "Pending"


def test_dat01_sensitive_data_requires_details():
    assert dat01_evidence_status(
        complete_dat01_assessment(sensitive_data_used=True)
    ) == "Pending"


def test_complete_reviewed_dat01_assessment_is_available():
    assert dat01_evidence_status(complete_dat01_assessment()) == "Available"


def test_truthy_boolean_is_not_dat01_evidence():
    assert dat01_evidence_status(True) == "Pending"


def complete_fai01_assessment(**overrides):
    record = {field: f"Documented {field}" for field in FAI_01_REQUIRED_TEXT_FIELDS}
    record["assessment_status"] = "Reviewed"
    record.update(overrides)
    return record


def fai01_evidence_status(evidence, risk_answers=None):
    return assess_control(
        "FAI-01",
        {"name": "Citizen Request Prioritisation AI"},
        risk_answers or answers(significant_decision=True, vulnerable_groups=True),
        {"FAI-01": evidence} if evidence is not None else {},
    )["Evidence Status"]


def test_required_fai01_without_evidence_is_pending():
    assert fai01_evidence_status(None) == "Pending"


def test_incomplete_fai01_assessment_is_pending():
    assert fai01_evidence_status({"assessment_status": "Reviewed"}) == "Pending"


def test_complete_fai01_draft_assessment_is_pending():
    assert fai01_evidence_status(
        complete_fai01_assessment(assessment_status="Draft")
    ) == "Pending"


def test_complete_reviewed_fai01_assessment_is_available_only_when_saved():
    evidence = complete_fai01_assessment()
    assert fai01_evidence_status(evidence) == "Available"
    assert fai01_evidence_status(None) == "Pending"


def test_fai01_is_not_required_without_fairness_screening_triggers():
    result = assess_control(
        "FAI-01",
        {"name": "Citizen Request Prioritisation AI"},
        answers(),
        {"FAI-01": complete_fai01_assessment()},
    )
    assert result["Applicability"] == "Not required"
    assert result["Evidence Status"] == "Not Due"


def complete_sec01_assessment(**overrides):
    record = {field: f"Documented {field}" for field in SEC_01_REQUIRED_TEXT_FIELDS}
    record["assessment_status"] = "Reviewed"
    record.update(overrides)
    return record


def sec01_assessment(evidence, use_case=None):
    return assess_control(
        "SEC-01",
        use_case if use_case is not None else {"name": "Citizen Request Prioritisation AI"},
        answers(),
        {"SEC-01": evidence} if evidence is not None else {},
    )


def test_required_sec01_without_evidence_is_pending():
    assert sec01_assessment(None)["Evidence Status"] == "Pending"


def test_incomplete_sec01_evidence_is_pending():
    assert sec01_assessment({"assessment_status": "Reviewed"})["Evidence Status"] == "Pending"


def test_complete_sec01_draft_is_pending():
    assert sec01_assessment(
        complete_sec01_assessment(assessment_status="Draft")
    )["Evidence Status"] == "Pending"


def test_reviewed_sec01_without_saved_record_is_pending():
    draft_form_values = complete_sec01_assessment()
    assert draft_form_values["assessment_status"] == "Reviewed"
    assert sec01_assessment(None)["Evidence Status"] == "Pending"


def test_complete_reviewed_saved_sec01_evidence_is_available():
    assert sec01_assessment(
        complete_sec01_assessment()
    )["Evidence Status"] == "Available"


def test_non_applicable_sec01_evidence_does_not_become_available():
    result = sec01_assessment(complete_sec01_assessment(), use_case={})
    assert result["Applicability"] == "Not required"
    assert result["Evidence Status"] == "Not Due"


def complete_trn01_assessment(**overrides):
    record = {field: f"Documented {field}" for field in TRN_01_REQUIRED_TEXT_FIELDS}
    record["assessment_status"] = "Reviewed"
    record.update(overrides)
    return record


def trn01_assessment(evidence, use_case=None):
    return assess_control(
        "TRN-01",
        use_case if use_case is not None else {"name": "Citizen Request Prioritisation AI"},
        answers(),
        {"TRN-01": evidence} if evidence is not None else {},
    )


def test_required_trn01_without_evidence_is_pending():
    assert trn01_assessment(None)["Evidence Status"] == "Pending"


def test_incomplete_trn01_evidence_is_pending():
    assert trn01_assessment({"assessment_status": "Reviewed"})["Evidence Status"] == "Pending"


def test_complete_trn01_draft_is_pending():
    assert trn01_assessment(
        complete_trn01_assessment(assessment_status="Draft")
    )["Evidence Status"] == "Pending"


def test_reviewed_trn01_form_values_are_pending_until_saved():
    unsaved_form_values = complete_trn01_assessment()
    assert unsaved_form_values["assessment_status"] == "Reviewed"
    assert trn01_assessment(None)["Evidence Status"] == "Pending"


def test_complete_reviewed_saved_trn01_evidence_is_available():
    assert trn01_assessment(
        complete_trn01_assessment()
    )["Evidence Status"] == "Available"


def test_non_applicable_trn01_evidence_does_not_become_available():
    result = trn01_assessment(
        complete_trn01_assessment(),
        use_case={},
    )
    assert result["Applicability"] == "Not required"
    assert result["Evidence Status"] == "Not Due"


def complete_val01_assessment(**overrides):
    record = {field: f"Documented {field}" for field in VAL_01_REQUIRED_TEXT_FIELDS}
    record["assessment_status"] = "Reviewed"
    record.update(overrides)
    return record


def val01_assessment(evidence, use_case=None):
    return assess_control(
        "VAL-01",
        use_case if use_case is not None else {"name": "Citizen Request Prioritisation AI"},
        answers(),
        {"VAL-01": evidence} if evidence is not None else {},
    )


def test_val01_is_required_when_a_use_case_exists():
    assert val01_assessment(None)["Applicability"] == "Required"


def test_val01_is_not_required_without_a_use_case():
    result = val01_assessment(None, use_case={})
    assert result["Applicability"] == "Not required"
    assert result["Evidence Status"] == "Not Due"


def test_incomplete_val01_evidence_is_pending():
    assert val01_assessment({"assessment_status": "Reviewed"})["Evidence Status"] == "Pending"


def test_complete_val01_draft_is_pending():
    assert val01_assessment(
        complete_val01_assessment(assessment_status="Draft")
    )["Evidence Status"] == "Pending"


def test_reviewed_val01_form_values_are_pending_until_saved():
    unsaved_form_values = complete_val01_assessment()
    assert unsaved_form_values["assessment_status"] == "Reviewed"
    assert val01_assessment(None)["Evidence Status"] == "Pending"


def test_complete_reviewed_saved_val01_evidence_is_available():
    assert val01_assessment(
        complete_val01_assessment()
    )["Evidence Status"] == "Available"


def complete_mon01_assessment(**overrides):
    record = {field: f"Planned {field}" for field in MON_01_REQUIRED_TEXT_FIELDS}
    record["assessment_status"] = "Reviewed"
    record.update(overrides)
    return record


def mon01_assessment(evidence, use_case=None):
    return assess_control(
        "MON-01",
        use_case if use_case is not None else {"name": "Citizen Request Prioritisation AI"},
        answers(),
        {"MON-01": evidence} if evidence is not None else {},
    )


def test_mon01_is_required_when_a_use_case_exists():
    assert mon01_assessment(None)["Applicability"] == "Required"


def test_mon01_is_not_required_without_a_use_case():
    result = mon01_assessment(None, use_case={})
    assert result["Applicability"] == "Not required"
    assert result["Evidence Status"] == "Not Due"


def test_incomplete_mon01_evidence_is_pending():
    assert mon01_assessment({"assessment_status": "Reviewed"})["Evidence Status"] == "Pending"


def test_complete_mon01_draft_is_pending():
    assert mon01_assessment(
        complete_mon01_assessment(assessment_status="Draft")
    )["Evidence Status"] == "Pending"


def test_reviewed_mon01_form_values_are_pending_until_saved():
    unsaved_form_values = complete_mon01_assessment()
    assert unsaved_form_values["assessment_status"] == "Reviewed"
    assert mon01_assessment(None)["Evidence Status"] == "Pending"


def test_complete_reviewed_saved_mon01_evidence_is_available():
    assert mon01_assessment(
        complete_mon01_assessment()
    )["Evidence Status"] == "Available"


def complete_inc01_assessment(**overrides):
    record = {field: f"Planned {field}" for field in INC_01_REQUIRED_TEXT_FIELDS}
    record["assessment_status"] = "Reviewed"
    record.update(overrides)
    return record


def inc01_assessment(evidence, use_case=None):
    return assess_control(
        "INC-01",
        use_case if use_case is not None else {"name": "Citizen Request Prioritisation AI"},
        answers(),
        {"INC-01": evidence} if evidence is not None else {},
    )


def test_inc01_is_required_when_a_use_case_exists():
    assert inc01_assessment(None)["Applicability"] == "Required"


def test_inc01_is_not_required_without_a_use_case():
    result = inc01_assessment(None, use_case={})
    assert result["Applicability"] == "Not required"
    assert result["Evidence Status"] == "Not Due"


def test_incomplete_inc01_evidence_is_pending():
    assert inc01_assessment({"assessment_status": "Reviewed"})["Evidence Status"] == "Pending"


def test_complete_inc01_draft_is_pending():
    assert inc01_assessment(
        complete_inc01_assessment(assessment_status="Draft")
    )["Evidence Status"] == "Pending"


def test_reviewed_inc01_form_values_are_pending_until_saved():
    unsaved_form_values = complete_inc01_assessment()
    assert unsaved_form_values["assessment_status"] == "Reviewed"
    assert inc01_assessment(None)["Evidence Status"] == "Pending"


def test_complete_reviewed_saved_inc01_evidence_is_available():
    assert inc01_assessment(
        complete_inc01_assessment()
    )["Evidence Status"] == "Available"
