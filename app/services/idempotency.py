import json
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import IdempotencyKey
from app.utils import stable_request_hash


def load_idempotent_response(
    db: Session, *, endpoint: str, key: str, payload: Dict[str, Any]
) -> Optional[Tuple[int, Dict[str, Any]]]:
    req_hash = stable_request_hash(payload)
    row = (
        db.query(IdempotencyKey)
        .filter(IdempotencyKey.key == key, IdempotencyKey.endpoint == endpoint)
        .one_or_none()
    )
    if not row:
        return None
    if row.request_hash != req_hash:
        raise HTTPException(
            status_code=409,
            detail="Idempotency-Key reuse with different request body",
        )
    return row.status_code, json.loads(row.response_body)


def store_idempotent_response(
    db: Session,
    *,
    endpoint: str,
    key: str,
    payload: Dict[str, Any],
    status_code: int,
    response_body: Dict[str, Any],
) -> None:
    req_hash = stable_request_hash(payload)
    encoded_body = jsonable_encoder(response_body)
    row = IdempotencyKey(
        key=key,
        endpoint=endpoint,
        request_hash=req_hash,
        status_code=int(status_code),
        response_body=json.dumps(encoded_body, sort_keys=True, separators=(",", ":")),
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(IdempotencyKey)
            .filter(IdempotencyKey.key == key, IdempotencyKey.endpoint == endpoint)
            .one_or_none()
        )
        if not existing:
            return
        if existing.request_hash != req_hash:
            raise HTTPException(
                status_code=409,
                detail="Idempotency-Key reuse with different request body",
            )
