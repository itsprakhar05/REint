import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.elexon_repository import fetch_dataset


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_fetch_dataset_returns_list(monkeypatch):
    async def fake_get(self, url, params):
        assert url.endswith("/datasets/WINDFOR/stream")
        assert params["publishDateTimeFrom"] == "2026-01-01T00:00:00Z"
        return DummyResponse([
            {"startTime": "2026-01-01T00:00:00Z", "generation": 100},
        ])

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    payload = httpx.AsyncClient
    assert payload is not None

    import asyncio

    result = asyncio.run(
        fetch_dataset(
            "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream",
            {"publishDateTimeFrom": "2026-01-01T00:00:00Z", "publishDateTimeTo": "2026-01-02T00:00:00Z"},
        )
    )

    assert result == [{"startTime": "2026-01-01T00:00:00Z", "generation": 100}]


def test_accuracy_endpoint_returns_metrics(monkeypatch):
    async def fake_get(self, url, params):
        payload = [
            {
                "startTime": "2026-01-01T00:00:00Z",
                "publishTime": "2026-01-01T00:05:00Z",
                "generation": 100,
            },
            {
                "startTime": "2026-01-01T00:30:00Z",
                "publishTime": "2026-01-01T00:35:00Z",
                "generation": 120,
            },
        ]
        if url.endswith("/datasets/FUELHH/stream"):
            return DummyResponse([
                {"startTime": "2026-01-01T00:00:00Z", "fuelType": "WIND", "generation": 90},
                {"startTime": "2026-01-01T00:30:00Z", "fuelType": "WIND", "generation": 130},
            ])
        return DummyResponse(payload)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    client = TestClient(app)
    response = client.get(
        "/api/v1/analytics/accuracy",
        params={"start": "2026-01-01T00:00:00Z", "end": "2026-01-01T01:00:00Z"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched_intervals"] == 2
    assert payload["mae_mw"] == 10.0
    assert payload["rmse_mw"] == 10.0
    assert payload["bias_mw"] == 0.0


def test_accuracy_endpoint_accepts_valid_day_range_without_false_400(monkeypatch):
    async def fake_get(self, url, params):
        return DummyResponse([])

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    client = TestClient(app)
    response = client.get(
        "/api/v1/analytics/accuracy",
        params={"start": "2026-01-01T00:00:00Z", "end": "2026-01-02T00:00:00Z"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched_intervals"] > 0


def test_series_endpoint_returns_point_data(monkeypatch):
    async def fake_get(self, url, params):
        if url.endswith("/datasets/FUELHH/stream"):
            return DummyResponse([
                {"startTime": "2026-01-01T00:00:00Z", "fuelType": "WIND", "generation": 90},
                {"startTime": "2026-01-01T00:30:00Z", "fuelType": "WIND", "generation": 110},
            ])
        return DummyResponse([
            {"startTime": "2026-01-01T00:00:00Z", "publishTime": "2025-12-31T23:55:00Z", "generation": 100},
            {"startTime": "2026-01-01T00:30:00Z", "publishTime": "2026-01-01T00:25:00Z", "generation": 120},
        ])

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    client = TestClient(app)
    response = client.get(
        "/api/v1/analytics/series",
        params={"start": "2026-01-01T00:00:00Z", "end": "2026-01-01T01:00:00Z"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["series"]) == 2
    assert payload["series"][0]["forecast_mw"] == 100
    assert payload["series"][0]["actual_mw"] == 90


def test_wind_filter_keeps_only_wind_records():
    rows = [
        {"fuelType": "WIND", "generation": 100},
        {"fuelType": "SOLAR", "generation": 200},
    ]

    filtered = [row for row in rows if str(row.get("fuelType", "")).upper() == "WIND"]

    assert filtered == [{"fuelType": "WIND", "generation": 100}]
