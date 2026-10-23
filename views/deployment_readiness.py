from copy import deepcopy
from pathlib import Path

import pandas as pd
import streamlit as st

from src.governance.case_persistence import DEFAULT_PLANS
from src.governance.control_assessment import (
    assess_control,
    has_complete_risk_answers,
)
from src.governance.constants import PRE_DEPLOYMENT_CONTROL_IDS
from src.governance.deployment_readiness import evaluate_readiness

st.title("Deployment Readiness")
st.write(
    "This is an illustrative governance workflow, not a legal compliance "
    "determination and not automatic deployment approval."
)

use_case = st.session_state.get("use_case")
risk_answers = st.session_state.get("risk_answers")
if not use_case or not has_complete_risk_answers(risk_answers):
    st.warning(
        "Complete the AI Use Case Intake and AI Risk Assessment before "
        "evaluating deployment readiness."
    )
    st.stop()

path = Path(__file__).resolve().parents[1] / "data" / "controls.csv"
catalogue = pd.read_csv(path)
explicit_evidence = st.session_state.get("control_evidence", {})
plans = st.session_state.setdefault(
    "deployment_readiness_plans",
    deepcopy(DEFAULT_PLANS),
)

st.subheader("Current AI use case")
st.write(f"**AI system name:** {use_case.get('name', 'Not specified')}")
st.write(f"**Risk score:** {st.session_state.get('risk_score')}")
st.write(f"**Governance tier:** {st.session_state.get('governance_tier')}")

assessments = {
    row["Control ID"]: assess_control(
        row["Control ID"],
        use_case,
        risk_answers,
        explicit_evidence,
        (path.parent / "ai_inventory.csv").exists(),
        (path.parent / "raci.csv").exists(),
    )
    for _, row in catalogue.iterrows()
}

st.subheader("Pre-deployment controls")
rows = []
for _, row in catalogue.iterrows():
    if row["Control ID"] not in PRE_DEPLOYMENT_CONTROL_IDS:
        continue
    assessment = assessments[row["Control ID"]]
    impact = (
        "Blocks readiness"
        if assessment["Applicability"] == "Required"
        and assessment["Evidence Status"] == "Pending"
        else "Does not block"
    )
    rows.append({
        "Control ID": row["Control ID"],
        "Control": row["Control"],
        "Applicability": assessment["Applicability"],
        "Evidence Status": assessment["Evidence Status"],
        "Readiness Impact": impact,
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.subheader("Operational readiness")
mon01_available = (
    assessments.get("MON-01", {}).get("Applicability") == "Required"
    and assessments.get("MON-01", {}).get("Evidence Status") == "Available"
)
inc01_available = (
    assessments.get("INC-01", {}).get("Applicability") == "Required"
    and assessments.get("INC-01", {}).get("Evidence Status") == "Available"
)
st.session_state["readiness_inc01_plan_approved"] = inc01_available
st.caption(
    "The first four monitoring requirements are derived from a complete, "
    "Reviewed MON-01 assessment. Incident response readiness is derived from "
    "a complete, Reviewed INC-01 plan."
)

st.checkbox(
    "Monitoring plan",
    value=mon01_available,
    disabled=True,
    key="readiness_mon01_plan_defined",
)
st.checkbox(
    "Metrics defined",
    value=mon01_available,
    disabled=True,
    key="readiness_mon01_metrics_defined",
)
st.checkbox(
    "Thresholds defined",
    value=mon01_available,
    disabled=True,
    key="readiness_mon01_thresholds_defined",
)
st.checkbox(
    "Responsibilities defined",
    value=mon01_available,
    disabled=True,
    key="readiness_mon01_responsibilities_defined",
)
st.checkbox(
    "Incident response and escalation plan approved",
    disabled=True,
    key="readiness_inc01_plan_approved",
)

st.subheader("Lifecycle")
st.write("**RET-01:** Lifecycle / Not Due — Does not block initial deployment readiness.")

readiness = evaluate_readiness(
    assessments, plans, has_complete_risk_answers(risk_answers),
    st.session_state.get("corrective_actions", []),
)
st.subheader("Readiness summary")
st.write(f"**Number of blocking controls:** {len(readiness['blocking_controls'])}")
st.write(
    f"**Number of incomplete operational requirements:** "
    f"{readiness['incomplete_operational_requirements']}"
)
st.write(f"**Open blocking corrective actions:** {len(readiness['blocking_actions'])}")
if readiness["blocking_actions"]:
    st.warning("Resolve and verify these actions: " + ", ".join(readiness["blocking_actions"]))
for error in readiness["action_errors"]:
    st.error(error)
st.caption("Action closure and readiness-impact choices are user-recorded attestations. They do not establish regulatory compliance or acceptance of residual risk.")
st.subheader(readiness["status"])
st.info("Final deployment approval remains a human governance decision.")
