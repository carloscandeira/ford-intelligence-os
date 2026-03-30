"""
Churn Risk Scorer v1 — Rule-based scoring system.

Architecture decisions from /plan-eng-review 2026-03-28:
- Rule-based v1 (no labeled dataset needed)
- NULL handling: dias_desde_ultima_visita_paga = NULL → +40pts (Issue 6A)
- Max score: 100 (40+20+15+15+10)
- Threshold "alto risco": >70
- Threshold "contatar esta semana": >85
- TODO: calibrate weights with real Ford data when available

SCORING RULES:
┌─────────────────────────────────────────────────┬────────┐
│ Rule                                            │ Points │
├─────────────────────────────────────────────────┼────────┤
│ dias_desde_ultima_visita_paga > 365 (or NULL)   │ +40    │
│ tipo_ultimo_servico == recall/garantia only      │ +20    │
│ idade_veiculo_anos > 5                          │ +15    │
│ qtd_visitas_pagas_2_anos == 0                   │ +15    │
│ km_estimado near revision (40k, 80k, etc.)      │ +10    │
└─────────────────────────────────────────────────┴────────┘
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


# Revision milestones in km (Ford standard service intervals)
REVISION_MILESTONES = [10_000, 20_000, 30_000, 40_000, 50_000, 60_000, 80_000, 100_000]
REVISION_PROXIMITY_KM = 5_000  # within 5k km of a milestone


@dataclass
class VehicleData:
    """Input data for churn scoring."""

    vehicle_id: str
    modelo: str
    ultima_visita_paga: Optional[date]
    tipo_ultimo_servico: Optional[str]  # 'pago', 'garantia', 'recall'
    ano_fabricacao: Optional[int]
    qtd_visitas_pagas_2_anos: int = 0
    km_estimado: Optional[int] = None
    connected_vehicle_available: bool = False
    sinal_falha_ativo: bool = False
    km_real_odometro: Optional[int] = None


@dataclass
class ScoreResult:
    """Output of churn scoring."""

    vehicle_id: str
    score: int  # 0-100
    breakdown: dict  # rule name → points awarded
    is_high_risk: bool  # score > 70
    contact_this_week: bool  # score > 85
    scored_at: datetime


def _days_since_last_paid_visit(ultima_visita_paga: Optional[date]) -> Optional[int]:
    """Calculate days since last paid visit. None if never visited."""
    if ultima_visita_paga is None:
        return None
    return (date.today() - ultima_visita_paga).days


def _vehicle_age_years(ano_fabricacao: Optional[int]) -> Optional[int]:
    """Calculate vehicle age in years."""
    if ano_fabricacao is None:
        return None
    return date.today().year - ano_fabricacao


def _near_revision_milestone(km: Optional[int]) -> bool:
    """Check if km is within REVISION_PROXIMITY_KM of any milestone."""
    if km is None:
        return False
    for milestone in REVISION_MILESTONES:
        if abs(km - milestone) <= REVISION_PROXIMITY_KM:
            return True
    return False


def calculate_churn_score(vehicle: VehicleData) -> ScoreResult:
    """
    Calculate churn risk score for a single vehicle.

    Returns ScoreResult with score 0-100 and detailed breakdown.
    """
    score = 0
    breakdown = {}

    # Rule 1: Days since last paid visit (NULL = max risk, Issue 6A)
    days = _days_since_last_paid_visit(vehicle.ultima_visita_paga)
    if days is None or days > 365:
        score += 40
        reason = "sem visita paga registrada" if days is None else f"{days} dias sem visita paga"
        breakdown["dias_sem_visita_paga"] = {"points": 40, "reason": reason}
    else:
        breakdown["dias_sem_visita_paga"] = {"points": 0, "reason": f"{days} dias (< 365)"}

    # Rule 2: Last service was warranty/recall only (never paid)
    if vehicle.tipo_ultimo_servico in ("garantia", "recall"):
        score += 20
        breakdown["tipo_ultimo_servico"] = {
            "points": 20,
            "reason": f"ultimo servico: {vehicle.tipo_ultimo_servico}",
        }
    else:
        breakdown["tipo_ultimo_servico"] = {
            "points": 0,
            "reason": f"ultimo servico: {vehicle.tipo_ultimo_servico or 'N/A'}",
        }

    # Rule 3: Vehicle age > 5 years
    age = _vehicle_age_years(vehicle.ano_fabricacao)
    if age is not None and age > 5:
        score += 15
        breakdown["idade_veiculo"] = {"points": 15, "reason": f"{age} anos (> 5)"}
    else:
        breakdown["idade_veiculo"] = {
            "points": 0,
            "reason": f"{age} anos" if age is not None else "ano desconhecido",
        }

    # Rule 4: Zero paid visits in last 2 years
    if vehicle.qtd_visitas_pagas_2_anos == 0:
        score += 15
        breakdown["visitas_pagas_2_anos"] = {"points": 15, "reason": "0 visitas pagas em 2 anos"}
    else:
        breakdown["visitas_pagas_2_anos"] = {
            "points": 0,
            "reason": f"{vehicle.qtd_visitas_pagas_2_anos} visitas pagas em 2 anos",
        }

    # Rule 5: Near revision milestone
    km = vehicle.km_real_odometro if vehicle.connected_vehicle_available else vehicle.km_estimado
    if _near_revision_milestone(km):
        score += 10
        breakdown["proximo_revisao"] = {"points": 10, "reason": f"{km} km (proximo de revisao)"}
    else:
        breakdown["proximo_revisao"] = {
            "points": 0,
            "reason": f"{km} km" if km is not None else "km desconhecido",
        }

    # Enriched mode: connected vehicle bonus
    if vehicle.connected_vehicle_available and vehicle.sinal_falha_ativo:
        # Bonus signal: vehicle is sending active fault codes
        # This doesn't change the max score (still 100) but can push borderline cases
        # into the "contact this week" zone
        breakdown["sinal_falha"] = {"points": 0, "reason": "ALERTA: falha ativa detectada"}

    # Clamp to 0-100
    score = max(0, min(100, score))

    return ScoreResult(
        vehicle_id=vehicle.vehicle_id,
        score=score,
        breakdown=breakdown,
        is_high_risk=score > 70,
        contact_this_week=score > 85,
        scored_at=datetime.now(),
    )


def score_all_vehicles(vehicles: list[VehicleData]) -> list[ScoreResult]:
    """Score all vehicles and return sorted by score descending."""
    results = [calculate_churn_score(v) for v in vehicles]
    results.sort(key=lambda r: r.score, reverse=True)
    return results
