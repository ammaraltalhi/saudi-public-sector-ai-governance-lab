import pandas as pd
import streamlit as st

from src.governance.saudi_risk_method import (
    SOURCE_URL, METHOD_ID, LIKELIHOOD, IMPACT, CATEGORIES, TREATMENTS, STAGES, matrix_result,
)

st.title("Saudi National Risk Method")
st.markdown(f"Source: [الإطار الوطني لإدارة مخاطر الذكاء الاصطناعي]({SOURCE_URL}), SDAIA-P145, version 1, April 2026. Method ID: `{METHOD_ID}`.")
st.caption("Verified against the supplied 48-page Arabic publication, including visual checks of the page-25 matrix. English labels are project translations. This prototype implements selected documentary and scoring components; it is not a conformity assessment.")
st.subheader("National risk-management workflow")
st.table(pd.DataFrame(STAGES, columns=["Stage", "Printed source pages"]))
st.caption("The four reference pillars (pp. 14–16) are general principles, AI regulations, data regulations and sector regulations. Each source still needs an applicability and evidence assessment.")
st.subheader("Likelihood × impact matrix — page 25")
st.table(pd.DataFrame([
    [f"{matrix_result(likelihood, impact)['score']} — {matrix_result(likelihood, impact)['level']}" for impact in IMPACT]
    for likelihood in reversed(LIKELIHOOD)
], index=[f"{value}: {LIKELIHOOD[value]}" for value in reversed(LIKELIHOOD)], columns=[f"{value}: {IMPACT[value]}" for value in IMPACT]))
st.write("Low: 1–2 · Medium: 3–6 · High: 8–12 · Catastrophic: 16. With integer inputs 1–4, scores 5, 7, 10, 11 and 13–15 cannot occur.")
st.info("The eight-question Risk Screening remains an illustrative intake aid. It is separate from the national per-risk matrix. Existing records retain their methodology until explicitly reviewed and resaved.")
st.subheader("Risk identification categories — pages 18–20")
for category in CATEGORIES:
    st.write(f"• {category}")
st.subheader("Treatment — pages 26–27")
st.write(" · ".join(TREATMENTS))
st.caption("Transfer does not remove entity accountability. Residual risk must be reassessed using the same method; acceptance or escalation depends on approved risk tolerance and governance decisions, not the product score alone. This app does not authenticate approvals or automatically accept risk.")
