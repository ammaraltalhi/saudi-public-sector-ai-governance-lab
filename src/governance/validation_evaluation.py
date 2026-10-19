from datetime import date
import math
import re


VALIDATION_EVALUATION_FIELDS = (
    "evaluation_stage",
    "evaluation_status",
    "dataset_source",
    "dataset_purpose",
    "dataset_population",
    "dataset_scope",
    "dataset_timeframe",
    "dataset_limitations",
    "validation_method",
    "test_objectives",
    "human_oversight_testing",
    "human_oversight_observations",
    "validation_outcome",
    "limitations",
    "outstanding_actions",
    "responsible_owner",
    "reviewer",
    "review_date",
    "metrics",
    "results",
)
VALIDATION_EVALUATION_WIDGET_FIELDS = tuple(
    field for field in VALIDATION_EVALUATION_FIELDS
    if field not in {"metrics", "results"}
) + ("metric_row_count", "result_row_count")
VALIDATION_EVALUATION_WIDGET_KEYS = {
    field: f"val01_evaluation_{field}"
    for field in VALIDATION_EVALUATION_WIDGET_FIELDS
}
VALIDATION_STAGES = ("Planned", "Performed")
VALIDATION_STATUSES = ("Draft", "Reviewed")
VALIDATION_METRIC_SCALES = (
    "unbounded",
    "percentage_0_100",
    "proportion_0_1",
)
VALIDATION_COMPARATORS = ("<", "<=", ">", ">=", "==")
HUMAN_REVIEW_COMPARATOR = "Human review required"
_OVERALL_PASS_FAIL_CLAIM = re.compile(
    r"\b(?:pass(?:ed|es)?|fail(?:ed|s|ure)?)\b",
    flags=re.IGNORECASE,
)

_TEXT_FIELDS = frozenset(
    field for field in VALIDATION_EVALUATION_FIELDS
    if field not in {"metrics", "results"}
)
_PLACEHOLDERS = {"tbd", "n/a", "na"}


def validation_row_widget_key(kind, index, field, generation=None):
    key = f"val01_evaluation_{kind}_{index}_{field}"
    return f"{key}_{generation}" if generation else key


def _meaningful(value):
    if not isinstance(value, str):
        return False
    normalized = value.strip().casefold()
    return bool(normalized) and normalized not in _PLACEHOLDERS and len(normalized) > 1


def _finite_number(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _valid_date(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _unit_matches_scale(unit, scale):
    if not isinstance(unit, str):
        return False
    normalized = unit.strip().casefold()
    bounded_units = {
        "percentage_0_100": {"%", "percent", "percentage", "percentage points"},
        "proportion_0_1": {"proportion", "fraction", "0-1 proportion"},
    }
    if scale == "unbounded":
        return normalized not in set().union(*bounded_units.values())
    return normalized in bounded_units.get(scale, set())


def _within_scale(value, scale):
    if scale == "percentage_0_100":
        return 0 <= value <= 100
    if scale == "proportion_0_1":
        return 0 <= value <= 1
    return True


def _validate_metric(metric, index):
    errors = []
    label = f"Metric {index + 1}"
    expected = {
        "metric_id",
        "metric_name",
        "definition",
        "unit",
        "scale",
        "threshold_comparator",
        "threshold_value",
        "threshold_rationale",
    }
    if not isinstance(metric, dict):
        return [f"{label} must be a structured object."]
    if set(metric) != expected:
        return [f"{label} has missing or unsupported fields."]
    for field in ("metric_id", "metric_name", "definition", "unit", "threshold_rationale"):
        if not _meaningful(metric[field]):
            errors.append(f"{label} {field.replace('_', ' ')} is required.")
    if metric["scale"] not in VALIDATION_METRIC_SCALES:
        errors.append(f"{label} has an invalid declared scale.")
    elif not _unit_matches_scale(metric["unit"], metric["scale"]):
        errors.append(f"{label} unit does not match its declared scale.")
    if metric["threshold_comparator"] == HUMAN_REVIEW_COMPARATOR:
        if metric["threshold_value"] is not None:
            errors.append(
                f"{label} must not include a numeric threshold when human review is required."
            )
    elif metric["threshold_comparator"] not in VALIDATION_COMPARATORS:
        errors.append(f"{label} has an invalid threshold comparator.")
    elif not _finite_number(metric["threshold_value"]):
        errors.append(f"{label} planned threshold must be a finite number.")
    elif metric["scale"] in VALIDATION_METRIC_SCALES and not _within_scale(
        metric["threshold_value"], metric["scale"]
    ):
        errors.append(f"{label} threshold is outside its declared scale.")
    return errors


def _validate_result(result, index, metrics_by_id):
    errors = []
    label = f"Result {index + 1}"
    expected = {
        "metric_id",
        "measured_value",
        "unit",
        "scale",
        "sample_size",
        "test_date",
        "evidence_reference",
    }
    if not isinstance(result, dict):
        return [f"{label} must be a structured object."]
    if set(result) != expected:
        return [f"{label} has missing or unsupported fields."]
    metric_id = result["metric_id"]
    if not _meaningful(metric_id):
        errors.append(f"{label} metric ID is required.")
        metric = None
    else:
        metric = metrics_by_id.get(metric_id)
        if metric is None:
            errors.append(f"{label} refers to an unknown metric ID.")
    if not _finite_number(result["measured_value"]):
        errors.append(f"{label} measured value must be a finite number.")
    if metric is not None:
        if result["unit"] != metric["unit"]:
            errors.append(f"{label} unit must match its identified metric.")
        if result["scale"] != metric["scale"]:
            errors.append(f"{label} scale must match its identified metric.")
        if _finite_number(result["measured_value"]) and not _within_scale(
            result["measured_value"], metric["scale"]
        ):
            errors.append(f"{label} measured value is outside its metric scale.")
    elif result["scale"] not in VALIDATION_METRIC_SCALES:
        errors.append(f"{label} has an invalid declared scale.")
    if result["sample_size"] is not None and (
        type(result["sample_size"]) is not int or result["sample_size"] <= 0
    ):
        errors.append(f"{label} sample size must be a positive integer when supplied.")
    if not _valid_date(result["test_date"]):
        errors.append(f"{label} test date must use valid YYYY-MM-DD format.")
    if not _meaningful(result["evidence_reference"]):
        errors.append(f"{label} evidence reference is required.")
    return errors


def validate_validation_evaluation(record):
    if not isinstance(record, dict):
        return ["Validation evaluation must be a field mapping."]
    errors = []
    if set(record) != set(VALIDATION_EVALUATION_FIELDS):
        errors.append("Validation evaluation must contain exactly the expected fields.")
    for field in VALIDATION_EVALUATION_FIELDS:
        expected = list if field in {"metrics", "results"} else str
        if not isinstance(record.get(field), expected):
            errors.append(f"{field.replace('_', ' ').capitalize()} must be {'a list' if expected is list else 'text'}.")
    if errors:
        return errors

    if record["evaluation_stage"] not in VALIDATION_STAGES:
        errors.append("Evaluation stage must be Planned or Performed.")
        return errors
    if record["evaluation_status"] not in VALIDATION_STATUSES:
        errors.append("Evaluation status must be Draft or Reviewed.")
    if _OVERALL_PASS_FAIL_CLAIM.search(record["validation_outcome"]):
        errors.append(
            "Validation outcome must use neutral documentation wording; "
            "overall Passed/Failed claims are not supported."
        )

    metrics_by_id = {}
    for index, metric in enumerate(record["metrics"]):
        errors.extend(_validate_metric(metric, index))
        if isinstance(metric, dict) and _meaningful(metric.get("metric_id")):
            metric_id = metric["metric_id"]
            if metric_id in metrics_by_id:
                errors.append(f"Metric ID '{metric_id}' must be unique.")
            else:
                metrics_by_id[metric_id] = metric
    for index, result in enumerate(record["results"]):
        errors.extend(_validate_result(result, index, metrics_by_id))

    if record["review_date"].strip() and not _valid_date(record["review_date"]):
        errors.append("Review date must use valid YYYY-MM-DD format.")

    if record["evaluation_stage"] == "Planned":
        if record["results"] or record["validation_outcome"].strip():
            errors.append(
                "Planned evaluations cannot contain measured results or a performed outcome."
            )
        if record["evaluation_status"] == "Reviewed":
            required = (
                "dataset_source",
                "dataset_purpose",
                "dataset_population",
                "dataset_scope",
                "dataset_timeframe",
                "dataset_limitations",
                "validation_method",
                "test_objectives",
                "human_oversight_testing",
                "human_oversight_observations",
                "limitations",
                "outstanding_actions",
                "responsible_owner",
                "reviewer",
            )
            for field in required:
                if not _meaningful(record[field]):
                    errors.append(f"{field.replace('_', ' ').capitalize()} is required before review.")
            if not record["metrics"]:
                errors.append("At least one metric is required before review.")
            if not _valid_date(record["review_date"]):
                errors.append("Review date must use valid YYYY-MM-DD format.")
    else:
        required = (
            "dataset_source",
            "dataset_purpose",
            "dataset_population",
            "dataset_scope",
            "dataset_timeframe",
            "dataset_limitations",
            "validation_method",
            "test_objectives",
            "human_oversight_testing",
            "human_oversight_observations",
            "validation_outcome",
            "limitations",
            "outstanding_actions",
            "responsible_owner",
            "reviewer",
        )
        for field in required:
            if not _meaningful(record[field]):
                errors.append(f"{field.replace('_', ' ').capitalize()} is required for performed validation.")
        if not record["metrics"]:
            errors.append("At least one metric is required for performed validation.")
        if not record["results"]:
            errors.append("At least one measured result is required for performed validation.")
        result_metric_ids = {
            result.get("metric_id")
            for result in record["results"]
            if isinstance(result, dict)
        }
        for metric_id in metrics_by_id:
            if metric_id not in result_metric_ids:
                errors.append(f"Performed validation is missing a result for metric '{metric_id}'.")
        if not _valid_date(record["review_date"]):
            errors.append("Review date must use valid YYYY-MM-DD format.")
    return errors


def metric_comparison_status(metric, result):
    """Compare one documented result with its own numeric threshold only."""
    if not isinstance(metric, dict) or not isinstance(result, dict):
        return "Not evaluated"
    if (
        result.get("unit") != metric.get("unit")
        or result.get("scale") != metric.get("scale")
        or metric.get("scale") not in VALIDATION_METRIC_SCALES
        or not _finite_number(result.get("measured_value"))
        or not _within_scale(result["measured_value"], metric["scale"])
    ):
        return "Not evaluated"
    comparator = metric.get("threshold_comparator")
    threshold = metric.get("threshold_value")
    if comparator == HUMAN_REVIEW_COMPARATOR:
        return "Requires human review"
    if (
        comparator not in VALIDATION_COMPARATORS
        or not _finite_number(threshold)
        or not _within_scale(threshold, metric["scale"])
    ):
        return "Requires human review"
    value = result["measured_value"]
    comparisons = {
        "<": value < threshold,
        "<=": value <= threshold,
        ">": value > threshold,
        ">=": value >= threshold,
        "==": value == threshold,
    }
    return "Threshold met" if comparisons[comparator] else "Threshold not met"


def validation_evaluation_from_form(values):
    record = {
        field: values[field]
        for field in VALIDATION_EVALUATION_FIELDS
        if field not in {"metrics", "results"}
    }
    record["metrics"] = [
        {
            "metric_id": row["metric_id"],
            "metric_name": row["metric_name"],
            "definition": row["definition"],
            "unit": row["unit"],
            "scale": row["scale"],
            "threshold_comparator": row["threshold_comparator"],
            "threshold_value": row["threshold_value"],
            "threshold_rationale": row["threshold_rationale"],
        }
        for row in values["metric_rows"]
    ]
    results = []
    for row in values["result_rows"]:
        sample_size = row["sample_size"]
        if sample_size == "":
            sample_size = None
        else:
            try:
                sample_size = int(sample_size)
            except (TypeError, ValueError):
                pass
        results.append({
            "metric_id": row["metric_id"],
            "measured_value": row["measured_value"],
            "unit": row["unit"],
            "scale": row["scale"],
            "sample_size": sample_size,
            "test_date": row["test_date"],
            "evidence_reference": row["evidence_reference"],
        })
    record["results"] = results
    return record
