from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.governance.risk_decisions import fingerprint, validate_decisions, review_blockers
from src.governance.risk_register import validate_register
from src.governance.case_persistence import (
    USE_CASE_KEYS, RISK_ANSWER_KEYS, save_case, load_case, restore_case,
    build_case_document, CasePersistenceError,
)
from src.governance.constants import PRE_DEPLOYMENT_CONTROL_IDS
from src.governance.control_assessment import (
    SEC_01_REQUIRED_TEXT_FIELDS, TRN_01_REQUIRED_TEXT_FIELDS, VAL_01_REQUIRED_TEXT_FIELDS,
    MON_01_REQUIRED_TEXT_FIELDS, INC_01_REQUIRED_TEXT_FIELDS,
)
from src.governance.deployment_readiness import evaluate_readiness
from src.governance.saudi_risk_method import METHOD_ID, CATEGORIES, TREATMENTS

ROOT = Path(__file__).resolve().parents[1]


def bundle():
    context = dict.fromkeys(USE_CASE_KEYS, 'Synthetic case')
    context.update(ai_role='Decision support', human_oversight='Required before action')
    risk = dict(
        risk_id='R-001', description='Retention without a justified schedule',
        cause='Schedule not documented', consequence='Unnecessary data exposure',
        owner='Synthetic privacy owner', controls='DAT-01', treatment='Document schedule',
        due_date=(date.today()+timedelta(days=10)).isoformat(), status='Closed',
        evidence='Synthetic disposal-test record', reviewer='Synthetic reviewer',
        review_date=date.today().isoformat(), likelihood=2, impact=2,
        residual_likelihood=1, residual_impact=1, methodology=METHOD_ID,
        category=CATEGORIES[1], assessment_horizon='Next twelve months',
        likelihood_rationale='Synthetic control and exposure review',
        impact_rationale='Synthetic scope and recovery analysis',
        treatment_strategy=TREATMENTS[1], residual_basis='Post-treatment reassessment',
        residual_rationale='Synthetic disposal-test findings support the revised estimate',
        assessment_evidence='Synthetic post-treatment test record v1',
    )
    decision = dict(
        risk_id='R-001', decision='Accept', authority='Synthetic authorized governance role',
        decision_date=date.today().isoformat(), tolerance_reference='Synthetic tolerance policy v1',
        rationale='Within the documented synthetic tolerance following reassessment',
        evidence='Synthetic governance review record v1',
        next_review_date=(date.today()+timedelta(days=30)).isoformat(),
        risk_fingerprint=fingerprint(risk), context_fingerprint=fingerprint(context),
    )
    return context, risk, decision


def complete_controls():
    return {key: {'Applicability':'Required','Evidence Status':'Available'}
            for key in PRE_DEPLOYMENT_CONTROL_IDS + ('MON-01','INC-01')}


def test_low_residual_and_closed_risk_do_not_automatically_accept():
    context, risk, _ = bundle()
    assert review_blockers([risk], {}, context)
    assert evaluate_readiness(complete_controls(), {}, True, [], [risk], {}, context)['status'] == 'Not Ready for Deployment Approval'


def test_complete_current_acceptance_allows_human_approval_gate():
    context, risk, decision = bundle()
    assert not review_blockers([risk], {'R-001':decision}, context)
    result = evaluate_readiness(complete_controls(), {}, True, [], [risk], {'R-001':decision}, context)
    assert result['status'] == 'Ready for Deployment Approval'
    assert result['risk_review_blockers'] == []


@pytest.mark.parametrize('decision_value', ['Escalate','Reject'])
def test_escalated_or_rejected_decisions_remain_blocking(decision_value):
    context, risk, decision = bundle()
    decision['decision'] = decision_value
    assert review_blockers([risk], {'R-001':decision}, context)


@pytest.mark.parametrize('change', ['risk','context','expiry','future_decision','planned_residual'])
def test_changes_and_review_dates_invalidate_gate(change):
    context, risk, decision = bundle()
    if change == 'risk':
        risk['residual_likelihood'] = 2
    elif change == 'context':
        context['purpose'] = 'Expanded scope'
    elif change == 'expiry':
        decision['decision_date'] = (date.today()-timedelta(days=2)).isoformat()
        decision['next_review_date'] = date.today().isoformat()
    elif change == 'future_decision':
        decision['decision_date'] = (date.today()+timedelta(days=1)).isoformat()
    else:
        risk['residual_basis'] = 'Planned estimate'
        decision['risk_fingerprint'] = fingerprint(risk)
    assert review_blockers([risk], {'R-001':decision}, context)


def test_empty_and_legacy_registers_block_national_readiness():
    context, risk, decision = bundle()
    assert review_blockers([], {}, context)
    from src.governance.saudi_risk_method import NATIONAL_FIELDS
    for field in NATIONAL_FIELDS:
        risk.pop(field)
    assert 'legacy' in review_blockers([risk], {'R-001':decision}, context)[0]


@pytest.mark.parametrize('change', [
    {'authority':'TBD'}, {'evidence':''}, {'decision':'Approved'}, {'risk_fingerprint':'bad'},
    {'decision_date':'not a date'}, {'next_review_date':'2020-01-01'}, {'risk_id':'R-999'},
])
def test_bad_decision_records_rejected(change):
    _,_,decision = bundle()
    decision.update(change)
    assert validate_decisions({'R-001':decision}, {'R-001'})


def test_missing_required_control_never_passes_ready_gate():
    controls = complete_controls()
    del controls['SEC-01']
    result = evaluate_readiness(controls,{},True)
    assert 'SEC-01' in result['blocking_controls']
    assert result['status'] == 'Not Ready for Deployment Approval'


def test_placeholder_risk_closure_evidence_rejected():
    _,risk,_ = bundle()
    risk['evidence']='TBD'
    assert validate_register([risk])


def test_decisions_persist_and_legacy_case_clears_them(tmp_path):
    context,risk,decision=bundle()
    state=dict(use_case=context,risk_answers=dict.fromkeys(RISK_ANSWER_KEYS,False),
               risk_register=[risk],risk_decisions={'R-001':decision})
    saved=save_case(state,tmp_path)
    loaded=load_case(saved['case_id'],tmp_path)
    restored={}
    restore_case(restored,loaded)
    assert restored['risk_decisions']==state['risk_decisions']
    assert not review_blockers(restored['risk_register'],restored['risk_decisions'],restored['use_case'])
    loaded.pop('risk_decisions')
    restore_case(restored,loaded)
    assert restored['risk_decisions']=={}
    assert review_blockers(restored['risk_register'],restored['risk_decisions'],restored['use_case'])


def test_stale_decision_remains_loadable_but_blocks_review():
    context,risk,decision=bundle()
    risk['description']='Changed scenario'
    doc=build_case_document(dict(use_case=context,risk_answers=dict.fromkeys(RISK_ANSWER_KEYS,False),risk_register=[risk],risk_decisions={'R-001':decision}))
    restored={}
    restore_case(restored,doc)
    assert any('changed' in message for message in review_blockers(restored['risk_register'],restored['risk_decisions'],restored['use_case']))
    doc['risk_decisions']['R-001']['evidence']=''
    before=deepcopy(restored)
    with pytest.raises(CasePersistenceError):
        restore_case(restored,doc)
    assert restored==before


def test_decision_page_save_rejects_incomplete_then_records_acceptance():
    context,risk,decision=bundle()
    app=AppTest.from_file(ROOT/'views/risk_decisions.py')
    app.session_state['use_case']=context
    app.session_state['risk_register']=[risk]
    app.run()
    assert not app.exception
    app.button[0].click().run()
    assert app.error
    for field in app.text_area:
        field.set_value(decision[field.label.lower().replace(' ','_')])
    next(field for field in app.selectbox if field.label=='Decision').set_value('Accept')
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state['risk_decisions']=={'R-001':decision}
    assert app.success
    app.session_state['risk_register'][0]['impact_rationale']='Updated harm analysis'
    app.run()
    assert any('changed' in warning.value for warning in app.warning)


@pytest.mark.parametrize('view',['dashboard.py','deployment_readiness.py'])
def test_views_gate_review_and_context_changes(view):
    context,risk,decision=bundle()
    evidence={}
    for control,fields in (
        ('SEC-01',SEC_01_REQUIRED_TEXT_FIELDS),('TRN-01',TRN_01_REQUIRED_TEXT_FIELDS),
        ('VAL-01',VAL_01_REQUIRED_TEXT_FIELDS),('MON-01',MON_01_REQUIRED_TEXT_FIELDS),('INC-01',INC_01_REQUIRED_TEXT_FIELDS),
    ):
        evidence[control]={field:'Synthetic documented evidence' for field in fields}
        evidence[control]['assessment_status']='Reviewed'
    app=AppTest.from_file(ROOT/'views'/view)
    for key,value in dict(use_case=context,risk_answers=dict.fromkeys(RISK_ANSWER_KEYS,False),control_evidence=evidence,risk_register=[risk],risk_decisions={'R-001':decision}).items():
        app.session_state[key]=value
    app.run()
    assert not app.exception
    assert any(item.value=='Ready for Deployment Approval' for item in list(app.success)+list(app.subheader))
    app.session_state['use_case']['purpose']='Material scope change'
    app.run()
    assert not app.exception
    assert any(item.value=='Not Ready for Deployment Approval' for item in list(app.warning)+list(app.subheader))
