import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from app.schemas.rrs import RrsAnalysisResponse

@dataclass
class Observation:
    timestamp: float
    confidence: float

class RrsEngine:
    """Maintains rolling observation windows and calculates Relapse Risk Score (RRS)."""

    def __init__(
        self,
        window_seconds: float = 15.0,
        t_ref: float = 10.0,
        context_enabled: bool = True,
        night_multiplier: float = 1.5,
        elevated_threshold: float = 0.40,
        high_threshold: float = 0.70,
        required_soft_interventions: int = 3
    ):
        self.window_seconds = window_seconds
        self.t_ref = t_ref
        self.context_enabled = context_enabled
        self.night_multiplier = night_multiplier
        self.elevated_threshold = elevated_threshold
        self.high_threshold = high_threshold
        self.required_soft_interventions = required_soft_interventions
        
        # session_id -> deque of Observation
        self._history: Dict[str, deque[Observation]] = {}

    def add_observation(self, session_id: str, confidence: float, now: float | None = None) -> List[float]:
        now = now or time.time()
        if session_id not in self._history:
            self._history[session_id] = deque()

        q = self._history[session_id]
        q.append(Observation(timestamp=now, confidence=confidence))

        # Evict older than window_seconds
        while q and (now - q[0].timestamp > self.window_seconds):
            q.popleft()

        return [obs.confidence for obs in q]

    def evaluate(
        self,
        session_id: str,
        current_confidence: float,
        exposure_seconds: float,
        soft_intervention_count: int,
        hour_of_day: int = 12,
        now: float | None = None
    ) -> RrsAnalysisResponse:
        observations = self.add_observation(session_id, current_confidence, now)

        # 1. Calculate Pavg from up to latest 3 observations
        recent = observations[-3:]
        p_avg = sum(recent) / len(recent) if recent else current_confidence

        # 2. Calculate Dn = min(Texposure / Tref, 1.0)
        dn = min(max(exposure_seconds / self.t_ref, 0.0), 1.0)

        # 3. Context Multiplier Ct (23:00 - 04:00 -> 1.5 if enabled)
        is_night = (hour_of_day >= 23 or hour_of_day < 4)
        ct = self.night_multiplier if (self.context_enabled and is_night) else 1.0

        # 4. RRS = clip(Pavg * Dn * Ct, 0, 1)
        raw_rrs = p_avg * dn * ct
        rrs = min(max(raw_rrs, 0.0), 1.0)

        # 5. Multi-gate decision policy
        level = "NORMAL"
        action = "NONE"
        sampling_interval = 3
        duration = 0

        if rrs < self.elevated_threshold:
            level = "NORMAL"
            action = "NONE"
            sampling_interval = 3
        elif rrs < self.high_threshold:
            level = "ELEVATED"
            action = "ELEVATED_MONITORING"
            sampling_interval = 2
        else:
            # Candidate for hard intervention
            level = "HIGH"
            sampling_interval = 2
            
            # Gating rules:
            # - Must have at least 3 valid observations
            # - Must have reached required soft intervention count (baseline 3)
            # - Current observation and Pavg must be sustained
            has_3_obs = len(recent) >= 3
            has_enough_soft = soft_intervention_count >= self.required_soft_interventions

            if has_3_obs and has_enough_soft:
                action = "HARD_INTERVENTION"
                # Duration formula: 60s base + 30s per soft intervention beyond 3, capped at 180s
                extra = max(0, soft_intervention_count - 3)
                duration = min(60 + extra * 30, 180)
            else:
                action = "ELEVATED_MONITORING"

        return RrsAnalysisResponse(
            visual_confidence=round(current_confidence, 4),
            p_avg=round(p_avg, 4),
            dn=round(dn, 4),
            ct=round(ct, 2),
            rrs=round(rrs, 4),
            level=level,
            action=action,
            duration_seconds=duration,
            sampling_interval_seconds=sampling_interval
        )
