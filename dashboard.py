from pathlib import Path
import pandas as pd
import streamlit as st

st.title("Governance Dashboard")
path = Path(__file__).resolve().parents[1] / "data" / "ai_inventory.csv"
df = pd.read_csv(path)

c1, c2, c3, c4 = st.columns(4)
c1.metric("AI systems", len(df))
c2.metric("High risk", int((df["Risk Level"] == "High").sum()))
c3.metric("Awaiting approval", int(df["Status"].str.contains("Review|Approval", case=False, regex=True).sum()))
c4.metric("Live systems", int((df["Status"] == "Live").sum()))

st.subheader("Systems by risk level")
risk_counts = df["Risk Level"].value_counts().rename_axis("Risk Level").to_frame("Systems")
st.bar_chart(risk_counts)

st.subheader("Portfolio register")
st.dataframe(df[["AI System", "Business Owner", "Risk Level", "Status", "Next Review"]], use_container_width=True, hide_index=True)
