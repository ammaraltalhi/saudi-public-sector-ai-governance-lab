"""User-recorded corrective actions; not independent assurance or approval."""
from datetime import date

from .constants import PRE_DEPLOYMENT_CONTROL_IDS

CONTROL_IDS = PRE_DEPLOYMENT_CONTROL_IDS + ("MON-01", "INC-01", "RET-01")
STATUSES = ("Open", "In progress", "Awaiting verification", "Closed")
TEXT_FIELDS = (
    "action_id", "finding", "risk_id", "control_id", "owner", "action_plan",
    "due_date", "status", "evidence", "reviewer", "review_date",
    "verification_notes", "readiness_rationale",
)


def meaningful(value):
    return isinstance(value, str) and value.strip().casefold() not in {
        "", "tbd", "n/a", "na", "pending", "placeholder",
    }


def valid_date(value):
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def validate_actions(records, risk_ids=None):
    if not isinstance(records, list):
        return ["Corrective actions must be a list."]
    errors, seen = [], set()
    for index, record in enumerate(records):
        prefix = f"Action {index + 1}"
        if not isinstance(record, dict) or set(record) != set(TEXT_FIELDS) | {"blocks_readiness"}:
            errors.append(f"{prefix}: missing or unsupported fields.")
            continue
        if any(not isinstance(record[field], str) for field in TEXT_FIELDS):
            errors.append(f"{prefix}: text fields must be strings.")
            continue
        if record["action_id"] in seen:
            errors.append(f"{prefix}: duplicate action ID.")
        seen.add(record["action_id"])
        for field in ("action_id", "finding", "owner", "action_plan", "readiness_rationale"):
            if not meaningful(record[field]):
                errors.append(f"{prefix}: {field} is required.")
        if type(record["blocks_readiness"]) is not bool:
            errors.append(f"{prefix}: blocks_readiness must be a boolean.")
        if record["status"] not in STATUSES:
            errors.append(f"{prefix}: invalid status.")
        if record["control_id"] and record["control_id"] not in CONTROL_IDS:
            errors.append(f"{prefix}: unknown control ID.")
        if not record["risk_id"] and not record["control_id"]:
            errors.append(f"{prefix}: link a risk or control.")
        if record["risk_id"] and risk_ids is not None and record["risk_id"] not in risk_ids:
            errors.append(f"{prefix}: unknown risk ID.")
        if not valid_date(record["due_date"]):
            errors.append(f"{prefix}: due_date must use YYYY-MM-DD.")
        if record["review_date"] and not valid_date(record["review_date"]):
            errors.append(f"{prefix}: review_date must use YYYY-MM-DD.")
        if record["status"] == "Closed":
            for field in ("evidence", "reviewer", "review_date", "verification_notes"):
                if not meaningful(record[field]):
                    errors.append(f"{prefix}: closure requires {field}.")
    return errors


def action_summary(records, today=None):
    """Fail closed for invalid records; caller must display errors."""
    errors = validate_actions(records)
    if errors:
        return {"errors": errors, "blocking_actions": [], "open_count": None, "overdue_count": None}
    today = today or date.today()
    open_actions = [record for record in records if record["status"] != "Closed"]
    return {
        "errors": [],
        "blocking_actions": [record["action_id"] for record in open_actions if record["blocks_readiness"]],
        "open_count": len(open_actions),
        "overdue_count": sum(date.fromisoformat(record["due_date"]) < today for record in open_actions),
    }
