import datetime as dt

from sqlalchemy import Column, DateTime, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Ride(Base):
    __tablename__ = "rides"
    __table_args__ = (
        # Enforce at most one active ride per user.
        Index("uq_rides_active_user", "user_id", unique=True, sqlite_where=text("ended_at IS NULL")),
        # Enforce at most one active ride per bike.
        Index("uq_rides_active_bike", "bike_id", unique=True, sqlite_where=text("ended_at IS NULL")),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    bike_id = Column(String(128), nullable=False, index=True)

    started_at = Column(DateTime(timezone=False), nullable=False, index=True)
    ended_at = Column(DateTime(timezone=False), nullable=True, index=True)

    # optimistic concurrency marker (updated whenever ride changes)
    updated_at = Column(DateTime(timezone=False), nullable=False, index=True)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("key", "endpoint", name="uq_idempotency_key_endpoint"),
    )

    id = Column(Integer, primary_key=True)
    key = Column(String(128), nullable=False)
    endpoint = Column(String(128), nullable=False)
    request_hash = Column(String(64), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=False), nullable=False, default=dt.datetime.utcnow)
