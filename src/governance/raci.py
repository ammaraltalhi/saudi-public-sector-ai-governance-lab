"""Case-specific RACI document validation."""

COLUMNS = ("Activity", "Business Owner", "AI/Product Team", "AI Governance",
           "Data Owner / Data Governance", "Privacy / DPO", "Information Security",
           "Executive Sponsor", "Internal Audit")


def raci_errors(records):
    if not isinstance(records, list) or not 1 <= len(records) <= 200:
        return ["RACI needs 1–200 activity rows."]
    errors, activities = [], set()
    for index, row in enumerate(records, 1):
        if not isinstance(row, dict) or set(row) != set(COLUMNS) or any(not isinstance(v, str) for v in row.values()):
            errors.append(f"RACI row {index}: use the expected text columns.")
            continue
        activity = row["Activity"].strip()
        if not activity or activity.casefold() in activities:
            errors.append(f"RACI row {index}: activity must be non-empty and unique.")
        activities.add(activity.casefold())
        accountable = 0
        for role in COLUMNS[1:]:
            value = row[role].strip().upper()
            tokens = value.split("/") if value else []
            if any(token not in {"A", "R", "C", "I"} for token in tokens) or len(tokens) != len(set(tokens)):
                errors.append(f"RACI row {index}: {role} must use A, R, C, I or slash-separated combinations.")
            accountable += int("A" in tokens)
        if accountable != 1:
            errors.append(f"RACI row {index}: expected one Accountable role; found {accountable}.")
    return errors


def normalize_raci(records):
    """Normalize grid blanks without converting non-text input into apparent evidence."""
    return [{key: ("" if value is None else value.strip().upper() if key != "Activity" and isinstance(value, str)
                   else value.strip() if isinstance(value, str) else value)
             for key, value in row.items()} for row in records]
