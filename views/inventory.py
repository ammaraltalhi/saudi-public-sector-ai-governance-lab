from pathlib import Path
import pandas as pd
import streamlit as st

st.title("AI Inventory")
path = Path(__file__).resolve().parents[1] / "data" / "ai_inventory.csv"
df = pd.read_csv(path)

current_use_case = st.session_state.get("use_case", {})
current_risk_tier = st.session_state.get("governance_tier")
matching_system = current_use_case.get("name")
inventory_match_found = (
    bool(matching_system) and matching_system in df["AI System"].values
)

if inventory_match_found and current_risk_tier:
    match = df["AI System"] == matching_system
    df.loc[match, "Risk Level"] = current_risk_tier
    df["Risk Level Source"] = "CSV baseline sample"
    df.loc[match, "Risk Level Source"] = "Current session risk assessment"
    st.info(
        f"Risk level for {matching_system} is from the current session risk assessment."
    )

st.dataframe(df, use_container_width=True, hide_index=True)
st.caption("In a real implementation this register would have controlled ownership, versioning, evidence links and lifecycle status.")
