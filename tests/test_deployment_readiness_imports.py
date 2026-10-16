from src.governance.constants import PRE_DEPLOYMENT_CONTROL_IDS
from src.governance.deployment_readiness import evaluate_readiness


def test_deployment_readiness_dependencies_import():
    assert PRE_DEPLOYMENT_CONTROL_IDS
    assert callable(evaluate_readiness)
