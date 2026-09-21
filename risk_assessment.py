import streamlit as st
from src.governance.risk import calculate_risk

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

answers = {}
for key, label in questions.items():
    answers[key] = st.checkbox(label, key=key)

if st.button("Calculate governance risk"):
    result = calculate_risk(answers)
    st.session_state["risk_result"] = result

if "risk_result" in st.session_state:
    result = st.session_state["risk_result"]
    c1, c2 = st.columns(2)
    c1.metric("Illustrative risk score", result.score)
    c2.metric("Governance tier", result.level)
    st.subheader("Required governance gates")
    for i, gate in enumerate(result.required_gates, start=1):
        st.write(f"{i}. {gate}")
