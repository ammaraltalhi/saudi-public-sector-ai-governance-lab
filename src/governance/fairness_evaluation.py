from datetime import date
import math


FAIRNESS_EVALUATION_FIELDS = (
    "evaluation_stage",
    "evaluation_status",
    "groups_and_selection_basis",
    "dataset_source",
    "dataset_scope",
    "dataset_population",
    "dataset_timeframe",
    "dataset_representativeness_limitations",
    "metric_name",
    "metric_definition",
    "calculation_approach",
    "thresholds",
    "subgroup_results",
    "evaluation_outcome",
    "test_date",
    "evidence_reference",
    "observed_limitations",
    "mitigation_actions",
    "responsible_owner",
    "reviewer",
    "review_date",
)
FAIRNESS_EVALUATION_WIDGET_FIELDS = tuple(
    field
    for field in FAIRNESS_EVALUATION_FIELDS
    if field not in {"thresholds", "subgroup_results"}
) + ("threshold_row_count", "subgroup_result_row_count")
FAIRNESS_EVALUATION_WIDGET_KEYS = {
    field: f"fai01_evaluation_{field}"
    for field in FAIRNESS_EVALUATION_WIDGET_FIELDS
}
EVALUATION_STAGES = ("Planned", "Performed")
EVALUATION_STATUSES = ("Draft", "Reviewed")
METRIC_SCALES = (
    "unbounded",
    "percentage_0_100",
    "proportion_0_1",
)
THRESHOLD_COMPARATORS = ("<", "<=", ">", ">=", "==")
PERFORMED_REQUIRED_FIELDS = frozenset(FAIRNESS_EVALUATION_FIELDS) - {
    "evaluation_stage",
    "evaluation_status",
}
PLANNING_REQUIRED_FIELDS = frozenset({
    "groups_and_selection_basis",
    "dataset_source",
    "dataset_scope",
    "dataset_population",
    "dataset_timeframe",
    "dataset_representativeness_limitations",
    "metric_name",
    "metric_definition",
    "calculation_approach",
    "thresholds",
    "observed_limitations",
    "mitigation_actions",
    "responsible_owner",
    "reviewer",
    "review_date",
})
PLACEHOLDERS = {"tbd", "n/a", "na"}
RESULT_FIELDS = (
    "subgroup_results",
    "evaluation_outcome",
    "test_date",
    "evidence_reference",
)


def _is_meaningful(value):
    if not isinstance(value, str):
        return False
    normalized = value.strip().casefold()
    return bool(normalized) and normalized not in PLACEHOLDERS and len(normalized) > 1


def _valid_iso_date(value):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed_date.isoformat() == value


def _finite_number(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


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


def validate_thresholds(thresholds):
    errors = []
    if not isinstance(thresholds, list):
        return ["Thresholds must be a list of structured entries."]
    for index, threshold in enumerate(thresholds):
        prefix = f"Threshold {index + 1}"
        if not isinstance(threshold, dict):
            errors.append(f"{prefix} must be an object.")
            continue
        kind = threshold.get("kind")
        if kind == "numeric":
            expected = {
                "kind",
                "comparator",
                "value",
                "metric_unit",
                "metric_scale",
                "rationale",
            }
            if set(threshold) != expected:
                errors.append(f"{prefix} has missing or unsupported fields.")
                continue
            if threshold["comparator"] not in THRESHOLD_COMPARATORS:
                errors.append(f"{prefix} has an invalid comparator.")
            if not _finite_number(threshold["value"]):
                errors.append(f"{prefix} value must be a finite number.")
            if not _is_meaningful(threshold["metric_unit"]):
                errors.append(f"{prefix} metric unit is required.")
            scale = threshold["metric_scale"]
            if scale not in METRIC_SCALES:
                errors.append(f"{prefix} has an invalid metric scale.")
            elif not _unit_matches_scale(threshold["metric_unit"], scale):
                errors.append(f"{prefix} metric unit does not match its declared scale.")
            elif _finite_number(threshold["value"]):
                if scale == "percentage_0_100" and not 0 <= threshold["value"] <= 100:
                    errors.append(f"{prefix} percentage value must be between 0 and 100.")
                if scale == "proportion_0_1" and not 0 <= threshold["value"] <= 1:
                    errors.append(f"{prefix} proportion value must be between 0 and 1.")
            if not _is_meaningful(threshold["rationale"]):
                errors.append(f"{prefix} rationale is required.")
        elif kind == "documented":
            expected = {"kind", "description", "rationale", "human_review_required"}
            if set(threshold) != expected:
                errors.append(f"{prefix} has missing or unsupported fields.")
                continue
            if not _is_meaningful(threshold["description"]):
                errors.append(f"{prefix} description is required.")
            if not _is_meaningful(threshold["rationale"]):
                errors.append(f"{prefix} rationale is required.")
            if threshold["human_review_required"] is not True:
                errors.append(f"{prefix} requires explicit human review.")
        else:
            errors.append(f"{prefix} kind must be numeric or documented.")
    return errors


def validate_subgroup_results(results):
    errors = []
    if not isinstance(results, list):
        return ["Subgroup results must be a list of structured entries."]
    for index, result in enumerate(results):
        prefix = f"Subgroup result {index + 1}"
        if not isinstance(result, dict):
            errors.append(f"{prefix} must be an object.")
            continue
        expected = {
            "subgroup_label",
            "metric_value",
            "metric_unit",
            "metric_scale",
            "sample_size",
            "event_numerator",
            "evidence_reference",
        }
        if set(result) != expected:
            errors.append(f"{prefix} has missing or unsupported fields.")
            continue
        for field in ("subgroup_label", "metric_unit", "evidence_reference"):
            if not _is_meaningful(result[field]):
                errors.append(f"{prefix} {field.replace('_', ' ')} is required.")
        metric_value = result["metric_value"]
        if not _finite_number(metric_value):
            errors.append(f"{prefix} metric value must be a finite number.")
        scale = result["metric_scale"]
        if scale not in METRIC_SCALES:
            errors.append(f"{prefix} has an invalid metric scale.")
        elif not _unit_matches_scale(result["metric_unit"], scale):
            errors.append(f"{prefix} metric unit does not match its declared scale.")
        elif _finite_number(metric_value):
            if scale == "percentage_0_100" and not 0 <= metric_value <= 100:
                errors.append(f"{prefix} percentage value must be between 0 and 100.")
            if scale == "proportion_0_1" and not 0 <= metric_value <= 1:
                errors.append(f"{prefix} proportion value must be between 0 and 1.")

        sample_size = result["sample_size"]
        numerator = result["event_numerator"]
        if sample_size is not None and (
            type(sample_size) is not int or sample_size <= 0
        ):
            errors.append(f"{prefix} sample size must be a positive integer when supplied.")
        if numerator is not None and (
            type(numerator) is not int or numerator < 0
        ):
            errors.append(f"{prefix} event numerator must be a nonnegative integer when supplied.")
        if numerator is not None and sample_size is None:
            errors.append(f"{prefix} event numerator requires a sample-size denominator.")
        elif (
            type(numerator) is int
            and type(sample_size) is int
            and numerator > sample_size
        ):
            errors.append(f"{prefix} event numerator cannot exceed sample size.")
    return errors


def fairness_row_widget_key(kind, index, field, generation=None):
    key = f"fai01_evaluation_{kind}_{index}_{field}"
    return f"{key}_{generation}" if generation else key


def _parse_optional_count(value):
    if value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def _metric_context(entry):
    return (
        entry["metric_unit"].strip().casefold(),
        entry["metric_scale"],
    )


def validate_metric_consistency(record):
    numeric_entries = [
        threshold
        for threshold in record["thresholds"]
        if isinstance(threshold, dict) and threshold.get("kind") == "numeric"
    ]
    numeric_entries.extend(
        result
        for result in record["subgroup_results"]
        if isinstance(result, dict)
    )
    valid_entries = [
        entry
        for entry in numeric_entries
        if isinstance(entry.get("metric_unit"), str)
        and entry.get("metric_scale") in METRIC_SCALES
    ]
    if len(valid_entries) < 2:
        return []
    expected_context = _metric_context(valid_entries[0])
    if any(_metric_context(entry) != expected_context for entry in valid_entries[1:]):
        return [
            "All numeric thresholds and subgroup results for the declared metric "
            "must use the same metric unit and scale."
        ]
    return []


def validate_fairness_evaluation(record):
    if not isinstance(record, dict):
        return ["Fairness evaluation must be a field mapping."]
    errors = []
    if set(record) != set(FAIRNESS_EVALUATION_FIELDS):
        errors.append("Fairness evaluation must contain exactly the expected fields.")
    for field in FAIRNESS_EVALUATION_FIELDS:
        expected_type = list if field in {"thresholds", "subgroup_results"} else str
        if not isinstance(record.get(field), expected_type):
            errors.append(f"{field} must be {'a list' if expected_type is list else 'text'}.")
    if errors:
        return errors

    stage = record["evaluation_stage"]
    status = record["evaluation_status"]
    if stage not in EVALUATION_STAGES:
        errors.append("Evaluation stage must be Planned or Performed.")
        return errors
    if status not in EVALUATION_STATUSES:
        errors.append("Evaluation status must be Draft or Reviewed.")
    errors.extend(validate_thresholds(record["thresholds"]))
    errors.extend(validate_subgroup_results(record["subgroup_results"]))
    errors.extend(validate_metric_consistency(record))

    for field in ("test_date", "review_date"):
        if record[field].strip() and not _valid_iso_date(record[field]):
            errors.append(
                f"{field.replace('_', ' ').capitalize()} must be a valid date in YYYY-MM-DD format."
            )

    if stage == "Planned":
        if record["subgroup_results"] or any(
            record[field].strip()
            for field in ("evaluation_outcome", "test_date", "evidence_reference")
        ):
            errors.append(
                "Planned evaluations must not contain performed results, test dates, or evidence references."
            )
        if status == "Reviewed":
            for field in sorted(PLANNING_REQUIRED_FIELDS):
                if field == "thresholds":
                    if not record[field]:
                        errors.append("At least one threshold or documented criterion is required before review.")
                elif not _is_meaningful(record[field]):
                    errors.append(f"{field.replace('_', ' ').capitalize()} is required before review.")
            if not _valid_iso_date(record["review_date"]):
                errors.append("Review date must be a valid date in YYYY-MM-DD format.")
    elif stage == "Performed":
        for field in sorted(PERFORMED_REQUIRED_FIELDS):
            if field in {"subgroup_results", "thresholds"}:
                if not record[field]:
                    errors.append(f"At least one {field.replace('_', ' ')} entry is required for performed evaluation.")
            elif not _is_meaningful(record[field]):
                errors.append(f"{field.replace('_', ' ').capitalize()} is required for performed evaluation.")
        if not _valid_iso_date(record["test_date"]):
            errors.append("Test date must be a valid date in YYYY-MM-DD format.")
        if not _valid_iso_date(record["review_date"]):
            errors.append("Review date must be a valid date in YYYY-MM-DD format.")
    return errors


def evaluation_from_form(values):
    record = {
        field: values[field]
        for field in FAIRNESS_EVALUATION_FIELDS
        if field not in {"thresholds", "subgroup_results"}
    }
    thresholds = []
    for row in values["threshold_rows"]:
        if row["kind"] == "numeric":
            thresholds.append({
                "kind": "numeric",
                "comparator": row["comparator"],
                "value": row["value"],
                "metric_unit": row["metric_unit"],
                "metric_scale": row["metric_scale"],
                "rationale": row["rationale"],
            })
        else:
            thresholds.append({
                "kind": "documented",
                "description": row["description"],
                "rationale": row["rationale"],
                "human_review_required": row["human_review_required"],
            })

    record["thresholds"] = thresholds
    record["subgroup_results"] = [
        {
            "subgroup_label": row["subgroup_label"],
            "metric_value": row["metric_value"],
            "metric_unit": row["metric_unit"],
            "metric_scale": row["metric_scale"],
            "sample_size": _parse_optional_count(row["sample_size"]),
            "event_numerator": _parse_optional_count(row["event_numerator"]),
            "evidence_reference": row["evidence_reference"],
        }
        for row in values["subgroup_rows"]
    ]
    return record, []
