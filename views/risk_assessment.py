import streamlit as st
from src.governance.risk import RISK_WEIGHTS, calculate_risk

st.title("AI Risk Assessment")
st.write("Answer the screening questions. The score is an illustrative portfolio heuristic, not a legal classification.")

questions = {
    "personal_data": "Does the system process personal data?",
    "sensitive_data": "Does it process sensitive or highly sensitive data?",
    "significant_decision": "Could it materially affect an individual's access, priority, rights or opportunities?",
    "vulnerable_groups": "Could it affect vulnerable groups?",
    "external_users": "Is it used by or directly exposed to external users?",
    "automated_action": "Can it trigger an action without meaningful human review?",
    "third_party_model": "Does it rely on a third-party AI model or API?",
    "security_critical": "Could failure create a significant security or safety impact?",
}


def recalculate_risk_result(risk_answers):
    result = calculate_risk(risk_answers)
    st.session_state["risk_result"] = result
    st.session_state["risk_score"] = result.score
    st.session_state["governance_tier"] = result.level
    st.session_state["risk_breakdown"] = [
        (questions[key], RISK_WEIGHTS[key])
        for key, value in risk_answers.items()
        if value
    ]


def sync_risk_answer(key):
    current_answers = st.session_state.get("risk_answers")
    if not isinstance(current_answers, dict) or set(current_answers) != set(questions):
        current_answers = {answer_key: False for answer_key in questions}
    else:
        current_answers = current_answers.copy()
    current_answers[key] = st.session_state[key]
    st.session_state["risk_answers"] = current_answers
    recalculate_risk_result(current_answers)


risk_answers = st.session_state.get("risk_answers")
if (
    not isinstance(risk_answers, dict)
    or set(risk_answers) != set(questions)
    or any(type(value) is not bool for value in risk_answers.values())
):
    risk_answers = None

answers = {}
for key, label in questions.items():
    st.session_state[key] = (
        risk_answers[key] if risk_answers is not None else False
    )
    answers[key] = st.checkbox(
        label,
        key=key,
        on_change=sync_risk_answer,
        args=(key,),
    )

if st.button("Calculate governance risk"):
    risk_answers = {key: bool(answers[key]) for key in questions}
    st.session_state["risk_answers"] = risk_answers.copy()
    recalculate_risk_result(risk_answers)

if risk_answers is not None and "risk_result" not in st.session_state:
    recalculate_risk_result(risk_answers)

if "risk_result" in st.session_state:
    result = st.session_state["risk_result"]
    st.subheader("Risk score breakdown")
    for factor, points in st.session_state["risk_breakdown"]:
        st.write(f"- {factor}: {points} point{'s' if points != 1 else ''}")

    st.write(f"**Total illustrative risk score:** {result.score}")
    st.write(f"**Governance tier:** {result.level}")
    st.subheader("Required governance gates")
    for i, gate in enumerate(result.required_gates, start=1):
        st.write(f"{i}. {gate}")
