"""Portfolio risk records. Scores are illustrative, not an official SDAIA scale."""
from datetime import date

TEXT_FIELDS = ("risk_id", "description", "cause", "consequence", "owner", "controls", "treatment", "due_date", "status", "evidence", "reviewer", "review_date")
SCORE_FIELDS = ("likelihood", "impact", "residual_likelihood", "residual_impact")
STATUSES = ("Open", "In treatment", "Ready for review", "Closed")


def validate_register(records):
    if not isinstance(records, list):
        return ["Risk register must be a list."]
    errors, seen = [], set()
    for index, record in enumerate(records):
        prefix = f"Risk {index + 1}"
        if not isinstance(record, dict) or set(record) != set(TEXT_FIELDS + SCORE_FIELDS):
            errors.append(f"{prefix}: unsupported or missing fields.")
            continue
        if any(not isinstance(record[field], str) for field in TEXT_FIELDS):
            errors.append(f"{prefix}: text fields must be strings.")
            continue
        if record["risk_id"] in seen:
            errors.append(f"{prefix}: duplicate risk ID.")
        seen.add(record["risk_id"])
        for field in ("risk_id", "description", "cause", "consequence", "owner", "treatment", "due_date"):
            if not record[field].strip() or record[field].strip().lower() in {"tbd", "n/a"}:
                errors.append(f"{prefix}: {field} is required.")
        for field in SCORE_FIELDS:
            if type(record[field]) is not int or not 1 <= record[field] <= 4:
                errors.append(f"{prefix}: {field} must be an integer from 1 to 4.")
        if record["status"] not in STATUSES:
            errors.append(f"{prefix}: invalid status.")
        for field in ("due_date", "review_date"):
            if field == "review_date" and not record[field]:
                continue
            try:
                if date.fromisoformat(record[field]).isoformat() != record[field]:
                    raise ValueError
            except ValueError:
                errors.append(f"{prefix}: {field} must use YYYY-MM-DD.")
        if record["status"] == "Closed" and any(not record[field].strip() for field in ("evidence", "reviewer", "review_date")):
            errors.append(f"{prefix}: closure needs evidence, reviewer and review date.")
    return errors


def score_record(record):
    errors = validate_register([record])
    if errors:
        raise ValueError("; ".join(errors))
    return {"inherent_score": record["likelihood"] * record["impact"],
            "residual_score": record["residual_likelihood"] * record["residual_impact"]}
