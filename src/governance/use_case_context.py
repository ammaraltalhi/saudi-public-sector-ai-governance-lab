"""Minimum documented intake context; not a regulatory completeness assessment."""
from .corrective_actions import meaningful

CONTEXT_LABELS = {
    "name": "AI system name", "owner": "Business owner", "purpose": "Intended purpose",
    "users": "Primary users", "affected_people": "Affected people", "data": "Main data categories",
    "decision": "Decision or output", "potential_impact": "Potential impact if the AI is wrong",
    "incident_response": "Incident response considerations",
}


def context_errors(context):
    if not isinstance(context, dict):
        return ["Complete the AI Use Case Intake first."]
    errors = [f"{label} needs meaningful text." for key, label in CONTEXT_LABELS.items()
              if not meaningful(context.get(key))]
    if context.get("ai_role") not in {"Recommendation only", "Decision support", "Automated decision"}:
        errors.append("Select a valid AI role.")
    if context.get("human_oversight") not in {"Required before action", "Human review after action", "No human review"}:
        errors.append("Select a valid human oversight approach.")
    return errors
