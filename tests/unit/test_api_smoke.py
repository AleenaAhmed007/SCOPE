"""API smoke tests using FastAPI TestClient."""

from __future__ import annotations

from fastapi.testclient import TestClient

from scope.api.app import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard() -> None:
    r = client.get("/api/v1/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["total_orders"] > 0
    assert "late_delivery_pct" in body


def test_predict_late() -> None:
    r = client.post("/api/v1/predictions/late-delivery", json={"order_id": 1})
    assert r.status_code == 200
    assert "late_probability" in r.json()


def test_predict_duration_reports_confidence() -> None:
    r = client.post("/api/v1/predictions/delivery-duration", json={"order_id": 1})
    assert r.status_code == 200
    assert isinstance(r.json()["low_confidence"], bool)


def test_rag_query() -> None:
    r = client.post("/api/v1/rag/query", json={"query": "late delivery escalation"})
    assert r.status_code == 200
    assert "answer" in r.json()
