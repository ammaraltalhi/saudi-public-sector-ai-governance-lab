import json
from uuid import uuid4
import streamlit as st
from src.governance.risk_register import TEXT_FIELDS, STATUSES, validate_register, score_record

st.title("Risk Register & Treatment")
st.caption("Synthetic portfolio records. The 1–4 scales and product scores are illustrative and have not been verified against the national framework. Residual scores are estimates, not proof of control effectiveness.")
if not st.session_state.get("use_case"):
    st.info("Save the AI Use Case Intake first.")
    st.stop()
records = st.session_state.get("risk_register", [])
options = ["New risk"] + [record["risk_id"] for record in records]
generation = st.session_state.get("_case_load_generation", "initial")
selected = st.selectbox("Record", options, key=f"register_selection_{generation}")
existing = next((record for record in records if record["risk_id"] == selected), {})
with st.form(f"risk_record_{generation}_{selected}"):
    record = {"risk_id": existing.get("risk_id", str(uuid4()))}
    for field in TEXT_FIELDS:
        if field == "risk_id":
            continue
        if field == "status":
            record[field] = st.selectbox("Status", STATUSES, index=STATUSES.index(existing.get(field, "Open")))
        else:
            record[field] = st.text_area(field.replace("_", " ").capitalize(), value=existing.get(field, ""))
    for field in ("likelihood", "impact", "residual_likelihood", "residual_impact"):
        record[field] = st.number_input(field.replace("_", " ").capitalize(), min_value=1, max_value=4, value=existing.get(field, 1), step=1)
    st.caption("Due date and review date: YYYY-MM-DD. Closing requires evidence, reviewer and review date. Save Case in the sidebar to persist changes to disk.")
    if st.form_submit_button("Save risk record"):
        updated = [item for item in records if item["risk_id"] != record["risk_id"]] + [record]
        errors = validate_register(updated)
        if errors:
            for error in errors:
                st.error(error)
        else:
            st.session_state["risk_register"] = updated
            st.rerun()
if records:
    st.dataframe([{**record, **score_record(record)} for record in records], use_container_width=True)
    st.download_button("Export risk register JSON", json.dumps(records, indent=2), "risk_register.json", "application/json")
