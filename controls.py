from pathlib import Path
import pandas as pd
import streamlit as st

st.title("AI Governance Control Library")
path = Path(__file__).resolve().parents[1] / "data" / "controls.csv"
df = pd.read_csv(path)
st.dataframe(df, use_container_width=True, hide_index=True)

area = st.selectbox("Filter by governance area", ["All"] + sorted(df["Governance Area"].unique().tolist()))
if area != "All":
    st.dataframe(df[df["Governance Area"] == area], use_container_width=True, hide_index=True)
