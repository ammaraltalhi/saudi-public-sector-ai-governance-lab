from copy import deepcopy
import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.governance.case_persistence import (USE_CASE_KEYS, RISK_ANSWER_KEYS, CasePersistenceError,
    build_case_document, restore_case, validate_case_document)
from src.governance.session_cases import (save_session_case, load_session_case, list_session_cases,
    parse_case_upload, remember_case, MAX_CASE_BYTES)
from src.governance.raci import raci_errors, normalize_raci
from src.governance.use_case_context import context_errors
from src.governance.deployment_readiness import evaluate_readiness

ROOT = Path(__file__).resolve().parents[1]


def state():
    use_case = dict.fromkeys(USE_CASE_KEYS, 'Synthetic context description')
    use_case.update(ai_role='Recommendation only', human_oversight='Required before action')
    return dict(use_case=use_case, risk_answers=dict.fromkeys(RISK_ANSWER_KEYS, False))


def baseline():
    return pd.read_csv(ROOT / 'data/raci.csv').fillna('').to_dict('records')


def test_session_snapshots_are_isolated_and_copied():
    first, second = state(), state()
    document = save_session_case(first)
    first['use_case']['purpose'] = 'Unsaved change'
    assert load_session_case(first, document['case_id'])['use_case']['purpose'] != 'Unsaved change'
    assert list_session_cases(second) == []
    with pytest.raises(CasePersistenceError):
        load_session_case(second, document['case_id'])
    document['use_case']['purpose'] = 'Outside mutation'
    assert load_session_case(first, document['case_id'])['use_case']['purpose'] != 'Outside mutation'


def test_download_import_restores_raci_and_existing_fields():
    original = state()
    original['raci_matrix'] = baseline()
    original['raci_matrix'][0]['Activity'] = 'Synthetic changed activity'
    document = save_session_case(original)
    parsed = parse_case_upload(json.dumps(document).encode())
    fresh = {}
    remember_case(fresh, parsed)
    restore_case(fresh, parsed)
    assert fresh['raci_matrix'] == original['raci_matrix']
    assert fresh['risk_answers'] == original['risk_answers']
    assert fresh['use_case'] == original['use_case']
    legacy = deepcopy(document)
    legacy.pop('raci_matrix')
    restore_case(fresh, legacy)
    assert 'raci_matrix' not in fresh


@pytest.mark.parametrize('payload', [b'{', b'[]', b'\xff', b'{"schema_version":NaN}', b'x'*(MAX_CASE_BYTES+1)])
def test_invalid_import_leaves_current_state_unchanged(payload):
    current = state()
    snapshot = deepcopy(current)
    with pytest.raises(CasePersistenceError):
        parse_case_upload(payload)
    assert current == snapshot


def test_import_rejects_incomplete_or_multi_accountable_raci():
    original = state()
    original['raci_matrix'] = baseline()
    document = build_case_document(original)
    document['raci_matrix'][0]['AI Governance'] = 'A'
    with pytest.raises(CasePersistenceError, match='Accountable'):
        parse_case_upload(json.dumps(document).encode())


@pytest.mark.parametrize('change', ['empty', 'duplicate', 'role', 'two_accounts', 'nontext'])
def test_raci_validation_enforces_activity_and_roles(change):
    matrix = baseline()
    if change == 'empty': matrix[0]['Activity'] = ' '
    elif change == 'duplicate': matrix[1]['Activity'] = matrix[0]['Activity']
    elif change == 'role': matrix[0]['Business Owner'] = 'ADMIN'
    elif change == 'two_accounts': matrix[0]['AI Governance'] = 'A'
    elif change == 'nontext': matrix[0]['Business Owner'] = 5
    assert raci_errors(matrix)


def test_raci_normalization_keeps_baseline_valid():
    matrix = baseline()
    matrix[0]['Business Owner'] = ' a/r '
    matrix[0]['Internal Audit'] = None
    normalized = normalize_raci(matrix)
    assert not raci_errors(normalized)
    assert normalized[0]['Business Owner'] == 'A/R'


@pytest.mark.parametrize('value', ['', ' ', 'TBD', 'N/A'])
def test_incomplete_context_blocks_readiness(value):
    use_case = state()['use_case']
    use_case['purpose'] = value
    assert context_errors(use_case)
    result = evaluate_readiness({}, {}, True, [], [], {}, use_case)
    assert any('Intended purpose' in text for text in result['risk_review_blockers'])
    assert result['status'] == 'Not Ready for Deployment Approval'


def test_intake_rejects_blank_without_overwriting_saved_context():
    app = AppTest.from_file(ROOT / 'views/use_case.py').run()
    app.button[0].click().run()
    saved = deepcopy(app.session_state['use_case'])
    next(widget for widget in app.text_area if widget.label == 'Intended purpose').set_value(' ')
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state['use_case'] == saved
    assert any('Intended purpose' in error.value for error in app.error)


def test_public_app_does_not_enumerate_or_write_shared_disk(monkeypatch):
    import src.governance.case_persistence as persistence
    monkeypatch.delenv('GOVERNANCE_CASE_STORAGE', raising=False)
    def forbidden(*args, **kwargs): raise AssertionError('Public UI accessed disk cases')
    monkeypatch.setattr(persistence, 'save_case', forbidden)
    monkeypatch.setattr(persistence, 'load_case', forbidden)
    monkeypatch.setattr(persistence, 'list_saved_cases', forbidden)
    app = AppTest.from_file(ROOT / 'app.py').run()
    for key, value in state().items(): app.session_state[key] = value
    next(button for button in app.button if button.label == 'Save Case').click().run()
    assert not app.exception
    assert len(list_session_cases(app.session_state)) == 1
    second = AppTest.from_file(ROOT / 'app.py').run()
    assert not second.exception
    assert list_session_cases(second.session_state) == []
    assert next(button for button in second.button if button.label == 'Load Case').disabled


def test_raci_save_and_load_uses_case_matrix_without_modifying_baseline():
    baseline_bytes = (ROOT / 'data/raci.csv').read_bytes()
    app = AppTest.from_file(ROOT / 'views/raci.py')
    app.session_state['use_case'] = state()['use_case']
    matrix = baseline()
    matrix[0]['Activity'] = 'Synthetic per-case approval activity'
    app.session_state['raci_matrix'] = matrix
    app.run()
    next(button for button in app.button if button.label == 'Save RACI to case').click().run()
    assert not app.exception
    document = build_case_document({**state(), 'raci_matrix':app.session_state['raci_matrix']})
    restored = {}
    restore_case(restored, document)
    assert restored['raci_matrix'][0]['Activity'] == 'Synthetic per-case approval activity'
    assert (ROOT / 'data/raci.csv').read_bytes() == baseline_bytes
