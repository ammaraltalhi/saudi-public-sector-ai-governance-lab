import streamlit as st
from src.governance.framework import NIST_FUNCTIONS, PRINCIPLES
from src.governance.saudi_risk_method import STAGES, SOURCE_URL

st.title("Saudi Public Sector AI Governance Lab")
st.caption("Self-directed portfolio case study — simulated environment, not a live client implementation.")

st.markdown(
    """
This prototype demonstrates how an organisation could operationalise AI governance for a
simulated Saudi public-sector AI use case. It turns governance principles into practical
artefacts: an AI inventory, risk assessment, RACI accountability model, lifecycle gates,
controls, evidence requirements and monitoring.
"""
)

st.subheader("Primary risk workflow: Saudi National Framework")
st.markdown(f"[SDAIA-P145, version 1, April 2026]({SOURCE_URL}) — selected scoring and documentation components, not a complete conformity implementation.")
for stage, pages in STAGES:
    st.write(f"• {stage} (pp. {pages})")
st.caption("Use Saudi National Risk Method for definitions and the verified matrix. Risk Screening remains a separate illustrative intake aid; national per-risk assessment is recorded in Risk Register & Treatment.")
st.subheader("Complementary conceptual reference: NIST AI RMF")
cols = st.columns(4)
for col, (name, desc) in zip(cols, NIST_FUNCTIONS.items()):
    with col:
        st.markdown(f"**{name}**")
        st.write(desc)

st.subheader("Governance principles used in the case study")
for p in PRINCIPLES:
    st.write(f"• {p}")

st.info("Portfolio note: the risk-scoring method in this demo is an illustrative heuristic. It is not a legal classification or an official NIST/SDAIA scoring model.")
