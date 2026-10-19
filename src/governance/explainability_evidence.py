from datetime import date
import re
import unicodedata
from uuid import UUID


EXPLAINABILITY_EVIDENCE_FIELDS = (
    "evaluation_stage",
    "evaluation_status",
    "explanation_method",
    "method_description",
    "intended_audiences",
    "planned_context",
    "planned_feedback_collection",
    "examples",
    "human_review_approach",
    "challenge_correction_process",
    "accessibility_usefulness_reviews",
    "limitations",
    "outstanding_actions",
    "responsible_owner",
    "reviewer",
    "review_date",
)
EXPLAINABILITY_WIDGET_FIELDS = tuple(
    field for field in EXPLAINABILITY_EVIDENCE_FIELDS
    if field not in {"examples", "accessibility_usefulness_reviews"}
) + ("example_row_ids", "review_row_ids")
EXPLAINABILITY_WIDGET_KEYS = {
    field: f"trn01_explainability_{field}"
    for field in EXPLAINABILITY_WIDGET_FIELDS
}
EXPLAINABILITY_STAGES = ("Planned", "Performed")
EXPLAINABILITY_STATUSES = ("Draft", "Reviewed")

EXAMPLE_FIELDS = (
    "example_id",
    "decision_reference_id",
    "intended_audience",
    "input_factor_summary",
    "recommendation_output",
    "human_readable_explanation",
    "evidence_reference",
    "example_date",
    "human_review_findings_reference",
)
REVIEW_FIELDS = (
    "review_id",
    "intended_audience",
    "review_method",
    "findings_feedback_summary",
    "evidence_reference",
    "review_date",
    "limitations_corrective_actions",
)
EXAMPLE_WIDGET_DEFAULTS = {field: "" for field in EXAMPLE_FIELDS}
REVIEW_WIDGET_DEFAULTS = {field: "" for field in REVIEW_FIELDS}
EXAMPLE_WIDGET_DEFAULTS["example_id"] = None
REVIEW_WIDGET_DEFAULTS["review_id"] = None

_PLACEHOLDER_BASES = (
    "n a",
    "na",
    "tbd",
    "to be determined",
    "not available",
    "pending evidence",
    "placeholder",
    "test reference",
    "unknown",
)
_PLACEHOLDER_SUFFIXES = (
    "pending",
    "pending evidence",
    "pending review",
    "pending confirmation",
    "pending upload",
    "later",
    "yet",
    "not yet",
    "soon",
    "to be completed",
    "to be provided",
    "to be added",
    "to be confirmed",
    "to be determined",
    "to be filled in",
    "to be reviewed",
    "when available",
    "when known",
    "not completed",
    "not provided",
    "will be added",
    "will be provided",
    "awaiting evidence",
)


def explainability_row_widget_key(kind, row_id, field, generation=None):
    key = f"trn01_explainability_{kind}_{row_id}_{field}"
    return f"{key}_{generation}" if generation else key


def _meaningful(value):
    if not isinstance(value, str):
        return False
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"\bt[\W_]*b[\W_]*d\b", "tbd", normalized)
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    normalized = " ".join(normalized.replace("_", " ").split())
    if not normalized or len(normalized) <= 1:
        return False
    if normalized in _PLACEHOLDER_BASES:
        return False
    for placeholder in _PLACEHOLDER_BASES:
        prefix = f"{placeholder} "
        if normalized.startswith(prefix):
            suffix = normalized[len(prefix):]
            if any(
                suffix == item or suffix.startswith(f"{item} ")
                for item in _PLACEHOLDER_SUFFIXES
            ):
                return False
    return True


def _valid_date(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _valid_id(value):
    if not isinstance(value, str):
        return False
    try:
        return str(UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def _validate_row(record, index, kind, required_fields, date_fields):
    label = f"{kind} {index + 1}"
    if not isinstance(record, dict) or set(record) != set(required_fields):
        return [f"{label} must contain exactly the expected structured fields."]
    errors = []
    id_field = "example_id" if kind == "Example" else "review_id"
    optional_fields = {"human_review_findings_reference"} if kind == "Example" else set()
    if not _valid_id(record[id_field]):
        errors.append(f"{label} must have a valid stable {id_field.replace('_', ' ')}.")
    for field in required_fields:
        if field == id_field:
            continue
        if field in optional_fields and record[field] == "":
            continue
        if field in date_fields:
            if not _valid_date(record[field]):
                errors.append(f"{label} {field.replace('_', ' ')} must use YYYY-MM-DD.")
        elif not _meaningful(record[field]):
            errors.append(f"{label} {field.replace('_', ' ')} is required.")
    return errors


def validate_explainability_evidence(record):
    if not isinstance(record, dict):
        return ["Explainability evidence must be a field mapping."]
    if set(record) != set(EXPLAINABILITY_EVIDENCE_FIELDS):
        return ["Explainability evidence must contain exactly the expected fields."]
    errors = []
    for field in EXPLAINABILITY_EVIDENCE_FIELDS:
        expected = list if field in {
            "examples", "accessibility_usefulness_reviews"
        } else str
        if not isinstance(record[field], expected):
            errors.append(
                f"{field.replace('_', ' ').capitalize()} must be "
                f"{'a list' if expected is list else 'text'}."
            )
    if errors:
        return errors
    if record["evaluation_stage"] not in EXPLAINABILITY_STAGES:
        errors.append("Evaluation stage must be Planned or Performed.")
        return errors
    if record["evaluation_status"] not in EXPLAINABILITY_STATUSES:
        errors.append("Evaluation status must be Draft or Reviewed.")
    if record["review_date"].strip() and not _valid_date(record["review_date"]):
        errors.append("Review date must use valid YYYY-MM-DD format.")

    examples = record["examples"]
    reviews = record["accessibility_usefulness_reviews"]
    example_ids = []
    review_ids = []
    for index, example in enumerate(examples):
        errors.extend(_validate_row(
            example,
            index,
            "Example",
            EXAMPLE_FIELDS,
            {"example_date"},
        ))
        if isinstance(example, dict):
            example_ids.append(example.get("example_id"))
    for index, review in enumerate(reviews):
        errors.extend(_validate_row(
            review,
            index,
            "Accessibility/usefulness review",
            REVIEW_FIELDS,
            {"review_date"},
        ))
        if isinstance(review, dict):
            review_ids.append(review.get("review_id"))
    valid_example_ids = [value for value in example_ids if isinstance(value, str)]
    valid_review_ids = [value for value in review_ids if isinstance(value, str)]
    if len(valid_example_ids) != len(set(valid_example_ids)):
        errors.append("Example IDs must be unique.")
    if len(valid_review_ids) != len(set(valid_review_ids)):
        errors.append("Review IDs must be unique.")

    if record["evaluation_stage"] == "Planned":
        if examples or reviews:
            errors.append(
                "Planned documentation cannot contain performed examples or completed reviews."
            )
        if record["evaluation_status"] == "Reviewed":
            required = (
                "explanation_method",
                "method_description",
                "intended_audiences",
                "planned_context",
                "planned_feedback_collection",
                "human_review_approach",
                "challenge_correction_process",
                "limitations",
                "outstanding_actions",
                "responsible_owner",
                "reviewer",
            )
            for field in required:
                if not _meaningful(record[field]):
                    errors.append(
                        f"{field.replace('_', ' ').capitalize()} is required "
                        "for reviewed planned documentation."
                    )
            if not _valid_date(record["review_date"]):
                errors.append("Review date must use valid YYYY-MM-DD.")
    else:
        required = (
            "explanation_method",
            "method_description",
            "intended_audiences",
            "human_review_approach",
            "challenge_correction_process",
            "limitations",
            "outstanding_actions",
            "responsible_owner",
            "reviewer",
        )
        for field in required:
            if not _meaningful(record[field]):
                errors.append(
                    f"{field.replace('_', ' ').capitalize()} is required "
                    "for performed explainability documentation."
                )
        if not examples:
            errors.append("Performed documentation requires at least one example.")
        if not _valid_date(record["review_date"]):
            errors.append("Review date must use valid YYYY-MM-DD.")
    return errors
