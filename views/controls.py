from pathlib import Path
import pandas as pd
import streamlit as st
from src.governance.control_assessment import (
    assess_control,
    control_is_required,
    has_complete_risk_answers,
)
from src.governance.case_persistence import (
    DAT01_WIDGET_KEYS,
    FAI01_WIDGET_KEYS,
    SEC01_WIDGET_KEYS,
    TRN01_WIDGET_KEYS,
    VAL01_WIDGET_KEYS,
    MON01_WIDGET_KEYS,
    INC01_WIDGET_KEYS,
)


def _case_widget_keys(widget_keys):
    generation = st.session_state.get("_case_load_generation")
    if not generation:
        return widget_keys
    return {
        field: f"{widget_key}_{generation}"
        for field, widget_key in widget_keys.items()
    }


def _hydrate_control_form(widget_keys, saved_assessment, defaults, control_id):
    generation = st.session_state.get("_case_load_generation")
    hydration_key = f"_control_form_hydrated_{control_id}"
    needs_hydration = (
        st.session_state.get(hydration_key) != generation
        or any(key not in st.session_state for key in widget_keys.values())
    )
    if not needs_hydration:
        return

    for field, widget_key in widget_keys.items():
        value = saved_assessment.get(field, defaults[field])
        if field == "assessment_status":
            if value not in ("Draft", "Reviewed"):
                value = "Draft"
        elif field == "sensitive_data_used":
            if type(value) is not bool:
                value = defaults[field]
        elif not isinstance(value, str):
            value = ""
        st.session_state[widget_key] = value
    st.session_state[hydration_key] = generation


st.title("AI Governance Control Library")
path = Path(__file__).resolve().parents[1] / "data" / "controls.csv"
df = pd.read_csv(path)

use_case = st.session_state.get("use_case", {})
risk_answers = st.session_state.get("risk_answers", {})
if not has_complete_risk_answers(risk_answers):
    st.warning("Complete the AI Risk Assessment before evaluating applicable controls.")
    st.stop()

has_use_case = bool(use_case)
explicit_evidence = st.session_state.get("control_evidence", {})

inventory_available = (path.parent / "ai_inventory.csv").exists()
raci_available = (path.parent / "raci.csv").exists()

dat01_required = control_is_required("DAT-01", risk_answers)
if dat01_required:
    st.subheader("DAT-01 Privacy & Data Governance Assessment")
    st.caption(
        "Illustrative governance assessment only; this is not a legal compliance "
        "determination or a DPIA."
    )
    control_evidence = (
        explicit_evidence if isinstance(explicit_evidence, dict) else {}
    )
    saved_assessment = control_evidence.get("DAT-01")
    if not isinstance(saved_assessment, dict):
        saved_assessment = {}
    dat01_widget_keys = _case_widget_keys(DAT01_WIDGET_KEYS)

    dat01_defaults = {
        "personal_data_categories": use_case.get("data", ""),
        "purpose_necessity": use_case.get("purpose", ""),
        "data_minimisation": "",
        "sensitive_data_used": bool(risk_answers.get("sensitive_data")),
        "sensitive_data_details": "",
        "data_access": "",
        "responsible_owner": use_case.get("owner", ""),
        "retention_deletion": "",
        "privacy_risks": "",
        "mitigations": "",
        "privacy_reviewer": "",
        "assessment_status": "Draft",
    }
    _hydrate_control_form(
        dat01_widget_keys,
        saved_assessment,
        dat01_defaults,
        "DAT-01",
    )

    with st.form("dat01_assessment_form"):
        personal_data_categories = st.text_area(
            "Personal data categories",
            key=dat01_widget_keys["personal_data_categories"],
        )
        purpose_necessity = st.text_area(
            "Purpose and necessity",
            key=dat01_widget_keys["purpose_necessity"],
        )
        data_minimisation = st.text_area(
            "Data minimisation measures",
            key=dat01_widget_keys["data_minimisation"],
        )
        sensitive_data_used = st.checkbox(
            "Sensitive data is used",
            key=dat01_widget_keys["sensitive_data_used"],
        )
        sensitive_data_details = ""
        if sensitive_data_used:
            sensitive_data_details = st.text_area(
                "Sensitive data categories/details",
                key=dat01_widget_keys["sensitive_data_details"],
            )
        data_access = st.text_area(
            "Who can access the data",
            key=dat01_widget_keys["data_access"],
        )
        responsible_owner = st.text_input(
            "Responsible data/business owner",
            key=dat01_widget_keys["responsible_owner"],
        )
        retention_deletion = st.text_area(
            "Retention or deletion approach",
            key=dat01_widget_keys["retention_deletion"],
        )
        privacy_risks = st.text_area(
            "Privacy risks",
            key=dat01_widget_keys["privacy_risks"],
        )
        mitigations = st.text_area(
            "Mitigations",
            key=dat01_widget_keys["mitigations"],
        )
        privacy_reviewer = st.text_input(
            "Privacy/DPO reviewer",
            key=dat01_widget_keys["privacy_reviewer"],
        )
        assessment_status = st.selectbox(
            "Assessment status",
            ["Draft", "Reviewed"],
            key=dat01_widget_keys["assessment_status"],
        )
        save_assessment = st.form_submit_button("Save DAT-01 assessment")

    if save_assessment:
        control_evidence["DAT-01"] = {
            "personal_data_categories": personal_data_categories,
            "purpose_necessity": purpose_necessity,
            "data_minimisation": data_minimisation,
            "sensitive_data_used": sensitive_data_used,
            "sensitive_data_details": sensitive_data_details,
            "data_access": data_access,
            "responsible_owner": responsible_owner,
            "retention_deletion": retention_deletion,
            "privacy_risks": privacy_risks,
            "mitigations": mitigations,
            "privacy_reviewer": privacy_reviewer,
            "assessment_status": assessment_status,
        }
        st.session_state["control_evidence"] = control_evidence
        st.success("DAT-01 assessment saved.")

fai01_required = control_is_required("FAI-01", risk_answers)
if fai01_required:
    st.subheader("FAI-01 Fairness Assessment")
    st.caption(
        "Illustrative governance assessment only; this does not claim that "
        "a real-world statistical fairness audit has been completed."
    )
    control_evidence = (
        explicit_evidence if isinstance(explicit_evidence, dict) else {}
    )
    saved_assessment = control_evidence.get("FAI-01")
    if not isinstance(saved_assessment, dict):
        saved_assessment = {}
    fai01_widget_keys = _case_widget_keys(FAI01_WIDGET_KEYS)

    fai01_defaults = {
        "affected_groups": use_case.get("affected_people", ""),
        "fairness_risk": "",
        "evaluation_approach": "",
        "data_evaluation_limitations": "",
        "findings_observations": "",
        "mitigation_actions": "",
        "responsible_owner": use_case.get("owner", ""),
        "fairness_reviewer": "",
        "assessment_status": "Draft",
    }
    _hydrate_control_form(
        fai01_widget_keys,
        saved_assessment,
        fai01_defaults,
        "FAI-01",
    )

    with st.form("fai01_assessment_form"):
        affected_groups = st.text_area(
            "Affected groups",
            key=fai01_widget_keys["affected_groups"],
        )
        fairness_risk = st.text_area(
            "Fairness risk",
            key=fai01_widget_keys["fairness_risk"],
        )
        evaluation_approach = st.text_area(
            "Evaluation approach",
            key=fai01_widget_keys["evaluation_approach"],
        )
        data_evaluation_limitations = st.text_area(
            "Data / evaluation limitations",
            key=fai01_widget_keys["data_evaluation_limitations"],
        )
        findings_observations = st.text_area(
            "Findings / observations",
            key=fai01_widget_keys["findings_observations"],
        )
        mitigation_actions = st.text_area(
            "Mitigation actions",
            key=fai01_widget_keys["mitigation_actions"],
        )
        responsible_owner = st.text_input(
            "Responsible owner",
            key=fai01_widget_keys["responsible_owner"],
        )
        fairness_reviewer = st.text_input(
            "Fairness / AI Governance reviewer",
            key=fai01_widget_keys["fairness_reviewer"],
        )
        assessment_status = st.selectbox(
            "FAI-01 assessment status",
            ["Draft", "Reviewed"],
            key=fai01_widget_keys["assessment_status"],
        )
        save_assessment = st.form_submit_button("Save FAI-01 assessment")

    if save_assessment:
        control_evidence["FAI-01"] = {
            "affected_groups": affected_groups,
            "fairness_risk": fairness_risk,
            "evaluation_approach": evaluation_approach,
            "data_evaluation_limitations": data_evaluation_limitations,
            "findings_observations": findings_observations,
            "mitigation_actions": mitigation_actions,
            "responsible_owner": responsible_owner,
            "fairness_reviewer": fairness_reviewer,
            "assessment_status": assessment_status,
        }
        st.session_state["control_evidence"] = control_evidence
        st.success("FAI-01 assessment saved.")

sec01_result = assess_control(
    "SEC-01",
    use_case,
    risk_answers,
    explicit_evidence,
    inventory_available,
    raci_available,
)
if sec01_result["Applicability"] == "Required":
    st.subheader("SEC-01 AI Security Assessment")
    st.caption(
        "Illustrative governance assessment only; this is not evidence of a "
        "completed technical security test or production security approval."
    )
    control_evidence = (
        explicit_evidence if isinstance(explicit_evidence, dict) else {}
    )
    saved_assessment = control_evidence.get("SEC-01")
    if not isinstance(saved_assessment, dict):
        saved_assessment = {}
    sec01_widget_keys = _case_widget_keys(SEC01_WIDGET_KEYS)

    sec01_defaults = {
        "security_scope": "",
        "key_security_risks": "",
        "access_control_approach": "",
        "data_protection_measures": "",
        "third_party_considerations": "",
        "security_monitoring_approach": "",
        "incident_escalation_approach": "",
        "security_limitations_actions": "",
        "responsible_owner": use_case.get("owner", ""),
        "security_reviewer": "",
        "assessment_status": "Draft",
    }
    _hydrate_control_form(
        sec01_widget_keys,
        saved_assessment,
        sec01_defaults,
        "SEC-01",
    )

    with st.form("sec01_assessment_form"):
        security_scope = st.text_area(
            "System / AI security scope",
            key=sec01_widget_keys["security_scope"],
        )
        key_security_risks = st.text_area(
            "Key security risks",
            key=sec01_widget_keys["key_security_risks"],
        )
        access_control_approach = st.text_area(
            "Access control approach",
            key=sec01_widget_keys["access_control_approach"],
        )
        data_protection_measures = st.text_area(
            "Data protection / secure handling measures",
            key=sec01_widget_keys["data_protection_measures"],
        )
        third_party_considerations = st.text_area(
            "Third-party / dependency considerations",
            key=sec01_widget_keys["third_party_considerations"],
        )
        security_monitoring_approach = st.text_area(
            "Security monitoring approach",
            key=sec01_widget_keys["security_monitoring_approach"],
        )
        incident_escalation_approach = st.text_area(
            "Incident / escalation approach",
            key=sec01_widget_keys["incident_escalation_approach"],
        )
        security_limitations_actions = st.text_area(
            "Security limitations / outstanding actions",
            key=sec01_widget_keys["security_limitations_actions"],
        )
        responsible_owner = st.text_input(
            "Responsible owner",
            key=sec01_widget_keys["responsible_owner"],
        )
        security_reviewer = st.text_input(
            "Security reviewer",
            key=sec01_widget_keys["security_reviewer"],
        )
        assessment_status = st.selectbox(
            "SEC-01 assessment status",
            ["Draft", "Reviewed"],
            key=sec01_widget_keys["assessment_status"],
        )
        save_assessment = st.form_submit_button("Save SEC-01 assessment")

    if save_assessment:
        control_evidence["SEC-01"] = {
            "security_scope": security_scope,
            "key_security_risks": key_security_risks,
            "access_control_approach": access_control_approach,
            "data_protection_measures": data_protection_measures,
            "third_party_considerations": third_party_considerations,
            "security_monitoring_approach": security_monitoring_approach,
            "incident_escalation_approach": incident_escalation_approach,
            "security_limitations_actions": security_limitations_actions,
            "responsible_owner": responsible_owner,
            "security_reviewer": security_reviewer,
            "assessment_status": assessment_status,
        }
        st.session_state["control_evidence"] = control_evidence
        st.success("SEC-01 assessment saved.")

trn01_result = assess_control(
    "TRN-01",
    use_case,
    risk_answers,
    explicit_evidence,
    inventory_available,
    raci_available,
)
if trn01_result["Applicability"] == "Required":
    st.subheader("TRN-01 Transparency Assessment")
    st.caption(
        "Illustrative governance assessment only; this does not prove that "
        "real-world disclosures or communications have occurred."
    )
    control_evidence = (
        explicit_evidence if isinstance(explicit_evidence, dict) else {}
    )
    saved_assessment = control_evidence.get("TRN-01")
    if not isinstance(saved_assessment, dict):
        saved_assessment = {}
    trn01_widget_keys = _case_widget_keys(TRN01_WIDGET_KEYS)

    users_and_stakeholders = "; ".join(
        value
        for value in (
            use_case.get("users", "").strip(),
            use_case.get("affected_people", "").strip(),
        )
        if value
    )
    trn01_defaults = {
        "ai_system_purpose": use_case.get("purpose", ""),
        "ai_decision_role": "; ".join(
            value
            for value in (
                use_case.get("ai_role", "").strip(),
                use_case.get("decision", "").strip(),
            )
            if value
        ),
        "intended_users_stakeholders": users_and_stakeholders,
        "key_system_limitations": "",
        "human_oversight_approach": use_case.get("human_oversight", ""),
        "information_to_communicate": "",
        "communication_disclosure_approach": "",
        "transparency_limitations_actions": "",
        "responsible_owner": use_case.get("owner", ""),
        "transparency_reviewer": "",
        "assessment_status": "Draft",
    }
    _hydrate_control_form(
        trn01_widget_keys,
        saved_assessment,
        trn01_defaults,
        "TRN-01",
    )

    with st.form("trn01_assessment_form"):
        ai_system_purpose = st.text_area(
            "AI system purpose",
            key=trn01_widget_keys["ai_system_purpose"],
        )
        ai_decision_role = st.text_area(
            "AI role in decision-making",
            key=trn01_widget_keys["ai_decision_role"],
        )
        intended_users_stakeholders = st.text_area(
            "Intended users / affected stakeholders",
            key=trn01_widget_keys["intended_users_stakeholders"],
        )
        key_system_limitations = st.text_area(
            "Key system limitations",
            key=trn01_widget_keys["key_system_limitations"],
        )
        human_oversight_approach = st.text_area(
            "Human oversight approach",
            key=trn01_widget_keys["human_oversight_approach"],
        )
        information_to_communicate = st.text_area(
            "Information to be communicated",
            key=trn01_widget_keys["information_to_communicate"],
        )
        communication_disclosure_approach = st.text_area(
            "Communication / disclosure approach",
            key=trn01_widget_keys["communication_disclosure_approach"],
        )
        transparency_limitations_actions = st.text_area(
            "Transparency limitations / outstanding actions",
            key=trn01_widget_keys["transparency_limitations_actions"],
        )
        responsible_owner = st.text_input(
            "Responsible transparency owner",
            key=trn01_widget_keys["responsible_owner"],
        )
        transparency_reviewer = st.text_input(
            "Transparency / AI Governance reviewer",
            key=trn01_widget_keys["transparency_reviewer"],
        )
        assessment_status = st.selectbox(
            "TRN-01 assessment status",
            ["Draft", "Reviewed"],
            key=trn01_widget_keys["assessment_status"],
        )
        save_assessment = st.form_submit_button("Save TRN-01 assessment")

    if save_assessment:
        control_evidence["TRN-01"] = {
            "ai_system_purpose": ai_system_purpose,
            "ai_decision_role": ai_decision_role,
            "intended_users_stakeholders": intended_users_stakeholders,
            "key_system_limitations": key_system_limitations,
            "human_oversight_approach": human_oversight_approach,
            "information_to_communicate": information_to_communicate,
            "communication_disclosure_approach": communication_disclosure_approach,
            "transparency_limitations_actions": transparency_limitations_actions,
            "responsible_owner": responsible_owner,
            "transparency_reviewer": transparency_reviewer,
            "assessment_status": assessment_status,
        }
        st.session_state["control_evidence"] = control_evidence
        st.success("TRN-01 assessment saved.")

val01_result = assess_control(
    "VAL-01",
    use_case,
    risk_answers,
    explicit_evidence,
    inventory_available,
    raci_available,
)
if val01_result["Applicability"] == "Required":
    st.subheader("VAL-01 AI Validation Assessment")
    st.caption(
        "Illustrative governance assessment only; this does not demonstrate "
        "completed real-world model validation or production performance."
    )
    control_evidence = (
        explicit_evidence if isinstance(explicit_evidence, dict) else {}
    )
    saved_assessment = control_evidence.get("VAL-01")
    if not isinstance(saved_assessment, dict):
        saved_assessment = {}
    val01_widget_keys = _case_widget_keys(VAL01_WIDGET_KEYS)

    val01_defaults = {
        "validation_scope": "; ".join(
            value
            for value in (
                use_case.get("purpose", "").strip(),
                use_case.get("decision", "").strip(),
            )
            if value
        ),
        "acceptance_criteria": "",
        "validation_approach": "",
        "data_test_set_considerations": "",
        "human_oversight_validation": use_case.get("human_oversight", ""),
        "validation_findings_evidence": "",
        "validation_limitations_actions": "",
        "responsible_owner": use_case.get("owner", ""),
        "validation_reviewer": "",
        "assessment_status": "Draft",
    }
    _hydrate_control_form(
        val01_widget_keys,
        saved_assessment,
        val01_defaults,
        "VAL-01",
    )

    with st.form("val01_assessment_form"):
        validation_scope = st.text_area(
            "Validation scope",
            key=val01_widget_keys["validation_scope"],
        )
        acceptance_criteria = st.text_area(
            "Intended performance / acceptance criteria",
            key=val01_widget_keys["acceptance_criteria"],
        )
        validation_approach = st.text_area(
            "Validation approach",
            key=val01_widget_keys["validation_approach"],
        )
        data_test_set_considerations = st.text_area(
            "Data / test-set considerations",
            key=val01_widget_keys["data_test_set_considerations"],
        )
        human_oversight_validation = st.text_area(
            "Human oversight validation",
            key=val01_widget_keys["human_oversight_validation"],
        )
        validation_findings_evidence = st.text_area(
            "Validation findings / current evidence",
            key=val01_widget_keys["validation_findings_evidence"],
        )
        validation_limitations_actions = st.text_area(
            "Limitations / outstanding validation actions",
            key=val01_widget_keys["validation_limitations_actions"],
        )
        responsible_owner = st.text_input(
            "Responsible validation owner",
            key=val01_widget_keys["responsible_owner"],
        )
        validation_reviewer = st.text_input(
            "Validation reviewer",
            key=val01_widget_keys["validation_reviewer"],
        )
        assessment_status = st.selectbox(
            "VAL-01 assessment status",
            ["Draft", "Reviewed"],
            key=val01_widget_keys["assessment_status"],
        )
        save_assessment = st.form_submit_button("Save VAL-01 assessment")

    if save_assessment:
        control_evidence["VAL-01"] = {
            "validation_scope": validation_scope,
            "acceptance_criteria": acceptance_criteria,
            "validation_approach": validation_approach,
            "data_test_set_considerations": data_test_set_considerations,
            "human_oversight_validation": human_oversight_validation,
            "validation_findings_evidence": validation_findings_evidence,
            "validation_limitations_actions": validation_limitations_actions,
            "responsible_owner": responsible_owner,
            "validation_reviewer": validation_reviewer,
            "assessment_status": assessment_status,
        }
        st.session_state["control_evidence"] = control_evidence
        st.success("VAL-01 assessment saved.")

mon01_result = assess_control(
    "MON-01",
    use_case,
    risk_answers,
    explicit_evidence,
    inventory_available,
    raci_available,
)
if mon01_result["Applicability"] == "Required":
    st.subheader("MON-01 AI Monitoring Plan")
    st.caption(
        "Illustrative governance monitoring plan only; this does not represent "
        "live production monitoring or actual operational metrics."
    )
    control_evidence = (
        explicit_evidence if isinstance(explicit_evidence, dict) else {}
    )
    saved_assessment = control_evidence.get("MON-01")
    if not isinstance(saved_assessment, dict):
        saved_assessment = {}
    mon01_widget_keys = _case_widget_keys(MON01_WIDGET_KEYS)

    mon01_defaults = {
        "monitoring_objectives": use_case.get("purpose", ""),
        "performance_metrics": "",
        "fairness_disparity_monitoring": "",
        "human_override_review_monitoring": "",
        "incident_complaint_indicators": "",
        "data_model_drift_indicators": "",
        "monitoring_thresholds": "",
        "monitoring_frequency": "",
        "monitoring_responsibilities": "",
        "threshold_breach_escalation": "",
        "monitoring_limitations_actions": "",
        "responsible_owner": use_case.get("owner", ""),
        "monitoring_reviewer": "",
        "assessment_status": "Draft",
    }
    _hydrate_control_form(
        mon01_widget_keys,
        saved_assessment,
        mon01_defaults,
        "MON-01",
    )

    with st.form("mon01_assessment_form"):
        monitoring_objectives = st.text_area(
            "Monitoring objectives",
            key=mon01_widget_keys["monitoring_objectives"],
        )
        performance_metrics = st.text_area(
            "Performance metrics to monitor",
            key=mon01_widget_keys["performance_metrics"],
        )
        fairness_disparity_monitoring = st.text_area(
            "Fairness / disparity monitoring",
            key=mon01_widget_keys["fairness_disparity_monitoring"],
        )
        human_override_review_monitoring = st.text_area(
            "Human override / review monitoring",
            key=mon01_widget_keys["human_override_review_monitoring"],
        )
        incident_complaint_indicators = st.text_area(
            "Incident and complaint indicators",
            key=mon01_widget_keys["incident_complaint_indicators"],
        )
        data_model_drift_indicators = st.text_area(
            "Data / model drift indicators",
            key=mon01_widget_keys["data_model_drift_indicators"],
        )
        monitoring_thresholds = st.text_area(
            "Monitoring thresholds / trigger conditions",
            key=mon01_widget_keys["monitoring_thresholds"],
        )
        monitoring_frequency = st.text_area(
            "Monitoring frequency",
            key=mon01_widget_keys["monitoring_frequency"],
        )
        monitoring_responsibilities = st.text_area(
            "Monitoring responsibilities",
            key=mon01_widget_keys["monitoring_responsibilities"],
        )
        threshold_breach_escalation = st.text_area(
            "Escalation when thresholds are breached",
            key=mon01_widget_keys["threshold_breach_escalation"],
        )
        monitoring_limitations_actions = st.text_area(
            "Monitoring limitations / outstanding actions",
            key=mon01_widget_keys["monitoring_limitations_actions"],
        )
        responsible_owner = st.text_input(
            "Responsible monitoring owner",
            key=mon01_widget_keys["responsible_owner"],
        )
        monitoring_reviewer = st.text_input(
            "Monitoring reviewer",
            key=mon01_widget_keys["monitoring_reviewer"],
        )
        assessment_status = st.selectbox(
            "MON-01 assessment status",
            ["Draft", "Reviewed"],
            key=mon01_widget_keys["assessment_status"],
        )
        save_assessment = st.form_submit_button("Save MON-01 assessment")

    if save_assessment:
        control_evidence["MON-01"] = {
            "monitoring_objectives": monitoring_objectives,
            "performance_metrics": performance_metrics,
            "fairness_disparity_monitoring": fairness_disparity_monitoring,
            "human_override_review_monitoring": human_override_review_monitoring,
            "incident_complaint_indicators": incident_complaint_indicators,
            "data_model_drift_indicators": data_model_drift_indicators,
            "monitoring_thresholds": monitoring_thresholds,
            "monitoring_frequency": monitoring_frequency,
            "monitoring_responsibilities": monitoring_responsibilities,
            "threshold_breach_escalation": threshold_breach_escalation,
            "monitoring_limitations_actions": monitoring_limitations_actions,
            "responsible_owner": responsible_owner,
            "monitoring_reviewer": monitoring_reviewer,
            "assessment_status": assessment_status,
        }
        st.session_state["control_evidence"] = control_evidence
        st.success("MON-01 assessment saved.")

inc01_result = assess_control(
    "INC-01",
    use_case,
    risk_answers,
    explicit_evidence,
    inventory_available,
    raci_available,
)
if inc01_result["Applicability"] == "Required":
    st.subheader("INC-01 AI Incident Management & Escalation Plan")
    st.caption(
        "Illustrative governance incident-response plan only; this does not "
        "represent actual production incidents or completed real-world incident response."
    )
    control_evidence = (
        explicit_evidence if isinstance(explicit_evidence, dict) else {}
    )
    saved_assessment = control_evidence.get("INC-01")
    if not isinstance(saved_assessment, dict):
        saved_assessment = {}
    inc01_widget_keys = _case_widget_keys(INC01_WIDGET_KEYS)

    inc01_defaults = {
        "incident_definition_scope": "",
        "detection_reporting_channels": "",
        "initial_assessment_triage": "",
        "severity_impact_classification": "",
        "immediate_containment_actions": "",
        "human_review_decision_correction": "",
        "escalation_criteria": "",
        "escalation_roles_notifications": "",
        "investigation_root_cause_approach": "",
        "corrective_preventive_actions": "",
        "recovery_return_to_service": "",
        "incident_documentation_records": "",
        "post_incident_review_lessons": "",
        "incident_limitations_actions": "",
        "responsible_owner": use_case.get("owner", ""),
        "incident_response_reviewer": "",
        "assessment_status": "Draft",
    }
    _hydrate_control_form(
        inc01_widget_keys,
        saved_assessment,
        inc01_defaults,
        "INC-01",
    )

    with st.form("inc01_assessment_form"):
        incident_definition_scope = st.text_area(
            "Incident definition / scope",
            key=inc01_widget_keys["incident_definition_scope"],
        )
        detection_reporting_channels = st.text_area(
            "Incident detection and reporting channels",
            key=inc01_widget_keys["detection_reporting_channels"],
        )
        initial_assessment_triage = st.text_area(
            "Initial assessment and triage approach",
            key=inc01_widget_keys["initial_assessment_triage"],
        )
        severity_impact_classification = st.text_area(
            "Severity / impact classification",
            key=inc01_widget_keys["severity_impact_classification"],
        )
        immediate_containment_actions = st.text_area(
            "Immediate containment / protective actions",
            key=inc01_widget_keys["immediate_containment_actions"],
        )
        human_review_decision_correction = st.text_area(
            "Human review and correction of affected decisions",
            key=inc01_widget_keys["human_review_decision_correction"],
        )
        escalation_criteria = st.text_area(
            "Escalation criteria",
            key=inc01_widget_keys["escalation_criteria"],
        )
        escalation_roles_notifications = st.text_area(
            "Escalation roles / notification responsibilities",
            key=inc01_widget_keys["escalation_roles_notifications"],
        )
        investigation_root_cause_approach = st.text_area(
            "Investigation and root-cause approach",
            key=inc01_widget_keys["investigation_root_cause_approach"],
        )
        corrective_preventive_actions = st.text_area(
            "Corrective and preventive actions",
            key=inc01_widget_keys["corrective_preventive_actions"],
        )
        recovery_return_to_service = st.text_area(
            "Recovery / return-to-service criteria",
            key=inc01_widget_keys["recovery_return_to_service"],
        )
        incident_documentation_records = st.text_area(
            "Incident documentation / record keeping",
            key=inc01_widget_keys["incident_documentation_records"],
        )
        post_incident_review_lessons = st.text_area(
            "Post-incident review / lessons learned",
            key=inc01_widget_keys["post_incident_review_lessons"],
        )
        incident_limitations_actions = st.text_area(
            "Incident-response limitations / outstanding actions",
            key=inc01_widget_keys["incident_limitations_actions"],
        )
        responsible_owner = st.text_input(
            "Responsible incident-response owner",
            key=inc01_widget_keys["responsible_owner"],
        )
        incident_response_reviewer = st.text_input(
            "Incident-response reviewer",
            key=inc01_widget_keys["incident_response_reviewer"],
        )
        assessment_status = st.selectbox(
            "INC-01 assessment status",
            ["Draft", "Reviewed"],
            key=inc01_widget_keys["assessment_status"],
        )
        save_assessment = st.form_submit_button("Save INC-01 assessment")

    if save_assessment:
        control_evidence["INC-01"] = {
            "incident_definition_scope": incident_definition_scope,
            "detection_reporting_channels": detection_reporting_channels,
            "initial_assessment_triage": initial_assessment_triage,
            "severity_impact_classification": severity_impact_classification,
            "immediate_containment_actions": immediate_containment_actions,
            "human_review_decision_correction": human_review_decision_correction,
            "escalation_criteria": escalation_criteria,
            "escalation_roles_notifications": escalation_roles_notifications,
            "investigation_root_cause_approach": investigation_root_cause_approach,
            "corrective_preventive_actions": corrective_preventive_actions,
            "recovery_return_to_service": recovery_return_to_service,
            "incident_documentation_records": incident_documentation_records,
            "post_incident_review_lessons": post_incident_review_lessons,
            "incident_limitations_actions": incident_limitations_actions,
            "responsible_owner": responsible_owner,
            "incident_response_reviewer": incident_response_reviewer,
            "assessment_status": assessment_status,
        }
        st.session_state["control_evidence"] = control_evidence
        st.success("INC-01 assessment saved.")


assessment = df.copy()
assessment[["Applicability", "Trigger / Reason", "Evidence Status"]] = [
    tuple(assess_control(
        control_id,
        use_case,
        risk_answers,
        explicit_evidence,
        inventory_available,
        raci_available,
    ).values())
    for control_id in assessment["Control ID"]
]

required_count = int((assessment["Applicability"] == "Required").sum())
available_count = int((assessment["Evidence Status"] == "Available").sum())
pending_count = int((assessment["Evidence Status"] == "Pending").sum())
not_due_count = int((assessment["Evidence Status"] == "Not Due").sum())

st.subheader("Control assessment for the current AI use case")
st.write(
    f"**Required controls:** {required_count}  |  "
    f"**Evidence available:** {available_count}  |  "
    f"**Evidence pending:** {pending_count}  |  "
    f"**Controls not due:** {not_due_count}"
)

area = st.selectbox(
    "Filter by governance area",
    ["All"] + sorted(assessment["Governance Area"].unique().tolist()),
)
displayed = assessment if area == "All" else assessment[assessment["Governance Area"] == area]
st.dataframe(displayed, use_container_width=True, hide_index=True)

with st.expander("Baseline control catalogue"):
    st.dataframe(df, use_container_width=True, hide_index=True)
