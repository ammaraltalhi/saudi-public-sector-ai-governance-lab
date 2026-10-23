from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.governance.case_persistence import DEFAULT_PLANS
from src.governance.control_assessment import (
    INC_01_REQUIRED_TEXT_FIELDS,
    MON_01_REQUIRED_TEXT_FIELDS,
    SEC_01_REQUIRED_TEXT_FIELDS,
    TRN_01_REQUIRED_TEXT_FIELDS,
    VAL_01_REQUIRED_TEXT_FIELDS,
    assess_control,
)
from src.governance.deployment_readiness import evaluate_readiness
from src.governance.risk import calculate_risk


ROOT = Path(__file__).resolve().parents[1]
USE_CASE = {
    "name": "Citizen Request Prioritisation AI",
    "owner": "Customer Services Directorate",
    "purpose": "Recommend a priority score for human review.",
    "ai_role": "Recommendation only",
    "human_oversight": "Required before action",
}
RISK_ANSWERS = {
    "personal_data": False,
    "sensitive_data": False,
    "significant_decision": False,
    "vulnerable_groups": False,
    "external_users": True,
    "automated_action": False,
    "third_party_model": False,
    "security_critical": False,
}


def complete_evidence(fields, prefix):
    result = {field: f"{prefix} {field}" for field in fields}
    result["assessment_status"] = "Reviewed"
    return result


def session_state(control_evidence=None):
    result = calculate_risk(RISK_ANSWERS)
    return {
        "use_case": USE_CASE.copy(),
        "risk_answers": RISK_ANSWERS.copy(),
        "risk_result": result,
        "risk_score": result.score,
        "governance_tier": result.level,
        "risk_breakdown": [("External users", 1)],
        "control_evidence": control_evidence or {},
        "deployment_readiness_plans": {
            "monitoring": {
                "plan_defined": True,
                "metrics_defined": True,
                "thresholds_defined": True,
                "responsibilities_defined": True,
            },
            "incident_response": {"plan_approved": True},
        },
    }


def render_dashboard(state):
    app = AppTest.from_file(ROOT / "views" / "dashboard.py")
    for key, value in state.items():
        app.session_state[key] = value
    app.run()
    assert not app.exception
    return app


def metric_values(app):
    return {metric.label: metric.value for metric in app.metric}


def find_control_table(app):
    return next(
        frame.value
        for frame in app.dataframe
        if {"Control ID", "Governance Area", "Applicability", "Evidence Status"}
        <= set(frame.value.columns)
    )


def complete_case_evidence():
    return {
        control_id: complete_evidence(fields, control_id)
        for control_id, fields in (
            ("SEC-01", SEC_01_REQUIRED_TEXT_FIELDS),
            ("TRN-01", TRN_01_REQUIRED_TEXT_FIELDS),
            ("VAL-01", VAL_01_REQUIRED_TEXT_FIELDS),
            ("MON-01", MON_01_REQUIRED_TEXT_FIELDS),
            ("INC-01", INC_01_REQUIRED_TEXT_FIELDS),
        )
    }


def test_dashboard_renders_current_case_and_uses_shared_control_and_readiness_logic():
    state = session_state()
    app = render_dashboard(state)

    assert any(item.value == "AI Use Case Summary" for item in app.subheader)
    assert any(item.value == "Executive Snapshot" for item in app.subheader)
    rendered_markdown = "\n".join(item.value for item in app.markdown)
    assert "max-width: 1160px" in rendered_markdown
    for summary_value in (
        USE_CASE["name"],
        USE_CASE["owner"],
        USE_CASE["purpose"],
        USE_CASE["ai_role"],
        USE_CASE["human_oversight"],
    ):
        assert summary_value in rendered_markdown
    assert any(
        item.value == "Final deployment approval remains a human governance decision."
        for item in app.info
    )
    metrics = metric_values(app)
    assert int(metrics["Risk Score"]) == state["risk_result"].score
    assert metrics["Governance Tier"] == state["risk_result"].level
    assert int(metrics["Required Controls"]) > 0
    assert int(metrics["Pending Controls"]) > 0
    assert int(metrics["Evidence Available"]) > 0
    assert any("Triggered risk factors: 1" in item.value for item in app.caption)

    catalogue = pd.read_csv(ROOT / "data" / "controls.csv")
    shared_assessments = {
        row["Control ID"]: assess_control(
            row["Control ID"],
            USE_CASE,
            RISK_ANSWERS,
            {},
            True,
            True,
        )
        for _, row in catalogue.iterrows()
    }
    table = find_control_table(app)
    assert list(table["Control ID"]) == list(catalogue["Control ID"])
    for control_id, assessment in shared_assessments.items():
        row = table.loc[table["Control ID"] == control_id].iloc[0]
        assert row["Applicability"] == assessment["Applicability"]
        assert row["Evidence Status"] == assessment["Evidence Status"]

    expected_readiness = evaluate_readiness(
        shared_assessments,
        state["deployment_readiness_plans"],
        True,
    )
    metrics = metric_values(app)
    assert int(metrics["Blocking controls"]) == len(expected_readiness["blocking_controls"])
    assert int(metrics["Incomplete operational requirements"]) == expected_readiness[
        "incomplete_operational_requirements"
    ]
    readiness_messages = [
        item.value for item in (*app.success, *app.warning)
    ]
    assert expected_readiness["status"] in readiness_messages
    outstanding = next(
        frame.value
        for frame in app.dataframe
        if "Current blockers and actions" in frame.value.columns
    )
    assert any(
        item.startswith("SEC-01:")
        for item in outstanding["Current blockers and actions"]
    )


def test_dashboard_derives_operational_readiness_only_from_mon01_and_inc01():
    evidence = complete_evidence(MON_01_REQUIRED_TEXT_FIELDS, "MON plan")
    state = session_state({"MON-01": evidence})
    app = render_dashboard(state)

    operational = next(
        frame.value
        for frame in app.dataframe
        if "Operational requirement" in frame.value.columns
    )
    status_by_requirement = dict(
        zip(
            operational["Operational requirement"],
            operational["Status"],
        )
    )
    assert status_by_requirement == {
        "Monitoring plan": "Complete",
        "Metrics defined": "Complete",
        "Thresholds defined": "Complete",
        "Responsibilities defined": "Complete",
        "Incident response and escalation plan": "Incomplete",
    }
    metrics = metric_values(app)
    assert int(metrics["Incomplete operational requirements"]) == 1
    assert any(
        item.value == "Not Ready for Deployment Approval"
        for item in app.warning
    )


def test_dashboard_complete_control_evidence_still_requires_national_risk_decision():
    app = render_dashboard(session_state(complete_case_evidence()))
    metrics = metric_values(app)

    assert int(metrics["Blocking controls"]) == 0
    assert int(metrics["Incomplete operational requirements"]) == 0
    assert any(
        item.value == "Not Ready for Deployment Approval"
        for item in app.warning
    )
    assert not any(
        item.value == "Approved for Deployment"
        for item in (*app.success, *app.warning, *app.subheader)
    )
    assert not any(
        "No current governance-readiness blockers are identified."
        in item.value
        for item in app.success
    )
    assert any(
        "RET-01" in frame.value.iloc[0, 0]
        for frame in app.dataframe
        if "Lifecycle follow-up" in frame.value.columns
    )
    assert any(
        item.value == "Final deployment approval remains a human governance decision."
        for item in app.info
    )
    assert any(
        "not a legal compliance determination, certification, or automatic deployment approval"
        in item.value
        for item in app.caption
    )
def test_dashboard_without_loaded_case_prompts_for_use_case():
    app = render_dashboard({})
    assert any(
        "Load or complete an AI use case" in item.value
        for item in app.info
    )
