from pathlib import Path

import pandas as pd
import streamlit as st

from src.governance.control_assessment import (
    assess_control,
    has_complete_risk_answers,
)
from src.governance.deployment_readiness import evaluate_readiness


def _status_style(value):
    if value in ("Available", "Complete"):
        return "color: #14532d; background-color: #dcfce7; font-weight: 600"
    if value in ("Pending", "Incomplete"):
        return "color: #78350f; background-color: #fef3c7; font-weight: 600"
    if value == "Not Due":
        return "color: #334155; background-color: #e2e8f0; font-weight: 600"
    return ""


st.markdown(
    """
    <style>
    .stMainBlockContainer {
        max-width: 1160px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    [data-testid="stMetric"] {
        min-height: 7rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Executive Governance Dashboard")
st.caption(
    "Illustrative portfolio governance prototype; this is not a legal "
    "compliance determination, certification, or automatic deployment approval."
)

use_case = st.session_state.get("use_case")
risk_answers = st.session_state.get("risk_answers")
risk_result = st.session_state.get("risk_result")
if not isinstance(use_case, dict) or not use_case:
    st.info("Load or complete an AI use case to view its governance overview.")
    st.stop()

risk_answers_complete = has_complete_risk_answers(risk_answers)
if not risk_answers_complete:
    st.warning("Complete the AI Risk Assessment to evaluate controls and readiness.")

st.subheader("AI Use Case Summary")
with st.container(border=True):
    st.markdown(f"### {use_case.get('name') or 'AI system not specified'}")
    st.markdown(f"**Business owner:** {use_case.get('owner') or 'Not specified'}")
    st.markdown(f"**Intended purpose:** {use_case.get('purpose') or 'Not specified'}")
    summary_columns = st.columns(2)
    summary_columns[0].markdown(
        f"**AI role in decision-making:** "
        f"{use_case.get('ai_role') or 'Not specified'}"
    )
    summary_columns[1].markdown(
        f"**Human oversight:** "
        f"{use_case.get('human_oversight') or 'Not specified'}"
    )

path = Path(__file__).resolve().parents[1] / "data" / "controls.csv"
catalogue = pd.read_csv(path)
explicit_evidence = st.session_state.get("control_evidence", {})
if not isinstance(explicit_evidence, dict):
    explicit_evidence = {}
inventory_available = (path.parent / "ai_inventory.csv").exists()
raci_available = (path.parent / "raci.csv").exists()

control_assessments = {}
if risk_answers_complete:
    control_assessments = {
        row["Control ID"]: assess_control(
            row["Control ID"],
            use_case,
            risk_answers,
            explicit_evidence,
            inventory_available,
            raci_available,
        )
        for _, row in catalogue.iterrows()
    }
    assessment_table = catalogue[["Control ID", "Governance Area"]].copy()
    assessment_table["Applicability"] = [
        control_assessments[control_id]["Applicability"]
        for control_id in assessment_table["Control ID"]
    ]
    assessment_table["Evidence Status"] = [
        control_assessments[control_id]["Evidence Status"]
        for control_id in assessment_table["Control ID"]
    ]
    required_count = int((assessment_table["Applicability"] == "Required").sum())
    available_count = int((assessment_table["Evidence Status"] == "Available").sum())
    pending_count = int((assessment_table["Evidence Status"] == "Pending").sum())
    lifecycle_count = int(
        (
            (assessment_table["Applicability"] == "Lifecycle")
            | (assessment_table["Evidence Status"] == "Not Due")
        ).sum()
    )
else:
    assessment_table = pd.DataFrame(
        columns=["Control ID", "Governance Area", "Applicability", "Evidence Status"]
    )
    required_count = available_count = pending_count = lifecycle_count = "Not evaluated"

st.subheader("Executive Snapshot")
metric_row_one = st.columns(3)
if risk_result is not None:
    risk_score = risk_result.score
    risk_tier = risk_result.level
    breakdown = st.session_state.get("risk_breakdown")
    triggered_factors = (
        len(breakdown) if isinstance(breakdown, list) else "Not calculated"
    )
else:
    risk_score = risk_tier = triggered_factors = "Not calculated"

for column, label, value in zip(
    metric_row_one,
    ("Risk Score", "Governance Tier", "Required Controls"),
    (risk_score, risk_tier, required_count),
):
    with column:
        with st.container(border=True):
            st.metric(label, value)

metric_row_two = st.columns(2)
for column, label, value in zip(
    metric_row_two,
    ("Evidence Available", "Pending Controls"),
    (available_count, pending_count),
):
    with column:
        with st.container(border=True):
            st.metric(label, value)
st.caption(f"Triggered risk factors: {triggered_factors}")

st.subheader("Deployment Readiness")
readiness = (
    evaluate_readiness(
        control_assessments,
        st.session_state.get("deployment_readiness_plans", {}),
        risk_answers_complete,
        st.session_state.get("corrective_actions", []),
    )
    if risk_answers_complete
    else None
)
with st.container(border=True):
    if readiness is None:
        st.warning(
            "Readiness is not evaluated until the risk assessment is complete."
        )
        blocking_count = incomplete_requirements = "Not evaluated"
    else:
        if readiness["status"] == "Ready for Deployment Approval":
            st.success(readiness["status"])
        else:
            st.warning(readiness["status"])
        blocking_count = len(readiness["blocking_controls"])
        incomplete_requirements = readiness["incomplete_operational_requirements"]

    readiness_columns = st.columns(2)
    readiness_columns[0].metric("Blocking controls", blocking_count)
    readiness_columns[1].metric(
        "Incomplete operational requirements",
        incomplete_requirements,
    )
    st.info("Final deployment approval remains a human governance decision.")

st.subheader("Governance Controls")
styled_assessment_table = assessment_table.style.map(
    _status_style,
    subset=["Evidence Status"],
)
st.dataframe(styled_assessment_table, width="stretch", hide_index=True)
st.caption(
    f"Required: {required_count}  ·  Available: {available_count}  ·  "
    f"Pending: {pending_count}  ·  Lifecycle / Not Due: {lifecycle_count}"
)

st.subheader("Operational Readiness")
monitoring_available = (
    control_assessments.get("MON-01", {}).get("Applicability") == "Required"
    and control_assessments.get("MON-01", {}).get("Evidence Status") == "Available"
)
incident_available = (
    control_assessments.get("INC-01", {}).get("Applicability") == "Required"
    and control_assessments.get("INC-01", {}).get("Evidence Status") == "Available"
)
operational_requirements = (
    ("Monitoring plan", monitoring_available),
    ("Metrics defined", monitoring_available),
    ("Thresholds defined", monitoring_available),
    ("Responsibilities defined", monitoring_available),
    ("Incident response and escalation plan", incident_available),
)
operational_table = pd.DataFrame(
    [
        {
            "Operational requirement": label,
            "Status": "Complete" if complete else "Incomplete",
        }
        for label, complete in operational_requirements
    ]
)
st.dataframe(
    operational_table.style.map(_status_style, subset=["Status"]),
    width="stretch",
    hide_index=True,
)

st.subheader("Outstanding Governance Actions")
actions = []
lifecycle_actions = []
if risk_answers_complete:
    for control_id, assessment in control_assessments.items():
        if (
            assessment["Applicability"] == "Required"
            and assessment["Evidence Status"] == "Pending"
        ):
            actions.append(
                f"{control_id}: required control evidence is Pending."
            )
    if readiness:
        if not monitoring_available:
            actions.extend(
                f"{label}: complete, review, and explicitly save MON-01."
                for label, complete in operational_requirements[:4]
                if not complete
            )
        if not incident_available:
            actions.append(
                "Incident response and escalation plan: complete, review, "
                "and explicitly save INC-01."
            )
    if readiness:
        actions.extend(f"{action_id}: corrective action requires verified closure." for action_id in readiness["blocking_actions"])
        actions.extend(readiness["action_errors"])
    lifecycle = control_assessments.get("RET-01")
    if lifecycle and lifecycle["Applicability"] == "Lifecycle":
        lifecycle_actions.append(
            "RET-01: address lifecycle planning at retirement or a relevant "
            "review/trigger event; it is not due for initial deployment readiness."
        )

if actions:
    st.dataframe(
        pd.DataFrame({"Current blockers and actions": actions}),
        width="stretch",
        hide_index=True,
    )
elif (
    readiness is not None
    and not readiness["blocking_controls"]
    and readiness["incomplete_operational_requirements"] == 0
    and not readiness["blocking_actions"]
    and not readiness["action_errors"]
):
    st.success(
        "No current governance-readiness blockers are identified. This is not "
        "a legal compliance, certification, or production-approval determination."
    )
elif readiness is None:
    st.info("Outstanding actions will be shown after risk assessment is complete.")

if lifecycle_actions:
    with st.container(border=True):
        st.markdown("**Lifecycle follow-up — not a current readiness blocker**")
        st.dataframe(
            pd.DataFrame({"Lifecycle follow-up": lifecycle_actions}),
            width="stretch",
            hide_index=True,
        )
