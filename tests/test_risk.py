from src.governance.risk import calculate_risk


def test_low_risk():
    result = calculate_risk({"external_users": True})
    assert result.level == "Low"


def test_medium_risk():
    result = calculate_risk({"personal_data": True, "automated_action": True, "external_users": True})
    assert result.level == "Medium"


def test_high_risk():
    result = calculate_risk({
        "personal_data": True,
        "sensitive_data": True,
        "significant_decision": True,
        "automated_action": True,
    })
    assert result.level == "High"
