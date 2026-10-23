from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.governance.corrective_actions import validate_actions, action_summary
from src.governance.case_persistence import (
    CasePersistenceError, RISK_ANSWER_KEYS, USE_CASE_KEYS,
    build_case_document, save_case, load_case, restore_case,
)
from src.governance.constants import PRE_DEPLOYMENT_CONTROL_IDS
from src.governance.deployment_readiness import evaluate_readiness

ROOT = Path(__file__).resolve().parents[1]


def action():
    return dict(
        action_id='A-001', finding='Retention period lacks a justification',
        risk_id='', control_id='DAT-01', owner='Synthetic privacy owner',
        action_plan='Document and review the retention schedule', due_date='2026-10-22',
        status='Open', evidence='', reviewer='', review_date='', verification_notes='',
        readiness_rationale='Unresolved data-retention risk prevents release', blocks_readiness=True,
    )


def closed_action():
    record = action()
    record.update(status='Closed', evidence='Synthetic retention review v1',
                  reviewer='Synthetic reviewer', review_date='2026-10-23',
                  verification_notes='Checked scope and rationale against the synthetic case')
    return record


def case_state():
    use_case = dict.fromkeys(USE_CASE_KEYS, 'Synthetic case')
    use_case.update(ai_role='Decision support', human_oversight='Required before action')
    return dict(use_case=use_case, risk_answers=dict.fromkeys(RISK_ANSWER_KEYS, False),
                corrective_actions=[action()])


def complete_controls():
    return {control: {'Applicability': 'Required', 'Evidence Status': 'Available'}
            for control in PRE_DEPLOYMENT_CONTROL_IDS + ('MON-01', 'INC-01')}


def test_closure_and_reopening_change_readiness():
    actions = [action()]
    before = evaluate_readiness(complete_controls(), {}, True, actions)
    assert before['status'] == 'Not Ready for Deployment Approval'
    assert before['blocking_actions'] == ['A-001']
    actions[0] = closed_action()
    after = evaluate_readiness(complete_controls(), {}, True, actions)
    assert after['status'] == 'Ready for Deployment Approval'
    actions[0]['status'] = 'In progress'
    assert evaluate_readiness(complete_controls(), {}, True, actions)['blocking_actions'] == ['A-001']


@pytest.mark.parametrize('field', ['evidence', 'reviewer', 'review_date', 'verification_notes'])
@pytest.mark.parametrize('value', ['', 'TBD', 'N/A', 'pending'])
def test_closure_rejects_missing_and_placeholder_evidence(field, value):
    record = closed_action()
    record[field] = value
    assert validate_actions([record])
    assert evaluate_readiness(complete_controls(), {}, True, [record])['status'] == 'Not Ready for Deployment Approval'


def test_summary_overdue_and_nonblocking():
    record = action()
    record['blocks_readiness'] = False
    assert action_summary([record], date(2026, 10, 23)) == {
        'errors': [], 'blocking_actions': [], 'open_count': 1, 'overdue_count': 1,
    }
    assert action_summary([record], date(2026, 10, 22))['overdue_count'] == 0
    assert action_summary([closed_action()], date(2026, 10, 24))['overdue_count'] == 0
    assert evaluate_readiness(complete_controls(), {}, True, [record])['status'] == 'Ready for Deployment Approval'


@pytest.mark.parametrize('change', [
    {'control_id': 'UNKNOWN'}, {'control_id': '', 'risk_id': ''},
    {'risk_id': 'missing'}, {'due_date': '2026-02-30'}, {'review_date': 'invalid'},
    {'blocks_readiness': 'False'}, {'status': 'Accepted'}, {'owner': 'TBD'},
    {'readiness_rationale': ''},
])
def test_invalid_records_are_rejected(change):
    record = action()
    record.update(change)
    assert validate_actions([record], set())


def test_unique_ids_and_structure():
    assert validate_actions([action(), action()])
    assert validate_actions({})
    assert validate_actions([None])
    record = action()
    record['unknown'] = 'value'
    assert validate_actions([record])
    record = action()
    record['finding'] = None
    assert validate_actions([record])


def test_invalid_actions_fail_readiness_closed():
    result = evaluate_readiness(complete_controls(), {}, True, {'bad': 'record'})
    assert result['status'] == 'Not Ready for Deployment Approval'
    assert result['action_errors']
    assert evaluate_readiness(complete_controls(), {}, False, [action()]) is None


def test_disk_roundtrip_and_legacy_case_reset(tmp_path):
    saved = save_case(case_state(), tmp_path)
    loaded = load_case(saved['case_id'], tmp_path)
    assert loaded['corrective_actions'] == [action()]
    state = {}
    restore_case(state, loaded)
    assert state['corrective_actions'] == [action()]
    legacy = deepcopy(loaded)
    legacy.pop('corrective_actions')
    restore_case(state, legacy)
    assert state['corrective_actions'] == []


def test_invalid_links_and_closure_rejected_before_state_mutation():
    document = build_case_document(case_state())
    document['corrective_actions'][0]['risk_id'] = 'missing'
    state = {'sentinel': 'unchanged'}
    with pytest.raises(CasePersistenceError):
        restore_case(state, document)
    assert state == {'sentinel': 'unchanged'}
    state = case_state()
    state['corrective_actions'][0]['status'] = 'Closed'
    with pytest.raises(CasePersistenceError):
        build_case_document(state)


def test_action_page_save_edit_close_and_case_isolation():
    app = AppTest.from_file(ROOT / 'views/corrective_actions.py')
    app.session_state['use_case'] = {'name': 'Synthetic case'}
    app.run()
    assert not app.exception
    for field in app.text_area:
        field.set_value(action()[field.label.lower().replace(' ', '_')])
    next(field for field in app.selectbox if field.label == 'Control id').set_value('DAT-01')
    app.button[0].click().run()
    assert not app.exception
    records = app.session_state['corrective_actions']
    assert len(records) == 1
    action_id = records[0]['action_id']
    app.selectbox[0].set_value(action_id).run()
    next(field for field in app.selectbox if field.label == 'Status').set_value('Closed')
    app.button[0].click().run()
    assert app.error
    assert app.session_state['corrective_actions'][0]['status'] == 'Open'
    for field in app.text_area:
        name = field.label.lower().replace(' ', '_')
        field.set_value(closed_action()[name])
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state['corrective_actions'][0]['status'] == 'Closed'
    app.session_state['corrective_actions'] = []
    app.session_state['_case_load_generation'] = 'another-case'
    app.run()
    assert not app.exception
    assert all(not field.value for field in app.text_area)


@pytest.mark.parametrize('view', ['dashboard.py', 'deployment_readiness.py'])
def test_readiness_views_show_action_blockers(view):
    from src.governance.control_assessment import (
        SEC_01_REQUIRED_TEXT_FIELDS, TRN_01_REQUIRED_TEXT_FIELDS,
        VAL_01_REQUIRED_TEXT_FIELDS, MON_01_REQUIRED_TEXT_FIELDS, INC_01_REQUIRED_TEXT_FIELDS,
    )
    state = case_state()
    state['control_evidence'] = {}
    for control, fields in (
        ('SEC-01', SEC_01_REQUIRED_TEXT_FIELDS), ('TRN-01', TRN_01_REQUIRED_TEXT_FIELDS),
        ('VAL-01', VAL_01_REQUIRED_TEXT_FIELDS), ('MON-01', MON_01_REQUIRED_TEXT_FIELDS),
        ('INC-01', INC_01_REQUIRED_TEXT_FIELDS),
    ):
        state['control_evidence'][control] = {field: 'Synthetic documentation' for field in fields}
        state['control_evidence'][control]['assessment_status'] = 'Reviewed'
    app = AppTest.from_file(ROOT / 'views' / view)
    for key, value in state.items():
        app.session_state[key] = value
    app.run()
    assert not app.exception
    assert any('Not Ready for Deployment Approval' in item.value for item in list(app.warning) + list(app.subheader))
    assert not any('No current governance-readiness blockers' in item.value for item in app.success)
    app.session_state['corrective_actions'] = [closed_action()]
    app.run()
    assert not app.exception
    assert any(item.value == 'Ready for Deployment Approval' for item in list(app.success) + list(app.subheader))
