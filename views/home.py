import streamlit as st
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
st.subheader("Saudi AI Ethics Principles")
for principle in (
    "Fairness — النزاهة والإنصاف",
    "Privacy & Security — الخصوصية والأمن",
    "Humanity — الإنسانية",
    "Social & Environmental Benefits — المنافع الاجتماعية والبيئية",
    "Reliability & Safety — الموثوقية والسلامة",
    "Transparency & Explainability — الشفافية وقابلية التفسير",
    "Accountability & Responsibility — المساءلة والمسؤولية",
):
    st.write(f"• {principle}")
st.caption("Source: SDAIA-P145, pp. 14–15. The separate SDAIA Framework Alignment page documents the ethics crosswalk and its evidence gaps.")
st.info("The eight-question screening is an illustrative intake aid. National matrix assessments and residual-risk decisions are separate records; neither a score nor a completed form establishes legal compliance or deployment approval.")
