import os


def _default_db_url() -> str:
    # Keep a simple, local sqlite file by default.
    # Can be overridden via environment variable for tests or deployment.
    return "sqlite:///./bike_ride_service.db"


DATABASE_URL = os.getenv("DATABASE_URL", _default_db_url())

# Cost cache TTL (seconds) for GET /ride/{id}/cost
COST_CACHE_TTL_SECONDS = int(os.getenv("COST_CACHE_TTL_SECONDS", "5"))
