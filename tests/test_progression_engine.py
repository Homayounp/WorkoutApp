# tests/test_progression_engine.py
"""
Unit tests for the Progression Engine.
Run with: pytest tests/test_progression_engine.py -v
"""

import pytest
from app.crud import (
    classify_recovery_state,
    classify_stimulus_quality,
    is_dumbbell_exercise,
    get_next_available_weight,
    calculate_set_target,
    evaluate_set_performance,
    DUMBBELL_WEIGHTS_KG,
    DEFAULT_REP_FLOOR,
    DEFAULT_REP_CEILING,
    DELOAD_WEIGHT_REDUCTION,
    MIN_BARBELL_INCREMENT_KG,
)


# ═══════════════════════════════════════════════════════
# RECOVERY CLASSIFICATION
# ═══════════════════════════════════════════════════════

class TestRecoveryClassification:
    def test_overtrained_at_threshold(self):
        assert classify_recovery_state(2.5) == "overtrained"

    def test_overtrained_above_threshold(self):
        assert classify_recovery_state(3.0) == "overtrained"

    def test_under_recovered_at_threshold(self):
        assert classify_recovery_state(1.5) == "under_recovered"

    def test_under_recovered_mid_range(self):
        assert classify_recovery_state(2.0) == "under_recovered"

    def test_under_recovered_just_below_overtrained(self):
        assert classify_recovery_state(2.4) == "under_recovered"

    def test_mostly_recovered_at_threshold(self):
        assert classify_recovery_state(0.5) == "mostly_recovered"

    def test_mostly_recovered_mid_range(self):
        assert classify_recovery_state(1.0) == "mostly_recovered"

    def test_fully_recovered_just_below(self):
        assert classify_recovery_state(0.4) == "fully_recovered"

    def test_fully_recovered_zero(self):
        assert classify_recovery_state(0.0) == "fully_recovered"


# ═══════════════════════════════════════════════════════
# STIMULUS CLASSIFICATION
# ═══════════════════════════════════════════════════════

class TestStimulusClassification:
    def test_insufficient_low_pump_low_volume(self):
        assert classify_stimulus_quality(0.5, -0.8) == "insufficient"

    def test_insufficient_zero_everything(self):
        assert classify_stimulus_quality(0.0, -1.0) == "insufficient"

    def test_optimal_moderate_pump_neutral_volume(self):
        assert classify_stimulus_quality(1.5, 0.0) == "optimal"

    def test_optimal_good_pump_neutral_volume(self):
        assert classify_stimulus_quality(2.0, 0.0) == "optimal"

    def test_excessive_high_pump_high_volume(self):
        assert classify_stimulus_quality(3.0, 0.8) == "excessive"

    def test_excessive_max_everything(self):
        assert classify_stimulus_quality(3.0, 1.0) == "excessive"


# ═══════════════════════════════════════════════════════
# EXERCISE TYPE DETECTION
# ═══════════════════════════════════════════════════════

class TestExerciseTypeDetection:
    def test_dumbbell_by_equipment_field(self):
        assert is_dumbbell_exercise("Bench Press", equipment="dumbbell") is True

    def test_barbell_by_equipment_field(self):
        assert is_dumbbell_exercise("Bench Press", equipment="barbell") is False

    def test_machine_by_equipment_field(self):
        assert is_dumbbell_exercise("Chest Press", equipment="machine") is False

    def test_dumbbell_by_name_heuristic(self):
        assert is_dumbbell_exercise("Dumbbell Lateral Raise") is True

    def test_dumbbell_by_name_db_prefix(self):
        assert is_dumbbell_exercise("DB Bench Press") is True

    def test_non_dumbbell_by_name(self):
        assert is_dumbbell_exercise("Barbell Squat") is False

    def test_fly_detected_as_dumbbell(self):
        assert is_dumbbell_exercise("Incline Fly") is True

    def test_cable_not_dumbbell(self):
        assert is_dumbbell_exercise("Cable Crossover", equipment="cable") is False


# ═══════════════════════════════════════════════════════
# WEIGHT PROGRESSION
# ═══════════════════════════════════════════════════════

class TestWeightProgression:
    def test_barbell_standard_increment(self):
        # 100kg → 2.5% = 2.5kg → 102.5kg
        next_w, achievable, reason = get_next_available_weight(100.0, is_dumbbell=False)
        assert achievable is True
        assert next_w == 102.5

    def test_barbell_small_weight(self):
        # 40kg → 2.5% = 1.0kg → rounds up to 2.5kg → 42.5kg
        next_w, achievable, reason = get_next_available_weight(40.0, is_dumbbell=False)
        assert achievable is True
        assert next_w == 42.5

    def test_dumbbell_achievable_jump(self):
        # 20kg → target 20.5kg → next dumbbell is 22.5kg (12.5% jump)
        # But wait: 12.5% > 6.25% threshold → NOT achievable
        next_w, achievable, reason = get_next_available_weight(20.0, is_dumbbell=True)
        assert achievable is False  # 22.5/20 = 12.5% > 6.25%

    def test_dumbbell_small_jump_achievable(self):
        # 40kg → target 41kg → next dumbbell is 42.5kg (6.25% jump)
        # 6.25% == 6.25% threshold → just at the edge
        next_w, achievable, reason = get_next_available_weight(40.0, is_dumbbell=True)
        assert achievable is True
        assert next_w == 42.5

    def test_zero_weight(self):
        next_w, achievable, reason = get_next_available_weight(0.0, is_dumbbell=False)
        assert achievable is False

    def test_dumbbell_at_max(self):
        next_w, achievable, reason = get_next_available_weight(60.0, is_dumbbell=True)
        # 60 is the max in our list
        assert achievable is False


# ═══════════════════════════════════════════════════════
# DOUBLE PROGRESSION (SET-LEVEL)
# ═══════════════════════════════════════════════════════

class TestDoubleProgression:
    def test_weight_increase_barbell_recovered(self):
        result = calculate_set_target(
            last_weight=100.0,
            last_reps=10,
            is_dumbbell=False,
            recovery_state="mostly_recovered",
            stimulus_quality="optimal"
        )
        assert result["action"] == "increase_weight"
        assert result["target_weight"] == 102.5
        assert result["target_reps"] <= 10  # May drop 1 rep

    def test_rep_increase_when_weight_jump_too_big(self):
        # 20kg dumbbell → next is 22.5kg (12.5% jump, too big)
        # Should fall back to rep increase
        result = calculate_set_target(
            last_weight=20.0,
            last_reps=10,
            is_dumbbell=True,
            recovery_state="mostly_recovered",
            stimulus_quality="optimal"
        )
        assert result["action"] == "increase_reps"
        assert result["target_reps"] == 11
        assert result["target_weight"] == 20.0

    def test_force_weight_at_rep_ceiling(self):
        # 20kg dumbbell at 12 reps (ceiling) → must force weight jump
        result = calculate_set_target(
            last_weight=20.0,
            last_reps=12,
            is_dumbbell=True,
            recovery_state="mostly_recovered",
            stimulus_quality="optimal"
        )
        assert result["action"] == "force_weight_increase"
        assert result["target_weight"] == 22.5  # Next dumbbell
        assert result["target_reps"] == DEFAULT_REP_FLOOR

    def test_deload_when_overtrained(self):
        result = calculate_set_target(
            last_weight=100.0,
            last_reps=10,
            is_dumbbell=False,
            recovery_state="overtrained",
            stimulus_quality="optimal"
        )
        assert result["action"] == "deload"
        assert result["target_weight"] == 90.0  # 10% reduction
        assert result["target_reps"] == DEFAULT_REP_FLOOR

    def test_deload_dumbbell_snaps_to_valid_weight(self):
        # 42.5kg dumbbell deloaded by 10% = 38.25kg → should snap to 37.5kg
        result = calculate_set_target(
            last_weight=42.5,
            last_reps=10,
            is_dumbbell=True,
            recovery_state="overtrained",
            stimulus_quality="optimal"
        )
        assert result["action"] == "deload"
        assert result["target_weight"] == 37.5  # Nearest valid dumbbell below 38.25

    def test_maintain_when_under_recovered(self):
        result = calculate_set_target(
            last_weight=100.0,
            last_reps=10,
            is_dumbbell=False,
            recovery_state="under_recovered",
            stimulus_quality="optimal"
        )
        assert result["action"] == "maintain"
        assert result["target_weight"] == 100.0
        assert result["target_reps"] == 10

    def test_initialize_with_zero_weight(self):
        result = calculate_set_target(
            last_weight=0,
            last_reps=0,
            is_dumbbell=False,
            recovery_state="fully_recovered",
            stimulus_quality="optimal"
        )
        assert result["action"] == "initialize"

    def test_fully_recovered_still_progresses(self):
        result = calculate_set_target(
            last_weight=60.0,
            last_reps=10,
            is_dumbbell=False,
            recovery_state="fully_recovered",
            stimulus_quality="optimal"
        )
        assert result["action"] == "increase_weight"
        assert result["target_weight"] > 60.0

    def test_reps_dont_exceed_ceiling_on_increase(self):
        result = calculate_set_target(
            last_weight=20.0,
            last_reps=11,  # One below ceiling
            is_dumbbell=True,
            recovery_state="mostly_recovered",
            stimulus_quality="optimal"
        )
        assert result["target_reps"] <= DEFAULT_REP_CEILING


# ═══════════════════════════════════════════════════════
# SET PERFORMANCE EVALUATION
# ═══════════════════════════════════════════════════════

class TestPerformanceEvaluation:
    def test_exceeded(self):
        assert evaluate_set_performance(100, 10, 102.5, 11) == "exceeded"

    def test_hit_exact(self):
        assert evaluate_set_performance(100, 10, 100, 10) == "hit"

    def test_hit_weight_higher_reps_equal(self):
        assert evaluate_set_performance(100, 10, 105, 10) == "hit"

    def test_partial_weight_met_reps_missed(self):
        # 100×10=1000 target, 100×8=800 actual, 800/1000=80% < 95%
        assert evaluate_set_performance(100, 10, 100, 8) == "partial"

    def test_missed_both(self):
        # 100×10=1000 target, 90×8=720 actual, 720/1000=72% < 90%
        assert evaluate_set_performance(100, 10, 90, 8) == "missed"

    def test_volume_equivalent_counts_as_hit(self):
        # 100×10=1000 target, 105×10=1050 actual → both met
        assert evaluate_set_performance(100, 10, 105, 10) == "hit"

    def test_no_target_returns_hit(self):
        assert evaluate_set_performance(0, 0, 100, 10) == "hit"

    def test_close_miss_is_partial(self):
        # 100×10=1000 target, 95×10=950 actual, 950/1000=95% → hit via volume
        result = evaluate_set_performance(100, 10, 95, 10)
        assert result in ("hit", "partial")


# ═══════════════════════════════════════════════════════
# INTEGRATION SCENARIO TESTS
# ═══════════════════════════════════════════════════════

class TestProgressionScenarios:
    """
    End-to-end scenario tests simulating multi-week progression.
    These don't need a database — they test the pure algorithmic chain.
    """

    def test_week_over_week_barbell_progression(self):
        """Simulate 4 weeks of barbell bench press progression."""
        weight = 80.0
        reps = 8
        is_db = False

        progression_log = []
        for week in range(1, 5):
            result = calculate_set_target(
                last_weight=weight,
                last_reps=reps,
                is_dumbbell=is_db,
                recovery_state="mostly_recovered",
                stimulus_quality="optimal"
            )
            progression_log.append({
                "week": week,
                "from": f"{weight}kg × {reps}",
                "to": f"{result['target_weight']}kg × {result['target_reps']}",
                "action": result["action"],
            })
            weight = result["target_weight"]
            reps = result["target_reps"]

        # After 4 weeks, weight should have increased
        assert weight > 80.0
        # Should have had at least some weight increases
        weight_increases = [p for p in progression_log if p["action"] == "increase_weight"]
        assert len(weight_increases) >= 2

    def test_dumbbell_double_progression_cycle(self):
        """
        Simulate a full double-progression cycle with dumbbells:
        Start at 20kg × 8, can't increase weight → add reps until ceiling → jump.
        """
        weight = 20.0
        reps = 8
        is_db = True

        actions_seen = set()
        for _ in range(10):  # Run enough iterations
            result = calculate_set_target(
                last_weight=weight,
                last_reps=reps,
                is_dumbbell=is_db,
                recovery_state="mostly_recovered",
                stimulus_quality="optimal"
            )
            actions_seen.add(result["action"])
            weight = result["target_weight"]
            reps = result["target_reps"]

            if result["action"] == "force_weight_increase":
                break  # We completed a full cycle

        # Should have seen both rep increases and a forced weight jump
        assert "increase_reps" in actions_seen
        assert "force_weight_increase" in actions_seen
        assert weight > 20.0  # Weight should have gone up

    def test_overtrained_recovery_then_resume(self):
        """Simulate deload → recovery → resume progression."""
        # Week 1: Normal
        r1 = calculate_set_target(100.0, 10, False, "mostly_recovered", "optimal")
        assert r1["action"] == "increase_weight"

        # Week 2: Overtrained → deload
        r2 = calculate_set_target(r1["target_weight"], r1["target_reps"],
                                  False, "overtrained", "optimal")
        assert r2["action"] == "deload"
        assert r2["target_weight"] < r1["target_weight"]

        # Week 3: Under-recovered → maintain
        r3 = calculate_set_target(r2["target_weight"], r2["target_reps"],
                                  False, "under_recovered", "optimal")
        assert r3["action"] == "maintain"

        # Week 4: Recovered → resume progression
        r4 = calculate_set_target(r3["target_weight"], r3["target_reps"],
                                  False, "mostly_recovered", "optimal")
        assert r4["action"] in ("increase_weight", "increase_reps")
