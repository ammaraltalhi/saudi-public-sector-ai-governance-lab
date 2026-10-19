from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.governance.case_persistence import (
    DEFAULT_PLANS,
    RISK_ANSWER_KEYS,
    TRN01_EXPLAINABILITY_WIDGET_KEYS,
    TRN01_WIDGET_KEYS,
    USE_CASE_KEYS,
    load_case,
    restore_case,
    save_case,
)
from src.governance.control_assessment import assess_control
from src.governance.deployment_readiness import evaluate_readiness
from src.governance.explainability_evidence import (
    EXPLAINABILITY_EVIDENCE_FIELDS,
    explainability_row_widget_key,
    validate_explainability_evidence,
)
from src.governance.risk import calculate_risk


ROOT = Path(__file__).resolve().parents[1]


def base_trn01(**overrides):
    record = {
        "ai_system_purpose": "Prioritise synthetic service requests for review.",
        "ai_decision_role": "Synthetic recommendation for staff review.",
        "intended_users_stakeholders": "Synthetic service staff and requesters.",
        "key_system_limitations": "Illustrative synthetic scenario only.",
        "human_oversight_approach": "Staff review before any action.",
        "information_to_communicate": "Purpose, role, and limitations.",
        "communication_disclosure_approach": "Plan synthetic communication review.",
        "transparency_limitations_actions": "No actual system or disclosure is claimed.",
        "responsible_owner": "Synthetic Service Owner",
        "transparency_reviewer": "Synthetic Governance Reviewer",
        "assessment_status": "Reviewed",
    }
    record.update(overrides)
    return record


def planned_record(**overrides):
    record = {
        field: [] if field in {"examples", "accessibility_usefulness_reviews"} else ""
        for field in EXPLAINABILITY_EVIDENCE_FIELDS
    }
    record.update({
        "evaluation_stage": "Planned",
        "evaluation_status": "Draft",
        "explanation_method": "Rule-based feature summary",
        "method_description": "Plan to describe selected synthetic factors.",
        "intended_audiences": "Synthetic service staff and requesters.",
        "planned_context": "Synthetic request-prioritisation examples.",
        "planned_feedback_collection": "Plan a moderated synthetic review.",
        "human_review_approach": "Plan review with a synthetic service reviewer.",
        "challenge_correction_process": "Plan a simulated correction pathway.",
        "limitations": "No generated explanation or deployed system.",
        "outstanding_actions": "Run synthetic review before making claims.",
        "responsible_owner": "Synthetic Service Owner",
        "reviewer": "Synthetic Governance Reviewer",
        "review_date": "",
    })
    record.update(overrides)
    return record


def performed_record(**overrides):
    record = planned_record(
        evaluation_stage="Performed",
        evaluation_status="Reviewed",
        review_date="2026-10-19",
        examples=[{
            "example_id": "2b52f43f-2321-4acb-91be-2772aa2c4d84",
            "decision_reference_id": "SYN-DEC-001",
            "intended_audience": "Synthetic service staff",
            "input_factor_summary": "Synthetic request category and urgency factors.",
            "recommendation_output": "Synthetic priority category: routine.",
            "human_readable_explanation": "The synthetic category and urgency drove the suggested routine priority.",
            "evidence_reference": "Synthetic example report, section 1.",
            "example_date": "2026-10-18",
            "human_review_findings_reference": "",
        }],
        accessibility_usefulness_reviews=[{
            "review_id": "0460daea-944d-47d8-bd94-49c7eefc42fa",
            "intended_audience": "Synthetic service staff",
            "review_method": "Moderated synthetic walkthrough.",
            "findings_feedback_summary": "Synthetic reviewer requested clearer factor labels.",
            "evidence_reference": "Synthetic review note 1.",
            "review_date": "2026-10-18",
            "limitations_corrective_actions": "One synthetic reviewer; revise labels.",
        }],
    )
    record.update(overrides)
    return record


def make_case(name="Synthetic explainability case", evidence=None):
    use_case = {field: f"Synthetic {field}" for field in USE_CASE_KEYS}
    use_case.update({
        "name": name,
        "owner": "Synthetic Service Owner",
        "purpose": "Prioritise synthetic requests for human review.",
        "decision": "Synthetic recommendation only",
        "ai_role": "Recommendation only",
        "human_oversight": "Required before action",
    })
    return {
        "use_case": use_case,
        "risk_answers": {key: key == "significant_decision" for key in RISK_ANSWER_KEYS},
        "control_evidence": deepcopy(evidence or {}),
        "deployment_readiness_plans": deepcopy(DEFAULT_PLANS),
    }


def control_app(evidence=None):
    app = AppTest.from_file(ROOT / "views" / "controls.py")
    case = make_case()
    app.session_state["use_case"] = case["use_case"]
    app.session_state["risk_answers"] = case["risk_answers"]
    app.session_state["control_evidence"] = deepcopy(evidence or {})
    app.run()
    return app


def find_widget(app, key):
    for widget_type in ("text_input", "text_area", "selectbox"):
        for widget in getattr(app, widget_type):
            if widget.key == key:
                return widget
    raise AssertionError(f"Widget not found: {key}")


def click(app, label):
    next(button for button in app.button if button.label == label).click().run()


def test_planned_and_performed_records_are_distinct_and_structured():
    planned = planned_record()
    performed = performed_record()
    assert validate_explainability_evidence(planned) == []
    assert validate_explainability_evidence(performed) == []
    assert validate_explainability_evidence({
        **planned,
        "examples": performed["examples"],
    })
    assert validate_explainability_evidence({
        **planned,
        "accessibility_usefulness_reviews": performed["accessibility_usefulness_reviews"],
    })


def test_malformed_examples_reviews_dates_ids_and_placeholders_are_invalid():
    base = performed_record()
    invalid_records = (
        {
            **base,
            "examples": [{**base["examples"][0], "evidence_reference": "N/A"}],
        },
        {
            **base,
            "examples": [{**base["examples"][0], "example_date": "2026-02-30"}],
        },
        {
            **base,
            "examples": [{**base["examples"][0], "example_id": "not-an-id"}],
        },
        {
            **base,
            "accessibility_usefulness_reviews": [{
                **base["accessibility_usefulness_reviews"][0],
                "review_date": "TBD",
            }],
        },
        {
            **base,
            "accessibility_usefulness_reviews": [
                base["accessibility_usefulness_reviews"][0],
                base["accessibility_usefulness_reviews"][0],
            ],
        },
    )
    for record in invalid_records:
        assert validate_explainability_evidence(record)


def test_common_placeholder_variants_are_rejected_in_performed_evidence_fields():
    placeholders = (
        "N/A",
        " N/A - pending. ",
        "TBD",
        "T.B.D. — later",
        "To be determined",
        "Not available yet",
        "Pending evidence",
        "Placeholder!",
        "Test reference pending",
    )
    for placeholder in placeholders:
        example = performed_record()
        example["examples"][0]["evidence_reference"] = placeholder
        assert validate_explainability_evidence(example), placeholder

    for field in ("human_readable_explanation", "input_factor_summary"):
        record = performed_record()
        record["examples"][0][field] = "TBD - later"
        assert validate_explainability_evidence(record), field

    for field in (
        "findings_feedback_summary",
        "review_method",
        "evidence_reference",
        "limitations_corrective_actions",
    ):
        record = performed_record()
        record["accessibility_usefulness_reviews"][0][field] = "N/A - pending"
        assert validate_explainability_evidence(record), field

    record = performed_record()
    record["examples"][0]["human_review_findings_reference"] = "TBD - later"
    assert validate_explainability_evidence(record)


def test_placeholder_checks_cover_all_required_performed_text_fields():
    for field in (
        "decision_reference_id",
        "intended_audience",
        "input_factor_summary",
        "recommendation_output",
        "human_readable_explanation",
        "evidence_reference",
    ):
        record = performed_record()
        record["examples"][0][field] = "Pending evidence."
        assert validate_explainability_evidence(record), field

    for field in (
        "intended_audience",
        "review_method",
        "findings_feedback_summary",
        "evidence_reference",
        "limitations_corrective_actions",
    ):
        record = performed_record()
        record["accessibility_usefulness_reviews"][0][field] = "To be determined!"
        assert validate_explainability_evidence(record), field

    for field in (
        "explanation_method",
        "method_description",
        "intended_audiences",
        "human_review_approach",
        "challenge_correction_process",
        "limitations",
        "outstanding_actions",
        "responsible_owner",
        "reviewer",
    ):
        record = performed_record()
        record[field] = "N/A - pending"
        assert validate_explainability_evidence(record), field


def test_placeholder_matching_does_not_reject_legitimate_pending_narrative():
    record = performed_record()
    record["examples"][0]["evidence_reference"] = (
        "Synthetic report; follow-up evidence is pending review, while these "
        "findings document the completed walkthrough."
    )
    record["examples"][0]["human_readable_explanation"] = (
        "This explanation describes the synthetic factors; further review is pending."
    )
    record["accessibility_usefulness_reviews"][0]["findings_feedback_summary"] = (
        "The synthetic review is complete; follow-up work remains pending."
    )
    record["examples"][0]["input_factor_summary"] = (
        "ملخص عوامل القرار الاصطناعي؛ المتابعة قيد الانتظار."
    )
    assert validate_explainability_evidence(record) == []


def test_performed_example_does_not_require_or_infer_accessibility_review():
    record = performed_record(accessibility_usefulness_reviews=[])
    assert validate_explainability_evidence(record) == []


def test_app_test_add_remove_rows_keeps_ids_and_values_stable():
    app = control_app()
    find_widget(
        app,
        TRN01_EXPLAINABILITY_WIDGET_KEYS["evaluation_stage"],
    ).select("Performed").run()
    click(app, "Add explanation example")
    click(app, "Add explanation example")
    example_ids_key = TRN01_EXPLAINABILITY_WIDGET_KEYS["example_row_ids"]
    ids = list(app.session_state[example_ids_key])
    assert len(ids) == 2 and ids[0] != ids[1]
    first_key = explainability_row_widget_key("example", ids[0], "evidence_reference")
    second_key = explainability_row_widget_key("example", ids[1], "evidence_reference")
    find_widget(app, first_key).set_value("Synthetic evidence first").run()
    find_widget(app, second_key).set_value("Synthetic evidence second").run()
    click(app, "Remove explanation example 1")
    assert app.session_state[example_ids_key] == [ids[1]]
    assert find_widget(app, second_key).value == "Synthetic evidence second"

    click(app, "Add audience review")
    review_ids_key = TRN01_EXPLAINABILITY_WIDGET_KEYS["review_row_ids"]
    click(app, "Add audience review")
    review_ids = list(app.session_state[review_ids_key])
    review_evidence = explainability_row_widget_key(
        "review", review_ids[1], "evidence_reference"
    )
    find_widget(app, review_evidence).set_value("Synthetic review reference").run()
    click(app, "Remove audience review 1")
    assert app.session_state[review_ids_key] == [review_ids[1]]
    assert find_widget(app, review_evidence).value == "Synthetic review reference"
    app.run()
    assert find_widget(app, review_evidence).value == "Synthetic review reference"


def test_invalid_and_duplicate_saved_row_ids_remain_invalid_until_explicit_repair():
    valid = performed_record()
    second_example = deepcopy(valid["examples"][0])
    second_example.update({
        "example_id": "2b52f43f-2321-4acb-91be-2772aa2c4d85",
        "decision_reference_id": "SYN-DEC-002",
        "evidence_reference": "Synthetic second report section 1.",
    })
    second_review = deepcopy(valid["accessibility_usefulness_reviews"][0])
    second_review.update({
        "review_id": "0460daea-944d-47d8-bd94-49c7eefc42fb",
        "evidence_reference": "Synthetic second review note.",
    })
    cases = (
        ("example", "invalid", {**valid, "examples": [
            {**valid["examples"][0], "example_id": "legacy-example"},
        ]}),
        ("example", "duplicate", {**valid, "examples": [
            valid["examples"][0],
            {**second_example, "example_id": valid["examples"][0]["example_id"]},
        ]}),
        ("review", "invalid", {**valid, "accessibility_usefulness_reviews": [
            {**valid["accessibility_usefulness_reviews"][0], "review_id": "legacy-review"},
        ]}),
        ("review", "duplicate", {**valid, "accessibility_usefulness_reviews": [
            valid["accessibility_usefulness_reviews"][0],
            {**second_review, "review_id": valid["accessibility_usefulness_reviews"][0]["review_id"]},
        ]}),
    )
    for kind, issue, saved in cases:
        app = control_app({"TRN-01": {
            **base_trn01(),
            "explainability_evidence": saved,
        }})
        original = deepcopy(saved)
        ids_key = TRN01_EXPLAINABILITY_WIDGET_KEYS[
            "example_row_ids" if kind == "example" else "review_row_ids"
        ]
        ui_ids = list(app.session_state[ids_key])
        assert len(ui_ids) == len(set(ui_ids))
        assert any(
            issue in warning.value
            for warning in app.warning
        )
        click(app, "Save TRN-01 explainability evidence")
        assert app.session_state["control_evidence"]["TRN-01"][
            "explainability_evidence"
        ] == original
        assert any("was not saved" in error.value for error in app.error)
        if issue == "duplicate":
            row_defaults = (
                ("example", saved["examples"], "evidence_reference")
                if kind == "example"
                else (
                    "review",
                    saved["accessibility_usefulness_reviews"],
                    "evidence_reference",
                )
            )
            row_kind, persisted_rows, field = row_defaults
            for ui_id, persisted_row in zip(ui_ids, persisted_rows):
                key = explainability_row_widget_key(row_kind, ui_id, field)
                assert find_widget(app, key).value == persisted_row[field]


def test_invalid_example_id_requires_remove_and_readd_before_replacement_save():
    saved = performed_record()
    saved["examples"][0]["example_id"] = "legacy-example-id"
    app = control_app({"TRN-01": {
        **base_trn01(),
        "explainability_evidence": saved,
    }})
    click(app, "Remove explanation example 1")
    assert app.session_state["control_evidence"]["TRN-01"][
        "explainability_evidence"
    ] == saved
    click(app, "Add explanation example")
    row_id = app.session_state[
        TRN01_EXPLAINABILITY_WIDGET_KEYS["example_row_ids"]
    ][0]
    replacement_values = {
        "decision_reference_id": "SYN-DEC-REPAIRED",
        "intended_audience": "Synthetic service staff",
        "input_factor_summary": "Synthetic category and urgency.",
        "recommendation_output": "Synthetic routine priority.",
        "human_readable_explanation": "Synthetic factors informed the recommendation.",
        "evidence_reference": "Synthetic replacement report section 1.",
        "example_date": "2026-10-18",
        "human_review_findings_reference": "",
    }
    for field, value in replacement_values.items():
        find_widget(
            app,
            explainability_row_widget_key("example", row_id, field),
        ).set_value(value)
    click(app, "Save TRN-01 explainability evidence")
    replacement = app.session_state["control_evidence"]["TRN-01"][
        "explainability_evidence"
    ]
    assert replacement["examples"][0]["example_id"] != "legacy-example-id"
    assert validate_explainability_evidence(replacement) == []


def test_explicit_save_and_invalid_replacement_preserve_canonical_evidence():
    saved = performed_record()
    app = control_app({"TRN-01": {
        **base_trn01(),
        "explainability_evidence": saved,
    }})
    find_widget(
        app,
        TRN01_EXPLAINABILITY_WIDGET_KEYS["explanation_method"],
    ).set_value("Changed but unsaved").run()
    assert app.session_state["control_evidence"]["TRN-01"]["explainability_evidence"] == saved

    example_id = app.session_state[
        TRN01_EXPLAINABILITY_WIDGET_KEYS["example_row_ids"]
    ][0]
    evidence_key = explainability_row_widget_key("example", example_id, "evidence_reference")
    find_widget(app, evidence_key).set_value("").run()
    click(app, "Save TRN-01 explainability evidence")
    assert app.session_state["control_evidence"]["TRN-01"]["explainability_evidence"] == saved
    assert any("Explainability evidence was not saved" in item.value for item in app.error)


def test_app_test_saves_performed_synthetic_example_explicitly():
    app = control_app()
    find_widget(
        app,
        TRN01_EXPLAINABILITY_WIDGET_KEYS["evaluation_stage"],
    ).select("Performed").run()
    root_values = {
        "evaluation_status": "Reviewed",
        "explanation_method": "Synthetic factor summary",
        "method_description": "A user-authored explanation of synthetic factors.",
        "intended_audiences": "Synthetic service staff.",
        "planned_context": "Synthetic priority recommendation.",
        "planned_feedback_collection": "Collect synthetic reviewer notes.",
        "human_review_approach": "A synthetic reviewer checks the example.",
        "challenge_correction_process": "Simulated challenge and correction route.",
        "limitations": "No live system or actual decision is represented.",
        "outstanding_actions": "Independent evaluation is not in scope.",
        "responsible_owner": "Synthetic Service Owner",
        "reviewer": "Synthetic Governance Reviewer",
        "review_date": "2026-10-19",
    }
    for field, value in root_values.items():
        key = TRN01_EXPLAINABILITY_WIDGET_KEYS[field]
        widget = find_widget(app, key)
        if field == "evaluation_stage":
            widget.select(value)
        elif field == "evaluation_status":
            widget.select(value)
        else:
            widget.set_value(value)
    click(app, "Add explanation example")
    example_id = app.session_state[
        TRN01_EXPLAINABILITY_WIDGET_KEYS["example_row_ids"]
    ][0]
    example_values = {
        "decision_reference_id": "SYN-DEC-UI-1",
        "intended_audience": "Synthetic service staff",
        "input_factor_summary": "Synthetic request category and urgency.",
        "recommendation_output": "Synthetic routine priority recommendation.",
        "human_readable_explanation": "Synthetic category and urgency informed the recommendation.",
        "evidence_reference": "Synthetic review record section 3",
        "example_date": "2026-10-18",
        "human_review_findings_reference": "",
    }
    for field, value in example_values.items():
        find_widget(
            app,
            explainability_row_widget_key("example", example_id, field),
        ).set_value(value)
    click(app, "Save TRN-01 explainability evidence")
    saved = app.session_state["control_evidence"]["TRN-01"]["explainability_evidence"]
    assert saved["evaluation_stage"] == "Performed"
    assert saved["examples"][0]["example_id"] == example_id
    assert saved["examples"][0]["evidence_reference"] == "Synthetic review record section 3"
    assert saved["accessibility_usefulness_reviews"] == []
    assert validate_explainability_evidence(saved) == []


def test_base_save_preserves_optional_nested_value_including_null_and_malformed():
    for nested in (None, "legacy unstructured note", {"examples": [{"bad": True}]}):
        app = control_app({"TRN-01": {
            **base_trn01(),
            "explainability_evidence": nested,
        }})
        find_widget(app, TRN01_WIDGET_KEYS["ai_system_purpose"]).set_value(
            "Updated synthetic base purpose"
        )
        click(app, "Save TRN-01 assessment")
        assert app.session_state["control_evidence"]["TRN-01"]["explainability_evidence"] == nested
        assert app.session_state["control_evidence"]["TRN-01"]["ai_system_purpose"] == "Updated synthetic base purpose"


def test_subsection_save_preserves_base_trn_fields():
    base = base_trn01(ai_system_purpose="Original synthetic purpose")
    app = control_app({"TRN-01": base})
    click(app, "Save TRN-01 explainability evidence")
    saved = app.session_state["control_evidence"]["TRN-01"]
    assert saved["ai_system_purpose"] == "Original synthetic purpose"
    assert saved["assessment_status"] == "Reviewed"
    assert validate_explainability_evidence(saved["explainability_evidence"]) == []


def test_case_save_load_fresh_restore_and_case_switch_isolation(tmp_path):
    first_record = performed_record()
    second_record = planned_record(explanation_method="Synthetic alternative method")
    first = make_case(evidence={"TRN-01": {
        **base_trn01(),
        "explainability_evidence": first_record,
    }})
    second = make_case("Second synthetic case", evidence={"TRN-01": {
        **base_trn01(),
        "explainability_evidence": second_record,
    }})
    first_doc = save_case(first, tmp_path)
    second_doc = save_case(second, tmp_path)
    loaded = load_case(first_doc["case_id"], tmp_path)
    assert loaded["schema_version"] == 1
    assert loaded["control_evidence"]["TRN-01"]["explainability_evidence"] == first_record

    app = AppTest.from_file(ROOT / "views" / "controls.py")
    restore_case(app.session_state, loaded)
    app.run()
    first_generation = app.session_state["_case_load_generation"]
    first_row_ids_key = (
        TRN01_EXPLAINABILITY_WIDGET_KEYS["example_row_ids"]
        + "_"
        + first_generation
    )
    first_key = explainability_row_widget_key(
        "example",
        app.session_state[first_row_ids_key][0],
        "evidence_reference",
        first_generation,
    )
    assert find_widget(app, first_key).value == "Synthetic example report, section 1."

    restore_case(app.session_state, load_case(second_doc["case_id"], tmp_path))
    app.run()
    generation = app.session_state["_case_load_generation"]
    method_key = TRN01_EXPLAINABILITY_WIDGET_KEYS["explanation_method"] + "_" + generation
    assert find_widget(app, method_key).value == "Synthetic alternative method"
    assert app.session_state["control_evidence"]["TRN-01"]["explainability_evidence"] == second_record


def test_schema_v1_preserves_malformed_nested_evidence_in_temporary_storage(tmp_path):
    malformed = {"examples": [{"example_id": "legacy"}], "old_field": "retained"}
    case = make_case(evidence={"TRN-01": {
        **base_trn01(),
        "explainability_evidence": malformed,
    }})
    saved = save_case(case, tmp_path)
    loaded = load_case(saved["case_id"], tmp_path)
    assert loaded["schema_version"] == 1
    assert loaded["control_evidence"]["TRN-01"]["explainability_evidence"] == malformed
    restored = {}
    restore_case(restored, loaded)
    assert restored["control_evidence"]["TRN-01"]["explainability_evidence"] == malformed


def test_schema_v1_legacy_malformed_nested_alignment_states(tmp_path):
    legacy = make_case(evidence={"TRN-01": base_trn01()})
    document = save_case(legacy, tmp_path)
    loaded = load_case(document["case_id"], tmp_path)
    assert "explainability_evidence" not in loaded["control_evidence"]["TRN-01"]

    app = AppTest.from_file(ROOT / "views" / "sdaia_alignment.py")
    app.run()
    assert any("Missing — no saved supplementary explainability" in item.value for item in app.caption)
    app.session_state["control_evidence"] = {"TRN-01": {
        "explainability_evidence": planned_record(),
    }}
    app.run()
    assert any("Planned" in item.value and "no performed examples" in item.value for item in app.caption)
    app.session_state["control_evidence"]["TRN-01"]["explainability_evidence"] = performed_record()
    app.run()
    assert any("Performed" in item.value and "not independently verified" in item.value for item in app.caption)
    app.session_state["control_evidence"]["TRN-01"]["explainability_evidence"] = None
    app.run()
    assert any("Invalid — supplementary explainability evidence" in item.value for item in app.caption)
    app.session_state["control_evidence"]["TRN-01"]["explainability_evidence"] = "legacy free text"
    app.run()
    assert any("Invalid — supplementary explainability evidence" in item.value for item in app.caption)


def test_nested_explainability_does_not_change_trn_status_risk_or_readiness():
    base = make_case(evidence={"TRN-01": base_trn01()})
    extended = deepcopy(base)
    extended["control_evidence"]["TRN-01"]["explainability_evidence"] = performed_record()
    control_ids = (
        "GOV-01", "MAP-01", "DAT-01", "FAI-01", "SEC-01",
        "TRN-01", "VAL-01", "MON-01", "INC-01",
    )

    def snapshot(case):
        controls = {
            control_id: assess_control(
                control_id,
                case["use_case"],
                case["risk_answers"],
                case["control_evidence"],
            )
            for control_id in control_ids
        }
        return (
            calculate_risk(case["risk_answers"]),
            controls,
            evaluate_readiness(
                controls,
                case["deployment_readiness_plans"],
                True,
            ),
        )

    assert snapshot(base) == snapshot(extended)
