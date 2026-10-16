from dataclasses import dataclass
from typing import Mapping


RISK_WEIGHTS = {
    "personal_data": 2,
    "sensitive_data": 3,
    "significant_decision": 3,
    "vulnerable_groups": 2,
    "external_users": 1,
    "automated_action": 2,
    "third_party_model": 1,
    "security_critical": 3,
}


@dataclass(frozen=True)
class RiskResult:
    score: int
    level: str
    required_gates: tuple[str, ...]


def calculate_risk(answers: Mapping[str, bool]) -> RiskResult:
    """Return an illustrative portfolio risk score and governance gates.

    This heuristic is for the case study only. It is not a legal or regulatory
    classification and should be replaced by an organisation-approved method
    in a real implementation.
    """
    score = sum(RISK_WEIGHTS[key] for key, value in answers.items() if value and key in RISK_WEIGHTS)

    if score >= 10:
        level = "High"
        gates = (
            "Business Owner Approval",
            "AI Governance Review",
            "Privacy Review",
            "Security Review",
            "Fairness & Performance Validation",
            "Executive Deployment Approval",
            "Enhanced Post-Deployment Monitoring",
        )
    elif score >= 5:
        level = "Medium"
        gates = (
            "Business Owner Approval",
            "AI Governance Review",
            "Privacy/Security Review as applicable",
            "Performance Validation",
            "Deployment Approval",
            "Periodic Monitoring",
        )
    else:
        level = "Low"
        gates = (
            "Business Owner Approval",
            "Basic Governance Review",
            "Basic Validation",
            "Periodic Monitoring",
        )

    return RiskResult(score=score, level=level, required_gates=gates)
