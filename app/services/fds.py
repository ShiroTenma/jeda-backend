"""Focus Deficit Score engine.

Pure functions, no framework types beyond the request model, so the formula is
directly unit-testable against fixtures (M3 acceptance).

Policy constraint enforced structurally: this module cannot emit a hard block.
`evaluate` only ever returns `NONE` or `SOFT_INTERVENTION`, and the response model
types the action as a Literal, so a hard block is unrepresentable on this path.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import FdsConfig
from app.schemas.behavior import BehaviorAnalysisRequest, BehaviorAnalysisResponse

NORMAL = "NORMAL"
ELEVATED = "ELEVATED"
HIGH = "HIGH"

ACTION_NONE = "NONE"
ACTION_SOFT = "SOFT_INTERVENTION"


@dataclass(frozen=True)
class NormalizedInputs:
    """All four factors on 0..1, ready for the weighted sum."""

    scroll: float
    switching: float
    session: float
    idle: float


def _clip01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _ratio(value: float, maximum: float) -> float:
    if maximum <= 0:
        return 0.0
    return _clip01(value / maximum)


def normalize(request: BehaviorAnalysisRequest, config: FdsConfig) -> NormalizedInputs:
    return NormalizedInputs(
        scroll=_ratio(request.scroll_events, config.scroll_normalization_max),
        switching=_ratio(request.social_app_switches, config.switch_normalization_max),
        session=_ratio(request.active_social_session_seconds, config.session_normalization_seconds),
        idle=_ratio(request.idle_seconds, config.idle_recovery_max_seconds),
    )


def score(inputs: NormalizedInputs, config: FdsConfig) -> float:
    """FDS = 100 * clip(wv*Vn + ws*Sn + wt*Tn - lambda*In, 0, 1)."""
    combined = (
        config.scroll_weight * inputs.scroll
        + config.switch_weight * inputs.switching
        + config.session_weight * inputs.session
        - config.idle_recovery * inputs.idle
    )
    return 100.0 * _clip01(combined)


def classify(fds: float, config: FdsConfig) -> str:
    if fds >= config.high_threshold:
        return HIGH
    if fds >= config.normal_threshold:
        return ELEVATED
    return NORMAL


def soft_duration(soft_count_24h: int, config: FdsConfig) -> int:
    """Escalation ladder: 8s, 15s, 30s, then the longest for anything beyond."""
    index = min(max(soft_count_24h, 0), 2)
    if index == 0:
        return config.soft_1_seconds
    if index == 1:
        return config.soft_2_seconds
    return config.soft_3_seconds


def evaluate(
    request: BehaviorAnalysisRequest,
    config: FdsConfig,
) -> BehaviorAnalysisResponse:
    inputs = normalize(request, config)
    fds = score(inputs, config)
    level = classify(fds, config)

    if level == NORMAL:
        return BehaviorAnalysisResponse(
            fds=round(fds, 2),
            level=level,
            action=ACTION_NONE,
            cooldown_seconds=0,
        )

    return BehaviorAnalysisResponse(
        fds=round(fds, 2),
        level=level,
        action=ACTION_SOFT,
        cooldown_seconds=soft_duration(request.soft_intervention_count_24h, config),
    )
