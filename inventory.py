from pathlib import Path
import pandas as pd
import streamlit as st

st.title("AI Inventory")
path = Path(__file__).resolve().parents[1] / "data" / "ai_inventory.csv"
df = pd.read_csv(path)
st.dataframe(df, use_container_width=True, hide_index=True)
st.caption("In a real implementation this register would have controlled ownership, versioning, evidence links and lifecycle status.")
