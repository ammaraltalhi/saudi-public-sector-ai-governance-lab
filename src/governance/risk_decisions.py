"""Documented residual-risk decisions, bound to the reviewed risk and context.

These records are user attestations, not authenticated authorizations.
"""
from datetime import date
import hashlib
import json

from .corrective_actions import meaningful, valid_date
from .risk_register import validate_register
from .saudi_risk_method import METHOD_ID

DECISIONS = ("Accept", "Escalate", "Reject")
FIELDS = (
    "risk_id", "decision", "authority", "decision_date", "tolerance_reference",
    "rationale", "evidence", "next_review_date", "risk_fingerprint", "context_fingerprint",
)


def fingerprint(value):
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_decisions(decisions, risk_ids=None):
    if not isinstance(decisions, dict):
        return ["Risk decisions must be a mapping by risk ID."]
    errors = []
    for risk_id, record in decisions.items():
        if not isinstance(record, dict) or set(record) != set(FIELDS):
            errors.append(f"{risk_id}: decision has missing or unsupported fields.")
            continue
        if any(not meaningful(record[field]) for field in FIELDS):
            errors.append(f"{risk_id}: every decision field needs meaningful text.")
            continue
        if record["risk_id"] != risk_id or risk_ids is not None and risk_id not in risk_ids:
            errors.append(f"{risk_id}: decision references an unknown or mismatched risk.")
        if record["decision"] not in DECISIONS:
            errors.append(f"{risk_id}: invalid decision.")
        if not valid_date(record["decision_date"]) or not valid_date(record["next_review_date"]):
            errors.append(f"{risk_id}: decision dates must use YYYY-MM-DD.")
        elif record["next_review_date"] <= record["decision_date"]:
            errors.append(f"{risk_id}: next review must follow the decision date.")
        for field in ("risk_fingerprint", "context_fingerprint"):
            value = record[field]
            if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
                errors.append(f"{risk_id}: invalid assessment fingerprint.")
    return errors


def review_blockers(risks, decisions, use_case, today=None):
    """No scoring band or treatment selection is itself an acceptance decision."""
    errors = validate_register(risks)
    if errors:
        return errors
    if not risks:
        return ["Complete a national per-risk assessment and record its residual-risk decision. An empty register is not a completed risk review."]
    errors = validate_decisions(decisions, {risk["risk_id"] for risk in risks})
    if errors:
        return errors
    if not isinstance(use_case, dict) or not use_case:
        return ["Document the use-case context before reviewing residual risk."]
    today = today or date.today()
    blockers = []
    for risk in risks:
        risk_id = risk["risk_id"]
        if risk.get("methodology") != METHOD_ID:
            blockers.append(f"{risk_id}: legacy illustrative record needs explicit national reassessment.")
            continue
        if risk["residual_basis"] != "Post-treatment reassessment":
            blockers.append(f"{risk_id}: planned residual estimate needs post-treatment reassessment and evidence.")
        decision = decisions.get(risk_id)
        if decision is None:
            blockers.append(f"{risk_id}: residual-risk acceptance or escalation has not been recorded.")
            continue
        if decision["risk_fingerprint"] != fingerprint(risk) or decision["context_fingerprint"] != fingerprint(use_case):
            blockers.append(f"{risk_id}: assessment or context changed; review the decision again.")
        if decision["decision"] != "Accept":
            blockers.append(f"{risk_id}: decision is {decision['decision']}; resolve before deployment approval.")
        if date.fromisoformat(decision["next_review_date"]) <= today:
            blockers.append(f"{risk_id}: residual-risk decision is due for review.")
        if date.fromisoformat(decision["decision_date"]) > today:
            blockers.append(f"{risk_id}: decision date is in the future.")
    return blockers
