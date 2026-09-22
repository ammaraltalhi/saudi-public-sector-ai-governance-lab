import streamlit as st

st.title("AI Use Case Intake")
st.write("Capture the business context before assessing AI risk.")

with st.form("use_case_form"):
    name = st.text_input("AI system name", "Citizen Request Prioritisation AI")
    owner = st.text_input("Business owner", "Customer Services Directorate")
    purpose = st.text_area("Intended purpose", "Prioritise municipal service requests for operational review.")
    users = st.text_input("Primary users", "Municipal operations staff")
    affected_people = st.text_input(
    "Affected people",
    "Citizens submitting service requests"
)
 ai_role = st.selectbox(
    "AI role in decision-making",
    [
        "Recommendation only",
        "Decision support",
        "Automated decision"
    ]
)

human_oversight = st.selectbox(
    "Human oversight",
    [
        "Required before action",
        "Human review after action",
        "No human review"
    ]
)   
potential_impact = st.text_area(
    "Potential impact if the AI is wrong",
    "Incorrect prioritisation could delay an important citizen service request."
)
incident_response = st.text_area(
    "Incident response considerations",
    "Human review, correct the affected decision, investigate the cause, and escalate based on severity."
)
    data = st.text_area("Main data categories", "Citizen requests, service category, location area, timestamps")
    decision = st.text_area("Decision or output", "Recommended priority score for human review")
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
