from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from uuid import UUID, uuid4

from .risk import RISK_WEIGHTS, calculate_risk
from .raci import raci_errors
from .risk_register import validate_register
from .risk_decisions import validate_decisions
from .corrective_actions import validate_actions
from .fairness_evaluation import FAIRNESS_EVALUATION_WIDGET_KEYS
from .validation_evaluation import VALIDATION_EVALUATION_WIDGET_KEYS
from .explainability_evidence import EXPLAINABILITY_WIDGET_KEYS
from .sdaia_impact import validate_impact_assessments

SCHEMA_VERSION = 1
RISK_ANSWER_KEYS = tuple(RISK_WEIGHTS)
USE_CASE_KEYS = (
    "name",
    "owner",
    "purpose",
    "users",
    "affected_people",
    "data",
    "decision",
    "ai_role",
    "human_oversight",
    "potential_impact",
    "incident_response",
)
PLAN_KEYS = {
    "monitoring": (
        "plan_defined",
        "metrics_defined",
        "thresholds_defined",
        "responsibilities_defined",
    ),
    "incident_response": ("plan_approved",),
}
RISK_LABELS = {
    "personal_data": "Does the system process personal data?",
    "sensitive_data": "Does it process sensitive or highly sensitive data?",
    "significant_decision": "Could it materially affect an individual's access, priority, rights or opportunities?",
    "vulnerable_groups": "Could it affect vulnerable groups?",
    "external_users": "Is it used by or directly exposed to external users?",
    "automated_action": "Can it trigger an action without meaningful human review?",
    "third_party_model": "Does it rely on a third-party AI model or API?",
    "security_critical": "Could failure create a significant security or safety impact?",
}
DEFAULT_PLANS = {
    "monitoring": {
        "plan_defined": False,
        "metrics_defined": False,
        "thresholds_defined": False,
        "responsibilities_defined": False,
    },
    "incident_response": {"plan_approved": False},
}
USE_CASE_WIDGET_KEYS = {
    field: f"use_case_{field}" for field in USE_CASE_KEYS
}
DAT01_WIDGET_FIELDS = (
    "personal_data_categories",
    "purpose_necessity",
    "data_minimisation",
    "sensitive_data_used",
    "sensitive_data_details",
    "data_access",
    "responsible_owner",
    "retention_deletion",
    "privacy_risks",
    "mitigations",
    "privacy_reviewer",
    "assessment_status",
)
PLAN_WIDGET_KEYS = {
    (group, field): f"deployment_{group}_{field}"
    for group, fields in PLAN_KEYS.items()
    for field in fields
}
DAT01_WIDGET_KEYS = {
    field: f"dat01_{field}" for field in DAT01_WIDGET_FIELDS
}
FAI01_WIDGET_FIELDS = (
    "affected_groups",
    "fairness_risk",
    "evaluation_approach",
    "data_evaluation_limitations",
    "findings_observations",
    "mitigation_actions",
    "responsible_owner",
    "fairness_reviewer",
    "assessment_status",
)
FAI01_WIDGET_KEYS = {
    field: f"fai01_{field}" for field in FAI01_WIDGET_FIELDS
}
FAI01_EVALUATION_WIDGET_KEYS = FAIRNESS_EVALUATION_WIDGET_KEYS
SEC01_WIDGET_FIELDS = (
    "security_scope",
    "key_security_risks",
    "access_control_approach",
    "data_protection_measures",
    "third_party_considerations",
    "security_monitoring_approach",
    "incident_escalation_approach",
    "security_limitations_actions",
    "responsible_owner",
    "security_reviewer",
    "assessment_status",
)
SEC01_WIDGET_KEYS = {
    field: f"sec01_{field}" for field in SEC01_WIDGET_FIELDS
}
TRN01_WIDGET_FIELDS = (
    "ai_system_purpose",
    "ai_decision_role",
    "intended_users_stakeholders",
    "key_system_limitations",
    "human_oversight_approach",
    "information_to_communicate",
    "communication_disclosure_approach",
    "transparency_limitations_actions",
    "responsible_owner",
    "transparency_reviewer",
    "assessment_status",
)
TRN01_WIDGET_KEYS = {
    field: f"trn01_{field}" for field in TRN01_WIDGET_FIELDS
}
TRN01_EXPLAINABILITY_WIDGET_KEYS = EXPLAINABILITY_WIDGET_KEYS
VAL01_WIDGET_FIELDS = (
    "validation_scope",
    "acceptance_criteria",
    "validation_approach",
    "data_test_set_considerations",
    "human_oversight_validation",
    "validation_findings_evidence",
    "validation_limitations_actions",
    "responsible_owner",
    "validation_reviewer",
    "assessment_status",
)
VAL01_WIDGET_KEYS = {
    field: f"val01_{field}" for field in VAL01_WIDGET_FIELDS
}
VAL01_EVALUATION_WIDGET_KEYS = VALIDATION_EVALUATION_WIDGET_KEYS
MON01_WIDGET_FIELDS = (
    "monitoring_objectives",
    "performance_metrics",
    "fairness_disparity_monitoring",
    "human_override_review_monitoring",
    "incident_complaint_indicators",
    "data_model_drift_indicators",
    "monitoring_thresholds",
    "monitoring_frequency",
    "monitoring_responsibilities",
    "threshold_breach_escalation",
    "monitoring_limitations_actions",
    "responsible_owner",
    "monitoring_reviewer",
    "assessment_status",
)
MON01_WIDGET_KEYS = {
    field: f"mon01_{field}" for field in MON01_WIDGET_FIELDS
}
INC01_WIDGET_FIELDS = (
    "incident_definition_scope",
    "detection_reporting_channels",
    "initial_assessment_triage",
    "severity_impact_classification",
    "immediate_containment_actions",
    "human_review_decision_correction",
    "escalation_criteria",
    "escalation_roles_notifications",
    "investigation_root_cause_approach",
    "corrective_preventive_actions",
    "recovery_return_to_service",
    "incident_documentation_records",
    "post_incident_review_lessons",
    "incident_limitations_actions",
    "responsible_owner",
    "incident_response_reviewer",
    "assessment_status",
)
INC01_WIDGET_KEYS = {
    field: f"inc01_{field}" for field in INC01_WIDGET_FIELDS
}
_CASE_ID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class CasePersistenceError(ValueError):
    """Raised when a saved case cannot be safely validated or accessed."""


def _valid_case_id(case_id):
    if not isinstance(case_id, str) or not _CASE_ID_PATTERN.fullmatch(case_id):
        return False
    try:
        return str(UUID(case_id)) == case_id
    except ValueError:
        return False


def _validate_json_value(value, location):
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise CasePersistenceError(f"{location} contains a non-finite number.")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise CasePersistenceError(f"{location} must use string keys.")
        for key, item in value.items():
            _validate_json_value(item, f"{location}.{key}")
        return
    raise CasePersistenceError(f"{location} contains a value that is not JSON-compatible.")


def validate_case_document(document):
    if not isinstance(document, dict):
        raise CasePersistenceError("Case document must be a JSON object.")
    if type(document.get("schema_version")) is not int or document["schema_version"] != SCHEMA_VERSION:
        raise CasePersistenceError("Unsupported case schema version.")
    if not _valid_case_id(document.get("case_id")):
        raise CasePersistenceError("Case ID is invalid.")
    if not isinstance(document.get("case_name"), str) or not document["case_name"].strip():
        raise CasePersistenceError("Case name is required.")
    if not isinstance(document.get("saved_at"), str) or not document["saved_at"].strip():
        raise CasePersistenceError("Saved timestamp is required.")
    try:
        datetime.fromisoformat(document["saved_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise CasePersistenceError("Saved timestamp must be ISO-8601.") from error

    use_case = document.get("use_case")
    if not isinstance(use_case, dict) or set(use_case) != set(USE_CASE_KEYS):
        raise CasePersistenceError("Use case must contain the expected fields.")
    if any(not isinstance(use_case[field], str) for field in USE_CASE_KEYS):
        raise CasePersistenceError("Use-case fields must be strings.")
    if not use_case["name"].strip() or document["case_name"] != use_case["name"]:
        raise CasePersistenceError("Case name must match the use-case name.")
    if use_case["ai_role"] not in {
        "Recommendation only",
        "Decision support",
        "Automated decision",
    }:
        raise CasePersistenceError("AI role is invalid.")
    if use_case["human_oversight"] not in {
        "Required before action",
        "Human review after action",
        "No human review",
    }:
        raise CasePersistenceError("Human oversight selection is invalid.")

    risk_answers = document.get("risk_answers")
    if not isinstance(risk_answers, dict) or set(risk_answers) != set(RISK_ANSWER_KEYS):
        raise CasePersistenceError("Risk answers must contain all eight screening keys.")
    if any(type(risk_answers[key]) is not bool for key in RISK_ANSWER_KEYS):
        raise CasePersistenceError("Every risk answer must be a boolean.")

    control_evidence = document.get("control_evidence")
    if not isinstance(control_evidence, dict):
        raise CasePersistenceError("Control evidence must be a mapping.")
    _validate_json_value(control_evidence, "control_evidence")
    impact_assessments = document.get("sdaia_impact_assessments", {})
    _validate_json_value(impact_assessments, "sdaia_impact_assessments")
    # Invalid optional records remain loadable so valid case data is not lost.
    # The shared validator separates canonical records from invalid entries.
    validate_impact_assessments(impact_assessments)

    plans = document.get("deployment_readiness_plans")
    if not isinstance(plans, dict) or set(plans) != set(PLAN_KEYS):
        raise CasePersistenceError("Deployment readiness plan structure is invalid.")
    for group, fields in PLAN_KEYS.items():
        group_value = plans.get(group)
        if not isinstance(group_value, dict) or set(group_value) != set(fields):
            raise CasePersistenceError(f"Deployment readiness plan '{group}' is invalid.")
        if any(type(group_value[field]) is not bool for field in fields):
            raise CasePersistenceError(f"Deployment readiness plan '{group}' values must be booleans.")

    register_errors = validate_register(document.get("risk_register", []))
    if register_errors:
        raise CasePersistenceError("; ".join(register_errors))

    action_errors = validate_actions(
        document.get("corrective_actions", []),
        {record["risk_id"] for record in document.get("risk_register", [])},
    )
    if action_errors:
        raise CasePersistenceError("; ".join(action_errors))

    decision_errors = validate_decisions(
        document.get("risk_decisions", {}),
        {record["risk_id"] for record in document.get("risk_register", [])},
    )
    if decision_errors:
        raise CasePersistenceError("; ".join(decision_errors))

    if "raci_matrix" in document:
        errors = raci_errors(document["raci_matrix"])
        if errors:
            raise CasePersistenceError("; ".join(errors))

    expected_fields = {
        "schema_version",
        "case_id",
        "case_name",
        "saved_at",
        "use_case",
        "risk_answers",
        "control_evidence",
        "deployment_readiness_plans",
    }
    if not expected_fields <= set(document) or set(document) - expected_fields - {"sdaia_impact_assessments", "risk_register", "corrective_actions", "risk_decisions", "raci_matrix"}:
        raise CasePersistenceError("Case document contains missing or unsupported fields.")
    return document


def build_case_document(session_state, case_id=None, saved_at=None):
    use_case = session_state.get("use_case")
    risk_answers = session_state.get("risk_answers")
    plans = session_state.get("deployment_readiness_plans", deepcopy(DEFAULT_PLANS))
    document = {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id or session_state.get("current_case_id") or str(uuid4()),
        "case_name": use_case.get("name") if isinstance(use_case, dict) else "",
        "saved_at": saved_at or datetime.now(timezone.utc).isoformat(),
        "use_case": deepcopy(use_case),
        "risk_answers": deepcopy(risk_answers),
        "control_evidence": deepcopy(session_state.get("control_evidence", {})),
        "deployment_readiness_plans": deepcopy(plans),
    }
    if "risk_register" in session_state:
        document["risk_register"] = deepcopy(session_state["risk_register"])
    if "corrective_actions" in session_state:
        document["corrective_actions"] = deepcopy(session_state["corrective_actions"])
    if "risk_decisions" in session_state:
        document["risk_decisions"] = deepcopy(session_state["risk_decisions"])
    if "raci_matrix" in session_state:
        document["raci_matrix"] = deepcopy(session_state["raci_matrix"])
    assessments = deepcopy(session_state.get("sdaia_impact_assessments", {}))
    invalid = deepcopy(session_state.get("_sdaia_impact_assessment_invalid", {}))
    if not isinstance(assessments, dict):
        assessments = {}
    if invalid:
        if "_root" in invalid:
            assessments["_invalid_payload"] = invalid["_root"]["record"]
        else:
            assessments.update({
                key: entry["record"]
                for key, entry in invalid.items()
                if isinstance(entry, dict) and "record" in entry
            })
    if assessments or "sdaia_impact_assessments" in session_state:
        document["sdaia_impact_assessments"] = assessments
    validate_case_document(document)
    return document


def save_case(session_state, cases_dir):
    cases_path = Path(cases_dir)
    document = build_case_document(session_state)
    try:
        cases_path.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise CasePersistenceError(f"Could not create case directory: {error}") from error
    target = cases_path / f"{document['case_id']}.json"
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=cases_path,
            prefix=f".{document['case_id']}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(document, temporary_file, ensure_ascii=False, indent=2, allow_nan=False)
            temporary_file.write("\n")
        os.replace(temporary_path, target)
    except OSError as error:
        raise CasePersistenceError(f"Could not save case file: {error}") from error
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return document


def load_case(case_id, cases_dir):
    if not _valid_case_id(case_id):
        raise CasePersistenceError("Selected case ID is invalid.")
    target = Path(cases_dir) / f"{case_id}.json"
    try:
        with target.open(encoding="utf-8") as case_file:
            document = json.load(
                case_file,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    CasePersistenceError(f"Invalid JSON number: {value}")
                ),
            )
    except FileNotFoundError as error:
        raise CasePersistenceError("Selected case file does not exist.") from error
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CasePersistenceError(f"Could not read case file: {error}") from error
    validate_case_document(document)
    if document["case_id"] != case_id:
        raise CasePersistenceError("Case ID does not match the selected filename.")
    return document


def list_saved_cases(cases_dir):
    cases_path = Path(cases_dir)
    if not cases_path.exists():
        return []
    saved_cases = []
    for case_path in sorted(cases_path.glob("*.json")):
        case_id = case_path.stem
        if not _valid_case_id(case_id):
            continue
        try:
            with case_path.open(encoding="utf-8") as case_file:
                preview = json.load(case_file)
            case_name = preview.get("case_name", case_id) if isinstance(preview, dict) else case_id
            if not isinstance(case_name, str) or not case_name.strip():
                case_name = case_id
        except (OSError, UnicodeError, json.JSONDecodeError):
            case_name = f"{case_id} (invalid file)"
        saved_cases.append({"case_id": case_id, "case_name": case_name})
    return saved_cases


def restore_case(session_state, document):
    validate_case_document(document)
    # Build every restored/derived value before modifying session state.
    risk_answers = deepcopy(document["risk_answers"])
    result = calculate_risk(risk_answers)
    risk_breakdown = [
        (RISK_LABELS[key], RISK_WEIGHTS[key])
        for key, answer in risk_answers.items()
        if answer
    ]
    use_case = deepcopy(document["use_case"])
    evidence = deepcopy(document["control_evidence"])
    plans = deepcopy(document["deployment_readiness_plans"])
    impact_assessments, invalid_impact_assessments = validate_impact_assessments(
        document.get("sdaia_impact_assessments", {})
    )
    widget_values = {
        **{USE_CASE_WIDGET_KEYS[field]: use_case[field] for field in USE_CASE_KEYS},
        **risk_answers,
        **{
            PLAN_WIDGET_KEYS[(group, field)]: plans[group][field]
            for group, fields in PLAN_KEYS.items()
            for field in fields
        },
    }

    restored_values = {
        "_case_load_generation": str(uuid4()),
        "current_case_id": document["case_id"],
        "use_case": use_case,
        "risk_register": deepcopy(document.get("risk_register", [])),
        "risk_decisions": deepcopy(document.get("risk_decisions", {})),
        "corrective_actions": deepcopy(document.get("corrective_actions", [])),
        "risk_answers": risk_answers,
        "control_evidence": evidence,
        "sdaia_impact_assessments": impact_assessments,
        "_sdaia_impact_assessment_invalid": invalid_impact_assessments,
        "deployment_readiness_plans": plans,
        "risk_result": result,
        "risk_score": result.score,
        "governance_tier": result.level,
        "risk_breakdown": risk_breakdown,
    }
    restored_values.update(widget_values)
    if "raci_matrix" in session_state:
        del session_state["raci_matrix"]
    if "raci_matrix" in document:
        restored_values["raci_matrix"] = deepcopy(document["raci_matrix"])
    for key, value in restored_values.items():
        session_state[key] = value
