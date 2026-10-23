from pathlib import Path
from copy import deepcopy
import pytest
from src.governance.risk_register import validate_register, score_record
from src.governance.case_persistence import build_case_document, restore_case, USE_CASE_KEYS, RISK_ANSWER_KEYS


def record():
    return dict(risk_id="R-001", description="Unjustified retention", cause="No schedule", consequence="Excess exposure", owner="Privacy owner", controls="DAT-01", treatment="Define schedule", due_date="2026-12-01", status="Open", evidence="", reviewer="", review_date="", likelihood=3, impact=4, residual_likelihood=2, residual_impact=3)


def test_products_and_closure():
    item = record()
    assert score_record(item) == {"inherent_score": 12, "residual_score": 6}
    item["status"] = "Closed"
    assert validate_register([item])
    item.update(evidence="Synthetic review report", reviewer="Demo reviewer", review_date="2026-11-01")
    assert not validate_register([item])


@pytest.mark.parametrize("value", [True, 0, 5, 1.5, "3"])
def test_invalid_scores(value):
    item = record()
    item["likelihood"] = value
    assert validate_register([item])


def test_duplicate_and_bad_date():
    item = record()
    assert validate_register([item, deepcopy(item)])
    item["due_date"] = "2026-02-30"
    assert validate_register([item])


def test_case_round_trip_and_legacy_reset():
    use_case = dict.fromkeys(USE_CASE_KEYS, "Synthetic")
    use_case.update(ai_role="Decision support", human_oversight="Required before action")
    state = dict(use_case=use_case, risk_answers=dict.fromkeys(RISK_ANSWER_KEYS, False), risk_register=[record()])
    document = build_case_document(state)
    restored = {}
    restore_case(restored, document)
    assert restored["risk_register"] == [record()]
    legacy = deepcopy(document)
    legacy.pop("risk_register")
    restore_case(restored, legacy)
    assert restored["risk_register"] == []


def test_register_page_save_and_export():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / 'views/risk_register.py')
    app.session_state['use_case'] = {'name': 'Synthetic intake'}
    app.run()
    assert not app.exception
    next(field for field in app.selectbox if field.label == "Assessment method").set_value("Illustrative (legacy)").run()
    values = record()
    for field in app.text_area:
        name = field.label.lower().replace(' ', '_')
        field.set_value(values[name])
    app.button[0].click().run()
    assert not app.exception
    assert len(app.session_state['risk_register']) == 1
    assert app.session_state['risk_register'][0]['description'] == values['description']
