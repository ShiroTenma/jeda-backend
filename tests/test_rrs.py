import pytest
from app.services.rrs import RrsEngine

def test_single_high_frame_cannot_trigger_hard_intervention():
    engine = RrsEngine()
    resp = engine.evaluate(
        session_id="s1",
        current_confidence=0.95,
        exposure_seconds=10.0,
        soft_intervention_count=5, # enough soft interventions, but only 1 observation
        hour_of_day=14
    )
    assert resp.level == "HIGH"
    # Action must be gated to ELEVATED_MONITORING because < 3 observations in window
    assert resp.action == "ELEVATED_MONITORING"
    assert resp.duration_seconds == 0

def test_low_confidence_results_in_normal_monitoring():
    engine = RrsEngine()
    resp = engine.evaluate(
        session_id="s2",
        current_confidence=0.20,
        exposure_seconds=10.0,
        soft_intervention_count=0,
        hour_of_day=14
    )
    assert resp.rrs < 0.40
    assert resp.level == "NORMAL"
    assert resp.action == "NONE"
    assert resp.sampling_interval_seconds == 3

def test_sustained_high_frames_with_soft_interventions_triggers_hard_intervention():
    engine = RrsEngine()
    sid = "s3"
    
    # 3 consecutive high observations
    engine.evaluate(sid, 0.85, 10.0, 3, 14)
    engine.evaluate(sid, 0.90, 10.0, 3, 14)
    resp = engine.evaluate(sid, 0.95, 10.0, 3, 14)

    assert resp.level == "HIGH"
    assert resp.action == "HARD_INTERVENTION"
    assert resp.duration_seconds == 60 # base 60s for 3 soft interventions

def test_hard_intervention_escalates_duration_capped_at_180s():
    engine = RrsEngine()
    sid = "s4"
    
    engine.evaluate(sid, 0.90, 10.0, 7, 14)
    engine.evaluate(sid, 0.90, 10.0, 7, 14)
    resp = engine.evaluate(sid, 0.90, 10.0, 7, 14)

    assert resp.action == "HARD_INTERVENTION"
    # 60 + (7-3)*30 = 60 + 120 = 180s
    assert resp.duration_seconds == 180

def test_nighttime_context_multiplier():
    engine = RrsEngine(context_enabled=True)
    # 23:00 local time
    resp = engine.evaluate("s5", 0.50, 10.0, 0, hour_of_day=23)
    assert resp.ct == 1.5
    # 0.5 * 1.0 * 1.5 = 0.75
    assert resp.rrs == 0.75
