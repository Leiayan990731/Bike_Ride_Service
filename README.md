# Bike Ride Service API (FastAPI + SQLite)

Simple API to start/end bike rides, fetch ride details, and calculate ride cost.

## Features

- **Endpoints**
  - `POST /ride/start`: create a ride session
  - `POST /ride/end`: end a ride session
  - `GET /ride/{id}`: get ride details
  - `GET /ride/{id}/cost`: get ride fare
- **Pricing**
  - Unlock fee: HKD 5
  - First 15 minutes: free
  - After 15 minutes: HKD 1 per 5 minutes (rounded up to the next 5-minute block)
  - Daily cap: HKD 25 (per calendar day, based on ride start date in UTC)
- **Idempotency + duplicate request handling**
  - `POST /ride/start` and `POST /ride/end` require `Idempotency-Key` in request headers.
  - Reusing the same key with the same request body returns the previous response.
  - Reusing the same key with a different request body returns `409`.
  - `POST /ride/start` also enforces one active ride per user and one active ride per bike (app checks + DB unique indexes).
- **Caching**
  - Small in-memory TTL cache for `/ride/{id}/cost` to reduce DB reads for repeated requests.
- **Concurrency-aware**
  - SQLite transactions for state transitions; safe handling for duplicate end requests.

## Requirements

- Python **3.7+**

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- Swagger UI: `http://127.0.0.1:8000/docs`

## Example requests

Start a ride:

```bash
curl -X POST "http://127.0.0.1:8000/ride/start" ^
  -H "Content-Type: application/json" ^
  -H "Idempotency-Key: demo-start-1" ^
  -d "{\"user_id\":\"u1\",\"bike_id\":\"b1\"}"
```

End a ride:

```bash
curl -X POST "http://127.0.0.1:8000/ride/end" ^
  -H "Content-Type: application/json" ^
  -H "Idempotency-Key: demo-end-1" ^
  -d "{\"ride_id\":1}"
```

Get ride:

```bash
curl "http://127.0.0.1:8000/ride/1"
```

Get cost:

```bash
curl "http://127.0.0.1:8000/ride/1/cost"
```

## Tests

```bash
pytest -q
```

## Notes / trade-offs

- SQLite stores timestamps as UTC ISO-8601 strings for portability.
- The daily cap is applied per ride (this assignment asks for “fare for the ride”). If you later need a true “per-user-per-day across all rides” cap, you’d add a daily ledger table keyed by user+date and sum rides into it.