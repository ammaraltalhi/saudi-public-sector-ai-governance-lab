from pathlib import Path

import streamlit as st

from src.governance.case_persistence import (
    CasePersistenceError,
    load_case,
    list_saved_cases,
    restore_case,
    save_case,
)

st.set_page_config(page_title="Saudi Public Sector AI Governance Lab", page_icon="⚖️", layout="wide")

CASES_DIR = Path(__file__).resolve().parent / "data" / "cases"

with st.sidebar:
    st.header("Case Management")
    current_case = st.session_state.get("use_case", {})
    st.write(f"**Current case name:** {current_case.get('name', 'Not saved to session')}")
    st.caption(
        "Case files are stored locally as JSON for this portfolio prototype. "
        "Do not enter real citizen personal data."
    )
    st.caption(
        "RACI editor changes are not persisted; data/raci.csv remains the baseline."
    )

    if st.button("Save Case", use_container_width=True):
        try:
            saved_document = save_case(st.session_state, CASES_DIR)
            st.session_state["current_case_id"] = saved_document["case_id"]
            st.session_state["case_management_message"] = (
                "success",
                f"Saved case '{saved_document['case_name']}'.",
            )
        except CasePersistenceError as error:
            st.session_state["case_management_message"] = ("error", str(error))
        st.rerun()

    saved_cases = list_saved_cases(CASES_DIR)
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
            case_document = load_case(selected_case_id, CASES_DIR)
            restore_case(st.session_state, case_document)
            st.session_state["case_management_message"] = (
                "success",
                f"Loaded case '{case_document['case_name']}'.",
            )
            st.rerun()
        except CasePersistenceError as error:
            st.session_state["case_management_message"] = ("error", str(error))
            st.rerun()

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
        st.Page("views/risk_assessment.py", title="Risk Assessment"),
        st.Page("views/deployment_readiness.py", title="Deployment Readiness"),
        st.Page("views/raci.py", title="RACI Matrix"),
        st.Page("views/inventory.py", title="AI Inventory"),
        st.Page("views/controls.py", title="Control Library"),
        st.Page("views/dashboard.py", title="Governance Dashboard"),
        st.Page("views/sdaia_alignment.py", title="SDAIA Framework Alignment"),
    ]
}

pg = st.navigation(pages)
pg.run()
