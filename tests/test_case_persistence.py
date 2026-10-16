import json
from copy import deepcopy

import pytest

from src.governance.case_persistence import (
    CasePersistenceError,
    DEFAULT_PLANS,
    RISK_ANSWER_KEYS,
    USE_CASE_KEYS,
    load_case,
    restore_case,
    save_case,
)
from src.governance.control_assessment import (
    INC_01_REQUIRED_TEXT_FIELDS,
    MON_01_REQUIRED_TEXT_FIELDS,
    VAL_01_REQUIRED_TEXT_FIELDS,
    assess_control,
)
from src.governance.deployment_readiness import evaluate_readiness


def sample_state():
    use_case = {key: f"Sample {key}" for key in USE_CASE_KEYS}
    use_case["name"] = "Citizen Request Prioritisation AI"
    use_case["ai_role"] = "Recommendation only"
    use_case["human_oversight"] = "Required before action"
    risk_answers = {key: False for key in RISK_ANSWER_KEYS}
    risk_answers["personal_data"] = True
    evidence = {
        "DAT-01": {
            "personal_data_categories": "Citizen requests",
            "purpose_necessity": "Prioritise service requests",
            "data_minimisation": "Only necessary fields",
            "sensitive_data_used": False,
            "sensitive_data_details": "",
            "data_access": "Operations staff",
            "responsible_owner": "Customer Services",
            "retention_deletion": "Delete after 12 months",
            "privacy_risks": "Unauthorised access",
            "mitigations": "Role-based access",
            "privacy_reviewer": "Privacy Reviewer",
            "assessment_status": "Reviewed",
        }
    }
    evidence["MON-01"] = {
        "monitoring_objectives": "Review intended-use performance",
        "performance_metrics": "Plan to review recommendation and override patterns",
        "fairness_disparity_monitoring": "Plan to review relevant groups and areas",
        "human_override_review_monitoring": "Plan to review human overrides",
        "incident_complaint_indicators": "Plan to review incidents and complaints",
        "data_model_drift_indicators": "Plan to review input and output drift indicators",
        "monitoring_thresholds": "Define trigger thresholds before operation",
        "monitoring_frequency": "Set a risk-based review cadence",
        "monitoring_responsibilities": "Business owner coordinates monitoring",
        "threshold_breach_escalation": "Escalate breaches to governance",
        "monitoring_limitations_actions": "No live monitoring is claimed",
        "responsible_owner": "Customer Services",
        "monitoring_reviewer": "Monitoring Reviewer",
        "assessment_status": "Reviewed",
    }
    plans = deepcopy(DEFAULT_PLANS)
    plans["monitoring"] = {key: True for key in plans["monitoring"]}
    plans["incident_response"]["plan_approved"] = True
    return {
        "use_case": use_case,
        "risk_answers": risk_answers,
        "control_evidence": evidence,
        "deployment_readiness_plans": plans,
    }


def test_valid_case_save(tmp_path):
    document = save_case(sample_state(), tmp_path)
    assert document["schema_version"] == 1
    assert (tmp_path / f"{document['case_id']}.json").is_file()


def test_valid_case_load(tmp_path):
    saved = save_case(sample_state(), tmp_path)
    loaded = load_case(saved["case_id"], tmp_path)
    assert loaded == saved


def test_save_load_round_trip_preserves_canonical_case_data(tmp_path):
    state = sample_state()
    document = save_case(state, tmp_path)
    loaded = load_case(document["case_id"], tmp_path)
    assert loaded["use_case"] == state["use_case"]
    assert loaded["risk_answers"] == state["risk_answers"]
    assert loaded["control_evidence"] == state["control_evidence"]
    assert loaded["deployment_readiness_plans"] == state["deployment_readiness_plans"]


def test_case_id_is_stable_across_saves(tmp_path):
    state = sample_state()
    first = save_case(state, tmp_path)
    state["current_case_id"] = first["case_id"]
    second = save_case(state, tmp_path)
    assert second["case_id"] == first["case_id"]
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_derived_risk_is_recalculated_after_load(tmp_path):
    document = save_case(sample_state(), tmp_path)
    state = {"risk_score": 999, "governance_tier": "Stale", "risk_result": None}
    restore_case(state, load_case(document["case_id"], tmp_path))
    assert state["risk_score"] == 2
    assert state["governance_tier"] == "Low"
    assert state["risk_result"].score == 2
    assert state["risk_breakdown"]


def test_invalid_schema_version_is_rejected(tmp_path):
    document = save_case(sample_state(), tmp_path)
    path = tmp_path / f"{document['case_id']}.json"
    content = json.loads(path.read_text(encoding="utf-8"))
    content["schema_version"] = 2
    path.write_text(json.dumps(content), encoding="utf-8")
    with pytest.raises(CasePersistenceError, match="schema version"):
        load_case(document["case_id"], tmp_path)


@pytest.mark.parametrize(
    "answer_change",
    [
        lambda answers: answers.pop("personal_data"),
        lambda answers: answers.__setitem__("personal_data", 1),
    ],
)
def test_invalid_or_missing_risk_answers_are_rejected(tmp_path, answer_change):
    state = sample_state()
    answer_change(state["risk_answers"])
    with pytest.raises(CasePersistenceError, match="answer"):
        save_case(state, tmp_path)


def test_invalid_readiness_plan_structure_is_rejected(tmp_path):
    state = sample_state()
    state["deployment_readiness_plans"]["monitoring"]["plan_defined"] = "yes"
    with pytest.raises(CasePersistenceError, match="must be booleans"):
        save_case(state, tmp_path)


def test_missing_readiness_plan_group_is_rejected(tmp_path):
    state = sample_state()
    state["deployment_readiness_plans"].pop("incident_response")
    with pytest.raises(CasePersistenceError, match="structure is invalid"):
        save_case(state, tmp_path)


def test_malformed_json_is_handled_safely(tmp_path):
    case_id = save_case(sample_state(), tmp_path)["case_id"]
    (tmp_path / f"{case_id}.json").write_text("{broken", encoding="utf-8")
    with pytest.raises(CasePersistenceError, match="Could not read case file"):
        load_case(case_id, tmp_path)


def test_dat01_evidence_survives_round_trip(tmp_path):
    state = sample_state()
    expected = deepcopy(state["control_evidence"]["DAT-01"])
    document = save_case(state, tmp_path)
    assert load_case(document["case_id"], tmp_path)["control_evidence"]["DAT-01"] == expected


def test_fai01_evidence_survives_round_trip(tmp_path):
    state = sample_state()
    state["risk_answers"]["significant_decision"] = True
    state["control_evidence"]["FAI-01"] = {
        "affected_groups": "Citizens relying on municipal services",
        "fairness_risk": "Prioritisation may affect service access",
        "evaluation_approach": "Review representative cases with service teams",
        "data_evaluation_limitations": "No statistical subgroup evaluation performed",
        "findings_observations": "Qualitative review only; no statistical result claimed",
        "mitigation_actions": "Provide human review and monitor complaints",
        "responsible_owner": "Customer Services Directorate",
        "fairness_reviewer": "AI Governance Reviewer",
        "assessment_status": "Reviewed",
    }
    expected = deepcopy(state["control_evidence"]["FAI-01"])
    document = save_case(state, tmp_path)
    loaded = load_case(document["case_id"], tmp_path)
    assert loaded["control_evidence"]["FAI-01"] == expected
    restored = {}
    restore_case(restored, loaded)
    assert restored["control_evidence"]["FAI-01"] == expected
    assert assess_control(
        "FAI-01",
        restored["use_case"],
        restored["risk_answers"],
        restored["control_evidence"],
    )["Evidence Status"] == "Available"


def test_sec01_evidence_survives_save_load_and_remains_available(tmp_path):
    state = sample_state()
    state["control_evidence"]["SEC-01"] = {
        "security_scope": "Application workflow and supporting data",
        "key_security_risks": "Unauthorised access and inappropriate changes",
        "access_control_approach": "Role-based access managed by the service owner",
        "data_protection_measures": "Use approved storage and minimise access",
        "third_party_considerations": "Review provider responsibilities and dependencies",
        "security_monitoring_approach": "Define operational security monitoring before launch",
        "incident_escalation_approach": "Escalate suspected incidents to security and governance leads",
        "security_limitations_actions": "No penetration test or vulnerability scan claimed",
        "responsible_owner": "Customer Services Directorate",
        "security_reviewer": "Information Security Reviewer",
        "assessment_status": "Reviewed",
    }
    expected = deepcopy(state["control_evidence"]["SEC-01"])
    document = save_case(state, tmp_path)
    loaded = load_case(document["case_id"], tmp_path)
    assert loaded["control_evidence"]["SEC-01"] == expected

    restored = {}
    restore_case(restored, loaded)
    assert restored["control_evidence"]["SEC-01"] == expected
    assert assess_control(
        "SEC-01",
        restored["use_case"],
        restored["risk_answers"],
        restored["control_evidence"],
    )["Evidence Status"] == "Available"


def test_trn01_evidence_survives_save_load_and_restores_widget_values(tmp_path):
    state = sample_state()
    state["control_evidence"]["TRN-01"] = {
        "ai_system_purpose": "Prioritise municipal service requests for review",
        "ai_decision_role": "Recommendation only; provides a score for human review",
        "intended_users_stakeholders": "Municipal operations staff; citizens",
        "key_system_limitations": "The score may be incomplete or inaccurate",
        "human_oversight_approach": "Staff review the recommendation before action",
        "information_to_communicate": "Explain the purpose, role, and limitations",
        "communication_disclosure_approach": "Develop and review appropriate disclosure materials",
        "transparency_limitations_actions": "No notice or production disclosure is claimed",
        "responsible_owner": "Customer Services Directorate",
        "transparency_reviewer": "AI Governance Reviewer",
        "assessment_status": "Reviewed",
    }
    expected = deepcopy(state["control_evidence"]["TRN-01"])
    document = save_case(state, tmp_path)
    loaded = load_case(document["case_id"], tmp_path)
    assert loaded["control_evidence"]["TRN-01"] == expected

    restored = {}
    restore_case(restored, loaded)
    assert restored["control_evidence"]["TRN-01"] == expected
    assert assess_control(
        "TRN-01",
        restored["use_case"],
        restored["risk_answers"],
        restored["control_evidence"],
    )["Evidence Status"] == "Available"


def test_val01_evidence_survives_save_load_and_remains_available(tmp_path):
    state = sample_state()
    state["control_evidence"]["VAL-01"] = {
        field: f"Documented {field}" for field in VAL_01_REQUIRED_TEXT_FIELDS
    }
    state["control_evidence"]["VAL-01"]["assessment_status"] = "Reviewed"
    expected = deepcopy(state["control_evidence"]["VAL-01"])
    document = save_case(state, tmp_path)
    loaded = load_case(document["case_id"], tmp_path)
    assert loaded["control_evidence"]["VAL-01"] == expected

    restored = {}
    restore_case(restored, loaded)
    assert restored["control_evidence"]["VAL-01"] == expected
    assert assess_control(
        "VAL-01",
        restored["use_case"],
        restored["risk_answers"],
        restored["control_evidence"],
    )["Evidence Status"] == "Available"


def test_mon01_evidence_survives_save_load_and_remains_available(tmp_path):
    state = sample_state()
    state["control_evidence"]["MON-01"] = {
        field: f"Planned {field}" for field in MON_01_REQUIRED_TEXT_FIELDS
    }
    state["control_evidence"]["MON-01"]["assessment_status"] = "Reviewed"
    expected = deepcopy(state["control_evidence"]["MON-01"])
    document = save_case(state, tmp_path)
    loaded = load_case(document["case_id"], tmp_path)
    assert loaded["control_evidence"]["MON-01"] == expected

    restored = {}
    restore_case(restored, loaded)
    assert restored["control_evidence"]["MON-01"] == expected
    assert assess_control(
        "MON-01",
        restored["use_case"],
        restored["risk_answers"],
        restored["control_evidence"],
    )["Evidence Status"] == "Available"


def test_inc01_evidence_survives_save_load_and_remains_available(tmp_path):
    state = sample_state()
    state["control_evidence"]["INC-01"] = {
        field: f"Planned {field}" for field in INC_01_REQUIRED_TEXT_FIELDS
    }
    state["control_evidence"]["INC-01"]["assessment_status"] = "Reviewed"
    expected = deepcopy(state["control_evidence"]["INC-01"])
    document = save_case(state, tmp_path)
    loaded = load_case(document["case_id"], tmp_path)
    assert loaded["control_evidence"]["INC-01"] == expected

    restored = {}
    restore_case(restored, loaded)
    assert restored["control_evidence"]["INC-01"] == expected
    assert assess_control(
        "INC-01",
        restored["use_case"],
        restored["risk_answers"],
        restored["control_evidence"],
    )["Evidence Status"] == "Available"


def test_loaded_risk_widget_values_match_canonical_answers(tmp_path):
    document = save_case(sample_state(), tmp_path)
    state = {}
    restore_case(state, load_case(document["case_id"], tmp_path))
    for key, value in document["risk_answers"].items():
        assert state[key] is value
    for field, value in document["use_case"].items():
        assert state[f"use_case_{field}"] == value
    for group, fields in document["deployment_readiness_plans"].items():
        for field, value in fields.items():
            assert state[f"deployment_{group}_{field}"] is value


def test_loaded_evidence_and_plans_update_deployment_readiness(tmp_path):
    state_to_save = sample_state()
    state_to_save["control_evidence"]["INC-01"] = {
        field: f"Planned {field}" for field in INC_01_REQUIRED_TEXT_FIELDS
    }
    state_to_save["control_evidence"]["INC-01"]["assessment_status"] = "Reviewed"
    document = save_case(state_to_save, tmp_path)
    state = {}
    restore_case(state, load_case(document["case_id"], tmp_path))
    answers = state["risk_answers"]
    use_case = state["use_case"]
    evidence = state["control_evidence"]
    control_ids = (
        "GOV-01",
        "MAP-01",
        "DAT-01",
        "FAI-01",
        "SEC-01",
        "TRN-01",
        "VAL-01",
        "MON-01",
        "INC-01",
    )
    assessments = {
        control_id: assess_control(
            control_id,
            use_case,
            answers,
            evidence,
        )
        for control_id in control_ids
    }
    result = evaluate_readiness(assessments, state["deployment_readiness_plans"], True)
    assert assessments["DAT-01"]["Evidence Status"] == "Available"
    assert "DAT-01" not in result["blocking_controls"]
    assert result["incomplete_operational_requirements"] == 0


def test_baseline_csv_files_remain_unchanged(tmp_path):
    from pathlib import Path

    data_dir = Path(__file__).resolve().parents[1] / "data"
    baseline_files = ("controls.csv", "ai_inventory.csv", "raci.csv")
    before = {name: (data_dir / name).read_bytes() for name in baseline_files}
    save_case(sample_state(), tmp_path)
    after = {name: (data_dir / name).read_bytes() for name in baseline_files}
    assert after == before
