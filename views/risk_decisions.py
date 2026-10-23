import json
from datetime import date

import streamlit as st

from src.governance.risk_register import validate_register, score_record
from src.governance.risk_decisions import DECISIONS, fingerprint, validate_decisions, review_blockers
from src.governance.saudi_risk_method import METHOD_ID

st.title("Residual Risk Decisions")
st.caption("Document the human decision after reassessment (SDAIA-P145, p. 27). A record here is a user attestation, not authenticated sign-off, legal compliance or final deployment approval.")
use_case = st.session_state.get("use_case", {})
risks = st.session_state.get("risk_register", [])
errors = validate_register(risks)
if errors:
    for error in errors:
        st.error(error)
    st.stop()
if not use_case or not risks:
    st.info("Complete the use-case intake and a national risk record first.")
    st.stop()
decisions = st.session_state.get("risk_decisions", {})
errors = validate_decisions(decisions, {risk["risk_id"] for risk in risks})
if errors:
    for error in errors:
        st.error(error)
    st.stop()
generation = st.session_state.get("_case_load_generation", "initial")
risk_id = st.selectbox("Risk to review", [risk["risk_id"] for risk in risks], key=f"decision_risk_{generation}")
risk = next(risk for risk in risks if risk["risk_id"] == risk_id)
st.write(risk["description"])
st.json(score_record(risk))
if risk.get("methodology") != METHOD_ID:
    st.warning("This is a legacy illustrative record. Review and resave it using the national method first.")
    st.stop()
if risk["residual_basis"] != "Post-treatment reassessment":
    st.warning("A planned residual estimate cannot support an acceptance record. Complete and document post-treatment reassessment first.")
    st.stop()
existing = decisions.get(risk_id, {})
st.caption("Document the approved tolerance reference and authorized decision-maker. The app does not invent a tolerance threshold or assume that low scores are acceptable.")
with st.form(f"decision_{generation}_{risk_id}_{fingerprint(risk)}_{fingerprint(use_case)}"):
    record = {
        "risk_id": risk_id,
        "risk_fingerprint": fingerprint(risk),
        "context_fingerprint": fingerprint(use_case),
    }
    record["decision"] = st.selectbox("Decision", DECISIONS, index=DECISIONS.index(existing.get("decision", "Escalate")))
    for field in ("authority", "decision_date", "tolerance_reference", "rationale", "evidence", "next_review_date"):
        record[field] = st.text_area(field.replace("_", " ").capitalize(), value=existing.get(field, ""))
    if st.form_submit_button("Record residual-risk decision"):
        updated = {**decisions, risk_id: record}
        errors = validate_decisions(updated, {risk["risk_id"] for risk in risks})
        if not errors and record["decision_date"] > date.today().isoformat():
            errors.append("A completed decision cannot have a future decision date.")
        if not errors and record["next_review_date"] <= date.today().isoformat():
            errors.append("Set a next review date after today.")
        if errors:
            for error in errors:
                st.error(error)
        else:
            st.session_state["risk_decisions"] = updated
            st.rerun()
blockers = review_blockers(risks, decisions, use_case)
for blocker in blockers:
    st.warning(blocker)
if not blockers:
    st.success("Current risk-decision records satisfy this prototype's review gate. Other controls and actions may still block readiness.")
if decisions:
    st.download_button("Export risk decisions", json.dumps(decisions, indent=2, ensure_ascii=False), "risk_decisions.json", "application/json")
st.caption("Changes to a risk or its use-case context invalidate the previous decision for readiness. Save Case persists decision records; retain supporting review evidence separately.")
