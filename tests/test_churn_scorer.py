"""
Tests for scoring/churn_scorer.py

Covers:
- Individual rule scoring
- NULL handling (Issue 6A: NULL = max risk)
- Score boundaries (0, 70, 85, 100)
- Edge cases: all rules fire, no rules fire
- Connected vehicle enrichment
- Batch scoring sort order
"""

import pytest
from datetime import date, timedelta

from scoring.churn_scorer import (
    VehicleData,
    ScoreResult,
    calculate_churn_score,
    score_all_vehicles,
    _days_since_last_paid_visit,
    _vehicle_age_years,
    _near_revision_milestone,
    REVISION_MILESTONES,
    REVISION_PROXIMITY_KM,
)


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

def _make_vehicle(**overrides) -> VehicleData:
    """Create a VehicleData with sensible defaults, overriding as needed."""
    defaults = {
        "vehicle_id": "VH-TEST",
        "modelo": "Ranger",
        "ultima_visita_paga": date.today() - timedelta(days=30),
        "tipo_ultimo_servico": "pago",
        "ano_fabricacao": 2023,
        "qtd_visitas_pagas_2_anos": 3,
        "km_estimado": 25000,
        "connected_vehicle_available": False,
        "sinal_falha_ativo": False,
        "km_real_odometro": None,
    }
    defaults.update(overrides)
    return VehicleData(**defaults)


# ─────────────────────────────────────────────────────────────
# Helper function tests
# ─────────────────────────────────────────────────────────────

class TestDaysSinceLastPaidVisit:
    def test_none_returns_none(self):
        assert _days_since_last_paid_visit(None) is None

    def test_today_returns_zero(self):
        assert _days_since_last_paid_visit(date.today()) == 0

    def test_past_date_returns_positive(self):
        past = date.today() - timedelta(days=100)
        assert _days_since_last_paid_visit(past) == 100


class TestVehicleAgeYears:
    def test_none_returns_none(self):
        assert _vehicle_age_years(None) is None

    def test_current_year_returns_zero(self):
        assert _vehicle_age_years(date.today().year) == 0

    def test_old_vehicle(self):
        assert _vehicle_age_years(2018) == date.today().year - 2018


class TestNearRevisionMilestone:
    def test_none_returns_false(self):
        assert _near_revision_milestone(None) is False

    def test_exact_milestone(self):
        for m in REVISION_MILESTONES:
            assert _near_revision_milestone(m) is True

    def test_within_proximity(self):
        assert _near_revision_milestone(40000 + REVISION_PROXIMITY_KM) is True
        assert _near_revision_milestone(40000 - REVISION_PROXIMITY_KM) is True

    def test_outside_proximity(self):
        # 66000 is 6000 from 60k and 14000 from 80k (both > REVISION_PROXIMITY_KM)
        assert _near_revision_milestone(66000) is False

    def test_far_from_any_milestone(self):
        # 70000 is 10k from both 60k and 80k milestones
        assert _near_revision_milestone(70000) is False


# ─────────────────────────────────────────────────────────────
# Rule 1: Days since last paid visit
# ─────────────────────────────────────────────────────────────

class TestRule1DaysSinceVisit:
    def test_null_visit_gives_40_points(self):
        """Issue 6A: NULL ultima_visita_paga = max risk (+40)."""
        v = _make_vehicle(ultima_visita_paga=None)
        result = calculate_churn_score(v)
        assert result.breakdown["dias_sem_visita_paga"]["points"] == 40

    def test_over_365_days_gives_40_points(self):
        v = _make_vehicle(ultima_visita_paga=date.today() - timedelta(days=400))
        result = calculate_churn_score(v)
        assert result.breakdown["dias_sem_visita_paga"]["points"] == 40

    def test_recent_visit_gives_0_points(self):
        v = _make_vehicle(ultima_visita_paga=date.today() - timedelta(days=30))
        result = calculate_churn_score(v)
        assert result.breakdown["dias_sem_visita_paga"]["points"] == 0

    def test_exactly_365_days_gives_0_points(self):
        """Boundary: exactly 365 days is NOT > 365."""
        v = _make_vehicle(ultima_visita_paga=date.today() - timedelta(days=365))
        result = calculate_churn_score(v)
        assert result.breakdown["dias_sem_visita_paga"]["points"] == 0

    def test_366_days_gives_40_points(self):
        v = _make_vehicle(ultima_visita_paga=date.today() - timedelta(days=366))
        result = calculate_churn_score(v)
        assert result.breakdown["dias_sem_visita_paga"]["points"] == 40


# ─────────────────────────────────────────────────────────────
# Rule 2: Last service type
# ─────────────────────────────────────────────────────────────

class TestRule2ServiceType:
    def test_recall_gives_20_points(self):
        v = _make_vehicle(tipo_ultimo_servico="recall")
        result = calculate_churn_score(v)
        assert result.breakdown["tipo_ultimo_servico"]["points"] == 20

    def test_garantia_gives_20_points(self):
        v = _make_vehicle(tipo_ultimo_servico="garantia")
        result = calculate_churn_score(v)
        assert result.breakdown["tipo_ultimo_servico"]["points"] == 20

    def test_pago_gives_0_points(self):
        v = _make_vehicle(tipo_ultimo_servico="pago")
        result = calculate_churn_score(v)
        assert result.breakdown["tipo_ultimo_servico"]["points"] == 0

    def test_none_gives_0_points(self):
        v = _make_vehicle(tipo_ultimo_servico=None)
        result = calculate_churn_score(v)
        assert result.breakdown["tipo_ultimo_servico"]["points"] == 0


# ─────────────────────────────────────────────────────────────
# Rule 3: Vehicle age
# ─────────────────────────────────────────────────────────────

class TestRule3VehicleAge:
    def test_old_vehicle_gives_15_points(self):
        v = _make_vehicle(ano_fabricacao=2015)
        result = calculate_churn_score(v)
        assert result.breakdown["idade_veiculo"]["points"] == 15

    def test_new_vehicle_gives_0_points(self):
        v = _make_vehicle(ano_fabricacao=date.today().year - 2)
        result = calculate_churn_score(v)
        assert result.breakdown["idade_veiculo"]["points"] == 0

    def test_exactly_5_years_gives_0_points(self):
        """Boundary: exactly 5 years is NOT > 5."""
        v = _make_vehicle(ano_fabricacao=date.today().year - 5)
        result = calculate_churn_score(v)
        assert result.breakdown["idade_veiculo"]["points"] == 0

    def test_none_gives_0_points(self):
        v = _make_vehicle(ano_fabricacao=None)
        result = calculate_churn_score(v)
        assert result.breakdown["idade_veiculo"]["points"] == 0


# ─────────────────────────────────────────────────────────────
# Rule 4: Paid visits in last 2 years
# ─────────────────────────────────────────────────────────────

class TestRule4PaidVisits:
    def test_zero_visits_gives_15_points(self):
        v = _make_vehicle(qtd_visitas_pagas_2_anos=0)
        result = calculate_churn_score(v)
        assert result.breakdown["visitas_pagas_2_anos"]["points"] == 15

    def test_one_visit_gives_0_points(self):
        v = _make_vehicle(qtd_visitas_pagas_2_anos=1)
        result = calculate_churn_score(v)
        assert result.breakdown["visitas_pagas_2_anos"]["points"] == 0

    def test_many_visits_gives_0_points(self):
        v = _make_vehicle(qtd_visitas_pagas_2_anos=8)
        result = calculate_churn_score(v)
        assert result.breakdown["visitas_pagas_2_anos"]["points"] == 0


# ─────────────────────────────────────────────────────────────
# Rule 5: Near revision milestone
# ─────────────────────────────────────────────────────────────

class TestRule5RevisionMilestone:
    def test_near_40k_gives_10_points(self):
        v = _make_vehicle(km_estimado=39000)
        result = calculate_churn_score(v)
        assert result.breakdown["proximo_revisao"]["points"] == 10

    def test_far_from_milestone_gives_0_points(self):
        v = _make_vehicle(km_estimado=70000)  # 10k from both 60k and 80k
        result = calculate_churn_score(v)
        assert result.breakdown["proximo_revisao"]["points"] == 0

    def test_connected_vehicle_uses_real_odometer(self):
        """Connected vehicle should prefer km_real_odometro over km_estimado."""
        v = _make_vehicle(
            km_estimado=75000,  # far from milestone
            connected_vehicle_available=True,
            km_real_odometro=40000,  # near milestone
        )
        result = calculate_churn_score(v)
        assert result.breakdown["proximo_revisao"]["points"] == 10


# ─────────────────────────────────────────────────────────────
# Composite scoring
# ─────────────────────────────────────────────────────────────

class TestCompositeScoring:
    def test_all_rules_fire_gives_100(self):
        """Maximum possible score: 40 + 20 + 15 + 15 + 10 = 100."""
        v = _make_vehicle(
            ultima_visita_paga=None,          # +40
            tipo_ultimo_servico="recall",      # +20
            ano_fabricacao=2015,               # +15
            qtd_visitas_pagas_2_anos=0,        # +15
            km_estimado=40000,                 # +10
        )
        result = calculate_churn_score(v)
        assert result.score == 100
        assert result.is_high_risk is True
        assert result.contact_this_week is True

    def test_no_rules_fire_gives_0(self):
        """Minimum possible score: 0."""
        v = _make_vehicle(
            ultima_visita_paga=date.today() - timedelta(days=10),
            tipo_ultimo_servico="pago",
            ano_fabricacao=date.today().year - 1,
            qtd_visitas_pagas_2_anos=5,
            km_estimado=70000,  # 10k from both 60k and 80k milestones
        )
        result = calculate_churn_score(v)
        assert result.score == 0
        assert result.is_high_risk is False
        assert result.contact_this_week is False

    def test_threshold_70_is_high_risk(self):
        """Score > 70 is high risk."""
        # 40 + 20 + 15 = 75 (high risk but not contact this week)
        v = _make_vehicle(
            ultima_visita_paga=None,
            tipo_ultimo_servico="garantia",
            ano_fabricacao=2015,
            qtd_visitas_pagas_2_anos=2,
            km_estimado=70000,  # far from milestones
        )
        result = calculate_churn_score(v)
        assert result.score == 75
        assert result.is_high_risk is True
        assert result.contact_this_week is False

    def test_threshold_85_is_contact_this_week(self):
        """Score > 85 triggers contact this week."""
        # 40 + 20 + 15 + 15 = 90
        v = _make_vehicle(
            ultima_visita_paga=None,
            tipo_ultimo_servico="recall",
            ano_fabricacao=2015,
            qtd_visitas_pagas_2_anos=0,
            km_estimado=70000,  # far from milestones
        )
        result = calculate_churn_score(v)
        assert result.score == 90
        assert result.contact_this_week is True

    def test_score_clamped_to_100(self):
        """Score should never exceed 100."""
        v = _make_vehicle(
            ultima_visita_paga=None,
            tipo_ultimo_servico="recall",
            ano_fabricacao=2010,
            qtd_visitas_pagas_2_anos=0,
            km_estimado=40000,
        )
        result = calculate_churn_score(v)
        assert result.score <= 100


class TestConnectedVehicle:
    def test_active_fault_recorded_in_breakdown(self):
        v = _make_vehicle(
            connected_vehicle_available=True,
            sinal_falha_ativo=True,
        )
        result = calculate_churn_score(v)
        assert "sinal_falha" in result.breakdown
        assert "ALERTA" in result.breakdown["sinal_falha"]["reason"]

    def test_no_fault_no_extra_breakdown(self):
        v = _make_vehicle(
            connected_vehicle_available=True,
            sinal_falha_ativo=False,
        )
        result = calculate_churn_score(v)
        assert "sinal_falha" not in result.breakdown


class TestBatchScoring:
    def test_sorted_descending(self):
        vehicles = [
            _make_vehicle(vehicle_id="LOW", ultima_visita_paga=date.today(), tipo_ultimo_servico="pago",
                          ano_fabricacao=2024, qtd_visitas_pagas_2_anos=5, km_estimado=75000),
            _make_vehicle(vehicle_id="HIGH", ultima_visita_paga=None, tipo_ultimo_servico="recall",
                          ano_fabricacao=2015, qtd_visitas_pagas_2_anos=0, km_estimado=40000),
        ]
        results = score_all_vehicles(vehicles)
        assert results[0].vehicle_id == "HIGH"
        assert results[1].vehicle_id == "LOW"
        assert results[0].score >= results[1].score

    def test_empty_list(self):
        results = score_all_vehicles([])
        assert results == []
