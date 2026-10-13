"""Contract tests for the M2 behavioural snapshot.

The Android client and this backend are written independently, so the payload
shape is the thing most likely to drift. These tests pin the field names and the
validation rules the aggregator depends on.
"""

import pytest
from pydantic import ValidationError

from app.schemas.behavior import BehaviorAnalysisRequest, BehaviorAnalysisResponse


def valid_payload() -> dict:
    return {
        "session_id": "3f1c8a20-77bd-4e2a-9f31-0c2b6d5e8a11",
        "request_id": "b7e4d9c1-2f55-4a80-9d13-6e0a1c4f2b33",
        "observation_window_seconds": 30,
        "scroll_events": 42,
        "social_app_switches": 3,
        "active_social_session_seconds": 186.0,
        "idle_seconds": 0.0,
        "foreground_package": "com.instagram.android",
        "soft_intervention_count_24h": 1,
    }


def test_snapshot_parses_with_raw_counters() -> None:
    snapshot = BehaviorAnalysisRequest(**valid_payload())

    assert snapshot.scroll_events == 42
    assert snapshot.social_app_switches == 3
    assert snapshot.active_social_session_seconds == 186.0
    assert snapshot.idle_seconds == 0.0
    assert snapshot.foreground_package == "com.instagram.android"
    assert snapshot.soft_intervention_count_24h == 1


def test_foreground_package_is_optional() -> None:
    payload = valid_payload() | {"foreground_package": None}
    assert BehaviorAnalysisRequest(**payload).foreground_package is None


def test_soft_intervention_count_defaults_to_zero() -> None:
    payload = valid_payload()
    del payload["soft_intervention_count_24h"]
    assert BehaviorAnalysisRequest(**payload).soft_intervention_count_24h == 0


@pytest.mark.parametrize("field", ["scroll_events", "social_app_switches", "idle_seconds"])
def test_negative_counters_are_rejected(field: str) -> None:
    with pytest.raises(ValidationError):
        BehaviorAnalysisRequest(**(valid_payload() | {field: -1}))


@pytest.mark.parametrize("field", ["session_id", "request_id"])
def test_identifiers_are_required(field: str) -> None:
    payload = valid_payload()
    del payload[field]
    with pytest.raises(ValidationError):
        BehaviorAnalysisRequest(**payload)


def test_response_rejects_fds_outside_range() -> None:
    with pytest.raises(ValidationError):
        BehaviorAnalysisResponse(
            fds=120.0,
            level="HIGH",
            action="HARD_INTERVENTION",
            cooldown_seconds=8,
        )


def test_response_rejects_a_hard_intervention_action() -> None:
    """FDS may never hard-block, at any score (FR-10, Appendix D.3)."""
    for action in ("HARD_INTERVENTION", "BLOCK", "FULL_BLOCK"):
        with pytest.raises(ValidationError):
            BehaviorAnalysisResponse(
                fds=99.0,
                level="HIGH",
                action=action,
                cooldown_seconds=30,
            )


def test_response_accepts_a_soft_intervention() -> None:
    response = BehaviorAnalysisResponse(
        fds=58.2,
        level="ELEVATED",
        action="SOFT_INTERVENTION",
        cooldown_seconds=15,
    )
    assert response.fds == 58.2
