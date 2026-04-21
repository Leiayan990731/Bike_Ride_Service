import datetime as dt
import hashlib
import json
from typing import Any, Dict


def utcnow() -> dt.datetime:
    return dt.datetime.utcnow().replace(tzinfo=None)


def stable_request_hash(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def datetime_to_iso(dt_value: dt.datetime) -> str:
    # Always serialize without timezone; treated as UTC for this project.
    return dt_value.replace(tzinfo=None).isoformat() + "Z"
