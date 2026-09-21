import streamlit as st

st.title("AI Use Case Intake")
st.write("Capture the business context before assessing AI risk.")

with st.form("use_case_form"):
    name = st.text_input("AI system name", "Citizen Request Prioritisation AI")
    owner = st.text_input("Business owner", "Customer Services Directorate")
    purpose = st.text_area("Intended purpose", "Prioritise municipal service requests for operational review.")
    users = st.text_input("Primary users", "Municipal operations staff")
    data = st.text_area("Main data categories", "Citizen requests, service category, location area, timestamps")
    decision = st.text_area("Decision or output", "Recommended priority score for human review")
    submitted = st.form_submit_button("Save to session")

if submitted:
    st.session_state["use_case"] = {
        "name": name,
        "owner": owner,
        "purpose": purpose,
        "users": users,
        "data": data,
        "decision": decision,
    }
    st.success("Use case saved for this session.")

if "use_case" in st.session_state:
    st.subheader("Current use case")
    st.json(st.session_state["use_case"])
