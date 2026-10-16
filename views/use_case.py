import streamlit as st
from src.governance.case_persistence import USE_CASE_WIDGET_KEYS

st.title("AI Use Case Intake")
st.write("Capture the business context before assessing AI risk.")

defaults = {
    "name": "Citizen Request Prioritisation AI",
    "owner": "Customer Services Directorate",
    "purpose": "Prioritise municipal service requests for operational review.",
    "users": "Municipal operations staff",
    "affected_people": "Citizens submitting service requests",
    "ai_role": "Recommendation only",
    "human_oversight": "Required before action",
    "potential_impact": "Incorrect prioritisation could delay an important citizen service request.",
    "incident_response": "Human review, correct the affected decision, investigate the cause, and escalate based on severity.",
    "data": "Citizen requests, service category, location area, timestamps",
    "decision": "Recommended priority score for human review",
}
current_use_case = st.session_state.get("use_case", {})
for field, key in USE_CASE_WIDGET_KEYS.items():
    st.session_state.setdefault(key, current_use_case.get(field, defaults[field]))

with st.form("use_case_form"):
    name = st.text_input("AI system name", key=USE_CASE_WIDGET_KEYS["name"])
    owner = st.text_input("Business owner", key=USE_CASE_WIDGET_KEYS["owner"])
    purpose = st.text_area("Intended purpose", key=USE_CASE_WIDGET_KEYS["purpose"])
    users = st.text_input("Primary users", key=USE_CASE_WIDGET_KEYS["users"])
    affected_people = st.text_input("Affected people", key=USE_CASE_WIDGET_KEYS["affected_people"])
    ai_role = st.selectbox(
        "AI role in decision-making",
        [
            "Recommendation only",
            "Decision support",
            "Automated decision"
        ],
        key=USE_CASE_WIDGET_KEYS["ai_role"],
    )

    human_oversight = st.selectbox(
        "Human oversight",
        [
            "Required before action",
            "Human review after action",
            "No human review"
        ],
        key=USE_CASE_WIDGET_KEYS["human_oversight"],
    )
    potential_impact = st.text_area("Potential impact if the AI is wrong", key=USE_CASE_WIDGET_KEYS["potential_impact"])
    incident_response = st.text_area("Incident response considerations", key=USE_CASE_WIDGET_KEYS["incident_response"])
    data = st.text_area("Main data categories", key=USE_CASE_WIDGET_KEYS["data"])
    decision = st.text_area("Decision or output", key=USE_CASE_WIDGET_KEYS["decision"])
    submitted = st.form_submit_button("Save to session")

if submitted:
    st.session_state["use_case"] = {
    "name": name,
    "owner": owner,
    "purpose": purpose,
    "users": users,
    "affected_people": affected_people,
    "data": data,
    "decision": decision,
    "ai_role": ai_role,
    "human_oversight": human_oversight,
    "potential_impact": potential_impact,
    "incident_response": incident_response,
}
    st.success("Use case saved for this session.")

if "use_case" in st.session_state:
    st.subheader("Current use case")
    st.json(st.session_state["use_case"])
