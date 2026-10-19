from pathlib import Path
import math
from uuid import UUID, uuid4
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
    FAI01_EVALUATION_WIDGET_KEYS,
    SEC01_WIDGET_KEYS,
    TRN01_WIDGET_KEYS,
    TRN01_EXPLAINABILITY_WIDGET_KEYS,
    VAL01_EVALUATION_WIDGET_KEYS,
    VAL01_WIDGET_KEYS,
    MON01_WIDGET_KEYS,
    INC01_WIDGET_KEYS,
)
from src.governance.fairness_evaluation import (
    EVALUATION_STAGES,
    EVALUATION_STATUSES,
    FAIRNESS_EVALUATION_FIELDS,
    FAIRNESS_EVALUATION_WIDGET_FIELDS,
    METRIC_SCALES,
    THRESHOLD_COMPARATORS,
    evaluation_from_form,
    fairness_row_widget_key,
    validate_fairness_evaluation,
)
from src.governance.validation_evaluation import (
    VALIDATION_COMPARATORS,
    VALIDATION_EVALUATION_FIELDS,
    VALIDATION_EVALUATION_WIDGET_FIELDS,
    VALIDATION_METRIC_SCALES,
    VALIDATION_STAGES,
    VALIDATION_STATUSES,
    HUMAN_REVIEW_COMPARATOR,
    metric_comparison_status,
    validation_evaluation_from_form,
    validation_row_widget_key,
    validate_validation_evaluation,
)
from src.governance.explainability_evidence import (
    EXAMPLE_FIELDS,
    EXAMPLE_WIDGET_DEFAULTS,
    EXPLAINABILITY_EVIDENCE_FIELDS,
    EXPLAINABILITY_STATUSES,
    EXPLAINABILITY_STAGES,
    REVIEW_FIELDS,
    REVIEW_WIDGET_DEFAULTS,
    explainability_row_widget_key,
    validate_explainability_evidence,
)


def _case_widget_keys(widget_keys):
    generation = st.session_state.get("_case_load_generation")
    if not generation:
        return widget_keys
    return {
        field: f"{widget_key}_{generation}"
        for field, widget_key in widget_keys.items()
    }


def _initialize_explainability_row_state(
    row_kind, row_id, saved_row, defaults, generation
):
    id_field = "example_id" if row_kind == "example" else "review_id"
    identity_key = explainability_row_widget_key(
        row_kind, row_id, "persisted_identity", generation
    )
    if identity_key not in st.session_state:
        saved_identity = (
            saved_row.get(id_field)
            if isinstance(saved_row, dict) and id_field in saved_row
            else row_id
        )
        st.session_state[identity_key] = saved_identity
    for field, default in defaults.items():
        if field == id_field:
            continue
        key = explainability_row_widget_key(row_kind, row_id, field, generation)
        if key not in st.session_state:
            value = saved_row.get(field, default) if isinstance(saved_row, dict) else default
            st.session_state[key] = value if isinstance(value, str) else default


def _is_finite_widget_number(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


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
        elif field.endswith("_row_count"):
            if type(value) is not int or value < 0:
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
        existing_fai01 = control_evidence.get("FAI-01", {})
        has_existing_evaluation = (
            isinstance(existing_fai01, dict)
            and "fairness_evaluation" in existing_fai01
        )
        existing_evaluation = existing_fai01.get("fairness_evaluation")
        base_assessment = {
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
        if has_existing_evaluation:
            base_assessment["fairness_evaluation"] = existing_evaluation
        control_evidence["FAI-01"] = base_assessment
        st.session_state["control_evidence"] = control_evidence
        st.success("FAI-01 assessment saved.")

    st.markdown("#### Optional fairness metrics & evaluation documentation")
    st.caption(
        "Planned records document a design only. Performed records are user-reported "
        "test documentation; this app does not verify results or statistical validity. "
        "Use synthetic information only."
    )
    current_fai01 = control_evidence.get("FAI-01", {})
    if not isinstance(current_fai01, dict):
        current_fai01 = {}
    has_saved_evaluation = "fairness_evaluation" in current_fai01
    saved_evaluation = current_fai01.get("fairness_evaluation", {})
    saved_evaluation_errors = (
        validate_fairness_evaluation(saved_evaluation)
        if has_saved_evaluation
        else []
    )
    if saved_evaluation_errors:
        st.warning(
            "Saved fairness evaluation is Invalid and is not treated as valid "
            "evaluation documentation. Review and explicitly save a corrected "
            "record to replace it. "
            + "; ".join(saved_evaluation_errors)
        )
    if not isinstance(saved_evaluation, dict):
        saved_evaluation = {}
    evaluation_widget_keys = _case_widget_keys(FAI01_EVALUATION_WIDGET_KEYS)
    saved_thresholds = saved_evaluation.get("thresholds", [])
    if not isinstance(saved_thresholds, list):
        saved_thresholds = []
    saved_subgroup_results = saved_evaluation.get("subgroup_results", [])
    if not isinstance(saved_subgroup_results, list):
        saved_subgroup_results = []
    evaluation_defaults = {
        field: "" for field in FAIRNESS_EVALUATION_WIDGET_FIELDS
    }
    evaluation_defaults.update({
        "evaluation_stage": "Planned",
        "evaluation_status": "Draft",
        "responsible_owner": use_case.get("owner", ""),
        "threshold_row_count": len(saved_thresholds),
        "subgroup_result_row_count": len(saved_subgroup_results),
    })
    saved_evaluation = dict(saved_evaluation)
    saved_evaluation.update({
        "threshold_row_count": len(saved_thresholds),
        "subgroup_result_row_count": len(saved_subgroup_results),
    })
    if saved_evaluation.get("evaluation_stage") not in EVALUATION_STAGES:
        saved_evaluation["evaluation_stage"] = evaluation_defaults["evaluation_stage"]
    if saved_evaluation.get("evaluation_status") not in EVALUATION_STATUSES:
        saved_evaluation["evaluation_status"] = evaluation_defaults["evaluation_status"]
    _hydrate_control_form(
        evaluation_widget_keys,
        saved_evaluation,
        evaluation_defaults,
        "FAI-01-evaluation",
    )
    generation = st.session_state.get("_case_load_generation")
    row_defaults = {
        "threshold": {
            "kind": "numeric",
            "comparator": "<=",
            "value": 0.0,
            "metric_unit": "",
            "metric_scale": "unbounded",
            "rationale": "",
            "description": "",
            "human_review_required": False,
        },
        "subgroup_result": {
            "subgroup_label": "",
            "metric_value": 0.0,
            "metric_unit": "",
            "metric_scale": "unbounded",
            "sample_size": "",
            "event_numerator": "",
            "evidence_reference": "",
        },
    }
    saved_rows = {
        "threshold": saved_thresholds,
        "subgroup_result": saved_subgroup_results,
    }
    count_fields = {
        "threshold": "threshold_row_count",
        "subgroup_result": "subgroup_result_row_count",
    }
    for row_kind, defaults in row_defaults.items():
        count = st.session_state[evaluation_widget_keys[count_fields[row_kind]]]
        for index in range(count):
            saved_row = (
                saved_rows[row_kind][index]
                if index < len(saved_rows[row_kind])
                else {}
            )
            if not isinstance(saved_row, dict):
                saved_row = {}
            for field, default in defaults.items():
                key = fairness_row_widget_key(row_kind, index, field, generation)
                if key in st.session_state:
                    continue
                value = saved_row.get(field, default)
                if field == "kind" and value not in ("numeric", "documented"):
                    value = default
                elif field == "comparator" and value not in THRESHOLD_COMPARATORS:
                    value = default
                elif field == "metric_scale" and value not in METRIC_SCALES:
                    value = default
                elif field in {"value", "metric_value"} and (
                    not _is_finite_widget_number(value)
                ):
                    value = default
                elif field == "human_review_required" and type(value) is not bool:
                    value = default
                elif field in {"sample_size", "event_numerator"}:
                    value = "" if value is None else str(value)
                elif field not in {
                    "value",
                    "metric_value",
                    "human_review_required",
                } and not isinstance(value, str):
                    value = default
                st.session_state[key] = value

    evaluation_text_areas = {
        "groups_and_selection_basis": "Groups/subgroups and selection basis",
        "dataset_scope": "Dataset scope",
        "dataset_population": "Dataset population",
        "dataset_representativeness_limitations": "Dataset representativeness limitations",
        "metric_definition": "Metric definition",
        "calculation_approach": "Calculation approach",
        "evaluation_outcome": "Evaluation outcome",
        "evidence_reference": "Evidence reference",
        "observed_limitations": "Observed limitations",
        "mitigation_actions": "Mitigation actions",
    }
    evaluation_values = {"threshold_rows": [], "subgroup_rows": []}
    for field in FAIRNESS_EVALUATION_WIDGET_FIELDS:
        if field.endswith("_row_count"):
            continue
        key = evaluation_widget_keys[field]
        if field == "evaluation_stage":
            evaluation_values[field] = st.selectbox(
                "Evaluation stage",
                EVALUATION_STAGES,
                key=key,
            )
        elif field == "evaluation_status":
            evaluation_values[field] = st.selectbox(
                "Evaluation documentation status",
                EVALUATION_STATUSES,
                key=key,
            )
        elif field in evaluation_text_areas:
            evaluation_values[field] = st.text_area(
                evaluation_text_areas[field],
                key=key,
            )
        else:
            labels = {
                "dataset_source": "Dataset source",
                "dataset_timeframe": "Dataset timeframe",
                "metric_name": "Fairness metric name",
                "test_date": "Test date (YYYY-MM-DD)",
                "responsible_owner": "Evaluation responsible owner",
                "reviewer": "Evaluation reviewer",
                "review_date": "Evaluation review date (YYYY-MM-DD)",
            }
            evaluation_values[field] = st.text_input(
                labels[field],
                key=key,
            )

    st.markdown("**Thresholds for this single declared metric**")
    st.caption(
        "Numeric thresholds and subgroup results must use the same metric unit "
        "and scale. Qualitative criteria require human review."
    )
    threshold_count_key = evaluation_widget_keys["threshold_row_count"]
    if st.button("Add threshold", key=f"{threshold_count_key}_add"):
        st.session_state[threshold_count_key] += 1
    threshold_count = st.session_state[threshold_count_key]
    for index in range(threshold_count):
        if st.button(
            f"Remove threshold {index + 1}",
            key=f"{threshold_count_key}_remove_{index}",
        ):
            for next_index in range(index, threshold_count - 1):
                for field, default in row_defaults["threshold"].items():
                    target_key = fairness_row_widget_key(
                        "threshold", next_index, field, generation
                    )
                    source_key = fairness_row_widget_key(
                        "threshold", next_index + 1, field, generation
                    )
                    st.session_state[target_key] = st.session_state.get(
                        source_key, default
                    )
            st.session_state[threshold_count_key] -= 1
            threshold_count -= 1
            break
    for index in range(threshold_count):
        st.markdown(f"**Threshold {index + 1}**")
        kind_key = fairness_row_widget_key("threshold", index, "kind", generation)
        kind = st.selectbox(
            "Threshold type",
            ("numeric", "documented"),
            format_func=lambda value: (
                "Numeric threshold" if value == "numeric" else "Qualitative criterion"
            ),
            key=kind_key,
        )
        if kind == "numeric":
            columns = st.columns(3)
            threshold_row = {
                "comparator": columns[0].selectbox(
                    "Comparator",
                    THRESHOLD_COMPARATORS,
                    key=fairness_row_widget_key(
                        "threshold", index, "comparator", generation
                    ),
                ),
                "value": columns[1].number_input(
                    "Threshold value",
                    key=fairness_row_widget_key(
                        "threshold", index, "value", generation
                    ),
                ),
                "metric_unit": columns[2].text_input(
                    "Metric unit",
                    key=fairness_row_widget_key(
                        "threshold", index, "metric_unit", generation
                    ),
                ),
                "metric_scale": st.selectbox(
                    "Metric scale",
                    METRIC_SCALES,
                    key=fairness_row_widget_key(
                        "threshold", index, "metric_scale", generation
                    ),
                ),
                "rationale": st.text_input(
                    "Threshold rationale",
                    key=fairness_row_widget_key(
                        "threshold", index, "rationale", generation
                    ),
                ),
            }
        else:
            threshold_row = {
                "description": st.text_input(
                    "Qualitative criterion description",
                    key=fairness_row_widget_key(
                        "threshold", index, "description", generation
                    ),
                ),
                "rationale": st.text_input(
                    "Human-review rationale",
                    key=fairness_row_widget_key(
                        "threshold", index, "rationale", generation
                    ),
                ),
                "human_review_required": st.checkbox(
                    "Human review is required for this criterion",
                    key=fairness_row_widget_key(
                        "threshold", index, "human_review_required", generation
                    ),
                ),
            }
        evaluation_values.setdefault("threshold_rows", []).append({
            "kind": kind,
            **threshold_row,
        })

    st.markdown("**Subgroup results for the declared metric**")
    subgroup_count_key = evaluation_widget_keys["subgroup_result_row_count"]
    if st.button("Add subgroup result", key=f"{subgroup_count_key}_add"):
        st.session_state[subgroup_count_key] += 1
    subgroup_count = st.session_state[subgroup_count_key]
    for index in range(subgroup_count):
        if st.button(
            f"Remove subgroup result {index + 1}",
            key=f"{subgroup_count_key}_remove_{index}",
        ):
            for next_index in range(index, subgroup_count - 1):
                for field, default in row_defaults["subgroup_result"].items():
                    target_key = fairness_row_widget_key(
                        "subgroup_result", next_index, field, generation
                    )
                    source_key = fairness_row_widget_key(
                        "subgroup_result", next_index + 1, field, generation
                    )
                    st.session_state[target_key] = st.session_state.get(
                        source_key, default
                    )
            st.session_state[subgroup_count_key] -= 1
            subgroup_count -= 1
            break
    for index in range(subgroup_count):
        st.markdown(f"**Subgroup result {index + 1}**")
        columns = st.columns(3)
        subgroup_row = {
            "subgroup_label": columns[0].text_input(
                "Subgroup name",
                key=fairness_row_widget_key(
                    "subgroup_result", index, "subgroup_label", generation
                ),
            ),
            "metric_value": columns[1].number_input(
                "Metric value",
                key=fairness_row_widget_key(
                    "subgroup_result", index, "metric_value", generation
                ),
            ),
            "metric_unit": columns[2].text_input(
                "Metric unit",
                key=fairness_row_widget_key(
                    "subgroup_result", index, "metric_unit", generation
                ),
            ),
            "metric_scale": st.selectbox(
                "Metric scale",
                METRIC_SCALES,
                key=fairness_row_widget_key(
                    "subgroup_result", index, "metric_scale", generation
                ),
            ),
            "sample_size": st.text_input(
                "Sample size / denominator (optional)",
                key=fairness_row_widget_key(
                    "subgroup_result", index, "sample_size", generation
                ),
            ),
            "event_numerator": st.text_input(
                "Event numerator (optional)",
                key=fairness_row_widget_key(
                    "subgroup_result", index, "event_numerator", generation
                ),
            ),
            "evidence_reference": st.text_input(
                "Subgroup evidence reference",
                key=fairness_row_widget_key(
                    "subgroup_result", index, "evidence_reference", generation
                ),
            ),
        }
        evaluation_values.setdefault("subgroup_rows", []).append(subgroup_row)

    save_evaluation = st.button("Save FAI-01 fairness evaluation")

    if save_evaluation:
        normalized_evaluation, errors = evaluation_from_form(evaluation_values)
        errors.extend(validate_fairness_evaluation(normalized_evaluation))
        if errors:
            st.error(
                "Fairness evaluation was not saved:\n\n"
                + "\n".join(f"- {error}" for error in errors)
            )
        else:
            current_fai01 = control_evidence.get("FAI-01", {})
            if not isinstance(current_fai01, dict):
                current_fai01 = {}
            current_fai01 = dict(current_fai01)
            current_fai01["fairness_evaluation"] = normalized_evaluation
            control_evidence["FAI-01"] = current_fai01
            st.session_state["control_evidence"] = control_evidence
            st.success(
                f"FAI-01 fairness evaluation saved as "
                f"{normalized_evaluation['evaluation_stage']} documentation."
            )

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
        current_trn01 = control_evidence.get("TRN-01", {})
        has_explainability = (
            isinstance(current_trn01, dict)
            and "explainability_evidence" in current_trn01
        )
        saved_explainability = (
            current_trn01.get("explainability_evidence")
            if isinstance(current_trn01, dict)
            else None
        )
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
        if has_explainability:
            control_evidence["TRN-01"]["explainability_evidence"] = (
                saved_explainability
            )
        st.session_state["control_evidence"] = control_evidence
        st.success("TRN-01 assessment saved.")

    st.markdown("#### Optional structured explainability evidence")
    st.caption(
        "Record synthetic, user-reported examples only. The application does not "
        "generate or verify explanations. A saved example does not establish "
        "correctness, accessibility, usefulness, or audience understanding. "
        "Evidence references are user-reported and are not independently authenticated."
    )
    current_trn01 = control_evidence.get("TRN-01", {})
    if not isinstance(current_trn01, dict):
        current_trn01 = {}
    has_saved_explainability = "explainability_evidence" in current_trn01
    saved_explainability = current_trn01.get("explainability_evidence")
    explainability_errors = (
        validate_explainability_evidence(saved_explainability)
        if has_saved_explainability
        else []
    )
    if explainability_errors:
        st.warning(
            "Saved explainability evidence is Invalid and remains unchanged "
            "unless a valid replacement is explicitly saved. "
            + "; ".join(explainability_errors)
        )
    if not isinstance(saved_explainability, dict):
        saved_explainability = {}
    explainability_keys = _case_widget_keys(TRN01_EXPLAINABILITY_WIDGET_KEYS)
    explainability_defaults = {
        field: "" for field in EXPLAINABILITY_EVIDENCE_FIELDS
        if field not in {"examples", "accessibility_usefulness_reviews"}
    }
    explainability_defaults.update({
        "evaluation_stage": "Planned",
        "evaluation_status": "Draft",
        "responsible_owner": use_case.get("owner", ""),
    })
    explainability_root_keys = {
        field: explainability_keys[field]
        for field in explainability_defaults
    }
    explainability_saved_root = {
        field: saved_explainability.get(field, default)
        for field, default in explainability_defaults.items()
    }
    if explainability_saved_root["evaluation_stage"] not in EXPLAINABILITY_STAGES:
        explainability_saved_root["evaluation_stage"] = "Planned"
    if explainability_saved_root["evaluation_status"] not in EXPLAINABILITY_STATUSES:
        explainability_saved_root["evaluation_status"] = "Draft"
    _hydrate_control_form(
        explainability_root_keys,
        explainability_saved_root,
        explainability_defaults,
        "TRN-01-explainability",
    )
    saved_examples = saved_explainability.get("examples", [])
    if not isinstance(saved_examples, list):
        saved_examples = []
    saved_reviews = saved_explainability.get("accessibility_usefulness_reviews", [])
    if not isinstance(saved_reviews, list):
        saved_reviews = []
    generation = st.session_state.get("_case_load_generation")
    examples_ids_key = explainability_keys["example_row_ids"]
    reviews_ids_key = explainability_keys["review_row_ids"]
    example_sources_key = f"{examples_ids_key}_source_rows"
    review_sources_key = f"{reviews_ids_key}_source_rows"
    if examples_ids_key not in st.session_state:
        example_ids = []
        for row in saved_examples:
            example_ids.append(str(uuid4()))
        st.session_state[examples_ids_key] = example_ids
        st.session_state[example_sources_key] = dict(zip(example_ids, saved_examples))
    elif example_sources_key not in st.session_state:
        st.session_state[example_sources_key] = dict(zip(
            st.session_state[examples_ids_key], saved_examples
        ))
    if reviews_ids_key not in st.session_state:
        review_ids = []
        for row in saved_reviews:
            review_ids.append(str(uuid4()))
        st.session_state[reviews_ids_key] = review_ids
        st.session_state[review_sources_key] = dict(zip(review_ids, saved_reviews))
    elif review_sources_key not in st.session_state:
        st.session_state[review_sources_key] = dict(zip(
            st.session_state[reviews_ids_key], saved_reviews
        ))
    example_sources = st.session_state[example_sources_key]
    review_sources = st.session_state[review_sources_key]
    examples_ids = st.session_state[examples_ids_key]
    review_ids = st.session_state[reviews_ids_key]
    for row_kind, row_ids, sources, defaults in (
        ("example", examples_ids, example_sources, EXAMPLE_WIDGET_DEFAULTS),
        ("review", review_ids, review_sources, REVIEW_WIDGET_DEFAULTS),
    ):
        for row_id in row_ids:
            _initialize_explainability_row_state(
                row_kind,
                row_id,
                sources.get(row_id, {}),
                defaults,
                generation,
            )

    for field in explainability_defaults:
        key = explainability_keys[field]
        label = {
            "evaluation_stage": "Explainability documentation stage",
            "evaluation_status": "Explainability documentation status",
            "explanation_method": "Explanation method",
            "method_description": "Method description",
            "intended_audiences": "Intended audiences",
            "planned_context": "Planned example/context (synthetic)",
            "planned_feedback_collection": "Planned accessibility/usefulness feedback collection",
            "human_review_approach": "Human review approach",
            "challenge_correction_process": "Challenge and correction process",
            "limitations": "Explainability limitations",
            "outstanding_actions": "Outstanding actions",
            "responsible_owner": "Explainability evidence owner",
            "reviewer": "Explainability evidence reviewer",
            "review_date": "Documentation review date (YYYY-MM-DD)",
        }[field]
        if field == "evaluation_stage":
            st.selectbox(label, EXPLAINABILITY_STAGES, key=key)
        elif field == "evaluation_status":
            st.selectbox(label, EXPLAINABILITY_STATUSES, key=key)
        elif field in {
            "method_description", "intended_audiences", "planned_context",
            "planned_feedback_collection",
            "human_review_approach", "challenge_correction_process",
            "limitations", "outstanding_actions",
        }:
            st.text_area(label, key=key)
        else:
            st.text_input(label, key=key)

    st.markdown("**Synthetic explanation examples**")
    explainability_stage = st.session_state[
        explainability_keys["evaluation_stage"]
    ]
    if st.button(
        "Add explanation example",
        key=f"{examples_ids_key}_add",
        disabled=explainability_stage == "Planned",
    ):
        row_id = str(uuid4())
        examples_ids.append(row_id)
        example_sources[row_id] = {}
        _initialize_explainability_row_state(
            "example", row_id, {}, EXAMPLE_WIDGET_DEFAULTS, generation
        )
        st.rerun()
    if explainability_stage == "Planned":
        st.caption(
            "Planned documentation records example context above; add example "
            "rows only after documenting a performed example."
        )
    example_labels = {
        "decision_reference_id": "Synthetic decision/reference ID",
        "intended_audience": "Example intended audience",
        "input_factor_summary": "Synthetic input / relevant factor summary",
        "recommendation_output": "Recommendation or decision-support output",
        "human_readable_explanation": "Human-readable explanation",
        "evidence_reference": "Example evidence reference",
        "example_date": "Example date (YYYY-MM-DD)",
        "human_review_findings_reference": "Human review findings/reference (optional)",
    }
    example_records = []
    example_identity_errors = []
    example_identity_values = [
        st.session_state[explainability_row_widget_key(
            "example", row_id, "persisted_identity", generation
        )]
        for row_id in examples_ids
    ]
    example_id_counts = {
        value: example_identity_values.count(value)
        for value in example_identity_values
        if isinstance(value, str)
    }
    for index, row_id in enumerate(list(examples_ids)):
        identity_key = explainability_row_widget_key(
            "example", row_id, "persisted_identity", generation
        )
        persisted_id = st.session_state[identity_key]
        try:
            valid_id = isinstance(persisted_id, str) and str(UUID(persisted_id)) == persisted_id
        except ValueError:
            valid_id = False
        duplicate_id = (
            isinstance(persisted_id, str) and example_id_counts[persisted_id] > 1
        )
        st.markdown(f"Example {index + 1}")
        if not valid_id or duplicate_id:
            issue = "duplicate" if duplicate_id else "invalid"
            st.warning(
                f"Example {index + 1} has a {issue} saved ID. Remove this row, "
                "add a replacement, and re-enter its documentation before saving."
            )
            example_identity_errors.append(
                f"Example {index + 1} has an {issue} saved ID; explicitly "
                "remove and re-add the row before saving."
            )
        if st.button(
            f"Remove explanation example {index + 1}",
            key=f"{examples_ids_key}_remove_{row_id}",
        ):
            examples_ids.remove(row_id)
            st.rerun()
        record = {"example_id": row_id}
        for field in EXAMPLE_FIELDS:
            if field == "example_id":
                continue
            key = explainability_row_widget_key("example", row_id, field, generation)
            record[field] = st.text_input(example_labels[field], key=key)
        record["example_id"] = persisted_id
        example_records.append(record)

    st.markdown("**Accessibility and usefulness feedback records**")
    st.caption(
        "These records document review activity only; their presence does not "
        "establish accessibility, usefulness, understanding, or acceptance."
    )
    if st.button(
        "Add audience review",
        key=f"{reviews_ids_key}_add",
        disabled=explainability_stage == "Planned",
    ):
        row_id = str(uuid4())
        review_ids.append(row_id)
        review_sources[row_id] = {}
        _initialize_explainability_row_state(
            "review", row_id, {}, REVIEW_WIDGET_DEFAULTS, generation
        )
        st.rerun()
    review_labels = {
        "intended_audience": "Review intended audience",
        "review_method": "Accessibility / usefulness review method",
        "findings_feedback_summary": "Synthetic findings / feedback summary",
        "evidence_reference": "Review evidence reference",
        "review_date": "Audience review date (YYYY-MM-DD)",
        "limitations_corrective_actions": "Review limitations / corrective actions",
    }
    review_records = []
    review_identity_errors = []
    review_identity_values = [
        st.session_state[explainability_row_widget_key(
            "review", row_id, "persisted_identity", generation
        )]
        for row_id in review_ids
    ]
    review_id_counts = {
        value: review_identity_values.count(value)
        for value in review_identity_values
        if isinstance(value, str)
    }
    for index, row_id in enumerate(list(review_ids)):
        identity_key = explainability_row_widget_key(
            "review", row_id, "persisted_identity", generation
        )
        persisted_id = st.session_state[identity_key]
        try:
            valid_id = isinstance(persisted_id, str) and str(UUID(persisted_id)) == persisted_id
        except ValueError:
            valid_id = False
        duplicate_id = (
            isinstance(persisted_id, str) and review_id_counts[persisted_id] > 1
        )
        st.markdown(f"Audience review {index + 1}")
        if not valid_id or duplicate_id:
            issue = "duplicate" if duplicate_id else "invalid"
            st.warning(
                f"Audience review {index + 1} has a {issue} saved ID. Remove "
                "this row, add a replacement, and re-enter its documentation before saving."
            )
            review_identity_errors.append(
                f"Audience review {index + 1} has an {issue} saved ID; "
                "explicitly remove and re-add the row before saving."
            )
        if st.button(
            f"Remove audience review {index + 1}",
            key=f"{reviews_ids_key}_remove_{row_id}",
        ):
            review_ids.remove(row_id)
            st.rerun()
        record = {"review_id": row_id}
        for field in REVIEW_FIELDS:
            if field == "review_id":
                continue
            key = explainability_row_widget_key("review", row_id, field, generation)
            record[field] = st.text_input(review_labels[field], key=key)
        record["review_id"] = persisted_id
        review_records.append(record)

    if st.button("Save TRN-01 explainability evidence"):
        explainability_record = {
            field: st.session_state[explainability_keys[field]]
            for field in explainability_defaults
        }
        explainability_record["examples"] = example_records
        explainability_record["accessibility_usefulness_reviews"] = review_records
        errors = (
            example_identity_errors
            + review_identity_errors
            + validate_explainability_evidence(explainability_record)
        )
        if errors:
            st.error(
                "Explainability evidence was not saved:\n\n"
                + "\n".join(f"- {error}" for error in errors)
            )
        else:
            current_trn01 = control_evidence.get("TRN-01", {})
            if not isinstance(current_trn01, dict):
                current_trn01 = {}
            current_trn01 = dict(current_trn01)
            current_trn01["explainability_evidence"] = explainability_record
            control_evidence["TRN-01"] = current_trn01
            st.session_state["control_evidence"] = control_evidence
            st.success(
                "TRN-01 explainability documentation saved as "
                f"{explainability_record['evaluation_stage']}."
            )

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
        existing_val01 = control_evidence.get("VAL-01", {})
        has_existing_evaluation = (
            isinstance(existing_val01, dict)
            and "validation_evaluation" in existing_val01
        )
        existing_evaluation = (
            existing_val01.get("validation_evaluation")
            if isinstance(existing_val01, dict)
            else None
        )
        base_assessment = {
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
        if has_existing_evaluation:
            base_assessment["validation_evaluation"] = existing_evaluation
        control_evidence["VAL-01"] = base_assessment
        st.session_state["control_evidence"] = control_evidence
        st.success("VAL-01 assessment saved.")

    st.markdown("#### Optional structured validation evaluation")
    st.caption(
        "Planned records describe intended validation. Performed records are "
        "user-reported documentation and do not independently verify model "
        "performance, safety, or compliance. Use synthetic information only."
    )
    current_val01 = control_evidence.get("VAL-01", {})
    if not isinstance(current_val01, dict):
        current_val01 = {}
    has_saved_validation = "validation_evaluation" in current_val01
    saved_validation = current_val01.get("validation_evaluation", {})
    validation_errors = (
        validate_validation_evaluation(saved_validation)
        if has_saved_validation
        else []
    )
    if validation_errors:
        st.warning(
            "Saved validation evaluation is Invalid and is not treated as valid "
            "validation documentation. Correct it and explicitly save to replace "
            "the saved record. " + "; ".join(validation_errors)
        )
    if not isinstance(saved_validation, dict):
        saved_validation = {}
    validation_widget_keys = _case_widget_keys(VAL01_EVALUATION_WIDGET_KEYS)
    saved_metrics = saved_validation.get("metrics", [])
    if not isinstance(saved_metrics, list):
        saved_metrics = []
    saved_results = saved_validation.get("results", [])
    if not isinstance(saved_results, list):
        saved_results = []
    validation_defaults = {
        field: "" for field in VALIDATION_EVALUATION_WIDGET_FIELDS
    }
    validation_defaults.update({
        "evaluation_stage": "Planned",
        "evaluation_status": "Draft",
        "metric_row_count": len(saved_metrics),
        "result_row_count": len(saved_results),
        "responsible_owner": use_case.get("owner", ""),
        "reviewer": "",
    })
    saved_validation = dict(saved_validation)
    saved_validation.update({
        "metric_row_count": len(saved_metrics),
        "result_row_count": len(saved_results),
    })
    if saved_validation.get("evaluation_stage") not in VALIDATION_STAGES:
        saved_validation["evaluation_stage"] = validation_defaults["evaluation_stage"]
    if saved_validation.get("evaluation_status") not in VALIDATION_STATUSES:
        saved_validation["evaluation_status"] = validation_defaults["evaluation_status"]
    _hydrate_control_form(
        validation_widget_keys,
        saved_validation,
        validation_defaults,
        "VAL-01-evaluation",
    )
    generation = st.session_state.get("_case_load_generation")
    metric_row_defaults = {
        "metric_id": "",
        "metric_name": "",
        "definition": "",
        "unit": "",
        "scale": "unbounded",
        "threshold_comparator": "<=",
        "threshold_value": 0.0,
        "threshold_rationale": "",
    }
    result_row_defaults = {
        "metric_id": "",
        "measured_value": 0.0,
        "unit": "",
        "scale": "unbounded",
        "sample_size": "",
        "test_date": "",
        "evidence_reference": "",
    }
    row_defaults = {"metric": metric_row_defaults, "result": result_row_defaults}
    saved_rows = {"metric": saved_metrics, "result": saved_results}
    for row_kind, defaults in row_defaults.items():
        count_field = f"{row_kind}_row_count"
        count = st.session_state[validation_widget_keys[count_field]]
        for index in range(count):
            saved_row = saved_rows[row_kind][index] if index < len(saved_rows[row_kind]) else {}
            if not isinstance(saved_row, dict):
                saved_row = {}
            for field, default in defaults.items():
                key = validation_row_widget_key(row_kind, index, field, generation)
                if key in st.session_state:
                    continue
                value = saved_row.get(field, default)
                if field in {"scale"} and value not in VALIDATION_METRIC_SCALES:
                    value = default
                elif field == "threshold_comparator" and value not in (
                    *VALIDATION_COMPARATORS,
                    HUMAN_REVIEW_COMPARATOR,
                ):
                    value = default
                elif field in {"threshold_value", "measured_value"} and (
                    not _is_finite_widget_number(value)
                ):
                    value = default
                elif field == "sample_size":
                    value = "" if value is None else str(value)
                elif field not in {"threshold_value", "measured_value"} and not isinstance(value, str):
                    value = default
                st.session_state[key] = value

    validation_form_values = {
        "metric_rows": [],
        "result_rows": [],
    }
    for field in VALIDATION_EVALUATION_WIDGET_FIELDS:
        if field.endswith("_row_count"):
            continue
        key = validation_widget_keys[field]
        if field == "evaluation_stage":
            validation_form_values[field] = st.selectbox(
                "Validation evaluation stage",
                VALIDATION_STAGES,
                key=key,
            )
        elif field == "evaluation_status":
            validation_form_values[field] = st.selectbox(
                "Validation documentation status",
                VALIDATION_STATUSES,
                key=key,
            )
        else:
            labels = {
                "dataset_source": "Dataset / test-set source",
                "dataset_purpose": "Dataset / test-set purpose",
                "dataset_population": "Dataset / test-set population",
                "dataset_scope": "Dataset / test-set scope",
                "dataset_timeframe": "Dataset / test-set timeframe",
                "dataset_limitations": "Dataset limitations",
                "validation_method": "Validation method",
                "test_objectives": "Test objectives",
                "human_oversight_testing": "Human oversight testing approach",
                "human_oversight_observations": "Human oversight test observations",
                "validation_outcome": "Validation observations (no overall pass/fail claim)",
                "limitations": "Validation limitations",
                "outstanding_actions": "Outstanding actions",
                "responsible_owner": "Evaluation responsible owner",
                "reviewer": "Evaluation reviewer",
                "review_date": "Evaluation review date (YYYY-MM-DD)",
            }
            if field in {
                "dataset_purpose", "dataset_population", "dataset_scope",
                "dataset_limitations", "validation_method", "test_objectives",
                "human_oversight_testing", "human_oversight_observations",
                "validation_outcome", "limitations", "outstanding_actions",
            }:
                validation_form_values[field] = st.text_area(labels[field], key=key)
            else:
                validation_form_values[field] = st.text_input(labels[field], key=key)

    st.markdown("**Validation metrics and planned acceptance thresholds**")
    st.caption(
        "Each metric has its own identifier, threshold, unit, and scale. Result "
        "rows select a metric and must match its unit and scale. No official "
        "pass threshold is supplied."
    )
    metric_count_key = validation_widget_keys["metric_row_count"]
    if st.button("Add validation metric", key=f"{metric_count_key}_add"):
        st.session_state[metric_count_key] += 1
    metric_count = st.session_state[metric_count_key]
    result_count_key = validation_widget_keys["result_row_count"]
    result_count_for_metrics = st.session_state[result_count_key]
    linked_metric_ids = {
        st.session_state.get(
            validation_row_widget_key("result", result_index, "metric_id", generation),
            "",
        )
        for result_index in range(result_count_for_metrics)
    }
    for index in range(metric_count):
        metric_id_key = validation_row_widget_key(
            "metric", index, "metric_id", generation
        )
        metric_id = st.session_state.get(metric_id_key, "")
        metric_has_results = bool(metric_id and metric_id in linked_metric_ids)
        if st.button(
            f"Remove validation metric {index + 1}",
            key=f"{metric_count_key}_remove_{index}",
            disabled=metric_has_results,
        ):
            for next_index in range(index, metric_count - 1):
                for field, default in metric_row_defaults.items():
                    target = validation_row_widget_key("metric", next_index, field, generation)
                    source = validation_row_widget_key("metric", next_index + 1, field, generation)
                    st.session_state[target] = st.session_state.get(source, default)
            st.session_state[metric_count_key] -= 1
            metric_count -= 1
            break
        if metric_has_results:
            st.caption(
                f"Remove linked result rows first, then remove metric '{metric_id}'."
            )
    for index in range(metric_count):
        st.markdown(f"**Metric {index + 1}**")
        id_key = validation_row_widget_key("metric", index, "metric_id", generation)
        metric_id = st.text_input("Metric ID", key=id_key)
        name_key = validation_row_widget_key("metric", index, "metric_name", generation)
        metric_name = st.text_input("Metric name", key=name_key)
        definition_key = validation_row_widget_key("metric", index, "definition", generation)
        definition = st.text_area("Metric definition", key=definition_key)
        columns = st.columns(3)
        unit = columns[0].text_input(
            "Metric unit",
            key=validation_row_widget_key("metric", index, "unit", generation),
        )
        scale = columns[1].selectbox(
            "Metric scale",
            VALIDATION_METRIC_SCALES,
            key=validation_row_widget_key("metric", index, "scale", generation),
        )
        comparator_options = (*VALIDATION_COMPARATORS, HUMAN_REVIEW_COMPARATOR)
        comparator = columns[2].selectbox(
            "Acceptance comparator",
            comparator_options,
            key=validation_row_widget_key(
                "metric", index, "threshold_comparator", generation
            ),
        )
        if comparator == HUMAN_REVIEW_COMPARATOR:
            threshold_value = None
            st.caption(
                "No numeric threshold is recorded; this metric requires human review."
            )
        else:
            threshold_value = st.number_input(
                "Planned acceptance threshold",
                key=validation_row_widget_key(
                    "metric", index, "threshold_value", generation
                ),
            )
        threshold_rationale = st.text_area(
            "Acceptance threshold rationale",
            key=validation_row_widget_key(
                "metric", index, "threshold_rationale", generation
            ),
        )
        validation_form_values["metric_rows"].append({
            "metric_id": metric_id,
            "metric_name": metric_name,
            "definition": definition,
            "unit": unit,
            "scale": scale,
            "threshold_comparator": comparator,
            "threshold_value": threshold_value,
            "threshold_rationale": threshold_rationale,
        })

    st.markdown("**Performed metric results**")
    if st.button("Add validation result", key=f"{result_count_key}_add"):
        st.session_state[result_count_key] += 1
    result_count = st.session_state[result_count_key]
    for index in range(result_count):
        if st.button(
            f"Remove validation result {index + 1}",
            key=f"{result_count_key}_remove_{index}",
        ):
            for next_index in range(index, result_count - 1):
                for field, default in result_row_defaults.items():
                    target = validation_row_widget_key("result", next_index, field, generation)
                    source = validation_row_widget_key("result", next_index + 1, field, generation)
                    st.session_state[target] = st.session_state.get(source, default)
            st.session_state[result_count_key] -= 1
            result_count -= 1
            break
    metric_ids = list(dict.fromkeys(
        row["metric_id"]
        for row in validation_form_values["metric_rows"]
        if row["metric_id"]
    ))
    for index in range(result_count):
        st.markdown(f"**Validation result {index + 1}**")
        result_id_key = validation_row_widget_key("result", index, "metric_id", generation)
        selected_metric_id = st.session_state.get(result_id_key, "")
        metric_options = list(metric_ids)
        if selected_metric_id and selected_metric_id not in metric_options:
            metric_options.append(selected_metric_id)
        if not metric_options:
            metric_options = [""]
        result_metric_id = st.selectbox(
            "Result metric ID",
            metric_options,
            key=result_id_key,
        )
        matched_metric = next(
            (row for row in validation_form_values["metric_rows"] if row["metric_id"] == result_metric_id),
            None,
        )
        if matched_metric is not None:
            st.caption(
                f"Metric: {matched_metric['metric_name']} · "
                f"{matched_metric['unit']} · {matched_metric['scale']}"
            )
        elif result_metric_id:
            st.error(
                f"Result references unknown metric ID '{result_metric_id}'. "
                "Select a defined metric before saving."
            )
        columns = st.columns(3)
        measured_value = columns[0].number_input(
            "Measured value",
            key=validation_row_widget_key("result", index, "measured_value", generation),
        )
        result_unit = columns[1].text_input(
            "Result unit",
            key=validation_row_widget_key("result", index, "unit", generation),
        )
        result_scale = columns[2].selectbox(
            "Result scale",
            VALIDATION_METRIC_SCALES,
            key=validation_row_widget_key("result", index, "scale", generation),
        )
        sample_size = st.text_input(
            "Sample size / denominator (optional)",
            key=validation_row_widget_key("result", index, "sample_size", generation),
        )
        test_date = st.text_input(
            "Test date (YYYY-MM-DD)",
            key=validation_row_widget_key("result", index, "test_date", generation),
        )
        evidence_reference = st.text_input(
            "Result evidence reference",
            key=validation_row_widget_key(
                "result", index, "evidence_reference", generation
            ),
        )
        validation_form_values["result_rows"].append({
            "metric_id": result_metric_id,
            "measured_value": measured_value,
            "unit": result_unit,
            "scale": result_scale,
            "sample_size": sample_size,
            "test_date": test_date,
            "evidence_reference": evidence_reference,
        })
        if matched_metric is not None:
            comparison = metric_comparison_status(
                {
                    **matched_metric,
                    "threshold_comparator": matched_metric["threshold_comparator"],
                    "threshold_value": matched_metric["threshold_value"],
                },
                {
                    "measured_value": measured_value,
                    "unit": result_unit,
                    "scale": result_scale,
                },
            )
            st.caption(f"Metric comparison: **{comparison}**. This is not an overall validation result.")

    if st.button("Save VAL-01 validation evaluation"):
        normalized_validation = validation_evaluation_from_form(validation_form_values)
        errors = validate_validation_evaluation(normalized_validation)
        if errors:
            st.error(
                "Validation evaluation was not saved:\n\n"
                + "\n".join(f"- {error}" for error in errors)
            )
        else:
            current_val01 = control_evidence.get("VAL-01", {})
            if not isinstance(current_val01, dict):
                current_val01 = {}
            current_val01 = dict(current_val01)
            current_val01["validation_evaluation"] = normalized_validation
            control_evidence["VAL-01"] = current_val01
            st.session_state["control_evidence"] = control_evidence
            st.success(
                "VAL-01 validation evaluation saved as "
                f"{normalized_validation['evaluation_stage']} documentation."
            )

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
