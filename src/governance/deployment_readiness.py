from .risk_decisions import review_blockers
from .corrective_actions import action_summary
from .constants import PRE_DEPLOYMENT_CONTROL_IDS


def evaluate_readiness(
    control_assessments,
    plans,
    risk_answers_complete,
    corrective_actions=None,
    risk_register=None,
    risk_decisions=None,
    use_case=None,
):
    if not risk_answers_complete:
        return None

    blocking_controls = [
        control_id
        for control_id in PRE_DEPLOYMENT_CONTROL_IDS
        if control_id not in control_assessments
        or control_assessments[control_id].get("Applicability") not in {"Required", "Not required"}
        or (control_assessments[control_id].get("Applicability") == "Required"
            and control_assessments[control_id].get("Evidence Status") != "Available")
    ]
    monitoring_plan_complete = (
        control_assessments.get("MON-01", {}).get("Applicability") == "Required"
        and control_assessments.get("MON-01", {}).get("Evidence Status") == "Available"
    )
    incident_plan_complete = (
        control_assessments.get("INC-01", {}).get("Applicability") == "Required"
        and control_assessments.get("INC-01", {}).get("Evidence Status") == "Available"
    )
    incomplete_operational_requirements = (
        4 * int(not monitoring_plan_complete)
        + int(not incident_plan_complete)
    )

    actions = action_summary([] if corrective_actions is None else corrective_actions)

    # Omitting register preserves the old helper API; both application views always supply it.
    risk_blockers = [] if risk_register is None else review_blockers(
        risk_register, {} if risk_decisions is None else risk_decisions, use_case,
    )

    status = (
        "Ready for Deployment Approval"
        if not blocking_controls and not incomplete_operational_requirements
        and not actions["blocking_actions"] and not actions["errors"] and not risk_blockers
        else "Not Ready for Deployment Approval"
    )
    return {
        "status": status,
        "blocking_controls": blocking_controls,
        "blocking_actions": actions["blocking_actions"],
        "risk_review_blockers": risk_blockers,
        "action_errors": actions["errors"],
        "incomplete_operational_requirements": incomplete_operational_requirements,
    }
