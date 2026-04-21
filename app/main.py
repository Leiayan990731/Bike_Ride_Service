from fastapi import Depends, FastAPI, Header, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import text

from app import models, schemas
from app.db import engine, get_db
from app.services.cache import TTLCache
from app.services.idempotency import load_idempotent_response, store_idempotent_response
from app.services.pricing import calculate_duration_seconds, calculate_ride_cost
from app.config import COST_CACHE_TTL_SECONDS
from app.utils import utcnow


app = FastAPI(title="Bike Ride Service API", version="1.0.0")

_cost_cache = TTLCache(ttl_seconds=COST_CACHE_TTL_SECONDS)


@app.on_event("startup")
def _startup():
    models.Base.metadata.create_all(bind=engine)
    # Backfill unique partial indexes for existing SQLite databases.
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_rides_active_user "
                "ON rides(user_id) WHERE ended_at IS NULL"
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_rides_active_bike "
                "ON rides(bike_id) WHERE ended_at IS NULL"
            )
        )


@app.post("/ride/start", response_model=schemas.RideResponse, status_code=201)
def start_ride(
    payload: schemas.RideStartRequest,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    endpoint = "POST /ride/start"
    body = payload.dict()
    existing = load_idempotent_response(db, endpoint=endpoint, key=idempotency_key, payload=body)
    if existing:
        status_code, data = existing
        response.status_code = status_code
        return data

    ongoing_user_ride = (
        db.query(models.Ride)
        .filter(models.Ride.user_id == payload.user_id, models.Ride.ended_at.is_(None))
        .first()
    )
    if ongoing_user_ride:
        raise HTTPException(status_code=409, detail="User is already on a ride")

    ongoing_bike_ride = (
        db.query(models.Ride)
        .filter(models.Ride.bike_id == payload.bike_id, models.Ride.ended_at.is_(None))
        .first()
    )
    if ongoing_bike_ride:
        raise HTTPException(status_code=409, detail="Bike is currently in use")

    now = utcnow()
    ride = models.Ride(
        user_id=payload.user_id,
        bike_id=payload.bike_id,
        started_at=now,
        ended_at=None,
        updated_at=now,
    )
    db.add(ride)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Unique partial indexes are the final guard in concurrent requests.
        user_conflict = (
            db.query(models.Ride)
            .filter(models.Ride.user_id == payload.user_id, models.Ride.ended_at.is_(None))
            .first()
        )
        if user_conflict:
            raise HTTPException(status_code=409, detail="User is already on a ride")
        bike_conflict = (
            db.query(models.Ride)
            .filter(models.Ride.bike_id == payload.bike_id, models.Ride.ended_at.is_(None))
            .first()
        )
        if bike_conflict:
            raise HTTPException(status_code=409, detail="Bike is currently in use")
        raise
    db.refresh(ride)

    data = schemas.RideResponse.from_orm(ride).dict()
    store_idempotent_response(
        db,
        endpoint=endpoint,
        key=idempotency_key,
        payload=body,
        status_code=201,
        response_body=data,
    )
    return data


@app.post("/ride/end", response_model=schemas.RideResponse)
def end_ride(
    payload: schemas.RideEndRequest,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    endpoint = "POST /ride/end"
    body = payload.dict()
    existing = load_idempotent_response(db, endpoint=endpoint, key=idempotency_key, payload=body)
    if existing:
        status_code, data = existing
        response.status_code = status_code
        return data

    ride = db.query(models.Ride).filter(models.Ride.id == payload.ride_id).one_or_none()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    now = utcnow()
    if ride.ended_at is None:
        ride.ended_at = now
        ride.updated_at = now
        db.add(ride)
        db.commit()
        db.refresh(ride)

        _cost_cache.invalidate(str(ride.id))

    data = schemas.RideResponse.from_orm(ride).dict()
    store_idempotent_response(
        db,
        endpoint=endpoint,
        key=idempotency_key,
        payload=body,
        status_code=200,
        response_body=data,
    )
    return data


@app.get("/ride/{id}", response_model=schemas.RideResponse)
def get_ride(id: int, db: Session = Depends(get_db)):
    ride = db.query(models.Ride).filter(models.Ride.id == id).one_or_none()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return schemas.RideResponse.from_orm(ride).dict()


@app.get("/ride/{id}/cost", response_model=schemas.RideCostResponse)
def get_ride_cost(id: int, db: Session = Depends(get_db)):
    cached = _cost_cache.get(str(id))
    if cached is not None:
        return cached

    ride = db.query(models.Ride).filter(models.Ride.id == id).one_or_none()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    if ride.ended_at is None:
        raise HTTPException(status_code=409, detail="Ride has not ended yet")

    cost = calculate_ride_cost(ride.started_at, ride.ended_at)
    duration_seconds = calculate_duration_seconds(ride.started_at, ride.ended_at)
    out = schemas.RideCostResponse(
        ride_id=ride.id,
        currency="HKD",
        cost=cost,
        duration_seconds=duration_seconds,
        started_at=ride.started_at,
        ended_at=ride.ended_at,
    ).dict()
    _cost_cache.set(str(id), out)
    return out

