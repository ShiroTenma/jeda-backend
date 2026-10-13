"""Typed prototype configuration.

Values are read once at startup into a frozen dataclass. No module reaches for
`os.environ` directly, so every tunable is visible in one place and can be
overridden by environment variable without editing formula code.

Defaults match the SRS Appendix C baseline. They are calibration targets, not
validated measurements.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _raw(key: str) -> str | None:
    value = os.environ.get(key)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _float(key: str, default: float) -> float:
    raw = _raw(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{key} must be a number, got {raw!r}") from exc


def _int(key: str, default: int) -> int:
    raw = _raw(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer, got {raw!r}") from exc


def _str(key: str, default: str) -> str:
    return _raw(key) or default


@dataclass(frozen=True)
class FdsConfig:
    scroll_weight: float
    switch_weight: float
    session_weight: float
    idle_recovery: float
    normal_threshold: float
    high_threshold: float
    observation_window_seconds: int
    scroll_normalization_max: int
    switch_normalization_max: int
    session_normalization_seconds: int
    idle_start_seconds: int
    idle_recovery_max_seconds: int
    soft_count_rolling_hours: int
    soft_1_seconds: int
    soft_2_seconds: int
    soft_3_seconds: int

    @classmethod
    def from_env(cls) -> "FdsConfig":
        return cls(
            scroll_weight=_float("FDS_SCROLL_WEIGHT", 0.40),
            switch_weight=_float("FDS_SWITCH_WEIGHT", 0.25),
            session_weight=_float("FDS_SESSION_WEIGHT", 0.35),
            idle_recovery=_float("FDS_IDLE_RECOVERY", 0.30),
            normal_threshold=_float("FDS_NORMAL_THRESHOLD", 40.0),
            high_threshold=_float("FDS_HIGH_THRESHOLD", 70.0),
            observation_window_seconds=_int("FDS_OBSERVATION_WINDOW_SECONDS", 30),
            scroll_normalization_max=_int("FDS_SCROLL_NORMALIZATION_MAX", 60),
            switch_normalization_max=_int("FDS_SWITCH_NORMALIZATION_MAX", 6),
            session_normalization_seconds=_int("FDS_SESSION_NORMALIZATION_SECONDS", 300),
            idle_start_seconds=_int("FDS_IDLE_START_SECONDS", 10),
            idle_recovery_max_seconds=_int("FDS_IDLE_RECOVERY_MAX_SECONDS", 60),
            soft_count_rolling_hours=_int("FDS_SOFT_COUNT_ROLLING_HOURS", 24),
            soft_1_seconds=_int("FDS_SOFT_1_SECONDS", 8),
            soft_2_seconds=_int("FDS_SOFT_2_SECONDS", 15),
            soft_3_seconds=_int("FDS_SOFT_3_SECONDS", 30),
        )


@dataclass(frozen=True)
class Settings:
    backend_token: str
    backend_host: str
    backend_port: int
    fds: FdsConfig

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            backend_token=_str("BACKEND_TOKEN", ""),
            backend_host=_str("BACKEND_HOST", "0.0.0.0"),
            backend_port=_int("BACKEND_PORT", 8000),
            fds=FdsConfig.from_env(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
