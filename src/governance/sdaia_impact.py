from datetime import date
from copy import deepcopy


COMMON_FIELDS = (
    "use_case",
    "affected_stakeholders",
    "adverse_outcomes",
    "oversight_or_remedy_mechanisms",
    "intended_benefits",
    "impact_indicators",
    "follow_up_responsibilities",
    "evidence_references",
    "evidence_type",
    "evidence_limitations",
    "responsible_owner",
    "reviewer",
    "review_date",
    "assessment_status",
)
HUMANITY_FIELDS = (
    "human_dignity_rights_choice_accessibility_culture",
)
SOCIAL_ENVIRONMENTAL_FIELDS = (
    "social_harms_mitigations",
    "environmental_applicability",
    "environmental_resource_impacts",
    "environmental_na_justification",
)
ASSESSMENT_FIELDS = {
    "humanity": COMMON_FIELDS + HUMANITY_FIELDS,
    "social_environmental": COMMON_FIELDS + SOCIAL_ENVIRONMENTAL_FIELDS,
}
EVIDENCE_TYPES = ("Planned", "Performed", "Operational")
ASSESSMENT_STATUSES = ("Draft", "Reviewed")
ASSESSMENT_TYPES = frozenset(ASSESSMENT_FIELDS)


def _is_placeholder(value):
    normalized = value.strip().casefold()
    return not normalized or normalized in {"tbd", "n/a", "na"} or len(normalized) == 1


def validate_impact_assessment(assessment, assessment_type):
    if assessment_type not in ASSESSMENT_FIELDS:
        return ["Unknown impact assessment type."]
    if not isinstance(assessment, dict):
        return ["Assessment must be a field mapping."]

    fields = ASSESSMENT_FIELDS[assessment_type]
    errors = []
    if set(assessment) != set(fields):
        errors.append("Assessment must contain exactly the expected fields.")
    for field in fields:
        value = assessment.get(field)
        if not isinstance(value, str):
            errors.append(f"{field} must be text.")

    if errors:
        return errors

    if assessment["assessment_status"] not in ASSESSMENT_STATUSES:
        errors.append("Assessment status must be Draft or Reviewed.")
    if assessment["evidence_type"] not in EVIDENCE_TYPES:
        errors.append("Evidence type must be Planned, Performed, or Operational.")

    if assessment["assessment_status"] == "Reviewed":
        required_fields = set(fields) - {"assessment_status"}
        if assessment_type == "social_environmental":
            required_fields -= {
                "environmental_resource_impacts",
                "environmental_na_justification",
            }
        for field in sorted(required_fields):
            if _is_placeholder(assessment[field]):
                label = field.replace("_", " ").capitalize()
                errors.append(f"{label} is required before review.")

        if assessment_type == "social_environmental":
            applicability = assessment["environmental_applicability"]
            if applicability == "Applicable":
                if _is_placeholder(assessment["environmental_resource_impacts"]):
                    errors.append(
                        "Environmental impacts are required when applicable."
                    )
            elif applicability == "Not Applicable":
                if _is_placeholder(assessment["environmental_na_justification"]):
                    errors.append(
                        "A reason is required when environmental impact is Not Applicable."
                    )
            else:
                errors.append(
                    "Environmental applicability must be Applicable or Not Applicable."
                )

        try:
            parsed_date = date.fromisoformat(assessment["review_date"])
            if parsed_date.isoformat() != assessment["review_date"]:
                raise ValueError
        except ValueError:
            errors.append(
                "Review date must be a valid date in YYYY-MM-DD format."
            )

    if assessment_type == "social_environmental" and assessment[
        "environmental_applicability"
    ] not in ("", "Applicable", "Not Applicable"):
        errors.append(
            "Environmental applicability must be Applicable or Not Applicable."
        )
    return errors


def validate_impact_assessments(assessments):
    """Separate valid canonical records from preserved invalid records.

    Reviewed-field checks reject only blank and obvious placeholder values; they
    do not evaluate the substantive quality or truth of governance evidence.
    """
    valid = {}
    invalid = {}
    if not isinstance(assessments, dict):
        return valid, {
            "_root": {
                "record": deepcopy(assessments),
                "errors": ["SDAIA impact assessments must be a field mapping."],
            }
        }

    for assessment_type, record in assessments.items():
        if assessment_type not in ASSESSMENT_TYPES:
            invalid[assessment_type] = {
                "record": deepcopy(record),
                "errors": ["Unknown impact assessment type."],
            }
            continue
        errors = validate_impact_assessment(record, assessment_type)
        if errors:
            invalid[assessment_type] = {
                "record": deepcopy(record),
                "errors": errors,
            }
        else:
            valid[assessment_type] = deepcopy(record)
    return valid, invalid
