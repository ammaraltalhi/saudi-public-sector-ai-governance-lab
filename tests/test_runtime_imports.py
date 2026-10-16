import importlib
import json
import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from src.governance.case_persistence import (
    DEFAULT_PLANS,
    DAT01_WIDGET_KEYS,
    FAI01_WIDGET_KEYS,
    INC01_WIDGET_KEYS,
    MON01_WIDGET_KEYS,
    RISK_ANSWER_KEYS,
    SEC01_WIDGET_KEYS,
    TRN01_WIDGET_KEYS,
    VAL01_WIDGET_KEYS,
    USE_CASE_KEYS,
    load_case,
    restore_case,
    save_case,
)
from src.governance.control_assessment import assess_control
from src.governance.control_assessment import (
    INC_01_REQUIRED_TEXT_FIELDS,
    MON_01_REQUIRED_TEXT_FIELDS,
    SEC_01_REQUIRED_TEXT_FIELDS,
    TRN_01_REQUIRED_TEXT_FIELDS,
    VAL_01_REQUIRED_TEXT_FIELDS,
)
from src.governance.risk import calculate_risk


MODULES = (
    "src.governance.control_assessment",
    "src.governance.deployment_readiness",
    "views.controls",
    "views.deployment_readiness",
    "app",
)

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


def test_requested_modules_import(monkeypatch):
    import streamlit as st

    state = {
        "use_case": {
            "name": "Runtime import validation",
            "human_oversight": "Required before action",
            "ai_role": "Decision support",
        },
        "risk_answers": {key: False for key in SCREENING_KEYS},
        "risk_score": 0,
        "governance_tier": "Low",
    }
    stubs = {
        "session_state": state,
        "title": lambda *args, **kwargs: None,
        "write": lambda *args, **kwargs: None,
        "warning": lambda *args, **kwargs: None,
        "subheader": lambda *args, **kwargs: None,
        "info": lambda *args, **kwargs: None,
        "dataframe": lambda *args, **kwargs: None,
        "form": lambda *args, **kwargs: nullcontext(),
        "form_submit_button": lambda *args, **kwargs: False,
        "text_area": lambda *args, **kwargs: "",
        "text_input": lambda *args, **kwargs: "",
        "selectbox": lambda label, options, **kwargs: options[0],
        "expander": lambda *args, **kwargs: nullcontext(),
        "checkbox": lambda label, value=False, **kwargs: value,
        "set_page_config": lambda *args, **kwargs: None,
        "Page": lambda *args, **kwargs: object(),
        "navigation": lambda *args, **kwargs: SimpleNamespace(run=lambda: None),
    }
    for name, stub in stubs.items():
        monkeypatch.setattr(st, name, stub)

    for module_name in MODULES:
        sys.modules.pop(module_name, None)
        importlib.import_module(module_name)


def test_deployment_readiness_executes_in_streamlit_runtime():
    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "views" / "deployment_readiness.py"
    )
    app.session_state["use_case"] = {
        "name": "Runtime page execution",
        "human_oversight": "Required before action",
        "ai_role": "Decision support",
    }
    app.session_state["risk_answers"] = {key: False for key in SCREENING_KEYS}
    app.session_state["risk_score"] = 0
    app.session_state["governance_tier"] = "Low"

    app.run()

    assert not app.exception


def test_app_entry_point_runs_with_case_management_sidebar():
    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "app.py"
    ).run()

    assert not app.exception
    assert {button.label for button in app.button} >= {"Save Case", "Load Case"}


def test_control_library_saves_reviewed_dat01_evidence():
    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "views" / "controls.py"
    )
    app.session_state["use_case"] = {
        "name": "Citizen Request Prioritisation AI",
        "owner": "Customer Services",
        "purpose": "Prioritise service requests",
        "data": "Citizen requests; location area; timestamps",
    }
    app.session_state["risk_answers"] = {
        key: key == "personal_data" for key in SCREENING_KEYS
    }
    app.run()

    for index, value in enumerate(
        (
            "Minimum necessary fields only",
            "Operations staff with role access",
            "Delete after 12 months",
            "Potential re-identification",
            "Limit access and review logs",
        ),
        start=2,
    ):
        app.text_area[index].set_value(value)
    app.text_input[1].set_value("Privacy Reviewer")
    app.selectbox[0].select("Reviewed")
    app.button[0].click().run()

    assert not app.exception
    evidence = app.session_state["control_evidence"]["DAT-01"]
    assert evidence["assessment_status"] == "Reviewed"
    assert evidence["privacy_reviewer"] == "Privacy Reviewer"


def test_control_library_saves_reviewed_fai01_evidence():
    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "views" / "controls.py"
    )
    app.session_state["use_case"] = {
        "name": "Citizen Request Prioritisation AI",
        "owner": "Customer Services Directorate",
        "affected_people": "Citizens submitting service requests",
    }
    app.session_state["risk_answers"] = {
        key: key in {"significant_decision", "vulnerable_groups"}
        for key in SCREENING_KEYS
    }
    app.run()

    text_values = {
        "Affected groups": "Citizens relying on municipal services",
        "Fairness risk": "Prioritisation could affect service access",
        "Evaluation approach": "Qualitative review with service teams",
        "Data / evaluation limitations": "No statistical subgroup evaluation performed",
        "Findings / observations": "Qualitative observations only; no statistical results claimed",
        "Mitigation actions": "Human review and monitor complaints",
    }
    for index, widget in enumerate(app.text_area):
        if widget.label in text_values:
            app.text_area[index].set_value(text_values[widget.label])
    for index, widget in enumerate(app.text_input):
        if widget.label == "Responsible owner":
            app.text_input[index].set_value("Customer Services Directorate")
        elif widget.label == "Fairness / AI Governance reviewer":
            app.text_input[index].set_value("AI Governance Reviewer")
    for index, widget in enumerate(app.selectbox):
        if widget.label == "FAI-01 assessment status":
            app.selectbox[index].select("Reviewed")
    assert "FAI-01" not in app.session_state.get("control_evidence", {})
    assert assess_control(
        "FAI-01",
        app.session_state["use_case"],
        app.session_state["risk_answers"],
        app.session_state.get("control_evidence", {}),
    )["Evidence Status"] == "Pending"
    submit_index = next(
        index
        for index, button in enumerate(app.button)
        if button.label == "Save FAI-01 assessment"
    )
    app.button[submit_index].click().run()

    assert not app.exception
    evidence = app.session_state["control_evidence"]["FAI-01"]
    assert evidence["assessment_status"] == "Reviewed"
    assert evidence["fairness_reviewer"] == "AI Governance Reviewer"
    assert assess_control(
        "FAI-01",
        app.session_state["use_case"],
        app.session_state["risk_answers"],
        app.session_state["control_evidence"],
    )["Evidence Status"] == "Available"


def test_control_library_saves_reviewed_sec01_evidence():
    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "views" / "controls.py"
    )
    app.session_state["use_case"] = {
        "name": "Citizen Request Prioritisation AI",
        "owner": "Customer Services Directorate",
    }
    app.session_state["risk_answers"] = {
        key: False for key in SCREENING_KEYS
    }
    app.run()

    field_values = {
        "System / AI security scope": "Application workflow and supporting data",
        "Key security risks": "Unauthorised access and inappropriate changes",
        "Access control approach": "Role-based access managed by the service owner",
        "Data protection / secure handling measures": "Approved storage and limited access",
        "Third-party / dependency considerations": "Review provider responsibilities",
        "Security monitoring approach": "Define monitoring before operational launch",
        "Incident / escalation approach": "Escalate incidents to security and governance leads",
        "Security limitations / outstanding actions": "No penetration test or scan results are claimed",
    }
    for index, widget in enumerate(app.text_area):
        if widget.label in field_values:
            app.text_area[index].set_value(field_values[widget.label])
    for index, widget in enumerate(app.text_input):
        if widget.label == "Responsible owner":
            app.text_input[index].set_value("Customer Services Directorate")
        elif widget.label == "Security reviewer":
            app.text_input[index].set_value("Information Security Reviewer")
    for index, widget in enumerate(app.selectbox):
        if widget.label == "SEC-01 assessment status":
            app.selectbox[index].select("Reviewed")

    assert "SEC-01" not in app.session_state.get("control_evidence", {})
    assert assess_control(
        "SEC-01",
        app.session_state["use_case"],
        app.session_state["risk_answers"],
        app.session_state.get("control_evidence", {}),
    )["Evidence Status"] == "Pending"

    submit_index = next(
        index
        for index, button in enumerate(app.button)
        if button.label == "Save SEC-01 assessment"
    )
    app.button[submit_index].click().run()

    assert not app.exception
    evidence = app.session_state["control_evidence"]["SEC-01"]
    assert evidence["assessment_status"] == "Reviewed"
    assert evidence["security_reviewer"] == "Information Security Reviewer"
    assert assess_control(
        "SEC-01",
        app.session_state["use_case"],
        app.session_state["risk_answers"],
        app.session_state["control_evidence"],
    )["Evidence Status"] == "Available"


def test_control_library_saves_reviewed_trn01_evidence_and_prefills_case_context():
    use_case = {
        "name": "Citizen Request Prioritisation AI",
        "owner": "Customer Services Directorate",
        "purpose": "Prioritise municipal service requests for operational review.",
        "users": "Municipal operations staff",
        "affected_people": "Citizens submitting service requests",
        "decision": "Recommended priority score for human review",
        "ai_role": "Recommendation only",
        "human_oversight": "Required before action",
    }
    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "views" / "controls.py"
    )
    app.session_state["use_case"] = use_case
    app.session_state["risk_answers"] = {
        key: False for key in SCREENING_KEYS
    }
    app.run()

    assert not app.exception
    assert app.session_state["trn01_ai_system_purpose"] == use_case["purpose"]
    assert app.session_state["trn01_ai_decision_role"] == (
        f'{use_case["ai_role"]}; {use_case["decision"]}'
    )
    assert app.session_state["trn01_intended_users_stakeholders"] == (
        f'{use_case["users"]}; {use_case["affected_people"]}'
    )
    assert app.session_state["trn01_human_oversight_approach"] == (
        use_case["human_oversight"]
    )
    assert app.session_state["trn01_responsible_owner"] == use_case["owner"]
    assert "TRN-01" not in app.session_state.get("control_evidence", {})
    assert assess_control(
        "TRN-01",
        app.session_state["use_case"],
        app.session_state["risk_answers"],
        app.session_state.get("control_evidence", {}),
    )["Evidence Status"] == "Pending"

    field_values = {
        "Key system limitations": "Recommendations may be incomplete or inaccurate.",
        "Information to be communicated": "Explain that staff make final decisions.",
        "Communication / disclosure approach": "Develop and review appropriate materials before use.",
        "Transparency limitations / outstanding actions": "No notices or production disclosures are claimed.",
    }
    for index, widget in enumerate(app.text_area):
        if widget.label in field_values:
            app.text_area[index].set_value(field_values[widget.label])
    for index, widget in enumerate(app.text_input):
        if widget.label == "Transparency / AI Governance reviewer":
            app.text_input[index].set_value("AI Governance Reviewer")
    for index, widget in enumerate(app.selectbox):
        if widget.label == "TRN-01 assessment status":
            app.selectbox[index].select("Reviewed")

    submit_index = next(
        index
        for index, button in enumerate(app.button)
        if button.label == "Save TRN-01 assessment"
    )
    app.button[submit_index].click().run()

    assert not app.exception
    evidence = app.session_state["control_evidence"]["TRN-01"]
    assert evidence["assessment_status"] == "Reviewed"
    assert evidence["transparency_reviewer"] == "AI Governance Reviewer"
    assert assess_control(
        "TRN-01",
        app.session_state["use_case"],
        app.session_state["risk_answers"],
        app.session_state["control_evidence"],
    )["Evidence Status"] == "Available"
    assert any(
        "does not prove that real-world disclosures or communications have occurred"
        in caption.value
        for caption in app.caption
    )


def test_trn01_save_case_restart_load_and_resave_preserves_every_field(
    tmp_path, monkeypatch
):
    import src.governance.case_persistence as case_persistence

    original_save_case = case_persistence.save_case
    original_load_case = case_persistence.load_case
    original_list_saved_cases = case_persistence.list_saved_cases

    monkeypatch.setattr(
        case_persistence,
        "save_case",
        lambda session_state, _cases_dir: original_save_case(session_state, tmp_path),
    )
    monkeypatch.setattr(
        case_persistence,
        "load_case",
        lambda case_id, _cases_dir: original_load_case(case_id, tmp_path),
    )
    monkeypatch.setattr(
        case_persistence,
        "list_saved_cases",
        lambda _cases_dir: original_list_saved_cases(tmp_path),
    )

    use_case = {key: f"Case {key}" for key in USE_CASE_KEYS}
    use_case.update({
        "name": "Citizen Request Prioritisation AI",
        "owner": "Use-case owner",
        "purpose": "Use-case purpose",
        "users": "Use-case staff",
        "affected_people": "Use-case citizens",
        "decision": "Priority score recommendation",
        "ai_role": "Recommendation only",
        "human_oversight": "Required before action",
    })
    risk_answers = {key: False for key in RISK_ANSWER_KEYS}
    evidence = {
        "ai_system_purpose": "TRN purpose entered in the form",
        "ai_decision_role": "Recommendation only; a person decides",
        "intended_users_stakeholders": "Operations staff and service users",
        "key_system_limitations": "The output may be incomplete",
        "human_oversight_approach": "Staff review before any action",
        "information_to_communicate": "Explain purpose, role, and limitations",
        "communication_disclosure_approach": "Prepare disclosures for review before use",
        "transparency_limitations_actions": "No disclosure is claimed to have been issued",
        "responsible_owner": "TRN responsible transparency owner",
        "transparency_reviewer": "TRN AI Governance reviewer",
        "assessment_status": "Reviewed",
    }
    initial_case = original_save_case(
        {
            "use_case": use_case,
            "risk_answers": risk_answers,
            "control_evidence": {},
            "deployment_readiness_plans": DEFAULT_PLANS,
        },
        tmp_path,
    )
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()
    initial_case_selector = next(
        index for index, selectbox in enumerate(app.selectbox)
        if selectbox.label == "Saved cases"
    )
    app.selectbox[initial_case_selector].select(initial_case["case_id"])
    initial_load_button = next(
        index for index, button in enumerate(app.button)
        if button.label == "Load Case"
    )
    app.button[initial_load_button].click().run()
    app.switch_page("views/controls.py").run()

    form_values = {
        "AI system purpose": evidence["ai_system_purpose"],
        "AI role in decision-making": evidence["ai_decision_role"],
        "Intended users / affected stakeholders": evidence["intended_users_stakeholders"],
        "Key system limitations": evidence["key_system_limitations"],
        "Human oversight approach": evidence["human_oversight_approach"],
        "Information to be communicated": evidence["information_to_communicate"],
        "Communication / disclosure approach": evidence["communication_disclosure_approach"],
        "Transparency limitations / outstanding actions": evidence["transparency_limitations_actions"],
    }
    for index, widget in enumerate(app.text_area):
        if widget.label in form_values:
            app.text_area[index].set_value(form_values[widget.label])
    for index, widget in enumerate(app.text_input):
        if widget.label == "Responsible transparency owner":
            app.text_input[index].set_value(evidence["responsible_owner"])
        elif widget.label == "Transparency / AI Governance reviewer":
            app.text_input[index].set_value(evidence["transparency_reviewer"])
    for index, widget in enumerate(app.selectbox):
        if widget.label == "TRN-01 assessment status":
            app.selectbox[index].select("Reviewed")

    save_assessment_index = next(
        index for index, button in enumerate(app.button)
        if button.label == "Save TRN-01 assessment"
    )
    app.button[save_assessment_index].click().run()
    assert not app.exception
    assert app.session_state["control_evidence"]["TRN-01"] == evidence
    assert assess_control(
        "TRN-01",
        app.session_state["use_case"],
        app.session_state["risk_answers"],
        app.session_state["control_evidence"],
    )["Evidence Status"] == "Available"

    save_case_button = next(
        index for index, button in enumerate(app.button)
        if button.label == "Save Case"
    )
    app.button[save_case_button].click().run()
    saved_case_id = app.session_state["current_case_id"]
    saved_case = load_case(saved_case_id, tmp_path)
    case_path = tmp_path / f"{saved_case['case_id']}.json"
    with case_path.open(encoding="utf-8") as case_file:
        disk_document = json.load(case_file)
    assert disk_document["control_evidence"]["TRN-01"] == evidence
    assert set(disk_document["control_evidence"]["TRN-01"]) == set(evidence)
    assert disk_document["control_evidence"]["TRN-01"]["assessment_status"] == "Reviewed"

    # A new AppTest session simulates stopping and restarting Streamlit.
    fresh_app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "app.py"
    ).run()
    saved_case_selector = next(
        index for index, selectbox in enumerate(fresh_app.selectbox)
        if selectbox.label == "Saved cases"
    )
    fresh_app.selectbox[saved_case_selector].select(saved_case["case_id"])
    load_case_button = next(
        index for index, button in enumerate(fresh_app.button)
        if button.label == "Load Case"
    )
    fresh_app.button[load_case_button].click().run()
    assert not fresh_app.exception
    fresh_app.switch_page("views/controls.py").run()
    assert not fresh_app.exception

    def assert_saved_form_is_visible():
        assert fresh_app.session_state["control_evidence"]["TRN-01"] == evidence
        for field, expected in evidence.items():
            widget_key = f"trn01_{field}_{fresh_app.session_state['_case_load_generation']}"
            widgets = [
                widget
                for widget in (
                    *fresh_app.text_area,
                    *fresh_app.text_input,
                    *fresh_app.selectbox,
                )
                if widget.key == widget_key
            ]
            assert len(widgets) == 1, field
            assert widgets[0].value == expected, field
        assert assess_control(
            "TRN-01",
            fresh_app.session_state["use_case"],
            fresh_app.session_state["risk_answers"],
            fresh_app.session_state["control_evidence"],
        )["Evidence Status"] == "Available"
        table = next(
            dataframe.value
            for dataframe in fresh_app.dataframe
            if "Control ID" in dataframe.value.columns
        )
        assert table.loc[table["Control ID"] == "TRN-01", "Evidence Status"].iloc[0] == "Available"

    assert_saved_form_is_visible()
    fresh_app.switch_page("views/risk_assessment.py").run()
    fresh_app.switch_page("views/controls.py").run()
    assert not fresh_app.exception
    assert_saved_form_is_visible()

    resave_button = next(
        index for index, button in enumerate(fresh_app.button)
        if button.label == "Save Case"
    )
    fresh_app.button[resave_button].click().run()
    resaved_case_id = fresh_app.session_state["current_case_id"]
    with (tmp_path / f"{resaved_case_id}.json").open(encoding="utf-8") as case_file:
        resaved_document = json.load(case_file)
    assert resaved_document["control_evidence"]["TRN-01"] == evidence


def test_mon01_save_case_restart_load_and_readiness_integration(tmp_path, monkeypatch):
    import src.governance.case_persistence as case_persistence

    original_save_case = case_persistence.save_case
    original_load_case = case_persistence.load_case
    original_list_saved_cases = case_persistence.list_saved_cases
    monkeypatch.setattr(
        case_persistence,
        "save_case",
        lambda session_state, _cases_dir: original_save_case(session_state, tmp_path),
    )
    monkeypatch.setattr(
        case_persistence,
        "load_case",
        lambda case_id, _cases_dir: original_load_case(case_id, tmp_path),
    )
    monkeypatch.setattr(
        case_persistence,
        "list_saved_cases",
        lambda _cases_dir: original_list_saved_cases(tmp_path),
    )

    use_case = {key: f"Case {key}" for key in USE_CASE_KEYS}
    use_case.update({
        "name": "Citizen Request Prioritisation AI",
        "owner": "Customer Services Directorate",
        "purpose": "Prioritise municipal service requests for operational review.",
        "users": "Municipal operations staff",
        "affected_people": "Citizens submitting service requests",
        "decision": "Recommended priority score for human review",
        "ai_role": "Recommendation only",
        "human_oversight": "Required before action",
    })
    risk_answers = {key: False for key in RISK_ANSWER_KEYS}
    initial_case = original_save_case(
        {
            "use_case": use_case,
            "risk_answers": risk_answers,
            "control_evidence": {},
            "deployment_readiness_plans": DEFAULT_PLANS,
        },
        tmp_path,
    )

    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()
    case_selector = next(
        index for index, selectbox in enumerate(app.selectbox)
        if selectbox.label == "Saved cases"
    )
    app.selectbox[case_selector].select(initial_case["case_id"])
    load_button = next(
        index for index, button in enumerate(app.button)
        if button.label == "Load Case"
    )
    app.button[load_button].click().run()
    app.switch_page("views/controls.py").run()

    evidence = {
        "monitoring_objectives": "Monitor intended-use performance and support human review.",
        "performance_metrics": "Track recommendation distributions, timeliness, and human overrides; no observed metrics are claimed.",
        "fairness_disparity_monitoring": "Review planned outcomes across relevant groups and service areas; no results are claimed.",
        "human_override_review_monitoring": "Track planned override and review patterns for governance follow-up.",
        "incident_complaint_indicators": "Monitor incident reports and complaint themes without asserting any current volumes.",
        "data_model_drift_indicators": "Define checks for changes in input data and recommendation patterns; no drift results are claimed.",
        "monitoring_thresholds": "Agree trigger conditions and thresholds with service and governance owners before operation.",
        "monitoring_frequency": "Set review cadence based on service criticality and operational use.",
        "monitoring_responsibilities": "Business owner coordinates review with operations, AI/Product, and governance roles.",
        "threshold_breach_escalation": "Escalate threshold breaches for human investigation and documented governance action.",
        "monitoring_limitations_actions": "No live production monitoring or operational history exists in this prototype.",
        "responsible_owner": "Customer Services Directorate",
        "monitoring_reviewer": "AI Governance Monitoring Reviewer",
        "assessment_status": "Reviewed",
    }
    form_labels = {
        "Monitoring objectives": "monitoring_objectives",
        "Performance metrics to monitor": "performance_metrics",
        "Fairness / disparity monitoring": "fairness_disparity_monitoring",
        "Human override / review monitoring": "human_override_review_monitoring",
        "Incident and complaint indicators": "incident_complaint_indicators",
        "Data / model drift indicators": "data_model_drift_indicators",
        "Monitoring thresholds / trigger conditions": "monitoring_thresholds",
        "Monitoring frequency": "monitoring_frequency",
        "Monitoring responsibilities": "monitoring_responsibilities",
        "Escalation when thresholds are breached": "threshold_breach_escalation",
        "Monitoring limitations / outstanding actions": "monitoring_limitations_actions",
    }
    for index, widget in enumerate(app.text_area):
        if widget.label in form_labels:
            app.text_area[index].set_value(evidence[form_labels[widget.label]])
    for index, widget in enumerate(app.text_input):
        if widget.label == "Responsible monitoring owner":
            app.text_input[index].set_value(evidence["responsible_owner"])
        elif widget.label == "Monitoring reviewer":
            app.text_input[index].set_value(evidence["monitoring_reviewer"])
    for index, widget in enumerate(app.selectbox):
        if widget.label == "MON-01 assessment status":
            app.selectbox[index].select("Reviewed")

    save_mon_button = next(
        index for index, button in enumerate(app.button)
        if button.label == "Save MON-01 assessment"
    )
    app.button[save_mon_button].click().run()
    assert not app.exception
    assert app.session_state["control_evidence"]["MON-01"] == evidence
    assert assess_control(
        "MON-01",
        app.session_state["use_case"],
        app.session_state["risk_answers"],
        app.session_state["control_evidence"],
    )["Evidence Status"] == "Available"

    save_case_button = next(
        index for index, button in enumerate(app.button)
        if button.label == "Save Case"
    )
    app.button[save_case_button].click().run()
    saved_case_id = app.session_state["current_case_id"]
    saved_path = tmp_path / f"{saved_case_id}.json"
    with saved_path.open(encoding="utf-8") as case_file:
        disk_document = json.load(case_file)
    assert disk_document["control_evidence"]["MON-01"] == evidence
    assert set(disk_document["control_evidence"]["MON-01"]) == set(evidence)
    assert disk_document["control_evidence"]["MON-01"]["assessment_status"] == "Reviewed"

    # A fresh app instance models a complete Streamlit restart.
    fresh_app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "app.py"
    ).run()
    fresh_selector = next(
        index for index, selectbox in enumerate(fresh_app.selectbox)
        if selectbox.label == "Saved cases"
    )
    fresh_app.selectbox[fresh_selector].select(saved_case_id)
    fresh_load_button = next(
        index for index, button in enumerate(fresh_app.button)
        if button.label == "Load Case"
    )
    fresh_app.button[fresh_load_button].click().run()
    fresh_app.switch_page("views/controls.py").run()
    assert not fresh_app.exception

    def assert_monitoring_form_restored():
        assert fresh_app.session_state["control_evidence"]["MON-01"] == evidence
        generation = fresh_app.session_state["_case_load_generation"]
        for field, expected in evidence.items():
            widget_key = f"{MON01_WIDGET_KEYS[field]}_{generation}"
            widgets = [
                widget
                for widget in (
                    *fresh_app.text_area,
                    *fresh_app.text_input,
                    *fresh_app.selectbox,
                )
                if widget.key == widget_key
            ]
            assert len(widgets) == 1, field
            assert widgets[0].value == expected, field
        control_table = next(
            dataframe.value
            for dataframe in fresh_app.dataframe
            if "Control ID" in dataframe.value.columns
        )
        assert control_table.loc[
            control_table["Control ID"] == "MON-01", "Evidence Status"
        ].iloc[0] == "Available"

    assert_monitoring_form_restored()
    fresh_app.switch_page("views/deployment_readiness.py").run()
    assert not fresh_app.exception
    for checkbox_key in (
        "readiness_mon01_plan_defined",
        "readiness_mon01_metrics_defined",
        "readiness_mon01_thresholds_defined",
        "readiness_mon01_responsibilities_defined",
    ):
        checkbox = next(widget for widget in fresh_app.checkbox if widget.key == checkbox_key)
        assert checkbox.value is True
        assert checkbox.disabled is True
    incident_checkbox = next(
        widget
        for widget in fresh_app.checkbox
        if widget.label == "Incident response and escalation plan approved"
    )
    assert incident_checkbox.value is False
    assert any(
        "Number of incomplete operational requirements:** 1" in markdown.value
        for markdown in fresh_app.markdown
    )
    assert any(
        element.value == "Not Ready for Deployment Approval"
        for element in fresh_app.subheader
    )

    fresh_app.switch_page("views/risk_assessment.py").run()
    fresh_app.switch_page("views/controls.py").run()
    assert not fresh_app.exception
    assert_monitoring_form_restored()

    fresh_save_button = next(
        index for index, button in enumerate(fresh_app.button)
        if button.label == "Save Case"
    )
    fresh_app.button[fresh_save_button].click().run()
    resaved_id = fresh_app.session_state["current_case_id"]
    with (tmp_path / f"{resaved_id}.json").open(encoding="utf-8") as case_file:
        resaved_document = json.load(case_file)
    assert resaved_document["control_evidence"]["MON-01"] == evidence


def test_inc01_save_restart_load_hydration_navigation_and_readiness(tmp_path, monkeypatch):
    import src.governance.case_persistence as case_persistence

    original_save_case = case_persistence.save_case
    original_load_case = case_persistence.load_case
    original_list_saved_cases = case_persistence.list_saved_cases
    monkeypatch.setattr(
        case_persistence,
        "save_case",
        lambda session_state, _cases_dir: original_save_case(session_state, tmp_path),
    )
    monkeypatch.setattr(
        case_persistence,
        "load_case",
        lambda case_id, _cases_dir: original_load_case(case_id, tmp_path),
    )
    monkeypatch.setattr(
        case_persistence,
        "list_saved_cases",
        lambda _cases_dir: original_list_saved_cases(tmp_path),
    )

    use_case = {key: f"Case {key}" for key in USE_CASE_KEYS}
    use_case.update({
        "name": "Citizen Request Prioritisation AI",
        "owner": "Customer Services Directorate",
        "purpose": "Prioritise service requests for operational review.",
        "ai_role": "Recommendation only",
        "decision": "Recommended priority score for human review",
        "human_oversight": "Required before action",
    })
    risk_answers = {key: False for key in RISK_ANSWER_KEYS}
    baseline_evidence = {}
    for control_id, fields in (
        ("SEC-01", SEC_01_REQUIRED_TEXT_FIELDS),
        ("TRN-01", TRN_01_REQUIRED_TEXT_FIELDS),
        ("VAL-01", VAL_01_REQUIRED_TEXT_FIELDS),
        ("MON-01", MON_01_REQUIRED_TEXT_FIELDS),
    ):
        baseline_evidence[control_id] = {
            field: f"Documented plan for {field}" for field in fields
        }
        baseline_evidence[control_id]["assessment_status"] = "Reviewed"
    initial_case = original_save_case(
        {
            "use_case": use_case,
            "risk_answers": risk_answers,
            "control_evidence": baseline_evidence,
            "deployment_readiness_plans": DEFAULT_PLANS,
        },
        tmp_path,
    )

    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run()
    selector = next(i for i, widget in enumerate(app.selectbox) if widget.label == "Saved cases")
    app.selectbox[selector].select(initial_case["case_id"])
    load_button = next(i for i, button in enumerate(app.button) if button.label == "Load Case")
    app.button[load_button].click().run()
    app.switch_page("views/controls.py").run()
    assert not app.exception
    app.session_state["readiness_inc01_plan_approved"] = True
    app.switch_page("views/deployment_readiness.py").run()
    incident_requirement = next(
        widget
        for widget in app.checkbox
        if widget.label == "Incident response and escalation plan approved"
    )
    assert incident_requirement.value is False
    assert incident_requirement.disabled is True
    assert any(
        "Number of incomplete operational requirements:** 1" in markdown.value
        for markdown in app.markdown
    )
    app.switch_page("views/controls.py").run()
    assert not app.exception

    evidence = {
        field: f"Documented incident-response plan for {field}"
        for field in INC_01_REQUIRED_TEXT_FIELDS
    }
    evidence.update({
        "incident_definition_scope": (
            "Material failures, harmful recommendations, repeated errors, or "
            "events affecting service, people, privacy, or security."
        ),
        "detection_reporting_channels": (
            "Staff reports, service complaints, monitoring alerts, and "
            "security or privacy reporting channels."
        ),
        "initial_assessment_triage": (
            "A designated lead assesses severity, recurrence, affected people, "
            "service impact, and available human oversight."
        ),
        "severity_impact_classification": (
            "Classify proportionately by severity, recurrence, affected people, "
            "service impact, and privacy or security implications."
        ),
        "immediate_containment_actions": (
            "Consider human correction, increased oversight, restrictions, "
            "rollback, or temporary suspension as appropriate to the risk."
        ),
        "human_review_decision_correction": (
            "Route affected recommendations for human review and correction "
            "where appropriate."
        ),
        "escalation_criteria": (
            "Escalate based on material impact, recurrence, inability to maintain "
            "meaningful oversight, or privacy/security implications."
        ),
        "escalation_roles_notifications": (
            "Notify the service owner and relevant AI governance, operations, "
            "privacy, or security leads according to severity."
        ),
        "investigation_root_cause_approach": (
            "Review relevant records, affected decisions, system inputs, and "
            "operational context; document uncertainties."
        ),
        "corrective_preventive_actions": (
            "Assign proportionate corrective actions, owners, and follow-up "
            "reviews before normal use resumes where required."
        ),
        "recovery_return_to_service": (
            "Resume or expand use only after responsible human review confirms "
            "risks are controlled and oversight is meaningful."
        ),
        "incident_documentation_records": (
            "Record reports, triage, decisions, actions, owners, and follow-up "
            "in the designated governance record."
        ),
        "post_incident_review_lessons": (
            "Review lessons and update controls, communications, monitoring, "
            "or procedures as appropriate."
        ),
        "incident_limitations_actions": (
            "This prototype has no production incident history; operational "
            "channels and responsibilities require confirmation."
        ),
        "responsible_owner": "Customer Services Directorate",
        "incident_response_reviewer": "AI Governance Reviewer",
        "assessment_status": "Reviewed",
    })
    labels = {
        "Incident definition / scope": "incident_definition_scope",
        "Incident detection and reporting channels": "detection_reporting_channels",
        "Initial assessment and triage approach": "initial_assessment_triage",
        "Severity / impact classification": "severity_impact_classification",
        "Immediate containment / protective actions": "immediate_containment_actions",
        "Human review and correction of affected decisions": "human_review_decision_correction",
        "Escalation criteria": "escalation_criteria",
        "Escalation roles / notification responsibilities": "escalation_roles_notifications",
        "Investigation and root-cause approach": "investigation_root_cause_approach",
        "Corrective and preventive actions": "corrective_preventive_actions",
        "Recovery / return-to-service criteria": "recovery_return_to_service",
        "Incident documentation / record keeping": "incident_documentation_records",
        "Post-incident review / lessons learned": "post_incident_review_lessons",
        "Incident-response limitations / outstanding actions": "incident_limitations_actions",
    }
    for index, widget in enumerate(app.text_area):
        if widget.label in labels:
            app.text_area[index].set_value(evidence[labels[widget.label]])
    for index, widget in enumerate(app.text_input):
        if widget.label == "Responsible incident-response owner":
            app.text_input[index].set_value(evidence["responsible_owner"])
        elif widget.label == "Incident-response reviewer":
            app.text_input[index].set_value(evidence["incident_response_reviewer"])
    for index, widget in enumerate(app.selectbox):
        if widget.label == "INC-01 assessment status":
            app.selectbox[index].select("Reviewed")

    save_inc_button = next(
        i for i, button in enumerate(app.button)
        if button.label == "Save INC-01 assessment"
    )
    app.button[save_inc_button].click().run()
    assert not app.exception
    assert app.session_state["control_evidence"]["INC-01"] == evidence
    assert assess_control(
        "INC-01",
        app.session_state["use_case"],
        app.session_state["risk_answers"],
        app.session_state["control_evidence"],
    )["Evidence Status"] == "Available"

    save_case_button = next(i for i, button in enumerate(app.button) if button.label == "Save Case")
    app.button[save_case_button].click().run()
    saved_case_id = app.session_state["current_case_id"]
    saved_path = tmp_path / f"{saved_case_id}.json"
    with saved_path.open(encoding="utf-8") as case_file:
        disk_document = json.load(case_file)
    assert disk_document["control_evidence"]["INC-01"] == evidence
    assert set(disk_document["control_evidence"]["INC-01"]) == set(evidence)
    assert disk_document["control_evidence"]["INC-01"]["assessment_status"] == "Reviewed"

    fresh_app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "app.py"
    ).run()
    fresh_selector = next(
        i for i, widget in enumerate(fresh_app.selectbox)
        if widget.label == "Saved cases"
    )
    fresh_app.selectbox[fresh_selector].select(saved_case_id)
    fresh_load_button = next(
        i for i, button in enumerate(fresh_app.button)
        if button.label == "Load Case"
    )
    fresh_app.button[fresh_load_button].click().run()
    fresh_app.switch_page("views/controls.py").run()
    assert not fresh_app.exception

    def assert_inc01_restored():
        assert fresh_app.session_state["control_evidence"]["INC-01"] == evidence
        generation = fresh_app.session_state["_case_load_generation"]
        for field, expected in evidence.items():
            key = f"{INC01_WIDGET_KEYS[field]}_{generation}"
            widgets = [
                widget
                for widget in (
                    *fresh_app.text_area,
                    *fresh_app.text_input,
                    *fresh_app.selectbox,
                )
                if widget.key == key
            ]
            assert len(widgets) == 1, field
            assert widgets[0].value == expected, field
        control_table = next(
            dataframe.value
            for dataframe in fresh_app.dataframe
            if "Control ID" in dataframe.value.columns
        )
        assert control_table.loc[
            control_table["Control ID"] == "INC-01", "Evidence Status"
        ].iloc[0] == "Available"

    assert_inc01_restored()
    fresh_app.switch_page("views/deployment_readiness.py").run()
    assert not fresh_app.exception
    incident_checkbox = next(
        widget
        for widget in fresh_app.checkbox
        if widget.label == "Incident response and escalation plan approved"
    )
    assert incident_checkbox.value is True
    assert incident_checkbox.disabled is True
    assert any(
        element.value == "Ready for Deployment Approval"
        for element in fresh_app.subheader
    )
    assert any(
        "Final deployment approval remains a human governance decision."
        in element.value
        for element in fresh_app.info
    )
    assert not any(
        element.value == "Approved for Deployment"
        for element in fresh_app.subheader
    )

    fresh_app.switch_page("views/risk_assessment.py").run()
    fresh_app.switch_page("views/controls.py").run()
    assert not fresh_app.exception
    assert_inc01_restored()

    fresh_save_button = next(
        i for i, button in enumerate(fresh_app.button)
        if button.label == "Save Case"
    )
    fresh_app.button[fresh_save_button].click().run()
    resaved_id = fresh_app.session_state["current_case_id"]
    with (tmp_path / f"{resaved_id}.json").open(encoding="utf-8") as case_file:
        resaved_document = json.load(case_file)
    assert resaved_document["control_evidence"]["INC-01"] == evidence


def test_control_library_saves_reviewed_val01_assessment():
    use_case = {
        "name": "Citizen Request Prioritisation AI",
        "owner": "Customer Services Directorate",
        "purpose": "Prioritise municipal service requests for review.",
        "ai_role": "Recommendation only",
        "decision": "Recommended priority score",
        "human_oversight": "Required before action",
    }
    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "views" / "controls.py"
    )
    app.session_state["use_case"] = use_case
    app.session_state["risk_answers"] = {
        key: False for key in SCREENING_KEYS
    }
    app.run()

    assert not app.exception
    assert app.session_state["val01_human_oversight_validation"] == (
        use_case["human_oversight"]
    )
    assert app.session_state["val01_responsible_owner"] == use_case["owner"]
    assert "VAL-01" not in app.session_state.get("control_evidence", {})
    assert assess_control(
        "VAL-01",
        app.session_state["use_case"],
        app.session_state["risk_answers"],
        app.session_state.get("control_evidence", {}),
    )["Evidence Status"] == "Pending"

    field_values = {
        "Validation scope": "Assess recommendations for human review",
        "Intended performance / acceptance criteria": "Define acceptable prioritisation behavior with service owners",
        "Validation approach": "Document the proposed review of intended-use scenarios",
        "Data / test-set considerations": "Document representativeness, privacy, and test-set limitations",
        "Validation findings / current evidence": "No completed model testing or performance results are claimed",
        "Limitations / outstanding validation actions": "Technical validation remains outstanding before deployment",
    }
    for index, widget in enumerate(app.text_area):
        if widget.label in field_values:
            app.text_area[index].set_value(field_values[widget.label])
    for index, widget in enumerate(app.text_input):
        if widget.label == "Validation reviewer":
            app.text_input[index].set_value("AI Validation Reviewer")
    for index, widget in enumerate(app.selectbox):
        if widget.label == "VAL-01 assessment status":
            app.selectbox[index].select("Reviewed")

    submit_index = next(
        index
        for index, button in enumerate(app.button)
        if button.label == "Save VAL-01 assessment"
    )
    app.button[submit_index].click().run()

    assert not app.exception
    evidence = app.session_state["control_evidence"]["VAL-01"]
    assert evidence["assessment_status"] == "Reviewed"
    assert evidence["validation_reviewer"] == "AI Validation Reviewer"
    assert assess_control(
        "VAL-01",
        app.session_state["use_case"],
        app.session_state["risk_answers"],
        app.session_state["control_evidence"],
    )["Evidence Status"] == "Available"
    assert any(
        "does not demonstrate completed real-world model validation"
        in caption.value
        for caption in app.caption
    )


def test_loaded_control_evidence_hydrates_forms_after_restart_and_navigation(tmp_path):
    use_case = {key: f"Case {key}" for key in USE_CASE_KEYS}
    use_case.update({
        "name": "Citizen Request Prioritisation AI",
        "owner": "Customer Services Directorate",
        "purpose": "Prioritise service requests for human review.",
        "users": "Municipal operations staff",
        "affected_people": "Citizens submitting requests",
        "decision": "Recommended priority score",
        "ai_role": "Recommendation only",
        "human_oversight": "Required before action",
    })
    risk_answers = {key: False for key in RISK_ANSWER_KEYS}
    risk_answers.update({
        "personal_data": True,
        "sensitive_data": True,
        "significant_decision": True,
        "vulnerable_groups": True,
    })
    evidence_by_control = {
        "DAT-01": {
            "personal_data_categories": "DAT categories",
            "purpose_necessity": "DAT purpose",
            "data_minimisation": "DAT minimisation",
            "sensitive_data_used": True,
            "sensitive_data_details": "DAT sensitive data details",
            "data_access": "DAT access",
            "responsible_owner": "DAT owner",
            "retention_deletion": "DAT retention",
            "privacy_risks": "DAT risks",
            "mitigations": "DAT mitigations",
            "privacy_reviewer": "DAT reviewer",
            "assessment_status": "Reviewed",
        },
        "VAL-01": {
            "validation_scope": "VAL scope",
            "acceptance_criteria": "VAL criteria",
            "validation_approach": "VAL approach",
            "data_test_set_considerations": "VAL data considerations",
            "human_oversight_validation": "VAL human oversight",
            "validation_findings_evidence": "No completed testing is claimed",
            "validation_limitations_actions": "VAL outstanding actions",
            "responsible_owner": "VAL owner",
            "validation_reviewer": "VAL reviewer",
            "assessment_status": "Reviewed",
        },
        "FAI-01": {
            "affected_groups": "FAI groups",
            "fairness_risk": "FAI risk",
            "evaluation_approach": "FAI approach",
            "data_evaluation_limitations": "FAI limitations",
            "findings_observations": "FAI observations",
            "mitigation_actions": "FAI mitigations",
            "responsible_owner": "FAI owner",
            "fairness_reviewer": "FAI reviewer",
            "assessment_status": "Reviewed",
        },
        "SEC-01": {
            "security_scope": "SEC scope",
            "key_security_risks": "SEC risks",
            "access_control_approach": "SEC access",
            "data_protection_measures": "SEC data handling",
            "third_party_considerations": "SEC dependencies",
            "security_monitoring_approach": "SEC monitoring",
            "incident_escalation_approach": "SEC escalation",
            "security_limitations_actions": "SEC limitations",
            "responsible_owner": "SEC owner",
            "security_reviewer": "SEC reviewer",
            "assessment_status": "Reviewed",
        },
        "TRN-01": {
            "ai_system_purpose": "TRN purpose",
            "ai_decision_role": "TRN role",
            "intended_users_stakeholders": "TRN stakeholders",
            "key_system_limitations": "TRN limitations",
            "human_oversight_approach": "TRN oversight",
            "information_to_communicate": "TRN information",
            "communication_disclosure_approach": "TRN disclosure approach",
            "transparency_limitations_actions": "TRN outstanding actions",
            "responsible_owner": "TRN owner",
            "transparency_reviewer": "TRN reviewer",
            "assessment_status": "Reviewed",
        },
    }
    saved = save_case(
        {
            "use_case": use_case,
            "risk_answers": risk_answers,
            "control_evidence": evidence_by_control,
            "deployment_readiness_plans": DEFAULT_PLANS,
        },
        tmp_path,
    )

    # A new AppTest instance represents a restarted Streamlit session.
    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "app.py"
    )
    restore_case(app.session_state, load_case(saved["case_id"], tmp_path))

    # Simulate stale page-scoped widget defaults left behind during hydration.
    base_widget_maps = {
        "DAT-01": DAT01_WIDGET_KEYS,
        "FAI-01": FAI01_WIDGET_KEYS,
        "SEC-01": SEC01_WIDGET_KEYS,
        "TRN-01": TRN01_WIDGET_KEYS,
        "VAL-01": VAL01_WIDGET_KEYS,
    }
    generation = app.session_state["_case_load_generation"]
    widget_maps = {
        control_id: {
            field: f"{widget_key}_{generation}"
            for field, widget_key in widget_keys.items()
        }
        for control_id, widget_keys in base_widget_maps.items()
    }
    for control_id, widget_keys in base_widget_maps.items():
        for field, widget_key in widget_keys.items():
            app.session_state[widget_key] = (
                False
                if field == "sensitive_data_used"
                else "Draft"
                if field == "assessment_status"
                else ""
            )

    app.run()
    assert not app.exception
    app.switch_page("views/controls.py").run()
    assert not app.exception

    def assert_forms_show_saved_evidence():
        for control_id, widget_keys in widget_maps.items():
            for field, expected in evidence_by_control[control_id].items():
                widget_key = widget_keys[field]
                widgets = [
                    widget
                    for widget in (*app.text_area, *app.text_input, *app.selectbox, *app.checkbox)
                    if widget.key == widget_key
                ]
                assert len(widgets) == 1, (control_id, field)
                assert widgets[0].value == expected, (
                    f"{control_id}.{field}: visible={widgets[0].value!r}, "
                    f"canonical={app.session_state['control_evidence'][control_id].get(field)!r}"
                )
            assert assess_control(
                control_id,
                app.session_state["use_case"],
                app.session_state["risk_answers"],
                app.session_state["control_evidence"],
            )["Evidence Status"] == "Available"

    assert_forms_show_saved_evidence()

    app.switch_page("views/risk_assessment.py").run()
    assert not app.exception
    app.switch_page("views/controls.py").run()
    assert not app.exception
    assert_forms_show_saved_evidence()


def test_loaded_risk_answers_survive_navigation_away_and_back(tmp_path):
    use_case = {
        key: f"Case {key}"
        for key in USE_CASE_KEYS
    }
    use_case.update({
        "name": "Citizen Request Prioritisation AI",
        "ai_role": "Recommendation only",
        "human_oversight": "Required before action",
    })
    answers = {key: False for key in RISK_ANSWER_KEYS}
    answers.update({
        "personal_data": True,
        "significant_decision": True,
        "vulnerable_groups": True,
    })
    document = save_case(
        {
            "use_case": use_case,
            "risk_answers": answers,
            "control_evidence": {},
            "deployment_readiness_plans": DEFAULT_PLANS,
        },
        tmp_path,
    )

    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "app.py"
    ).run()
    restore_case(app.session_state, load_case(document["case_id"], tmp_path))
    app.switch_page("views/risk_assessment.py").run()

    assert not app.exception
    assert app.session_state["risk_answers"] == answers
    assert app.session_state["risk_score"] == 7
    assert app.session_state["governance_tier"] == "Medium"
    expected_visible_values = [
        answers[key] for key in RISK_ANSWER_KEYS
    ]
    assert [checkbox.value for checkbox in app.checkbox] == expected_visible_values

    app.switch_page("views/controls.py").run()
    assert not app.exception
    app.switch_page("views/risk_assessment.py").run()

    assert not app.exception
    assert app.session_state["risk_answers"] == answers
    assert app.session_state["risk_score"] == 7
    assert app.session_state["governance_tier"] == "Medium"
    assert [checkbox.value for checkbox in app.checkbox] == expected_visible_values

    app.checkbox[4].check().run()

    expected_after_change = answers.copy()
    expected_after_change["external_users"] = True
    assert app.session_state["risk_answers"] == expected_after_change
    assert [checkbox.value for checkbox in app.checkbox] == [
        expected_after_change[key] for key in RISK_ANSWER_KEYS
    ]
    assert app.session_state["risk_score"] == 8
    assert app.session_state["governance_tier"] == "Medium"


def test_risk_checkbox_change_updates_canonical_answers():
    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "views" / "risk_assessment.py"
    )
    app.run()

    app.checkbox[0].check().run()

    assert app.session_state["risk_answers"]["personal_data"] is True
    assert app.session_state["risk_score"] == 2
    assert app.session_state["governance_tier"] == "Low"


def test_loaded_case_survives_dat01_save_and_page_navigation(tmp_path):
    use_case = {key: f"Case {key}" for key in USE_CASE_KEYS}
    use_case.update({
        "name": "Citizen Request Prioritisation AI",
        "ai_role": "Recommendation only",
        "human_oversight": "Required before action",
    })
    risk_answers = {key: False for key in RISK_ANSWER_KEYS}
    risk_answers.update({
        "personal_data": True,
        "significant_decision": True,
        "vulnerable_groups": True,
    })
    plans = {
        "monitoring": {
            "plan_defined": True,
            "metrics_defined": True,
            "thresholds_defined": True,
            "responsibilities_defined": True,
        },
        "incident_response": {"plan_approved": True},
    }
    saved = save_case(
        {
            "use_case": use_case,
            "risk_answers": risk_answers,
            "control_evidence": {},
            "deployment_readiness_plans": plans,
        },
        tmp_path,
    )

    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "app.py"
    ).run()
    restore_case(app.session_state, load_case(saved["case_id"], tmp_path))
    app.switch_page("views/risk_assessment.py").run()
    assert app.session_state["risk_score"] == 7
    assert app.session_state["governance_tier"] == "Medium"

    app.switch_page("views/controls.py").run()
    dat01_values = {
        "Personal data categories": "Citizen requests; location; timestamps",
        "Purpose and necessity": "Prioritise requests for human operational review",
        "Data minimisation measures": "Use only fields necessary for prioritisation",
        "Who can access the data": "Authorised municipal operations staff",
        "Retention or deletion approach": "Delete after the approved retention period",
        "Privacy risks": "Unauthorised access or excessive retention",
        "Mitigations": "Role-based access and scheduled deletion",
    }
    for index, widget in enumerate(app.text_area):
        if widget.label in dat01_values:
            app.text_area[index].set_value(dat01_values[widget.label])
    for index, widget in enumerate(app.text_input):
        if widget.label == "Responsible data/business owner":
            app.text_input[index].set_value("Customer Services Directorate")
        elif widget.label == "Privacy/DPO reviewer":
            app.text_input[index].set_value("Privacy/DPO Reviewer")
    for index, widget in enumerate(app.selectbox):
        if widget.label == "Assessment status":
            app.selectbox[index].select("Reviewed")
    submit_index = next(
        index
        for index, button in enumerate(app.button)
        if button.label == "Save DAT-01 assessment"
    )
    app.button[submit_index].click().run()

    assert not app.exception
    assert not any(
        "Complete the AI Risk Assessment before evaluating applicable controls."
        in warning.value
        for warning in app.warning
    )
    assert app.session_state["use_case"] == use_case
    assert app.session_state["risk_answers"] == risk_answers
    assert app.session_state["risk_score"] == 7
    assert app.session_state["governance_tier"] == "Medium"
    assert app.session_state["deployment_readiness_plans"] == plans
    evidence = app.session_state["control_evidence"]["DAT-01"]
    assert isinstance(evidence, dict)
    assert evidence["assessment_status"] == "Reviewed"
    assert evidence["privacy_reviewer"] == "Privacy/DPO Reviewer"
    assert assess_control(
        "DAT-01",
        app.session_state["use_case"],
        app.session_state["risk_answers"],
        app.session_state["control_evidence"],
    )["Evidence Status"] == "Available"

    for page in ("views/controls.py", "views/risk_assessment.py", "views/controls.py"):
        app.switch_page(page).run()
        assert not app.exception
        assert app.session_state["use_case"] == use_case
        assert app.session_state["risk_answers"] == risk_answers
        assert app.session_state["risk_score"] == 7
        assert app.session_state["governance_tier"] == "Medium"
        assert app.session_state["deployment_readiness_plans"] == plans
        assert app.session_state["control_evidence"]["DAT-01"] == evidence
