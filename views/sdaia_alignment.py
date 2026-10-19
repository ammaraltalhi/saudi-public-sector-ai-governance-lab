import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.governance.fairness_evaluation import validate_fairness_evaluation
from src.governance.sdaia_impact import validate_impact_assessments
from src.governance.validation_evaluation import validate_validation_evaluation
from src.governance.explainability_evidence import validate_explainability_evidence


ROOT = Path(__file__).resolve().parents[1]
ALIGNMENT_PATH = ROOT / "data" / "sdaia_alignment.json"
CONTROLS_PATH = ROOT / "data" / "controls.csv"
EXPECTED_PRINCIPLES = {
    "Fairness",
    "Privacy & Security",
    "Humanity",
    "Social & Environmental Benefits",
    "Reliability & Safety",
    "Transparency & Explainability",
    "Accountability & Responsibility",
}


def load_alignment_data(alignment_path=ALIGNMENT_PATH, controls_path=CONTROLS_PATH):
    try:
        with alignment_path.open(encoding="utf-8") as alignment_file:
            alignment = json.load(alignment_file)
    except FileNotFoundError as error:
        raise ValueError("SDAIA alignment data file is missing.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("SDAIA alignment data file is not valid UTF-8 JSON.") from error
    except OSError as error:
        raise ValueError("SDAIA alignment data file cannot be read.") from error

    if not isinstance(alignment, dict) or alignment.get("schema_version") != 1:
        raise ValueError("SDAIA alignment data has an unsupported or invalid structure.")
    source = alignment.get("source")
    if not isinstance(source, dict) or not all(
        isinstance(source.get(field), str) and source[field].strip()
        for field in (
            "title", "publisher", "document_number", "version",
            "date", "url", "reference_note",
        )
    ):
        raise ValueError("SDAIA alignment data is missing required source details.")
    principles = alignment.get("principles")
    if not isinstance(principles, list):
        raise ValueError("SDAIA alignment data must contain a principles list.")
    names = [
        principle.get("name")
        for principle in principles
        if isinstance(principle, dict)
    ]
    if len(names) != len(principles) or any(
        not isinstance(name, str) for name in names
    ):
        raise ValueError("SDAIA alignment data contains an invalid principle entry.")
    if len(names) != len(set(names)):
        raise ValueError("SDAIA alignment data contains duplicate principles.")
    if set(names) != EXPECTED_PRINCIPLES:
        raise ValueError(
            "SDAIA alignment data must contain exactly the seven named principles."
        )

    required_fields = (
        "controls", "rationale", "references", "coverage", "gaps", "limitations",
    )
    for principle in principles:
        if any(field not in principle for field in required_fields):
            raise ValueError(
                f"SDAIA alignment data for {principle['name']} is incomplete."
            )
        if (
            not isinstance(principle["controls"], list)
            or not principle["controls"]
            or any(not isinstance(control_id, str) for control_id in principle["controls"])
            or any(
                not isinstance(principle[field], str) or not principle[field].strip()
                for field in ("rationale", "coverage", "gaps", "limitations")
            )
        ):
            raise ValueError(
                f"SDAIA alignment data for {principle['name']} has invalid fields."
            )
        references = principle["references"]
        if (
            not isinstance(references, dict)
            or not isinstance(references.get("principle"), str)
            or not isinstance(references.get("printed_pages"), list)
            or any(type(page) is not int for page in references["printed_pages"])
            or not isinstance(references.get("annexure_c"), list)
            or any(not isinstance(item, str) for item in references["annexure_c"])
        ):
            raise ValueError(
                f"SDAIA references for {principle['name']} have an invalid structure."
            )

    try:
        controls = pd.read_csv(controls_path)
    except FileNotFoundError as error:
        raise ValueError("Governance control catalogue is missing.") from error
    except (
        OSError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ) as error:
        raise ValueError("Governance control catalogue cannot be read.") from error
    if not {"Control ID", "Governance Area"} <= set(controls.columns):
        raise ValueError("Governance control catalogue is missing required columns.")
    control_areas = dict(zip(controls["Control ID"], controls["Governance Area"]))
    unknown_control_ids = sorted({
        control_id
        for principle in principles
        for control_id in principle["controls"]
        if control_id not in control_areas
    })
    if unknown_control_ids:
        raise ValueError(
            "SDAIA alignment data references unknown controls: "
            + ", ".join(unknown_control_ids)
        )
    return alignment, control_areas


try:
    alignment, control_areas = load_alignment_data()
except ValueError as error:
    st.error(f"Unable to display SDAIA Framework Alignment: {error}")
    st.stop()

st.title("SDAIA Framework Alignment")
st.caption(
    "Illustrative analytical crosswalk to SDAIA's AI Ethics Principles. "
    "This is not SDAIA certification, official conformity assessment, legal "
    "compliance, or deployment approval."
)

source = alignment["source"]
st.markdown(
    f"Source: [{source['title']} ({source['document_number']}, "
    f"Version {source['version']})]({source['url']}) — "
    f"{source['publisher']}, {source['date']}."
)
st.info(
    "This page maps documented governance coverage and known gaps. A mapped "
    "control, completed form, or Reviewed status is not proof that a practice "
    "was implemented, tested, or effective."
)
impact_assessments, invalid_impact_assessments = validate_impact_assessments(
    st.session_state.get("sdaia_impact_assessments", {})
)
saved_invalid = st.session_state.get(
    "_sdaia_impact_assessment_invalid", {}
)
if isinstance(saved_invalid, dict):
    invalid_impact_assessments.update(saved_invalid)
if "_root" in invalid_impact_assessments:
    invalid_impact_assessments = {
        assessment_type: invalid_impact_assessments["_root"]
        for assessment_type, _ in (
            ("humanity", "Humanity"),
            ("social_environmental", "Social & Environmental Benefits"),
        )
    }
st.markdown("### Principle-specific impact documentation")
st.caption(
    "Open the SDAIA Impact Assessment page from app navigation to create or "
    "review these records."
)
for assessment_type, principle in (
    ("humanity", "Humanity"),
    ("social_environmental", "Social & Environmental Benefits"),
):
    assessment = impact_assessments.get(assessment_type)
    st.markdown(f"**{principle}:**")
    invalid = invalid_impact_assessments.get(assessment_type)
    if invalid:
        st.caption(
            "Invalid — assessment record is excluded from canonical "
            "documentation status. Saved source data is retained. "
            + "; ".join(invalid.get("errors", ["Assessment data is invalid."]))
        )
        continue
    if assessment is None:
        st.caption("Missing — no saved assessment documentation.")
        continue
    status = assessment["assessment_status"]
    evidence_type = assessment["evidence_type"]
    st.caption(
        f"Assessment documentation saved ({status}); user-entered evidence "
        f"type: {evidence_type}. Reviewed is a user-recorded attestation, "
        "not independently verified evidence of implementation or effectiveness."
    )

st.markdown("### Supplementary FAI-01 fairness evaluation documentation")
control_evidence = st.session_state.get("control_evidence", {})
has_fai01_record = (
    isinstance(control_evidence, dict) and "FAI-01" in control_evidence
)
fai01_evidence = control_evidence.get("FAI-01") if has_fai01_record else None
has_fairness_evaluation = (
    isinstance(fai01_evidence, dict)
    and "fairness_evaluation" in fai01_evidence
)
if not has_fai01_record or (
    isinstance(fai01_evidence, dict) and not has_fairness_evaluation
):
    st.caption("Missing — no saved supplementary fairness evaluation.")
else:
    fairness_evaluation = (
        fai01_evidence.get("fairness_evaluation")
        if isinstance(fai01_evidence, dict)
        else fai01_evidence
    )
    fairness_errors = validate_fairness_evaluation(fairness_evaluation)
    if fairness_errors:
        st.caption(
            "Invalid — supplementary fairness evaluation is excluded from "
            "valid evaluation documentation. "
            + "; ".join(fairness_errors)
        )
    else:
        stage = fairness_evaluation["evaluation_stage"]
        status = fairness_evaluation["evaluation_status"]
        if stage == "Planned":
            st.caption(
                f"Saved evaluation design: Planned ({status}). No performed "
                "test results are recorded."
            )
        else:
            st.caption(
                f"Saved evaluation documentation: Performed ({status}); "
                "test results are user-reported and not independently verified "
                "for authenticity, implementation, or statistical validity."
            )

st.markdown("### Supplementary VAL-01 validation evaluation documentation")
control_evidence = st.session_state.get("control_evidence", {})
has_val01_record = (
    isinstance(control_evidence, dict) and "VAL-01" in control_evidence
)
val01_evidence = control_evidence.get("VAL-01") if has_val01_record else None
has_validation_evaluation = (
    isinstance(val01_evidence, dict)
    and "validation_evaluation" in val01_evidence
)
if not has_val01_record or (
    isinstance(val01_evidence, dict) and not has_validation_evaluation
):
    st.caption("Missing — no saved supplementary validation evaluation.")
else:
    validation_evaluation = (
        val01_evidence.get("validation_evaluation")
        if isinstance(val01_evidence, dict)
        else val01_evidence
    )
    validation_errors = validate_validation_evaluation(validation_evaluation)
    if validation_errors:
        st.caption(
            "Invalid — supplementary validation evaluation is excluded from "
            "valid evaluation documentation. "
            + "; ".join(validation_errors)
        )
    elif validation_evaluation["evaluation_stage"] == "Planned":
        st.caption(
            "Saved validation documentation: Planned "
            f"({validation_evaluation['evaluation_status']}). No measured "
            "validation results are recorded."
        )
    else:
        st.caption(
            "Saved validation documentation: Performed "
            f"({validation_evaluation['evaluation_status']}); results are "
            "user-reported and not independently verified for performance, "
            "safety, or compliance."
        )

st.markdown("### Supplementary TRN-01 explainability documentation")
control_evidence = st.session_state.get("control_evidence", {})
has_trn01_record = isinstance(control_evidence, dict) and "TRN-01" in control_evidence
trn01_evidence = control_evidence.get("TRN-01") if has_trn01_record else None
has_explainability_evidence = (
    isinstance(trn01_evidence, dict)
    and "explainability_evidence" in trn01_evidence
)
if not has_trn01_record or (
    isinstance(trn01_evidence, dict) and not has_explainability_evidence
):
    st.caption("Missing — no saved supplementary explainability documentation.")
else:
    explainability_evidence = (
        trn01_evidence.get("explainability_evidence")
        if isinstance(trn01_evidence, dict)
        else trn01_evidence
    )
    explainability_errors = validate_explainability_evidence(explainability_evidence)
    if explainability_errors:
        st.caption(
            "Invalid — supplementary explainability evidence is excluded from "
            "valid documentation status. "
            + "; ".join(explainability_errors)
        )
    elif explainability_evidence["evaluation_stage"] == "Planned":
        st.caption(
            "Saved explainability documentation: Planned "
            f"({explainability_evidence['evaluation_status']}); no performed "
            "examples or completed audience reviews are recorded."
        )
    else:
        st.caption(
            "Saved explainability documentation: Performed "
            f"({explainability_evidence['evaluation_status']}); examples are "
            "user-reported and not independently verified. Audience accessibility "
            "or usefulness is documented separately and is not inferred from examples."
        )

for principle in alignment["principles"]:
    st.subheader(principle["name"])
    labels = [
        f"{control_id} — {control_areas[control_id]}"
        for control_id in principle["controls"]
    ]
    st.caption("Related existing controls: " + "; ".join(labels))
    st.markdown(f"**Alignment rationale:** {principle['rationale']}")
    st.markdown(f"**Documented coverage:** {principle['coverage']}")
    st.markdown(f"**Known evidence gaps:** {principle['gaps']}")
    with st.expander(f"References and limitations — {principle['name']}"):
        references = principle["references"]
        checklist_ids = ", ".join(references["annexure_c"])
        pages = ", ".join(str(page) for page in references["printed_pages"])
        st.markdown(
            f"**Official principle:** {references['principle']} "
            f"(printed pages {pages})"
        )
        st.markdown(f"**Annexure C checklist IDs:** {checklist_ids}")
        st.markdown(f"**Limitations:** {principle['limitations']}")

st.caption(source["reference_note"])
