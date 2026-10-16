from pathlib import Path
import pandas as pd
import streamlit as st

st.title("RACI Accountability Matrix")
st.write("R = Responsible, A = Accountable, C = Consulted, I = Informed")

path = Path(__file__).resolve().parents[1] / "data" / "raci.csv"
df = pd.read_csv(path)

edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")
st.caption("Good practice for this portfolio: keep one clear Accountable owner for each activity wherever practical.")

if st.button("Validate accountable ownership"):
    role_cols = [c for c in edited.columns if c != "Activity"]
    issues = []
    for _, row in edited.iterrows():
        accountable = sum(str(row[c]).upper() == "A" or "A" in str(row[c]).upper().split("/") for c in role_cols)
        if accountable != 1:
            issues.append(f"{row['Activity']}: {accountable} Accountable roles found")
    if issues:
        st.warning("Review these rows:\n\n" + "\n\n".join(issues))
    else:
        st.success("Each activity has one clear Accountable role.")
