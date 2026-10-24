from pathlib import Path
from copy import deepcopy
import pandas as pd
import streamlit as st
from src.governance.raci import COLUMNS, normalize_raci, raci_errors

st.title("RACI Accountability Matrix")
st.write("R = Responsible, A = Accountable, C = Consulted, I = Informed")
path = Path(__file__).resolve().parents[1] / "data" / "raci.csv"
baseline = pd.read_csv(path).fillna("").to_dict("records")
records = st.session_state.get("raci_matrix", baseline)
generation = st.session_state.get("_case_load_generation", "initial")
edited = st.data_editor(pd.DataFrame(records, columns=COLUMNS), use_container_width=True,
                        num_rows="dynamic", key=f"raci_editor_{generation}",
                        column_config={column: st.column_config.TextColumn(column) for column in COLUMNS})
candidate = normalize_raci(edited.where(pd.notnull(edited), None).to_dict("records"))
st.caption("Keep one Accountable role per activity. Use A, R, C, I or combinations such as A/R. Save RACI to case before saving or downloading the whole case. The repository baseline is unchanged.")
if candidate != records:
    st.info("Unsaved RACI edits. Save this matrix before leaving the page.")
errors = raci_errors(candidate)
if st.button("Validate accountable ownership"):
    if errors:
        for error in errors:
            st.warning(error)
    else:
        st.success("Each activity has one clear Accountable role.")
if st.button("Save RACI to case"):
    if not st.session_state.get("use_case"):
        st.error("Save the AI Use Case Intake first.")
    elif errors:
        for error in errors:
            st.error(error)
    else:
        st.session_state["raci_matrix"] = deepcopy(candidate)
        st.success("RACI saved to this case. Use Save Case, then Download Case JSON to retain it after this session.")
