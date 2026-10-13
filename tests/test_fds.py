"""M3 FDS engine tests.

The config is constructed explicitly rather than read from the environment so these
tests are immune to whatever is set on the developer's machine.
"""

from __future__ import annotations

import pytest

from app.config import FdsConfig
from app.schemas.behavior import BehaviorAnalysisRequest
from app.services import fds

CONFIG = FdsConfig(
    scroll_weight=0.40,
    switch_weight=0.25,
    session_weight=0.35,
    idle_recovery=0.30,
    normal_threshold=40.0,
    high_threshold=70.0,
    observation_window_seconds=30,
    scroll_normalization_max=60,
    switch_normalization_max=6,
    session_normalization_seconds=300,
    idle_start_seconds=10,
    idle_recovery_max_seconds=60,
    soft_count_rolling_hours=24,
    soft_1_seconds=8,
    soft_2_seconds=15,
    soft_3_seconds=30,
)


def make_request(**overrides) -> BehaviorAnalysisRequest:
    payload = {
        "session_id": "session",
        "request_id": "request",
        "observation_window_seconds": 30,
        "scroll_events": 0,
        "social_app_switches": 0,
        "active_social_session_seconds": 0.0,
        "idle_seconds": 0.0,
        "foreground_package": "com.instagram.android",
        "soft_intervention_count_24h": 0,
    }
    payload.update(overrides)
    return BehaviorAnalysisRequest(**payload)


# --- normalization -------------------------------------------------------------


def test_normalization_maps_each_input_onto_zero_to_one() -> None:
    inputs = fds.normalize(
        make_request(
            scroll_events=30,
            social_app_switches=3,
            active_social_session_seconds=150.0,
            idle_seconds=30.0,
        ),
        CONFIG,
    )

    assert inputs.scroll == pytest.approx(0.5)
    assert inputs.switching == pytest.approx(0.5)
    assert inputs.session == pytest.approx(0.5)
    assert inputs.idle == pytest.approx(0.5)


def test_normalization_saturates_above_each_maximum() -> None:
    inputs = fds.normalize(
        make_request(
            scroll_events=6000,
            social_app_switches=600,
            active_social_session_seconds=99_999.0,
            idle_seconds=99_999.0,
        ),
        CONFIG,
    )

    assert inputs.scroll == 1.0
    assert inputs.switching == 1.0
    assert inputs.session == 1.0
    assert inputs.idle == 1.0


# --- formula -------------------------------------------------------------------


def test_quiet_usage_scores_zero() -> None:
    assert fds.score(fds.normalize(make_request(), CONFIG), CONFIG) == 0.0


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"scroll_events": 60}, 40.0),
        ({"social_app_switches": 6}, 25.0),
        ({"active_social_session_seconds": 300.0}, 35.0),
    ],
)
def test_each_factor_contributes_its_weight(overrides: dict, expected: float) -> None:
    scored = fds.score(fds.normalize(make_request(**overrides), CONFIG), CONFIG)
    assert scored == pytest.approx(expected)


def test_all_factors_saturated_reaches_one_hundred() -> None:
    request = make_request(
        scroll_events=60,
        social_app_switches=6,
        active_social_session_seconds=300.0,
    )
    assert fds.score(fds.normalize(request, CONFIG), CONFIG) == pytest.approx(100.0)


def test_idle_subtracts_as_recovery() -> None:
    request = make_request(
        scroll_events=60,
        social_app_switches=6,
        active_social_session_seconds=300.0,
        idle_seconds=60.0,
    )
    # 1.0 of weighted activity minus 0.30 of recovery credit
    assert fds.score(fds.normalize(request, CONFIG), CONFIG) == pytest.approx(70.0)


def test_score_is_clipped_at_zero() -> None:
    request = make_request(idle_seconds=60.0)
    assert fds.score(fds.normalize(request, CONFIG), CONFIG) == 0.0


# --- thresholds ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("fds_value", "expected"),
    [
        (0.0, fds.NORMAL),
        (39.99, fds.NORMAL),
        (40.0, fds.ELEVATED),
        (69.99, fds.ELEVATED),
        (70.0, fds.HIGH),
        (100.0, fds.HIGH),
    ],
)
def test_threshold_boundaries(fds_value: float, expected: str) -> None:
    assert fds.classify(fds_value, CONFIG) == expected


def test_scroll_alone_lands_exactly_on_the_elevated_boundary() -> None:
    request = make_request(scroll_events=60)
    scored = fds.score(fds.normalize(request, CONFIG), CONFIG)
    assert scored == pytest.approx(40.0)
    assert fds.classify(scored, CONFIG) == fds.ELEVATED


# --- escalation ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("count", "seconds"),
    [(0, 8), (1, 15), (2, 30), (3, 30), (99, 30)],
)
def test_soft_duration_escalates_and_then_plateaus(count: int, seconds: int) -> None:
    assert fds.soft_duration(count, CONFIG) == seconds


# --- policy guarantee ----------------------------------------------------------


def test_normal_snapshot_asks_for_nothing() -> None:
    response = fds.evaluate(make_request(), CONFIG)
    assert response.action == fds.ACTION_NONE
    assert response.cooldown_seconds == 0


def test_elevated_snapshot_asks_for_a_soft_intervention() -> None:
    response = fds.evaluate(make_request(scroll_events=60), CONFIG)
    assert response.level == fds.ELEVATED
    assert response.action == fds.ACTION_SOFT
    assert response.cooldown_seconds == 8


def test_evaluation_is_deterministic() -> None:
    request = make_request(scroll_events=42, social_app_switches=3)
    assert fds.evaluate(request, CONFIG) == fds.evaluate(request, CONFIG)


def test_fds_never_emits_a_hard_block() -> None:
    """FR-10 and Appendix D.3. Swept rather than asserted on a single case."""
    forbidden = {"HARD_INTERVENTION", "BLOCK", "FULL_BLOCK", "LOCK"}

    for scroll in (0, 15, 30, 45, 60, 120):
        for switches in (0, 3, 6, 12):
            for session in (0.0, 75.0, 150.0, 300.0, 900.0):
                for idle in (0.0, 15.0, 30.0, 60.0):
                    response = fds.evaluate(
                        make_request(
                            scroll_events=scroll,
                            social_app_switches=switches,
                            active_social_session_seconds=session,
                            idle_seconds=idle,
                        ),
                        CONFIG,
                    )
                    assert response.action not in forbidden
                    assert response.action in {fds.ACTION_NONE, fds.ACTION_SOFT}
                    assert 0.0 <= response.fds <= 100.0


def test_fds_is_monotonic_in_scrolling() -> None:
    previous = -1.0
    for scroll in range(0, 61, 5):
        scored = fds.score(fds.normalize(make_request(scroll_events=scroll), CONFIG), CONFIG)
        assert scored >= previous
        previous = scored
