import os

from fastapi.testclient import TestClient


def _make_client(tmp_path):
    # Use a per-test sqlite file to keep tests isolated.
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = "sqlite:///%s" % str(db_path)

    # Import after setting env so app uses the test DB.
    from app.main import app

    return TestClient(app)


def test_start_end_get_cost_happy_path(tmp_path):
    with _make_client(tmp_path) as client:
        start = client.post(
            "/ride/start",
            headers={"Idempotency-Key": "start-k1"},
            json={"user_id": "u1", "bike_id": "b1"},
        )
        assert start.status_code == 201, start.text
        ride = start.json()
        ride_id = ride["id"]

        get1 = client.get("/ride/%s" % ride_id)
        assert get1.status_code == 200
        assert get1.json()["ended_at"] is None

        cost_before_end = client.get("/ride/%s/cost" % ride_id)
        assert cost_before_end.status_code == 409

        end = client.post(
            "/ride/end",
            headers={"Idempotency-Key": "end-k1"},
            json={"ride_id": ride_id},
        )
        assert end.status_code == 200

        cost = client.get("/ride/%s/cost" % ride_id)
        assert cost.status_code == 200
        payload = cost.json()
        assert payload["currency"] == "HKD"
        assert isinstance(payload["cost"], float)
        assert payload["cost"] >= 5.00
        assert payload["cost"] == round(payload["cost"], 2)


def test_start_rejects_user_with_ongoing_ride(tmp_path):
    with _make_client(tmp_path) as client:
        r1 = client.post(
            "/ride/start",
            headers={"Idempotency-Key": "start-user-1"},
            json={"user_id": "u1", "bike_id": "b1"},
        )
        assert r1.status_code == 201

        r2 = client.post(
            "/ride/start",
            headers={"Idempotency-Key": "start-user-2"},
            json={"user_id": "u1", "bike_id": "b1"},
        )
        assert r2.status_code == 409
        assert r2.json()["detail"] == "User is already on a ride"


def test_start_rejects_bike_already_in_use(tmp_path):
    with _make_client(tmp_path) as client:
        r1 = client.post(
            "/ride/start",
            headers={"Idempotency-Key": "start-bike-1"},
            json={"user_id": "u3", "bike_id": "b3"},
        )
        assert r1.status_code == 201

        r2 = client.post(
            "/ride/start",
            headers={"Idempotency-Key": "start-bike-2"},
            json={"user_id": "u4", "bike_id": "b3"},
        )
        assert r2.status_code == 409
        assert r2.json()["detail"] == "Bike is currently in use"


def test_end_duplicate_request_with_same_key_is_idempotent(tmp_path):
    with _make_client(tmp_path) as client:
        start = client.post(
            "/ride/start",
            headers={"Idempotency-Key": "start-enddup-1"},
            json={"user_id": "u5", "bike_id": "b5"},
        )
        assert start.status_code == 201
        ride_id = start.json()["id"]

        end1 = client.post(
            "/ride/end",
            headers={"Idempotency-Key": "end-dup-1"},
            json={"ride_id": ride_id},
        )
        assert end1.status_code == 200
        ended_at_first = end1.json()["ended_at"]
        assert ended_at_first is not None

        end2 = client.post(
            "/ride/end",
            headers={"Idempotency-Key": "end-dup-1"},
            json={"ride_id": ride_id},
        )
        assert end2.status_code == 200
        # Duplicate request with same idempotency key returns same response.
        assert end2.json()["ended_at"] == ended_at_first


def test_missing_idempotency_key_returns_validation_error(tmp_path):
    with _make_client(tmp_path) as client:
        start = client.post("/ride/start", json={"user_id": "u10", "bike_id": "b10"})
        assert start.status_code == 422

        create = client.post(
            "/ride/start",
            headers={"Idempotency-Key": "start-missing-end-key"},
            json={"user_id": "u11", "bike_id": "b11"},
        )
        assert create.status_code == 201
        ride_id = create.json()["id"]

        end = client.post("/ride/end", json={"ride_id": ride_id})
        assert end.status_code == 422

