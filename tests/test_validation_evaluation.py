from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.governance.case_persistence import (
    DEFAULT_PLANS,
    RISK_ANSWER_KEYS,
    USE_CASE_KEYS,
    VAL01_EVALUATION_WIDGET_KEYS,
    load_case,
    restore_case,
    save_case,
)
from src.governance.control_assessment import assess_control
from src.governance.deployment_readiness import evaluate_readiness
from src.governance.risk import calculate_risk
from src.governance.validation_evaluation import (
    HUMAN_REVIEW_COMPARATOR,
    VALIDATION_EVALUATION_FIELDS,
    metric_comparison_status,
    validation_row_widget_key,
    validate_validation_evaluation,
)


ROOT = Path(__file__).resolve().parents[1]


def make_case(name="Synthetic validation case", evidence=None):
    use_case = {field: f"Synthetic {field}" for field in USE_CASE_KEYS}
    use_case.update({
        "name": name,
        "owner": "Synthetic Service Owner",
        "purpose": "Prioritise synthetic service requests for human review.",
        "decision": "Synthetic priority recommendation",
        "ai_role": "Recommendation only",
        "human_oversight": "Required before action",
    })
    return {
        "use_case": use_case,
        "risk_answers": {key: key == "significant_decision" for key in RISK_ANSWER_KEYS},
        "control_evidence": deepcopy(evidence or {}),
        "deployment_readiness_plans": deepcopy(DEFAULT_PLANS),
    }


def base_val01(**overrides):
    record = {
        "validation_scope": "Synthetic prioritisation recommendations",
        "acceptance_criteria": "Service owners define criteria before testing.",
        "validation_approach": "Synthetic validation plan",
        "data_test_set_considerations": "Synthetic aggregate test-set considerations",
        "human_oversight_validation": "Review recommendation before action",
        "validation_findings_evidence": "No real test results are claimed.",
        "validation_limitations_actions": "Real validation remains outstanding.",
        "responsible_owner": "Synthetic Service Owner",
        "validation_reviewer": "Synthetic Validation Reviewer",
        "assessment_status": "Reviewed",
    }
    record.update(overrides)
    return record


def planned_evaluation(**overrides):
    record = {
        field: [] if field in {"metrics", "results"} else ""
        for field in VALIDATION_EVALUATION_FIELDS
    }
    record.update({
        "evaluation_stage": "Planned",
        "evaluation_status": "Draft",
    })
    record.update(overrides)
    return record


def performed_evaluation(**overrides):
    record = {
        "evaluation_stage": "Performed",
        "evaluation_status": "Reviewed",
        "dataset_source": "Synthetic generated test dataset",
        "dataset_purpose": "Exercise the simulated prioritisation workflow.",
        "dataset_population": "Aggregate synthetic service requests",
        "dataset_scope": "Synthetic service categories A and B",
        "dataset_timeframe": "Synthetic test period",
        "dataset_limitations": "No real citizen data; not representative.",
        "validation_method": "Synthetic scenario-based test",
        "test_objectives": "Check synthetic recommendation behavior against intended use.",
        "human_oversight_testing": "Simulated staff review before action.",
        "human_oversight_observations": "Synthetic review observations only.",
        "validation_outcome": "Synthetic example; no actual model result.",
        "limitations": "No deployed model or real validation data.",
        "outstanding_actions": "Independent validation remains outstanding.",
        "responsible_owner": "Synthetic Service Owner",
        "reviewer": "Synthetic Validation Reviewer",
        "review_date": "2026-10-19",
        "metrics": [{
            "metric_id": "coverage",
            "metric_name": "Synthetic coverage metric",
            "definition": "Synthetic numerator divided by denominator.",
            "unit": "percent",
            "scale": "percentage_0_100",
            "threshold_comparator": ">=",
            "threshold_value": 80.0,
            "threshold_rationale": "Synthetic criterion chosen for demonstration.",
        }, {
            "metric_id": "latency",
            "metric_name": "Synthetic latency metric",
            "definition": "Synthetic elapsed time per test scenario.",
            "unit": "milliseconds",
            "scale": "unbounded",
            "threshold_comparator": "<=",
            "threshold_value": 500.0,
            "threshold_rationale": "Synthetic criterion chosen for demonstration.",
        }],
        "results": [{
            "metric_id": "coverage",
            "measured_value": 88.0,
            "unit": "percent",
            "scale": "percentage_0_100",
            "sample_size": 50,
            "test_date": "2026-10-18",
            "evidence_reference": "Synthetic aggregate report section A",
        }, {
            "metric_id": "latency",
            "measured_value": 240.0,
            "unit": "milliseconds",
            "scale": "unbounded",
            "sample_size": 50,
            "test_date": "2026-10-18",
            "evidence_reference": "Synthetic aggregate report section B",
        }],
    }
    record.update(overrides)
    return record


def widget(app, key):
    for widget_type in ("text_input", "text_area", "selectbox", "number_input"):
        for item in getattr(app, widget_type):
            if item.key == key:
                return item
    raise AssertionError(f"Widget not found: {key}")


def click(app, label):
    next(item for item in app.button if item.label == label).click().run()


def control_app(evidence=None):
    app = AppTest.from_file(ROOT / "views" / "controls.py")
    case = make_case()
    app.session_state["use_case"] = case["use_case"]
    app.session_state["risk_answers"] = case["risk_answers"]
    app.session_state["control_evidence"] = deepcopy(evidence or {})
    app.run()
    return app


def test_planned_record_has_no_performed_results_and_invalid_combinations_fail():
    record = planned_evaluation()
    assert validate_validation_evaluation(record) == []
    assert validate_validation_evaluation({
        **record,
        "results": performed_evaluation()["results"],
    })
    assert validate_validation_evaluation({
        **record,
        "validation_outcome": "Claimed completed test",
    })


def test_performed_records_require_results_for_each_metric_and_valid_context():
    assert validate_validation_evaluation(performed_evaluation()) == []
    invalid = performed_evaluation(
        dataset_population="",
        results=performed_evaluation()["results"][:1],
    )
    errors = validate_validation_evaluation(invalid)
    assert any("Dataset population is required" in error for error in errors)
    assert any("missing a result for metric 'latency'" in error for error in errors)


def test_invalid_metric_values_units_scales_dates_and_evidence_are_rejected():
    invalid_records = (
        performed_evaluation(metrics=[{
            **performed_evaluation()["metrics"][0],
            "threshold_value": float("inf"),
        }]),
        performed_evaluation(results=[{
            **performed_evaluation()["results"][0],
            "measured_value": float("nan"),
        }, performed_evaluation()["results"][1]]),
        performed_evaluation(results=[{
            **performed_evaluation()["results"][0],
            "unit": "proportion",
        }, performed_evaluation()["results"][1]]),
        performed_evaluation(results=[{
            **performed_evaluation()["results"][0],
            "scale": "proportion_0_1",
        }, performed_evaluation()["results"][1]]),
        performed_evaluation(results=[{
            **performed_evaluation()["results"][0],
            "test_date": "not-a-date",
        }, performed_evaluation()["results"][1]]),
        performed_evaluation(results=[{
            **performed_evaluation()["results"][0],
            "evidence_reference": "N/A",
        }, performed_evaluation()["results"][1]]),
        performed_evaluation(results=[{
            **performed_evaluation()["results"][0],
            "sample_size": 0,
        }, performed_evaluation()["results"][1]]),
    )
    for record in invalid_records:
        assert validate_validation_evaluation(record)


def test_each_metric_has_its_own_explicit_unit_scale_and_results():
    record = performed_evaluation()
    assert record["metrics"][0]["unit"] != record["metrics"][1]["unit"]
    assert record["results"][0]["metric_id"] == "coverage"
    assert record["results"][1]["metric_id"] == "latency"
    assert validate_validation_evaluation(record) == []

    mismatched = deepcopy(record)
    mismatched["results"][1]["unit"] = "percent"
    assert any(
        "unit must match its identified metric" in error
        for error in validate_validation_evaluation(mismatched)
    )


def test_duplicate_metric_ids_and_unknown_result_ids_are_invalid():
    record = performed_evaluation()
    duplicate = deepcopy(record)
    duplicate["metrics"][1]["metric_id"] = duplicate["metrics"][0]["metric_id"]
    assert any("must be unique" in error for error in validate_validation_evaluation(duplicate))

    unknown = deepcopy(record)
    unknown["results"][0]["metric_id"] = "undefined"
    assert any("unknown metric ID" in error for error in validate_validation_evaluation(unknown))


def test_metric_comparison_status_uses_only_declared_numeric_comparator():
    metric = performed_evaluation()["metrics"][0]
    result = performed_evaluation()["results"][0]
    assert metric_comparison_status(metric, {**result, "measured_value": 40.0}) == "Threshold not met"
    assert metric_comparison_status(metric, {**result, "measured_value": 80.0}) == "Threshold met"

    boundary_cases = (
        ("<", 80, 79.99, "Threshold met"),
        ("<", 80, 80, "Threshold not met"),
        ("<=", 80, 80, "Threshold met"),
        (">", 80, 80.01, "Threshold met"),
        (">=", 80, 80, "Threshold met"),
        ("==", 80, 80, "Threshold met"),
        ("==", 80, 79, "Threshold not met"),
    )
    for comparator, threshold, value, expected in boundary_cases:
        current_metric = {**metric, "threshold_comparator": comparator, "threshold_value": threshold}
        assert metric_comparison_status(
            current_metric,
            {**result, "measured_value": value},
        ) == expected

    assert metric_comparison_status(
        metric,
        {**result, "unit": "proportion"},
    ) == "Not evaluated"
    assert metric_comparison_status(
        {**metric, "threshold_comparator": HUMAN_REVIEW_COMPARATOR, "threshold_value": None},
        result,
    ) == "Requires human review"


def test_human_review_threshold_and_neutral_outcome_are_required_for_unassessable_metric():
    record = performed_evaluation()
    record["metrics"][0]["threshold_comparator"] = HUMAN_REVIEW_COMPARATOR
    record["metrics"][0]["threshold_value"] = None
    assert validate_validation_evaluation(record) == []

    invalid = deepcopy(record)
    invalid["metrics"][0]["threshold_value"] = 80
    assert any(
        "must not include a numeric threshold" in error
        for error in validate_validation_evaluation(invalid)
    )

    contradictory = performed_evaluation(validation_outcome="Passed")
    assert any(
        "overall Passed/Failed claims" in error
        for error in validate_validation_evaluation(contradictory)
    )


def test_app_displays_threshold_not_met_instead_of_global_pass_claim():
    app = control_app()
    click(app, "Add validation metric")
    metric_fields = {
        "metric_id": "coverage",
        "metric_name": "Synthetic coverage",
        "definition": "Synthetic percentage coverage.",
        "unit": "percent",
        "scale": "percentage_0_100",
        "threshold_comparator": ">=",
        "threshold_value": 80.0,
        "threshold_rationale": "Synthetic demonstration threshold.",
    }
    for field, value in metric_fields.items():
        item = widget(app, validation_row_widget_key("metric", 0, field))
        if field in {"scale", "threshold_comparator"}:
            item.select(value)
        else:
            item.set_value(value)
    app.run()

    click(app, "Add validation result")
    result_fields = {
        "metric_id": "coverage",
        "measured_value": 40.0,
        "unit": "percent",
        "scale": "percentage_0_100",
    }
    for field, value in result_fields.items():
        item = widget(app, validation_row_widget_key("result", 0, field))
        if field in {"metric_id", "scale"}:
            item.select(value)
        else:
            item.set_value(value)
    app.run()
    assert any(
        "Metric comparison: **Threshold not met**" in item.value
        for item in app.caption
    )
    assert any(
        "no overall pass/fail claim" in item.label.lower()
        for item in app.text_area
    )


def test_malformed_nested_record_is_invalid_and_does_not_crash_controls():
    for malformed in (
        "legacy free-text validation result",
        None,
        {**planned_evaluation(), "metrics": [{"metric_id": []}]},
        {
            **performed_evaluation(),
            "results": [{
                **performed_evaluation()["results"][0],
                "metric_id": "unknown-metric",
            }],
        },
        performed_evaluation(validation_outcome="Passed"),
    ):
        app = control_app({"VAL-01": {
            **base_val01(),
            "validation_evaluation": malformed,
        }})
        assert not app.exception
        assert any("Saved validation evaluation is Invalid" in item.value for item in app.warning)
        assert app.session_state["control_evidence"]["VAL-01"]["validation_evaluation"] == malformed
        widget(app, "val01_validation_scope").set_value("Updated synthetic base assessment")
        click(app, "Save VAL-01 assessment")
        assert app.session_state["control_evidence"]["VAL-01"]["validation_evaluation"] == malformed


def test_explicit_save_and_base_nested_field_preservation():
    app = control_app()
    assert "VAL-01" not in app.session_state.get("control_evidence", {})
    click(app, "Save VAL-01 validation evaluation")
    saved = app.session_state["control_evidence"]["VAL-01"]["validation_evaluation"]
    assert saved["evaluation_stage"] == "Planned"
    assert saved["results"] == []

    app.session_state["control_evidence"]["VAL-01"]["validation_evaluation"] = None
    widget(app, "val01_validation_scope").set_value("Updated synthetic base scope")
    click(app, "Save VAL-01 assessment")
    assert app.session_state["control_evidence"]["VAL-01"]["validation_evaluation"] is None


def test_valid_evaluation_save_preserves_base_and_invalid_resave_preserves_saved():
    saved = performed_evaluation()
    app = control_app({"VAL-01": {
        **base_val01(),
        "validation_evaluation": saved,
    }})
    widget(app, "val01_validation_scope").set_value("Updated base scope")
    click(app, "Save VAL-01 assessment")
    assert app.session_state["control_evidence"]["VAL-01"]["validation_evaluation"] == saved

    widget(app, VAL01_EVALUATION_WIDGET_KEYS["dataset_source"]).set_value("")
    click(app, "Save VAL-01 validation evaluation")
    assert app.session_state["control_evidence"]["VAL-01"]["validation_evaluation"] == saved
    assert any("Validation evaluation was not saved" in item.value for item in app.error)
    assert app.session_state["control_evidence"]["VAL-01"]["validation_scope"] == "Updated base scope"


def test_validation_ui_add_remove_metric_and_result_rows():
    app = control_app()
    click(app, "Add validation metric")
    click(app, "Add validation metric")
    widget(app, validation_row_widget_key("metric", 0, "metric_id")).set_value("first")
    app.run()
    widget(app, validation_row_widget_key("metric", 1, "metric_id")).set_value("second")
    app.run()
    click(app, "Remove validation metric 1")
    assert app.session_state[VAL01_EVALUATION_WIDGET_KEYS["metric_row_count"]] == 1
    assert widget(app, validation_row_widget_key("metric", 0, "metric_id")).value == "second"

    click(app, "Add validation result")
    click(app, "Add validation result")
    widget(app, validation_row_widget_key("result", 0, "evidence_reference")).set_value("Synthetic result A")
    app.run()
    widget(app, validation_row_widget_key("result", 1, "evidence_reference")).set_value("Synthetic result B")
    app.run()
    click(app, "Remove validation result 1")
    assert app.session_state[VAL01_EVALUATION_WIDGET_KEYS["result_row_count"]] == 1
    assert widget(app, validation_row_widget_key("result", 0, "evidence_reference")).value == "Synthetic result B"


def test_metric_with_linked_result_cannot_be_removed_or_reassign_its_result():
    app = control_app()
    click(app, "Add validation metric")
    click(app, "Add validation metric")
    first_id = validation_row_widget_key("metric", 0, "metric_id")
    second_id = validation_row_widget_key("metric", 1, "metric_id")
    widget(app, first_id).set_value("first").run()
    widget(app, second_id).set_value("second").run()
    click(app, "Add validation result")
    result_id = validation_row_widget_key("result", 0, "metric_id")
    widget(app, result_id).select("first").run()
    value_key = validation_row_widget_key("result", 0, "measured_value")
    evidence_key = validation_row_widget_key("result", 0, "evidence_reference")
    widget(app, value_key).set_value(37.0).run()
    widget(app, evidence_key).set_value("Synthetic first metric evidence").run()

    remove_first = next(item for item in app.button if item.label == "Remove validation metric 1")
    assert remove_first.disabled
    assert any("Remove linked result rows first" in item.value for item in app.caption)
    assert widget(app, result_id).value == "first"
    assert widget(app, value_key).value == 37.0
    assert widget(app, evidence_key).value == "Synthetic first metric evidence"
    assert widget(app, second_id).value == "second"

    click(app, "Remove validation result 1")
    app.run()
    click(app, "Remove validation metric 1")
    assert app.session_state[VAL01_EVALUATION_WIDGET_KEYS["metric_row_count"]] == 1
    assert widget(app, validation_row_widget_key("metric", 0, "metric_id")).value == "second"
    assert app.session_state[VAL01_EVALUATION_WIDGET_KEYS["result_row_count"]] == 0


def test_removing_unrelated_metric_preserves_result_metric_identity_and_values():
    app = control_app()
    click(app, "Add validation metric")
    click(app, "Add validation metric")
    widget(app, validation_row_widget_key("metric", 0, "metric_id")).set_value("first").run()
    widget(app, validation_row_widget_key("metric", 1, "metric_id")).set_value("second").run()
    click(app, "Add validation result")
    result_id = validation_row_widget_key("result", 0, "metric_id")
    widget(app, result_id).select("second").run()
    value_key = validation_row_widget_key("result", 0, "measured_value")
    evidence_key = validation_row_widget_key("result", 0, "evidence_reference")
    widget(app, value_key).set_value(22.0).run()
    widget(app, evidence_key).set_value("Synthetic second metric evidence").run()

    click(app, "Remove validation metric 1")
    assert widget(app, validation_row_widget_key("metric", 0, "metric_id")).value == "second"
    assert widget(app, result_id).value == "second"
    assert widget(app, value_key).value == 22.0
    assert widget(app, evidence_key).value == "Synthetic second metric evidence"


def test_repeated_dynamic_metric_result_edits_and_reruns_remain_stable():
    app = control_app()
    for iteration in range(3):
        click(app, "Add validation metric")
        metric_index = app.session_state[VAL01_EVALUATION_WIDGET_KEYS["metric_row_count"]] - 1
        widget(app, validation_row_widget_key("metric", metric_index, "metric_id")).set_value(
            f"metric-{iteration}"
        ).run()
        click(app, "Add validation result")
        result_index = app.session_state[VAL01_EVALUATION_WIDGET_KEYS["result_row_count"]] - 1
        result_id = validation_row_widget_key("result", result_index, "metric_id")
        widget(app, result_id).select(f"metric-{iteration}").run()
        app.run()
        assert widget(app, result_id).value == f"metric-{iteration}"

    assert not app.exception


def test_app_test_saves_structured_performed_validation_without_json():
    record = performed_evaluation()
    app = control_app()
    for field, value in record.items():
        if field in {"metrics", "results"}:
            continue
        key = VAL01_EVALUATION_WIDGET_KEYS[field]
        item = widget(app, key)
        if field == "evaluation_stage":
            item.select(value)
        elif field == "evaluation_status":
            item.select(value)
        else:
            item.set_value(value)

    click(app, "Add validation metric")
    click(app, "Add validation metric")
    click(app, "Add validation result")
    click(app, "Add validation result")
    for index, metric in enumerate(record["metrics"]):
        for field, value in metric.items():
            key = validation_row_widget_key("metric", index, field)
            item = widget(app, key)
            if field in {"scale", "threshold_comparator"}:
                item.select(value)
            else:
                item.set_value(value)
    app.run()
    for index, result in enumerate(record["results"]):
        for field, value in result.items():
            if field == "sample_size":
                value = str(value)
            key = validation_row_widget_key("result", index, field)
            item = widget(app, key)
            if field == "metric_id":
                item.select(value)
            elif field == "scale":
                item.select(value)
            else:
                item.set_value(value)

    assert "VAL-01" not in app.session_state.get("control_evidence", {})
    click(app, "Save VAL-01 validation evaluation")
    saved = app.session_state["control_evidence"]["VAL-01"]["validation_evaluation"]
    assert saved == record
    assert not any("Validation evaluation was not saved" in item.value for item in app.error)


def test_unsaved_nested_edits_do_not_mutate_canonical_record():
    saved = planned_evaluation(dataset_source="Saved synthetic dataset")
    app = control_app({"VAL-01": {
        **base_val01(),
        "validation_evaluation": saved,
    }})
    widget(app, VAL01_EVALUATION_WIDGET_KEYS["dataset_source"]).set_value("Unsaved edit").run()
    assert app.session_state["control_evidence"]["VAL-01"]["validation_evaluation"] == saved


def test_schema_v1_persistence_and_case_switch_restore_optional_nested_evaluation(tmp_path):
    first = make_case(evidence={"VAL-01": {
        **base_val01(),
        "validation_evaluation": performed_evaluation(),
    }})
    second = make_case("Second synthetic case", evidence={"VAL-01": {
        **base_val01(),
        "validation_evaluation": planned_evaluation(dataset_source="Second synthetic source"),
    }})
    first_doc = save_case(first, tmp_path)
    second_doc = save_case(second, tmp_path)
    loaded = load_case(first_doc["case_id"], tmp_path)
    assert loaded["schema_version"] == 1
    assert loaded["control_evidence"]["VAL-01"]["validation_evaluation"] == performed_evaluation()

    app = AppTest.from_file(ROOT / "views" / "controls.py")
    restore_case(app.session_state, loaded)
    app.run()
    first_gen = app.session_state["_case_load_generation"]
    first_key = validation_row_widget_key("metric", 0, "metric_id", first_gen)
    assert widget(app, first_key).value == "coverage"

    restore_case(app.session_state, second_doc)
    app.run()
    second_gen = app.session_state["_case_load_generation"]
    second_key = VAL01_EVALUATION_WIDGET_KEYS["dataset_source"] + "_" + second_gen
    assert widget(app, second_key).value == "Second synthetic source"
    assert app.session_state[VAL01_EVALUATION_WIDGET_KEYS["result_row_count"] + "_" + second_gen] == 0

    legacy = make_case(evidence={"VAL-01": base_val01()})
    legacy_doc = save_case(legacy, tmp_path)
    legacy_loaded = load_case(legacy_doc["case_id"], tmp_path)
    assert "validation_evaluation" not in legacy_loaded["control_evidence"]["VAL-01"]


def test_alignment_displays_missing_planned_performed_and_invalid_validation_docs():
    app = AppTest.from_file(ROOT / "views" / "sdaia_alignment.py")
    app.run()
    assert any("Missing — no saved supplementary validation evaluation" in item.value for item in app.caption)

    app.session_state["control_evidence"] = {"VAL-01": {
        "validation_evaluation": planned_evaluation(),
    }}
    app.run()
    assert any("Planned" in item.value and "No measured validation results" in item.value for item in app.caption)

    app.session_state["control_evidence"]["VAL-01"]["validation_evaluation"] = performed_evaluation()
    app.run()
    assert any("Performed" in item.value and "user-reported" in item.value for item in app.caption)

    app.session_state["control_evidence"]["VAL-01"]["validation_evaluation"] = None
    app.run()
    assert any("Invalid — supplementary validation evaluation" in item.value for item in app.caption)


def test_optional_evaluation_does_not_change_risk_val01_status_or_readiness():
    case = make_case(evidence={"VAL-01": base_val01()})
    extended = deepcopy(case)
    extended["control_evidence"]["VAL-01"]["validation_evaluation"] = performed_evaluation()
    control_ids = (
        "GOV-01", "MAP-01", "DAT-01", "FAI-01", "SEC-01", "TRN-01",
        "VAL-01", "MON-01", "INC-01", "HUM-01", "RET-01",
    )

    def snapshot(state):
        risk = calculate_risk(state["risk_answers"])
        controls = {
            control_id: assess_control(
                control_id,
                state["use_case"],
                state["risk_answers"],
                state["control_evidence"],
            )
            for control_id in control_ids
        }
        readiness = evaluate_readiness(
            controls,
            state["deployment_readiness_plans"],
            True,
        )
        return risk, controls, readiness

    assert snapshot(case) == snapshot(extended)
