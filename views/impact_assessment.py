from copy import deepcopy

import streamlit as st

from src.governance.sdaia_impact import (
    ASSESSMENT_FIELDS,
    ASSESSMENT_STATUSES,
    EVIDENCE_TYPES,
    validate_impact_assessment,
    validate_impact_assessments,
)


ASSESSMENT_LABELS = {
    "humanity": ("Humanity", "Human & Dignity Impact Assessment"),
    "social_environmental": (
        "Social & Environmental Benefits",
        "Social & Environmental Impact Assessment",
    ),
}
FIELD_LABELS = {
    "use_case": "Use case",
    "affected_stakeholders": "Affected stakeholder groups",
    "human_dignity_rights_choice_accessibility_culture": (
        "Potential effects on human dignity, rights, choice, accessibility, "
        "and Saudi cultural context"
    ),
    "adverse_outcomes": "Potential adverse outcomes",
    "oversight_or_remedy_mechanisms": (
        "Human oversight, correction, or remedy mechanisms"
    ),
    "intended_benefits": "Intended community or public-service benefits",
    "social_harms_mitigations": "Potential social harms and mitigation actions",
    "environmental_applicability": "Environmental/resource impacts",
    "environmental_resource_impacts": (
        "Potential environmental, resource, or energy impacts"
    ),
    "environmental_na_justification": (
        "Reason environmental impacts are Not Applicable"
    ),
    "impact_indicators": "Proposed impact indicators",
    "follow_up_responsibilities": "Follow-up responsibilities",
    "evidence_references": "Evidence references (do not include sensitive data)",
    "evidence_type": "Evidence type",
    "evidence_limitations": "Evidence limitations",
    "responsible_owner": "Responsible owner",
    "reviewer": "Reviewer",
    "review_date": "Review date (YYYY-MM-DD)",
    "assessment_status": "Assessment status",
}
TEXT_AREA_FIELDS = set(ASSESSMENT_FIELDS["humanity"]) | set(
    ASSESSMENT_FIELDS["social_environmental"]
)
TEXT_AREA_FIELDS -= {
    "use_case",
    "affected_stakeholders",
    "evidence_type",
    "responsible_owner",
    "reviewer",
    "review_date",
    "assessment_status",
    "environmental_applicability",
}


def _widget_key(assessment_type, field):
    generation = st.session_state.get("_case_load_generation")
    key = f"sdaia_impact_{assessment_type}_{field}"
    return f"{key}_{generation}" if generation else key


def _hydrate_form(assessment_type, saved_assessment, use_case):
    generation = st.session_state.get("_case_load_generation")
    hydration_key = f"_sdaia_impact_hydrated_{assessment_type}"
    if st.session_state.get(hydration_key) == generation:
        return

    defaults = {
        "use_case": use_case.get("name", ""),
        "affected_stakeholders": use_case.get("affected_people", ""),
        "responsible_owner": use_case.get("owner", ""),
        "evidence_type": "Planned",
        "environmental_applicability": "",
        "assessment_status": "Draft",
    }
    for field in ASSESSMENT_FIELDS[assessment_type]:
        value = saved_assessment.get(field, defaults.get(field, ""))
        if field == "assessment_status" and value not in ASSESSMENT_STATUSES:
            value = "Draft"
        elif field == "evidence_type" and value not in EVIDENCE_TYPES:
            value = "Planned"
        elif field == "environmental_applicability" and value not in (
            "",
            "Applicable",
            "Not Applicable",
        ):
            value = ""
        elif not isinstance(value, str):
            value = ""
        st.session_state[_widget_key(assessment_type, field)] = value
    st.session_state[hydration_key] = generation


def _render_assessment(assessment_type, saved_assessments, use_case):
    principle, title = ASSESSMENT_LABELS[assessment_type]
    st.subheader(title)
    saved = saved_assessments.get(assessment_type, {})
    if not isinstance(saved, dict):
        saved = {}
    _hydrate_form(assessment_type, saved, use_case)
    invalid_entry = st.session_state.get(
        "_sdaia_impact_assessment_invalid", {}
    ).get(assessment_type)
    if invalid_entry:
        st.warning(
            "The loaded assessment is Invalid and is excluded from canonical "
            "documentation status. Its saved source data is retained. "
            + "; ".join(invalid_entry["errors"])
        )

    with st.form(f"sdaia_impact_form_{assessment_type}"):
        values = {}
        for field in ASSESSMENT_FIELDS[assessment_type]:
            key = _widget_key(assessment_type, field)
            label = FIELD_LABELS[field]
            if field == "evidence_type":
                values[field] = st.selectbox(
                    label,
                    EVIDENCE_TYPES,
                    key=key,
                )
            elif field == "assessment_status":
                values[field] = st.selectbox(
                    label,
                    ASSESSMENT_STATUSES,
                    key=key,
                )
            elif field == "environmental_applicability":
                values[field] = st.selectbox(
                    label,
                    ["", "Applicable", "Not Applicable"],
                    format_func=lambda value: value or "Select applicability",
                    key=key,
                )
            elif field in TEXT_AREA_FIELDS:
                values[field] = st.text_area(label, key=key)
            else:
                values[field] = st.text_input(label, key=key)
        submitted = st.form_submit_button(
            f"Save {principle} Impact Assessment"
        )

    if submitted:
        errors = validate_impact_assessment(values, assessment_type)
        if errors:
            st.error(
                "Assessment was not saved:\n\n"
                + "\n".join(f"- {error}" for error in errors)
            )
        else:
            saved_assessments[assessment_type] = deepcopy(values)
            st.session_state["sdaia_impact_assessments"] = saved_assessments
            invalid = st.session_state.get(
                "_sdaia_impact_assessment_invalid", {}
            )
            invalid.pop(assessment_type, None)
            st.session_state["_sdaia_impact_assessment_invalid"] = invalid
            st.success(
                f"{principle} assessment saved as "
                f"{values['assessment_status']} documentation."
            )


st.title("SDAIA Impact Assessment")
st.caption(
    "Illustrative documentation for the Humanity and Social & Environmental "
    "Benefits principles. Use synthetic information only; do not enter real "
    "citizen personal data, confidential details, or actual incident records."
)
st.warning(
    "A planned activity is not work performed. Evidence type is user-entered "
    "and not independently verified. Do not invent stakeholder consultation, "
    "test results, environmental measurements, or approvals. A Reviewed "
    "assessment is a documentation status, not implementation evidence or "
    "SDAIA conformity."
)
st.info(
    "Use Save Case in the sidebar after saving an assessment to persist it "
    "locally and make it available after restarting the application."
)

use_case = st.session_state.get("use_case", {})
if not isinstance(use_case, dict):
    use_case = {}
saved_assessments = st.session_state.setdefault(
    "sdaia_impact_assessments",
    {},
)
valid_assessments, invalid_assessments = validate_impact_assessments(
    saved_assessments
)
if invalid_assessments:
    previous_invalid = st.session_state.get(
        "_sdaia_impact_assessment_invalid", {}
    )
    invalid_assessments.update(previous_invalid)
    st.session_state["_sdaia_impact_assessment_invalid"] = invalid_assessments
    st.warning(
        "One or more loaded SDAIA impact assessments are Invalid and will not "
        "be treated as reviewed documentation. Save a corrected assessment "
        "explicitly to replace its invalid record."
    )
saved_assessments = valid_assessments
st.session_state["sdaia_impact_assessments"] = saved_assessments

_render_assessment("humanity", saved_assessments, use_case)
_render_assessment("social_environmental", saved_assessments, use_case)
