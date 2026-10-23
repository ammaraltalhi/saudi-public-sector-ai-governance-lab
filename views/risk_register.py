import json
from uuid import uuid4

import streamlit as st

from src.governance.risk_register import TEXT_FIELDS, STATUSES, validate_register, score_record
from src.governance.saudi_risk_method import (
    METHOD_ID, CATEGORIES, TREATMENTS, RESIDUAL_BASES, LIKELIHOOD, IMPACT,
)

st.title("Risk Register & Treatment")
st.caption("Synthetic portfolio records. The national method implements the verified SDAIA-P145 v1 matrix (page 25), not framework-wide conformity. Residual values remain user estimates or reported reassessments, not proof of effectiveness or acceptance.")
if not st.session_state.get("use_case"):
    st.info("Save the AI Use Case Intake first.")
    st.stop()
records = st.session_state.get("risk_register", [])
errors = validate_register(records)
if errors:
    for error in errors:
        st.error(error)
    st.stop()
options = ["New risk"] + [record["risk_id"] for record in records]
generation = st.session_state.get("_case_load_generation", "initial")
selected = st.selectbox("Record", options, key=f"register_selection_{generation}")
existing = next((record for record in records if record["risk_id"] == selected), {})
legacy = "Illustrative (legacy)"
method = st.selectbox(
    "Assessment method", [METHOD_ID] if existing.get("methodology") == METHOD_ID else [METHOD_ID, legacy],
    index=0 if not existing or existing.get("methodology") == METHOD_ID else 1,
    key=f"risk_method_{generation}_{selected}",
)
if existing and "methodology" not in existing:
    st.info("This saved record is illustrative. To migrate, explicitly select the national method, review all ratings against its definitions, document the assessment basis, and save. Previous scores are not automatically reclassified.")
if method == METHOD_ID:
    st.caption("Likelihood: 1 Rare, 2 Unlikely, 3 Likely, 4 Almost certain (pp. 22–23). Impact: 1 Low, 2 Medium, 3 High, 4 Catastrophic (pp. 23–24). Use evidence and a defined time horizon; percentage ranges in the source are contextual references, not a required probability input.")
with st.form(f"risk_record_{generation}_{selected}_{method}"):
    record = {"risk_id": existing.get("risk_id", str(uuid4()))}
    for field in TEXT_FIELDS:
        if field == "risk_id":
            continue
        if field == "status":
            record[field] = st.selectbox("Status", STATUSES, index=STATUSES.index(existing.get(field, "Open")))
        else:
            record[field] = st.text_area(field.replace("_", " ").capitalize(), value=existing.get(field, ""))
    for field in ("likelihood", "impact", "residual_likelihood", "residual_impact"):
        record[field] = st.number_input(field.replace("_", " ").capitalize(), min_value=1, max_value=4, value=existing.get(field, 1), step=1)
        if method == METHOD_ID:
            labels = LIKELIHOOD if "likelihood" in field else IMPACT
            st.caption(" · ".join(f"{value}: {label}" for value, label in labels.items()))
    if method == METHOD_ID:
        record["methodology"] = METHOD_ID
        for field, choices in (("category", CATEGORIES), ("treatment_strategy", TREATMENTS), ("residual_basis", RESIDUAL_BASES)):
            value = existing.get(field, choices[0])
            record[field] = st.selectbox(field.replace("_", " ").capitalize(), choices, index=choices.index(value))
        for field in ("assessment_horizon", "likelihood_rationale", "impact_rationale", "residual_rationale", "assessment_evidence"):
            record[field] = st.text_area(field.replace("_", " ").capitalize(), value=existing.get(field, ""))
        st.caption("Document exposure, preventive controls, ease of occurrence or precedents for likelihood; harm, scope, sensitivity or recovery for impact. Explain catastrophic impact only in the extreme context defined on pp. 23–24. An Accept strategy is not an approval record.")
    st.caption("Dates: YYYY-MM-DD. Closing requires evidence, reviewer and review date. Save Case persists records to disk.")
    if st.form_submit_button("Save risk record"):
        updated = [item for item in records if item["risk_id"] != record["risk_id"]] + [record]
        errors = validate_register(updated)
        if errors:
            for error in errors:
                st.error(error)
        else:
            st.session_state["risk_register"] = updated
            st.rerun()
if records:
    st.dataframe([
        {**record, "methodology": record.get("methodology", legacy), **score_record(record)}
        for record in records
    ], use_container_width=True)
    st.download_button("Export risk register JSON", json.dumps(records, indent=2, ensure_ascii=False), "risk_register.json", "application/json")
