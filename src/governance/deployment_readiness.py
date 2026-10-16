from .constants import PRE_DEPLOYMENT_CONTROL_IDS


def evaluate_readiness(
    control_assessments,
    plans,
    risk_answers_complete,
):
    if not risk_answers_complete:
        return None

    blocking_controls = [
        control_id
        for control_id in PRE_DEPLOYMENT_CONTROL_IDS
        if control_id in control_assessments
        and control_assessments[control_id]["Applicability"] == "Required"
        and control_assessments[control_id]["Evidence Status"] == "Pending"
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

    status = (
        "Ready for Deployment Approval"
        if not blocking_controls and not incomplete_operational_requirements
        else "Not Ready for Deployment Approval"
    )
    return {
        "status": status,
        "blocking_controls": blocking_controls,
        "incomplete_operational_requirements": incomplete_operational_requirements,
    }
