import json
from datetime import date
from uuid import uuid4

import streamlit as st

from src.governance.corrective_actions import (
    CONTROL_IDS, STATUSES, TEXT_FIELDS, action_summary, validate_actions,
)

st.title("Corrective Actions")
st.caption("Synthetic case workflow. Review fields record user attestations; reviewer identities and evidence authenticity are not independently verified.")
if not st.session_state.get("use_case"):
    st.info("Save the AI Use Case Intake first.")
    st.stop()

records = st.session_state.get("corrective_actions", [])
risk_ids = [record["risk_id"] for record in st.session_state.get("risk_register", [])]
errors = validate_actions(records, set(risk_ids))
if errors:
    for error in errors:
        st.error(error)
    st.stop()

generation = st.session_state.get("_case_load_generation", "initial")
selected = st.selectbox(
    "Action record", ["New action"] + [record["action_id"] for record in records],
    key=f"action_selection_{generation}",
)
existing = next((record for record in records if record["action_id"] == selected), {})
with st.form(f"action_form_{generation}_{selected}"):
    record = {"action_id": existing.get("action_id", str(uuid4()))}
    for field in TEXT_FIELDS:
        if field == "action_id":
            continue
        label = field.replace("_", " ").capitalize()
        choices = None
        if field == "status":
            choices = list(STATUSES)
        elif field == "risk_id":
            choices = [""] + risk_ids
        elif field == "control_id":
            choices = [""] + list(CONTROL_IDS)
        if choices is not None:
            value = existing.get(field, choices[0])
            record[field] = st.selectbox(label, choices, index=choices.index(value))
        else:
            record[field] = st.text_area(label, value=existing.get(field, ""))
    record["blocks_readiness"] = st.checkbox(
        "Blocks deployment readiness until closed", value=existing.get("blocks_readiness", True),
    )
    st.caption("Explain the readiness impact in Readiness rationale. Dates use YYYY-MM-DD. Closure requires evidence, reviewer, review date and verification notes. Save Case persists records to disk.")
    if st.form_submit_button("Save corrective action"):
        updated = [item for item in records if item["action_id"] != record["action_id"]] + [record]
        errors = validate_actions(updated, set(risk_ids))
        if errors:
            for error in errors:
                st.error(error)
        else:
            st.session_state["corrective_actions"] = updated
            st.rerun()

summary = action_summary(records)
columns = st.columns(3)
columns[0].metric("Open actions", summary["open_count"])
columns[1].metric("Overdue actions", summary["overdue_count"])
columns[2].metric("Readiness blockers", len(summary["blocking_actions"]))
st.caption("Overdue actions exclude closed records and actions due today.")
if records:
    st.dataframe(records, hide_index=True, use_container_width=True)
    report = {
        "case_name": st.session_state["use_case"].get("name", ""),
        "report_date": date.today().isoformat(),
        "scope": "Synthetic, user-recorded corrective actions; not a compliance certificate or deployment approval.",
        "summary": summary,
        "actions": records,
    }
    st.download_button("Export corrective-action report", json.dumps(report, indent=2), "corrective_action_report.json", "application/json")
