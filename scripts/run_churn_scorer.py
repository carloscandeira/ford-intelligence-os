"""
CLI script to run churn scoring on all vehicles in the database.

Usage: python scripts/run_churn_scorer.py [--threshold 70]

Reads from retention_vehicles table, calculates scores,
updates churn_score and score_calculado_em columns.
"""

import argparse
import os
import sys
from datetime import date, datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from db.connection import engine
from scoring.churn_scorer import VehicleData, calculate_churn_score


def load_vehicles():
    """Load all vehicles with LGPD consent from DB."""
    query = text("""
        SELECT vehicle_id, modelo, ultima_visita_paga, tipo_ultimo_servico,
               ano_fabricacao, qtd_visitas_pagas_2_anos, km_estimado,
               connected_vehicle_available, sinal_falha_ativo, km_real_odometro
        FROM retention_vehicles
        WHERE lgpd_consent = TRUE
    """)
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    return [
        VehicleData(
            vehicle_id=r.vehicle_id,
            modelo=r.modelo,
            ultima_visita_paga=r.ultima_visita_paga,
            tipo_ultimo_servico=r.tipo_ultimo_servico,
            ano_fabricacao=r.ano_fabricacao,
            qtd_visitas_pagas_2_anos=r.qtd_visitas_pagas_2_anos or 0,
            km_estimado=r.km_estimado,
            connected_vehicle_available=r.connected_vehicle_available or False,
            sinal_falha_ativo=r.sinal_falha_ativo or False,
            km_real_odometro=r.km_real_odometro,
        )
        for r in rows
    ]


def update_scores(scores: list):
    """Write scores back to retention_vehicles."""
    update_query = text("""
        UPDATE retention_vehicles
        SET churn_score = :score,
            score_calculado_em = :scored_at,
            updated_at = NOW()
        WHERE vehicle_id = :vehicle_id
    """)
    with engine.connect() as conn:
        for result in scores:
            conn.execute(update_query, {
                "vehicle_id": result.vehicle_id,
                "score": result.score,
                "scored_at": result.scored_at,
            })
        conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Run churn scoring on all vehicles")
    parser.add_argument("--threshold", type=int, default=70, help="High risk threshold (default: 70)")
    args = parser.parse_args()

    print("Ford Intelligence OS — Churn Scorer")
    print("=" * 50)

    vehicles = load_vehicles()
    print(f"Loaded {len(vehicles)} vehicles (with LGPD consent)")

    if not vehicles:
        print("No vehicles found. Run ingestion first: python -m ingestion.load_data")
        return

    # Score all
    results = [calculate_churn_score(v) for v in vehicles]
    results.sort(key=lambda r: r.score, reverse=True)

    # Stats
    high_risk = [r for r in results if r.score > args.threshold]
    contact_now = [r for r in results if r.contact_this_week]
    avg_score = sum(r.score for r in results) / len(results)

    print(f"\nResults:")
    print(f"  Average score: {avg_score:.1f}")
    print(f"  High risk (>{args.threshold}): {len(high_risk)}")
    print(f"  Contact this week (>85): {len(contact_now)}")

    # Show top 10
    print(f"\nTop 10 highest risk:")
    for r in results[:10]:
        v = next(v for v in vehicles if v.vehicle_id == r.vehicle_id)
        flag = " *** CONTATAR" if r.contact_this_week else ""
        print(f"  {r.vehicle_id} | {v.modelo:12s} | Score: {r.score:3d}{flag}")

    # Write to DB
    update_scores(results)
    print(f"\nUpdated {len(results)} scores in database.")


if __name__ == "__main__":
    main()
