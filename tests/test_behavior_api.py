"""M3 endpoint tests: routing, auth, and the payload contract."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app

TOKEN = "test-token-abc123"

BASE_CONFIG = Settings(
    backend_token=TOKEN,
    backend_host="0.0.0.0",
    backend_port=8000,
    fds=get_settings().fds,
)

ANON_CONFIG = Settings(
    backend_token="",
    backend_host="0.0.0.0",
    backend_port=8000,
    fds=get_settings().fds,
)


def payload(**overrides) -> dict:
    body = {
        "session_id": "3f1c8a20-77bd-4e2a-9f31-0c2b6d5e8a11",
        "request_id": "b7e4d9c1-2f55-4a80-9d13-6e0a1c4f2b33",
        "observation_window_seconds": 30,
        "scroll_events": 0,
        "social_app_switches": 0,
        "active_social_session_seconds": 0.0,
        "idle_seconds": 0.0,
        "foreground_package": "com.instagram.android",
        "soft_intervention_count_24h": 0,
    }
    body.update(overrides)
    return body


def client(config: Settings) -> TestClient:
    app.dependency_overrides[get_settings] = lambda: config
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


# --- routing -------------------------------------------------------------------


def test_quiet_usage_scores_zero_and_asks_for_nothing() -> None:
    response = client(ANON_CONFIG).post("/api/analyze-behavior", json=payload())

    assert response.status_code == 200
    body = response.json()
    assert body["fds"] == 0.0
    assert body["level"] == "NORMAL"
    assert body["action"] == "NONE"
    assert body["cooldown_seconds"] == 0


def test_heavy_usage_asks_for_a_soft_intervention() -> None:
    response = client(ANON_CONFIG).post(
        "/api/analyze-behavior",
        json=payload(scroll_events=60, social_app_switches=6, active_social_session_seconds=300.0),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["fds"] == 100.0
    assert body["level"] == "HIGH"
    assert body["action"] == "SOFT_INTERVENTION"


def test_escalation_uses_the_client_supplied_soft_count() -> None:
    http = client(ANON_CONFIG)
    heavy = payload(scroll_events=60, social_app_switches=6, active_social_session_seconds=300.0)

    first = http.post("/api/analyze-behavior", json=heavy | {"soft_intervention_count_24h": 0}).json()
    third = http.post("/api/analyze-behavior", json=heavy | {"soft_intervention_count_24h": 2}).json()

    assert first["cooldown_seconds"] == 8
    assert third["cooldown_seconds"] == 30


def test_invalid_payload_is_rejected() -> None:
    response = client(ANON_CONFIG).post(
        "/api/analyze-behavior",
        json=payload(scroll_events=-1),
    )
    assert response.status_code == 422


def test_missing_identifiers_are_rejected() -> None:
    body = payload()
    del body["session_id"]
    response = client(ANON_CONFIG).post("/api/analyze-behavior", json=body)
    assert response.status_code == 422


def test_endpoint_never_returns_a_hard_block() -> None:
    http = client(ANON_CONFIG)
    for scroll in (0, 30, 60, 240):
        for switches in (0, 6, 24):
            for session in (0.0, 300.0, 1800.0):
                body = http.post(
                    "/api/analyze-behavior",
                    json=payload(
                        scroll_events=scroll,
                        social_app_switches=switches,
                        active_social_session_seconds=session,
                    ),
                ).json()
                assert body["action"] in {"NONE", "SOFT_INTERVENTION"}


# --- authentication ------------------------------------------------------------


def test_token_is_required_when_configured() -> None:
    response = client(BASE_CONFIG).post("/api/analyze-behavior", json=payload())
    assert response.status_code == 401
    assert response.json()["detail"]["error"]["code"] == "UNAUTHORIZED"


def test_wrong_token_is_rejected() -> None:
    response = (
        client(BASE_CONFIG)
        .post("/api/analyze-behavior", json=payload(), headers={"Authorization": "Bearer wrong"})
    )
    assert response.status_code == 401


def test_correct_token_is_accepted() -> None:
    response = (
        client(BASE_CONFIG)
        .post("/api/analyze-behavior", json=payload(), headers={"Authorization": f"Bearer {TOKEN}"})
    )
    assert response.status_code == 200


def test_health_stays_unauthenticated() -> None:
    assert client(BASE_CONFIG).get("/health").status_code == 200


def test_no_token_configured_means_no_auth() -> None:
    assert client(ANON_CONFIG).post("/api/analyze-behavior", json=payload()).status_code == 200
