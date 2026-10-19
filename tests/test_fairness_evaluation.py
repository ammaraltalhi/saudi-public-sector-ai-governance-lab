from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.governance.case_persistence import (
    DEFAULT_PLANS,
    FAI01_EVALUATION_WIDGET_KEYS,
    RISK_ANSWER_KEYS,
    USE_CASE_KEYS,
    load_case,
    restore_case,
    save_case,
)
from src.governance.control_assessment import assess_control
from src.governance.deployment_readiness import evaluate_readiness
from src.governance.fairness_evaluation import (
    FAIRNESS_EVALUATION_FIELDS,
    fairness_row_widget_key,
    validate_fairness_evaluation,
)
from src.governance.risk import calculate_risk


ROOT = Path(__file__).resolve().parents[1]


def make_case(name="Citizen Request Prioritisation AI", evidence=None):
    use_case = {field: f"Synthetic {field}" for field in USE_CASE_KEYS}
    use_case.update({
        "name": name,
        "owner": "Synthetic Service Owner",
        "affected_people": "Synthetic residents",
        "ai_role": "Recommendation only",
        "human_oversight": "Required before action",
    })
    return {
        "use_case": use_case,
        "risk_answers": {
            key: key in {"significant_decision", "vulnerable_groups"}
            for key in RISK_ANSWER_KEYS
        },
        "control_evidence": deepcopy(evidence or {}),
        "deployment_readiness_plans": deepcopy(DEFAULT_PLANS),
    }


def base_fai01(**overrides):
    record = {
        "affected_groups": "Synthetic residents",
        "fairness_risk": "Potential differences in prioritisation",
        "evaluation_approach": "Illustrative review plan",
        "data_evaluation_limitations": "No real dataset or results",
        "findings_observations": "No test performed",
        "mitigation_actions": "Human review is planned",
        "responsible_owner": "Synthetic Service Owner",
        "fairness_reviewer": "Synthetic Governance Reviewer",
        "assessment_status": "Draft",
    }
    record.update(overrides)
    return record


def planned_evaluation(**overrides):
    record = {
        field: [] if field in {"thresholds", "subgroup_results"} else ""
        for field in FAIRNESS_EVALUATION_FIELDS
    }
    record.update({
        "evaluation_stage": "Planned",
        "evaluation_status": "Draft",
    })
    record.update(overrides)
    return record


def performed_evaluation(**overrides):
    record = {
        field: (
            [{
                "kind": "numeric",
                "comparator": "<=",
                "value": 90,
                "metric_unit": "percent",
                "metric_scale": "percentage_0_100",
                "rationale": "Synthetic planning threshold only.",
            }]
            if field == "thresholds"
            else [{
                "subgroup_label": "Synthetic group A",
                "metric_value": 87.5,
                "metric_unit": "percent",
                "metric_scale": "percentage_0_100",
                "sample_size": 50,
                "event_numerator": 43,
                "evidence_reference": "Synthetic aggregate test record.",
            }, {
                "subgroup_label": "Synthetic group B",
                "metric_value": 74,
                "metric_unit": "percent",
                "metric_scale": "percentage_0_100",
                "sample_size": 50,
                "event_numerator": 37,
                "evidence_reference": "Synthetic aggregate test record.",
            }]
            if field == "subgroup_results"
            else f"Synthetic evaluation detail for {field}"
        )
        for field in FAIRNESS_EVALUATION_FIELDS
    }
    record.update({
        "evaluation_stage": "Performed",
        "evaluation_status": "Reviewed",
        "test_date": "2026-10-18",
        "review_date": "2026-10-19",
        "evaluation_outcome": "Synthetic example; not a real test result.",
        "evidence_reference": "Synthetic fixture reference; no real evidence.",
    })
    record.update(overrides)
    return record


def click_form_button(app, label):
    next(button for button in app.button if button.label == label).click().run()


def input_by_key(app, key):
    for widget_type in (
        "text_input",
        "text_area",
        "selectbox",
        "number_input",
        "checkbox",
    ):
        for widget in getattr(app, widget_type):
            if widget.key == key:
                return widget
    raise AssertionError(f"Widget not found: {key}")


def test_planned_evaluation_can_be_saved_without_results():
    record = planned_evaluation(
        groups_and_selection_basis="Potentially affected service users, selected by service context.",
        metric_name="Illustrative metric name",
        thresholds=[{
            "kind": "numeric",
            "comparator": "<=",
            "value": 1.25,
            "metric_unit": "score points",
            "metric_scale": "unbounded",
            "rationale": "Illustrative threshold for a non-normalised metric.",
        }],
    )

    assert validate_fairness_evaluation(record) == []
    assert not any(record[field] for field in (
        "subgroup_results",
        "evaluation_outcome",
        "test_date",
        "evidence_reference",
    ))


def test_planned_evaluation_rejects_performed_results():
    record = planned_evaluation(
        evaluation_outcome="Claimed outcome",
        evidence_reference="Claimed report",
        subgroup_results=[{
            "subgroup_label": "Synthetic group",
            "metric_value": 0.5,
            "metric_unit": "proportion",
            "metric_scale": "proportion_0_1",
            "sample_size": 10,
            "event_numerator": 5,
            "evidence_reference": "Synthetic reference",
        }],
    )

    assert any(
        "must not contain performed results" in error
        for error in validate_fairness_evaluation(record)
    )


def test_performed_evaluation_requires_context_results_and_valid_dates():
    assert validate_fairness_evaluation(performed_evaluation()) == []

    invalid = performed_evaluation(
        dataset_population=" ",
        subgroup_results=[],
        test_date="yesterday",
        evidence_reference="N/A",
    )
    errors = validate_fairness_evaluation(invalid)
    assert any("Dataset population is required" in error for error in errors)
    assert any("At least one subgroup results entry" in error for error in errors)
    assert any("Test date must be a valid date" in error for error in errors)
    assert any("Evidence reference is required" in error for error in errors)


def test_missing_extra_and_malformed_nested_fields_are_invalid():
    record = planned_evaluation()
    assert validate_fairness_evaluation({})
    assert validate_fairness_evaluation({**record, "unexpected": "value"})
    assert validate_fairness_evaluation({**record, "metric_name": 42})


def test_invalid_subgroup_counts_numbers_and_scales_are_rejected():
    cases = (
        {"sample_size": -1},
        {"sample_size": 0},
        {"event_numerator": 51},
        {"metric_value": "not numeric"},
        {"metric_value": float("nan")},
        {"metric_value": float("inf")},
        {"metric_scale": "unknown"},
        {"metric_value": 1.1, "metric_scale": "proportion_0_1"},
    )
    for override in cases:
        result = performed_evaluation()
        result["subgroup_results"][0].update(override)
        assert validate_fairness_evaluation(result), override


def test_invalid_threshold_shape_unit_scale_and_rationale_are_rejected():
    thresholds = (
        [{"kind": "numeric", "comparator": "approx", "value": 0.5,
          "metric_unit": "proportion", "metric_scale": "proportion_0_1",
          "rationale": "Synthetic rationale"}],
        [{"kind": "numeric", "comparator": "<=", "value": 0.5,
          "metric_unit": "N/A", "metric_scale": "proportion_0_1",
          "rationale": "Synthetic rationale"}],
        [{"kind": "numeric", "comparator": "<=", "value": 0.5,
          "metric_unit": "proportion", "metric_scale": "percentage_0_100",
          "rationale": "Synthetic rationale"}],
        [{"kind": "numeric", "comparator": "<=", "value": float("inf"),
          "metric_unit": "score", "metric_scale": "unbounded",
          "rationale": "Synthetic rationale"}],
        [{"kind": "numeric", "comparator": "<=", "value": 0.5,
          "metric_unit": "proportion", "metric_scale": "proportion_0_1",
          "rationale": " "}],
        [{"kind": "documented", "description": "Qualitative criterion",
          "rationale": "Requires judgment", "human_review_required": False}],
    )
    for value in thresholds:
        result = performed_evaluation(thresholds=value)
        assert validate_fairness_evaluation(result)

    malformed_unit = performed_evaluation()
    malformed_unit["subgroup_results"][0]["metric_unit"] = 17
    assert validate_fairness_evaluation(malformed_unit)


def test_valid_metric_values_support_distinct_declared_scales():
    examples = (
        (88.0, "percent", "percentage_0_100"),
        (0.88, "proportion", "proportion_0_1"),
        (-12.5, "signed score points", "unbounded"),
    )
    for value, unit, scale in examples:
        result = performed_evaluation()
        result["thresholds"][0].update({
            "value": value,
            "metric_unit": unit,
            "metric_scale": scale,
        })
        for subgroup_result in result["subgroup_results"]:
            subgroup_result.update({
                "metric_value": value,
                "metric_unit": unit,
                "metric_scale": scale,
            })
        assert validate_fairness_evaluation(result) == []


def test_subgroup_results_and_thresholds_must_share_one_metric_unit_and_scale():
    result = performed_evaluation()
    result["subgroup_results"][1]["metric_unit"] = "milliseconds"
    result["subgroup_results"][1]["metric_scale"] = "unbounded"
    assert any(
        "same metric unit and scale" in error
        for error in validate_fairness_evaluation(result)
    )

    result = performed_evaluation()
    result["thresholds"][0].update({
        "metric_unit": "proportion",
        "metric_scale": "proportion_0_1",
        "value": 0.8,
    })
    assert any(
        "same metric unit and scale" in error
        for error in validate_fairness_evaluation(result)
    )


def test_non_numeric_threshold_can_be_documented_for_human_review():
    result = planned_evaluation(
        thresholds=[{
            "kind": "documented",
            "description": "Qualitative parity review against documented service criteria.",
            "rationale": "The selected criterion is qualitative and not meaningfully numeric.",
            "human_review_required": True,
        }],
    )
    assert validate_fairness_evaluation(result) == []


def test_form_values_build_json_compatible_structured_records():
    from src.governance.fairness_evaluation import evaluation_from_form

    record, errors = evaluation_from_form({
        **planned_evaluation(),
        "threshold_rows": [{
            "kind": "documented",
            "description": "Synthetic qualitative criterion",
            "rationale": "Requires a human judgment.",
            "human_review_required": True,
        }],
        "subgroup_rows": [{
            "subgroup_label": "Synthetic group",
            "metric_value": 2.5,
            "metric_unit": "points",
            "metric_scale": "unbounded",
            "sample_size": "10",
            "event_numerator": "4",
            "evidence_reference": "Synthetic aggregate record",
        }],
    })
    assert errors == []
    assert record["thresholds"][0]["human_review_required"] is True
    assert record["subgroup_results"][0]["sample_size"] == 10


def test_optional_fai01_nested_record_round_trips_and_legacy_record_still_loads(tmp_path):
    evaluation = planned_evaluation(metric_name="Synthetic metric")
    state = make_case(evidence={
        "FAI-01": {
            **base_fai01(),
            "fairness_evaluation": evaluation,
        }
    })
    document = save_case(state, tmp_path)
    loaded = load_case(document["case_id"], tmp_path)
    restored = {}
    restore_case(restored, loaded)
    assert restored["control_evidence"]["FAI-01"]["fairness_evaluation"] == evaluation

    legacy = make_case(evidence={"FAI-01": base_fai01()})
    legacy_document = save_case(legacy, tmp_path)
    old_restored = {}
    restore_case(old_restored, load_case(legacy_document["case_id"], tmp_path))
    assert "fairness_evaluation" not in old_restored["control_evidence"]["FAI-01"]


def test_evaluation_and_base_fai01_saves_preserve_each_other():
    evaluation = planned_evaluation(
        metric_name="Saved synthetic metric",
        thresholds=[{
            "kind": "numeric",
            "comparator": "<=",
            "value": 0.9,
            "metric_unit": "proportion",
            "metric_scale": "proportion_0_1",
            "rationale": "Synthetic illustrative threshold.",
        }],
    )
    original = base_fai01()
    app = AppTest.from_file(ROOT / "views" / "controls.py")
    app.session_state["use_case"] = make_case()["use_case"]
    app.session_state["risk_answers"] = make_case()["risk_answers"]
    app.session_state["control_evidence"] = {
        "FAI-01": {**original, "fairness_evaluation": evaluation}
    }
    app.run()

    input_by_key(app, "fai01_fairness_risk").set_value("Updated synthetic risk")
    click_form_button(app, "Save FAI-01 assessment")
    saved = app.session_state["control_evidence"]["FAI-01"]
    assert saved["fairness_risk"] == "Updated synthetic risk"
    assert saved["fairness_evaluation"] == evaluation

    input_by_key(app, FAI01_EVALUATION_WIDGET_KEYS["metric_name"]).set_value("Updated synthetic metric")
    input_by_key(
        app,
        fairness_row_widget_key("threshold", 0, "value"),
    ).set_value(0.85)
    click_form_button(app, "Save FAI-01 fairness evaluation")
    saved = app.session_state["control_evidence"]["FAI-01"]
    assert saved["fairness_evaluation"]["metric_name"] == "Updated synthetic metric"
    assert saved["fairness_evaluation"]["thresholds"][0]["value"] == 0.85
    assert saved["fairness_risk"] == "Updated synthetic risk"


def test_evaluation_form_requires_explicit_save_and_rejects_invalid_performed():
    app = AppTest.from_file(ROOT / "views" / "controls.py")
    app.session_state["use_case"] = make_case()["use_case"]
    app.session_state["risk_answers"] = make_case()["risk_answers"]
    app.run()
    assert "FAI-01" not in app.session_state.get("control_evidence", {})

    stage_key = FAI01_EVALUATION_WIDGET_KEYS["evaluation_stage"]
    input_by_key(app, stage_key).select("Performed")
    click_form_button(app, "Save FAI-01 fairness evaluation")
    assert "FAI-01" not in app.session_state.get("control_evidence", {})
    assert any("Fairness evaluation was not saved" in error.value for error in app.error)


def test_app_test_saves_structured_performed_result_only_on_submit():
    app = AppTest.from_file(ROOT / "views" / "controls.py")
    app.session_state["use_case"] = make_case()["use_case"]
    app.session_state["risk_answers"] = make_case()["risk_answers"]
    app.run()
    result = performed_evaluation()
    click_form_button(app, "Add threshold")
    click_form_button(app, "Add subgroup result")
    click_form_button(app, "Add subgroup result")
    for field in FAIRNESS_EVALUATION_FIELDS:
        if field in {"thresholds", "subgroup_results"}:
            continue
        if field == "evaluation_stage":
            value = "Performed"
        elif field == "evaluation_status":
            value = "Reviewed"
        else:
            value = result[field]
        input_by_key(app, FAI01_EVALUATION_WIDGET_KEYS[field]).set_value(value)
    threshold = result["thresholds"][0]
    for field, value in threshold.items():
        if field == "kind":
            continue
        input_by_key(
            app,
            fairness_row_widget_key("threshold", 0, field),
        ).set_value(value)
    for index, subgroup in enumerate(result["subgroup_results"]):
        for field, value in subgroup.items():
            if field in {"sample_size", "event_numerator"}:
                value = str(value)
            input_by_key(
                app,
                fairness_row_widget_key("subgroup_result", index, field),
            ).set_value(value)
    assert "FAI-01" not in app.session_state.get("control_evidence", {})
    click_form_button(app, "Save FAI-01 fairness evaluation")
    saved = app.session_state["control_evidence"]["FAI-01"]["fairness_evaluation"]
    assert saved == result
    assert not any("Fairness evaluation was not saved" in item.value for item in app.error)


def test_app_test_can_add_remove_structured_rows_and_repeats_interactions():
    app = AppTest.from_file(ROOT / "views" / "controls.py")
    app.session_state["use_case"] = make_case()["use_case"]
    app.session_state["risk_answers"] = make_case()["risk_answers"]
    app.run()

    click_form_button(app, "Add subgroup result")
    first_label_key = fairness_row_widget_key(
        "subgroup_result", 0, "subgroup_label"
    )
    input_by_key(app, first_label_key).set_value("Synthetic group A")
    app.run()
    click_form_button(app, "Add subgroup result")
    second_label_key = fairness_row_widget_key(
        "subgroup_result", 1, "subgroup_label"
    )
    input_by_key(app, second_label_key).set_value("Synthetic group B")
    app.run()
    click_form_button(app, "Remove subgroup result 1")

    assert app.session_state[
        FAI01_EVALUATION_WIDGET_KEYS["subgroup_result_row_count"]
    ] == 1
    assert input_by_key(app, first_label_key).value == "Synthetic group B"
    click_form_button(app, "Add threshold")
    assert app.session_state[
        FAI01_EVALUATION_WIDGET_KEYS["threshold_row_count"]
    ] == 1
    click_form_button(app, "Remove threshold 1")
    assert app.session_state[
        FAI01_EVALUATION_WIDGET_KEYS["threshold_row_count"]
    ] == 0


def test_app_test_saves_qualitative_threshold_with_explicit_human_review():
    app = AppTest.from_file(ROOT / "views" / "controls.py")
    app.session_state["use_case"] = make_case()["use_case"]
    app.session_state["risk_answers"] = make_case()["risk_answers"]
    app.run()
    click_form_button(app, "Add threshold")

    input_by_key(
        app,
        fairness_row_widget_key("threshold", 0, "kind"),
    ).select("documented").run()
    input_by_key(
        app,
        fairness_row_widget_key("threshold", 0, "description"),
    ).set_value("Synthetic qualitative criterion")
    input_by_key(
        app,
        fairness_row_widget_key("threshold", 0, "rationale"),
    ).set_value("The criterion requires human judgment.")
    input_by_key(
        app,
        fairness_row_widget_key("threshold", 0, "human_review_required"),
    ).check()
    click_form_button(app, "Save FAI-01 fairness evaluation")

    threshold = app.session_state["control_evidence"]["FAI-01"][
        "fairness_evaluation"
    ]["thresholds"][0]
    assert threshold == {
        "kind": "documented",
        "description": "Synthetic qualitative criterion",
        "rationale": "The criterion requires human judgment.",
        "human_review_required": True,
    }


def test_invalid_submission_does_not_replace_previously_saved_evaluation():
    saved = performed_evaluation()
    app = AppTest.from_file(ROOT / "views" / "controls.py")
    app.session_state["use_case"] = make_case()["use_case"]
    app.session_state["risk_answers"] = make_case()["risk_answers"]
    app.session_state["control_evidence"] = {
        "FAI-01": {
            **base_fai01(),
            "fairness_evaluation": saved,
        }
    }
    app.run()
    input_by_key(
        app,
        fairness_row_widget_key("subgroup_result", 1, "metric_unit"),
    ).set_value("milliseconds")
    input_by_key(
        app,
        fairness_row_widget_key("subgroup_result", 1, "metric_scale"),
    ).select("unbounded")
    click_form_button(app, "Save FAI-01 fairness evaluation")

    assert (
        app.session_state["control_evidence"]["FAI-01"]["fairness_evaluation"]
        == saved
    )
    assert any("same metric unit and scale" in error.value for error in app.error)


def test_null_and_malformed_nested_data_survive_base_fai01_save():
    for nested in (None, "legacy free text"):
        app = AppTest.from_file(ROOT / "views" / "controls.py")
        app.session_state["use_case"] = make_case()["use_case"]
        app.session_state["risk_answers"] = make_case()["risk_answers"]
        app.session_state["control_evidence"] = {
            "FAI-01": {**base_fai01(), "fairness_evaluation": nested}
        }
        app.run()
        input_by_key(app, "fai01_fairness_risk").set_value("Updated base field")
        click_form_button(app, "Save FAI-01 assessment")
        assert (
            app.session_state["control_evidence"]["FAI-01"]["fairness_evaluation"]
            == nested
        )


def test_malformed_saved_rows_are_invalid_without_crashing_controls_page():
    malformed = performed_evaluation(
        thresholds=[{"kind": []}],
        subgroup_results=["legacy free-text result"],
        threshold_row_count=1000,
    )
    app = AppTest.from_file(ROOT / "views" / "controls.py")
    app.session_state["use_case"] = make_case()["use_case"]
    app.session_state["risk_answers"] = make_case()["risk_answers"]
    app.session_state["control_evidence"] = {
        "FAI-01": {
            **base_fai01(),
            "fairness_evaluation": malformed,
        }
    }
    app.run()

    assert not app.exception
    assert any("Saved fairness evaluation is Invalid" in item.value for item in app.warning)
    assert app.session_state[
        FAI01_EVALUATION_WIDGET_KEYS["threshold_row_count"]
    ] == 1
    assert (
        app.session_state["control_evidence"]["FAI-01"]["fairness_evaluation"]
        == malformed
    )


def test_unsaved_evaluation_edit_does_not_change_canonical_record():
    saved = planned_evaluation(metric_name="Saved value")
    app = AppTest.from_file(ROOT / "views" / "controls.py")
    app.session_state["use_case"] = make_case()["use_case"]
    app.session_state["risk_answers"] = make_case()["risk_answers"]
    app.session_state["control_evidence"] = {
        "FAI-01": {**base_fai01(), "fairness_evaluation": saved}
    }
    app.run()

    input_by_key(
        app,
        FAI01_EVALUATION_WIDGET_KEYS["metric_name"],
    ).set_value("Unsaved change").run()
    assert (
        app.session_state["control_evidence"]["FAI-01"]["fairness_evaluation"]
        == saved
    )


def test_case_switch_rehydrates_evaluation_widgets_without_cross_case_data(tmp_path):
    first = make_case(evidence={
        "FAI-01": {
            **base_fai01(),
            "fairness_evaluation": performed_evaluation(metric_name="Case One metric"),
        }
    })
    second = make_case("Second synthetic case", evidence={
        "FAI-01": {
            **base_fai01(),
            "fairness_evaluation": performed_evaluation(metric_name="Case Two metric"),
        }
    })
    first_document = save_case(first, tmp_path)
    second_document = save_case(second, tmp_path)
    app = AppTest.from_file(ROOT / "views" / "controls.py")
    restore_case(app.session_state, first_document)
    app.run()
    first_generation = app.session_state["_case_load_generation"]
    first_key = f"{FAI01_EVALUATION_WIDGET_KEYS['metric_name']}_{first_generation}"
    assert input_by_key(app, first_key).value == "Case One metric"
    first_row_key = fairness_row_widget_key(
        "subgroup_result", 0, "subgroup_label", first_generation
    )
    assert input_by_key(app, first_row_key).value == "Synthetic group A"

    restore_case(app.session_state, second_document)
    app.run()
    second_generation = app.session_state["_case_load_generation"]
    second_key = f"{FAI01_EVALUATION_WIDGET_KEYS['metric_name']}_{second_generation}"
    assert second_generation != first_generation
    assert input_by_key(app, second_key).value == "Case Two metric"
    second_row_key = fairness_row_widget_key(
        "subgroup_result", 0, "subgroup_label", second_generation
    )
    assert input_by_key(app, second_row_key).value == "Synthetic group A"


def test_optional_evaluation_does_not_change_fai01_status_or_readiness():
    state = make_case(evidence={"FAI-01": base_fai01(assessment_status="Reviewed")})
    with_evaluation = deepcopy(state)
    with_evaluation["control_evidence"]["FAI-01"]["fairness_evaluation"] = (
        performed_evaluation()
    )
    control_ids = (
        "GOV-01", "MAP-01", "DAT-01", "FAI-01", "SEC-01", "TRN-01",
        "VAL-01", "MON-01", "INC-01", "HUM-01", "RET-01",
    )

    def snapshot(case):
        risk = calculate_risk(case["risk_answers"])
        controls = {
            control_id: assess_control(
                control_id,
                case["use_case"],
                case["risk_answers"],
                case["control_evidence"],
            )
            for control_id in control_ids
        }
        readiness = evaluate_readiness(
            controls,
            case["deployment_readiness_plans"],
            True,
        )
        return risk, controls, readiness

    assert snapshot(state) == snapshot(with_evaluation)


def test_alignment_distinguishes_planned_performed_and_invalid_evaluation_records():
    app = AppTest.from_file(ROOT / "views" / "sdaia_alignment.py")
    app.run()
    assert any(
        "Missing — no saved supplementary fairness evaluation" in item.value
        for item in app.caption
    )
    app.session_state["control_evidence"] = {
        "FAI-01": {
            "fairness_evaluation": planned_evaluation(
                metric_name="Synthetic planned metric",
            )
        }
    }
    app.run()
    assert any("Saved evaluation design: Planned" in item.value for item in app.caption)

    app.session_state["control_evidence"]["FAI-01"]["fairness_evaluation"] = (
        performed_evaluation()
    )
    app.run()
    assert any(
        "user-reported and not independently verified" in item.value
        for item in app.caption
    )

    app.session_state["control_evidence"]["FAI-01"]["fairness_evaluation"] = {
        "evaluation_stage": "Performed",
        "evaluation_status": "Reviewed",
    }
    app.run()
    assert any("Invalid — supplementary fairness evaluation" in item.value for item in app.caption)
    app.session_state["control_evidence"]["FAI-01"]["fairness_evaluation"] = None
    app.run()
    assert any("Invalid — supplementary fairness evaluation" in item.value for item in app.caption)
