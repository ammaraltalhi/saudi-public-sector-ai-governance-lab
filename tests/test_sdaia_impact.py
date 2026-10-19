import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.governance.case_persistence import (
    DEFAULT_PLANS,
    RISK_ANSWER_KEYS,
    USE_CASE_KEYS,
    load_case,
    restore_case,
    save_case,
)
from src.governance.sdaia_impact import (
    ASSESSMENT_FIELDS,
    validate_impact_assessment,
    validate_impact_assessments,
)


ROOT = Path(__file__).resolve().parents[1]


def case_state(name="Citizen Request Prioritisation AI", impact_assessments=None):
    use_case = {field: f"Synthetic {field}" for field in USE_CASE_KEYS}
    use_case.update({
        "name": name,
        "ai_role": "Recommendation only",
        "human_oversight": "Required before action",
        "affected_people": "Synthetic stakeholder group",
    })
    state = {
        "use_case": use_case,
        "risk_answers": {key: False for key in RISK_ANSWER_KEYS},
        "control_evidence": {},
        "deployment_readiness_plans": DEFAULT_PLANS,
    }
    if impact_assessments is not None:
        state["sdaia_impact_assessments"] = impact_assessments
    return state


def complete_assessment(assessment_type, **overrides):
    assessment = {
        field: f"Synthetic fixture for {field}"
        for field in ASSESSMENT_FIELDS[assessment_type]
    }
    assessment.update({
        "assessment_status": "Reviewed",
        "evidence_type": "Planned",
        "review_date": "2026-10-19",
    })
    if assessment_type == "social_environmental":
        assessment["environmental_applicability"] = "Applicable"
        assessment["environmental_resource_impacts"] = "No measured results."
        assessment["environmental_na_justification"] = ""
    assessment.update(overrides)
    return assessment


def widget_value(app, widget_type, key):
    widget = next(item for item in getattr(app, widget_type) if item.key == key)
    return widget.value


def test_incomplete_draft_is_valid_but_review_requires_completed_fields():
    draft = {
        field: ""
        for field in ASSESSMENT_FIELDS["humanity"]
    }
    draft.update({"assessment_status": "Draft", "evidence_type": "Planned"})

    assert validate_impact_assessment(draft, "humanity") == []
    draft["assessment_status"] = "Reviewed"
    errors = validate_impact_assessment(draft, "humanity")

    assert any("Use case is required" in error for error in errors)
    assert any("Review date must be a valid date" in error for error in errors)


def test_review_rejects_invalid_date_and_not_applicable_without_reason():
    assessment = complete_assessment(
        "social_environmental",
        environmental_applicability="Not Applicable",
        environmental_na_justification=" ",
        review_date="19-10-2026",
    )
    errors = validate_impact_assessment(assessment, "social_environmental")

    assert any("A reason is required" in error for error in errors)
    assert any("YYYY-MM-DD" in error for error in errors)


def test_review_rejects_placeholder_only_required_values():
    assessment = complete_assessment(
        "humanity",
        use_case="TBD",
        affected_stakeholders="N/A",
        responsible_owner="x",
        reviewer=" ",
    )
    errors = validate_impact_assessment(assessment, "humanity")

    assert any("Use case is required" in error for error in errors)
    assert any("Affected stakeholders is required" in error for error in errors)
    assert any("Responsible owner is required" in error for error in errors)
    assert any("Reviewer is required" in error for error in errors)


def test_reasoned_environmental_not_applicable_is_valid():
    assessment = complete_assessment(
        "social_environmental",
        environmental_applicability="Not Applicable",
        environmental_resource_impacts="",
        environmental_na_justification=(
            "This desk-based documentation activity does not operate equipment."
        ),
    )

    assert validate_impact_assessment(assessment, "social_environmental") == []


def test_central_validator_separates_valid_and_invalid_records():
    valid = complete_assessment("humanity", assessment_status="Draft")
    invalid = complete_assessment("social_environmental")
    invalid["reviewer"] = 42
    invalid["assessment_status"] = "Approved"

    accepted, rejected = validate_impact_assessments({
        "humanity": valid,
        "social_environmental": invalid,
        "unknown": {},
    })

    assert accepted == {"humanity": valid}
    assert set(rejected) == {"social_environmental", "unknown"}
    assert any("must be text" in error for error in rejected["social_environmental"]["errors"])
    assert any("Unknown impact assessment type" in error for error in rejected["unknown"]["errors"])


def test_draft_save_requires_explicit_submit_and_keeps_evidence_blank():
    app = AppTest.from_file(ROOT / "views" / "impact_assessment.py")
    app.session_state["use_case"] = case_state()["use_case"]
    app.run()

    assert not app.exception
    assert app.session_state["sdaia_impact_assessments"] == {}
    assert any(
        "Do not invent stakeholder consultation" in item.value
        for item in app.warning
    )

    save_button = next(
        item for item in app.button
        if item.label == "Save Humanity Impact Assessment"
    )
    save_button.click().run()

    saved = app.session_state["sdaia_impact_assessments"]["humanity"]
    assert saved["assessment_status"] == "Draft"
    assert saved["evidence_references"] == ""
    assert saved["evidence_type"] == "Planned"


def test_incomplete_review_submission_is_rejected_without_saving():
    app = AppTest.from_file(ROOT / "views" / "impact_assessment.py")
    app.session_state["use_case"] = case_state()["use_case"]
    app.run()

    save = next(
        item for item in app.button
        if item.label == "Save Humanity Impact Assessment"
    )
    save.click().run()
    saved_draft = app.session_state["sdaia_impact_assessments"]["humanity"].copy()
    assert saved_draft["assessment_status"] == "Draft"

    status = next(
        widget for widget in app.selectbox
        if widget.label == "Assessment status"
        and widget.key.startswith("sdaia_impact_humanity_")
    )
    status.select("Reviewed")
    assert status.value == "Reviewed"
    save = next(
        item for item in app.button
        if item.label == "Save Humanity Impact Assessment"
    )
    save.click().run()

    assert app.session_state["sdaia_impact_assessments"]["humanity"] == saved_draft
    assert any(
        "Assessment was not saved" in item.value
        for item in app.error
    )


def test_case_file_round_trip_restores_impact_assessments(tmp_path):
    assessment = complete_assessment(
        "humanity",
        use_case="Citizen Request Prioritisation AI",
        evidence_references="Synthetic document reference",
    )
    state = case_state(impact_assessments={"humanity": assessment})
    saved = save_case(state, tmp_path)
    disk_document = json.loads(
        (tmp_path / f"{saved['case_id']}.json").read_text(encoding="utf-8")
    )
    assert disk_document["sdaia_impact_assessments"]["humanity"] == assessment

    loaded = load_case(saved["case_id"], tmp_path)
    restored = {}
    restore_case(restored, loaded)
    assert restored["sdaia_impact_assessments"]["humanity"] == assessment


def test_schema_v1_case_without_impact_extension_remains_loadable(tmp_path):
    saved = save_case(case_state(), tmp_path)
    assert "sdaia_impact_assessments" not in saved

    existing_v1_path = tmp_path / f"{saved['case_id']}.json"
    existing_v1_path.write_text(json.dumps(saved), encoding="utf-8")
    loaded = load_case(saved["case_id"], tmp_path)
    restored = {}
    restore_case(restored, loaded)

    assert loaded["schema_version"] == 1
    assert restored["sdaia_impact_assessments"] == {}


def test_invalid_optional_json_records_are_isolated_and_source_is_unchanged(tmp_path):
    valid = complete_assessment("social_environmental", assessment_status="Draft")
    invalid = complete_assessment("humanity")
    invalid["assessment_status"] = "Reviewed"
    invalid["review_date"] = "not-a-date"
    invalid["responsible_owner"] = "TBD"
    saved = save_case(case_state(), tmp_path)
    target = tmp_path / f"{saved['case_id']}.json"
    saved["sdaia_impact_assessments"] = {
        "humanity": invalid,
        "social_environmental": valid,
    }
    target.write_text(json.dumps(saved), encoding="utf-8")
    original_bytes = target.read_bytes()

    loaded = load_case(saved["case_id"], tmp_path)
    restored = {}
    restore_case(restored, loaded)

    assert restored["sdaia_impact_assessments"] == {
        "social_environmental": valid,
    }
    assert "humanity" in restored["_sdaia_impact_assessment_invalid"]
    assert target.read_bytes() == original_bytes


def test_invalid_optional_assessment_types_and_statuses_remain_diagnostic(tmp_path):
    saved = save_case(case_state(), tmp_path)
    saved["sdaia_impact_assessments"] = {
        "humanity": {"assessment_status": "Reviewed"},
        "social_environmental": complete_assessment(
            "social_environmental",
            assessment_status="Approved",
        ),
    }
    target = tmp_path / f"{saved['case_id']}.json"
    target.write_text(json.dumps(saved), encoding="utf-8")

    restored = {}
    restore_case(restored, load_case(saved["case_id"], tmp_path))

    assert restored["sdaia_impact_assessments"] == {}
    assert set(restored["_sdaia_impact_assessment_invalid"]) == {
        "humanity",
        "social_environmental",
    }


def test_fresh_session_restores_visible_fields_and_case_switch_rehydrates(tmp_path):
    first_assessment = complete_assessment(
        "humanity",
        use_case="Case One",
        affected_stakeholders="Group One",
        human_dignity_rights_choice_accessibility_culture="First case impact",
    )
    second_assessment = complete_assessment(
        "humanity",
        use_case="Case Two",
        affected_stakeholders="Group Two",
        human_dignity_rights_choice_accessibility_culture="Second case impact",
    )
    first_document = save_case(
        case_state("Case One", {"humanity": first_assessment}),
        tmp_path / "case-one",
    )
    second_document = save_case(
        case_state("Case Two", {"humanity": second_assessment}),
        tmp_path / "case-two",
    )

    app = AppTest.from_file(ROOT / "views" / "impact_assessment.py")
    restore_case(app.session_state, first_document)
    app.run()
    first_generation = app.session_state["_case_load_generation"]
    first_key = f"sdaia_impact_humanity_human_dignity_rights_choice_accessibility_culture_{first_generation}"
    assert widget_value(app, "text_area", first_key) == "First case impact"
    assert widget_value(
        app,
        "selectbox",
        f"sdaia_impact_humanity_assessment_status_{first_generation}",
    ) == "Reviewed"

    restore_case(app.session_state, second_document)
    app.run()
    second_generation = app.session_state["_case_load_generation"]
    second_key = f"sdaia_impact_humanity_human_dignity_rights_choice_accessibility_culture_{second_generation}"
    assert widget_value(app, "text_area", second_key) == "Second case impact"
    assert second_generation != first_generation


def test_unsaved_form_edits_do_not_change_saved_canonical_assessment():
    saved = complete_assessment(
        "humanity",
        assessment_status="Reviewed",
        human_dignity_rights_choice_accessibility_culture="Saved value",
    )
    app = AppTest.from_file(ROOT / "views" / "impact_assessment.py")
    app.session_state["use_case"] = case_state()["use_case"]
    app.session_state["sdaia_impact_assessments"] = {"humanity": saved}
    app.run()

    widget = next(
        widget for widget in app.text_area
        if widget.key.startswith(
            "sdaia_impact_humanity_human_dignity_rights_choice_accessibility_culture"
        )
    )
    widget.set_value("Unsaved change").run()

    assert (
        app.session_state["sdaia_impact_assessments"]["humanity"][
            "human_dignity_rights_choice_accessibility_culture"
        ]
        == "Saved value"
    )


def test_impact_assessment_page_is_registered_in_app_navigation():
    app = AppTest.from_file(ROOT / "app.py").run()
    app.switch_page("views/impact_assessment.py").run()

    assert not app.exception
    assert app.title[0].value == "SDAIA Impact Assessment"


def test_alignment_reports_saved_documentation_without_verifying_implementation():
    app = AppTest.from_file(ROOT / "views" / "sdaia_alignment.py")
    app.session_state["sdaia_impact_assessments"] = {
        "humanity": complete_assessment(
            "humanity",
            assessment_status="Reviewed",
            evidence_type="Planned",
        ),
        "social_environmental": complete_assessment(
            "social_environmental",
            assessment_status="Draft",
            evidence_type="Operational",
        ),
    }
    app.run()

    assert not app.exception
    captions = "\n".join(item.value for item in app.caption)
    assert "Assessment documentation saved (Reviewed)" in captions
    assert "user-entered evidence type: Planned" in captions
    assert "not independently verified evidence of implementation" in captions
    assert any(
        item.value == "**Social & Environmental Benefits:**"
        for item in app.markdown
    )


def test_alignment_marks_invalid_records_and_only_validates_canonical_status():
    app = AppTest.from_file(ROOT / "views" / "sdaia_alignment.py")
    app.session_state["sdaia_impact_assessments"] = {
        "humanity": {"assessment_status": "Reviewed"},
        "social_environmental": complete_assessment(
            "social_environmental",
            assessment_status="Draft",
        ),
    }
    app.run()

    captions = "\n".join(item.value for item in app.caption)
    assert "Invalid — assessment record is excluded" in captions
    assert "Assessment documentation saved (Draft)" in captions


def test_alignment_marks_absent_assessments_as_missing():
    app = AppTest.from_file(ROOT / "views" / "sdaia_alignment.py").run()

    assert not app.exception
    captions = "\n".join(item.value for item in app.caption)
    assert captions.count("Missing — no saved assessment documentation.") == 2
