from pathlib import Path
import os
import json

import streamlit as st

from src.governance.case_persistence import (
    CasePersistenceError,
    load_case,
    list_saved_cases,
    restore_case,
    save_case,
)
from src.governance.session_cases import (
    save_session_case, load_session_case, list_session_cases, parse_case_upload, remember_case,
)

st.set_page_config(page_title="Saudi Public Sector AI Governance Lab", page_icon="⚖️", layout="wide")

LOCAL_STORAGE = os.environ.get("GOVERNANCE_CASE_STORAGE") == "local"
CASES_DIR = Path(__file__).resolve().parent / "data" / "cases"

with st.sidebar:
    st.header("Case Management")
    current_case = st.session_state.get("use_case", {})
    st.write(f"**Current case name:** {current_case.get('name', 'Not saved to session')}")
    if LOCAL_STORAGE:
        st.warning("Private local storage mode: case files are shared by this runtime. Do not enable this mode on a public host.")
    else:
        st.caption("Public synthetic demo: saved snapshots belong to this session only. No shared server case files are listed or written. Download Case JSON before refreshing or closing; import it to resume later.")
    st.caption("Use invented data only. No authentication, verified approvals or production storage is provided. RACI changes saved to the case are included in case JSON.")

    if st.button("Save Case", use_container_width=True):
        try:
            saved_document = (save_case(st.session_state, CASES_DIR) if LOCAL_STORAGE
                              else save_session_case(st.session_state))
            st.session_state["current_case_id"] = saved_document["case_id"]
            st.session_state["case_management_message"] = (
                "success",
                f"Saved case '{saved_document['case_name']}'.",
            )
        except CasePersistenceError as error:
            st.session_state["case_management_message"] = ("error", str(error))
        st.rerun()

    saved_cases = (list_saved_cases(CASES_DIR) if LOCAL_STORAGE
                   else list_session_cases(st.session_state))
    saved_case_ids = [case["case_id"] for case in saved_cases]
    case_names = {case["case_id"]: case["case_name"] for case in saved_cases}
    current_case_id = st.session_state.get("current_case_id")
    selected_index = (
        saved_case_ids.index(current_case_id)
        if current_case_id in saved_case_ids
        else 0
    )
    selected_case_id = st.selectbox(
        "Saved cases",
        saved_case_ids or [""],
        index=selected_index,
        format_func=lambda case_id: case_names.get(case_id, "No saved cases"),
        disabled=not saved_case_ids,
        key="case_load_selection",
    )
    if st.button("Load Case", disabled=not saved_case_ids, use_container_width=True):
        try:
            case_document = (load_case(selected_case_id, CASES_DIR) if LOCAL_STORAGE
                             else load_session_case(st.session_state, selected_case_id))
            restore_case(st.session_state, case_document)
            st.session_state["case_management_message"] = (
                "success",
                f"Loaded case '{case_document['case_name']}'.",
            )
            st.rerun()
        except CasePersistenceError as error:
            st.session_state["case_management_message"] = ("error", str(error))
            st.rerun()

    if selected_case_id:
        try:
            snapshot = (load_case(selected_case_id, CASES_DIR) if LOCAL_STORAGE
                        else load_session_case(st.session_state, selected_case_id))
            st.download_button("Download Case JSON", json.dumps(snapshot, ensure_ascii=False, indent=2),
                               file_name=f"governance-case-{selected_case_id}.json", mime="application/json")
            st.caption("Download contains the selected saved snapshot. Save Case again to include newer edits.")
        except CasePersistenceError as error:
            st.warning(str(error))
    uploaded = st.file_uploader("Import Case JSON (synthetic data only, max 2 MiB)", type=["json"])
    if st.button("Import and load case", disabled=uploaded is None):
        try:
            if uploaded.size > 2 * 1024 * 1024:
                raise CasePersistenceError("Upload a JSON case no larger than 2 MiB.")
            document = parse_case_upload(uploaded.getvalue())
            remember_case(st.session_state, document)
            restore_case(st.session_state, document)
            st.session_state["case_management_message"] = ("success", f"Imported case '{document['case_name']}'.")
            st.rerun()
        except CasePersistenceError as error:
            st.error(str(error))

    message = st.session_state.pop("case_management_message", None)
    if message:
        level, text = message
        if level == "success":
            st.success(text)
        else:
            st.error(text)

pages = {
    "Governance Lab": [
        st.Page("views/home.py", title="Overview"),
        st.Page("views/use_case.py", title="AI Use Case Intake"),
        st.Page("views/risk_assessment.py", title="Risk Screening"),
        st.Page("views/saudi_risk_method.py", title="Saudi National Risk Method"),
        st.Page("views/risk_register.py", title="Risk Register & Treatment"),
        st.Page("views/corrective_actions.py", title="Corrective Actions"),
        st.Page("views/risk_decisions.py", title="Residual Risk Decisions"),
        st.Page("views/deployment_readiness.py", title="Deployment Readiness"),
        st.Page("views/raci.py", title="RACI Matrix"),
        st.Page("views/inventory.py", title="AI Inventory"),
        st.Page("views/controls.py", title="Control Library"),
        st.Page("views/dashboard.py", title="Governance Dashboard"),
        st.Page("views/sdaia_alignment.py", title="SDAIA Framework Alignment"),
        st.Page("views/impact_assessment.py", title="SDAIA Impact Assessment"),
    ]
}

pg = st.navigation(pages)
pg.run()
