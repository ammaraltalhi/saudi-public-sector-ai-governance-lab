from copy import deepcopy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.governance.saudi_risk_method import METHOD_ID, CATEGORIES, TREATMENTS, matrix_result
from src.governance.risk_register import score_record, validate_register
from src.governance.case_persistence import (
    RISK_ANSWER_KEYS, USE_CASE_KEYS, load_case, restore_case, save_case,
)

ROOT = Path(__file__).resolve().parents[1]
# Independent transcription of printed page 25, Figures 4 and 5.
EXPECTED = (
    ((1, 'Low'), (2, 'Low'), (3, 'Medium'), (4, 'Medium')),
    ((2, 'Low'), (4, 'Medium'), (6, 'Medium'), (8, 'High')),
    ((3, 'Medium'), (6, 'Medium'), (9, 'High'), (12, 'High')),
    ((4, 'Medium'), (8, 'High'), (12, 'High'), (16, 'Catastrophic')),
)


def national_record():
    return dict(
        risk_id='R-001', description='Unjustified retention', cause='No documented schedule',
        consequence='Excess exposure of citizen request data', owner='Synthetic privacy owner',
        controls='DAT-01', treatment='Review retention scope and disposal plan',
        due_date='2026-12-01', status='Open', evidence='', reviewer='', review_date='',
        likelihood=3, impact=3, residual_likelihood=2, residual_impact=2,
        methodology=METHOD_ID, category=CATEGORIES[1], assessment_horizon='Next 12 months',
        likelihood_rationale='Synthetic exposure assumptions with limited preventive controls',
        impact_rationale='Synthetic privacy harm and recovery analysis',
        treatment_strategy=TREATMENTS[1], residual_basis='Planned estimate',
        residual_rationale='Expected reduction conditional on planned disposal controls',
        assessment_evidence='Synthetic assessment assumptions v1; no operational data',
    )


@pytest.mark.parametrize('likelihood', [1, 2, 3, 4])
@pytest.mark.parametrize('impact', [1, 2, 3, 4])
def test_full_source_matrix(likelihood, impact):
    expected_score, expected_level = EXPECTED[likelihood - 1][impact - 1]
    actual = matrix_result(likelihood, impact)
    assert actual['score'] == expected_score
    assert actual['level'].split(' — ')[0] == expected_level


@pytest.mark.parametrize('value', [True, False, 0, 5, '2', 2.5, None])
def test_invalid_matrix_inputs(value):
    with pytest.raises(ValueError):
        matrix_result(value, 2)
    with pytest.raises(ValueError):
        matrix_result(2, value)


def test_national_and_legacy_records_keep_distinct_meanings():
    record = national_record()
    result = score_record(record)
    assert result['inherent_score'] == 9
    assert result['inherent_level'].startswith('High')
    assert result['residual_score'] == 4
    assert result['residual_level'].startswith('Medium')
    from src.governance.saudi_risk_method import NATIONAL_FIELDS
    legacy = {key: value for key, value in record.items() if key not in NATIONAL_FIELDS}
    assert score_record(legacy) == {'inherent_score': 9, 'residual_score': 4}
    assert 'methodology' not in legacy


@pytest.mark.parametrize('change', [
    {'methodology': 'unverified-method'}, {'category': 'unknown'},
    {'likelihood_rationale': ''}, {'impact_rationale': 'TBD'},
    {'assessment_horizon': ''}, {'assessment_evidence': 'pending'},
    {'residual_rationale': ''}, {'residual_basis': 'Verified automatically'},
    {'treatment_strategy': 'Approved automatically'}, {'category': []},
])
def test_national_documentary_requirements(change):
    record = national_record()
    record.update(change)
    assert validate_register([record])


def test_incomplete_migration_is_rejected():
    record = national_record()
    record.pop('category')
    assert validate_register([record])


def test_national_case_disk_roundtrip_and_legacy_restore(tmp_path):
    use_case = dict.fromkeys(USE_CASE_KEYS, 'Synthetic')
    use_case.update(ai_role='Decision support', human_oversight='Required before action')
    state = dict(use_case=use_case, risk_answers=dict.fromkeys(RISK_ANSWER_KEYS, False),
                 risk_register=[national_record()])
    saved = save_case(state, tmp_path)
    loaded = load_case(saved['case_id'], tmp_path)
    restored = {}
    restore_case(restored, loaded)
    assert restored['risk_register'] == [national_record()]
    assert score_record(restored['risk_register'][0])['residual_level'].startswith('Medium')
    legacy = deepcopy(loaded)
    from src.governance.saudi_risk_method import NATIONAL_FIELDS
    for field in NATIONAL_FIELDS:
        legacy['risk_register'][0].pop(field)
    restore_case(restored, legacy)
    assert 'methodology' not in restored['risk_register'][0]


def test_risk_page_national_save_and_legacy_migration():
    from src.governance.saudi_risk_method import NATIONAL_FIELDS
    record = national_record()
    legacy = {key: value for key, value in record.items() if key not in NATIONAL_FIELDS}
    app = AppTest.from_file(ROOT / 'views/risk_register.py')
    app.session_state['use_case'] = {'name': 'Synthetic'}
    app.session_state['risk_register'] = [legacy]
    app.run()
    assert not app.exception
    app.selectbox[0].set_value('R-001').run()
    method = next(field for field in app.selectbox if field.label == 'Assessment method')
    assert method.value == 'Illustrative (legacy)'
    method.set_value(METHOD_ID).run()
    app.button[0].click().run()
    assert app.error
    assert 'methodology' not in app.session_state['risk_register'][0]
    for field in app.text_area:
        field.set_value(record[field.label.lower().replace(' ', '_')])
    for field in app.selectbox:
        name = field.label.lower().replace(' ', '_')
        if name in ('category', 'treatment_strategy', 'residual_basis'):
            field.set_value(record[name])
    app.button[0].click().run()
    assert not app.exception
    saved = app.session_state['risk_register'][0]
    assert saved['methodology'] == METHOD_ID
    assert score_record(saved)['inherent_score'] == 9
    assert len(app.session_state['risk_register']) == 1


@pytest.mark.parametrize('view', ['home.py', 'saudi_risk_method.py'])
def test_national_reference_views_render(view):
    app = AppTest.from_file(ROOT / 'views' / view).run()
    assert not app.exception
    if view == 'saudi_risk_method.py':
        assert len(app.table) == 2
