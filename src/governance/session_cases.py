"""Session-isolated case snapshots for the public synthetic demo.

No filesystem access, authentication or durable hosted storage is provided.
"""
from copy import deepcopy
import json
from .case_persistence import CasePersistenceError, build_case_document, validate_case_document

MAX_CASE_BYTES = 2 * 1024 * 1024
MAX_CASES = 20
STORE_KEY = "_session_case_snapshots"


def parse_case_upload(payload):
    if not isinstance(payload, bytes) or len(payload) > MAX_CASE_BYTES:
        raise CasePersistenceError("Upload a JSON case no larger than 2 MiB.")
    try:
        document = json.loads(payload.decode("utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        validate_case_document(document)
        return document
    except (UnicodeError, ValueError, TypeError, RecursionError) as error:
        raise CasePersistenceError(f"Invalid case JSON: {error}") from error


def remember_case(state, document):
    validate_case_document(document)
    encoded = json.dumps(document, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(encoded) > MAX_CASE_BYTES:
        raise CasePersistenceError("Case exceeds the 2 MiB download/import limit.")
    snapshots = dict(state.get(STORE_KEY, {}))
    case_id = document["case_id"]
    if case_id not in snapshots and len(snapshots) >= MAX_CASES:
        raise CasePersistenceError("This session has reached its 20-case limit. Download your cases before starting a new session.")
    snapshots[case_id] = deepcopy(document)
    state[STORE_KEY] = snapshots
    return deepcopy(document)


def save_session_case(state):
    return remember_case(state, build_case_document(state))


def load_session_case(state, case_id):
    document = state.get(STORE_KEY, {}).get(case_id)
    if document is None:
        raise CasePersistenceError("Case is not available in this session. Import your downloaded JSON case.")
    validate_case_document(document)
    return deepcopy(document)


def list_session_cases(state):
    return [{"case_id": item["case_id"], "case_name": item["case_name"]}
            for item in state.get(STORE_KEY, {}).values()]
