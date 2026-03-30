"""
Railway setup script — runs once after deploy to initialize DB and load data.

Usage: railway run python scripts/setup_railway.py

This:
1. Creates all tables from schema.sql
2. Generates synthetic data
3. Loads into PostgreSQL
4. Runs churn scoring
"""

import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

random.seed(42)


def main():
    print("Ford Intelligence OS — Railway Setup")
    print("=" * 50)

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set. Add PostgreSQL plugin in Railway dashboard.")
        return

    print(f"Database: {db_url[:30]}...")

    # Step 1: Init DB
    print("\n[1/4] Creating tables...")
    from db.connection import init_db
    init_db()

    # Step 2: Generate synthetic data
    print("\n[2/4] Generating synthetic data...")
    from data.synthetic.generate_synthetic import generate_specs_csv, generate_retention_csv
    generate_specs_csv()
    generate_retention_csv()

    # Step 3: Load data
    print("\n[3/4] Loading data...")
    from ingestion.load_data import load_specs_csv, load_retention_csv
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic")
    load_specs_csv(os.path.join(data_dir, "vehicle_specs.csv"))
    load_retention_csv(os.path.join(data_dir, "retention_vehicles.csv"))

    # Step 4: Score
    print("\n[4/4] Running churn scorer...")
    from scoring.churn_scorer import VehicleData, calculate_churn_score
    from sqlalchemy import text
    from db.connection import engine

    query = text("""
        SELECT vehicle_id, modelo, ultima_visita_paga, tipo_ultimo_servico,
               ano_fabricacao, qtd_visitas_pagas_2_anos, km_estimado,
               connected_vehicle_available, sinal_falha_ativo, km_real_odometro
        FROM retention_vehicles WHERE lgpd_consent = TRUE
    """)
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    scored = 0
    with engine.connect() as conn:
        for r in rows:
            v = VehicleData(
                vehicle_id=r.vehicle_id, modelo=r.modelo,
                ultima_visita_paga=r.ultima_visita_paga,
                tipo_ultimo_servico=r.tipo_ultimo_servico,
                ano_fabricacao=r.ano_fabricacao,
                qtd_visitas_pagas_2_anos=r.qtd_visitas_pagas_2_anos or 0,
                km_estimado=r.km_estimado,
                connected_vehicle_available=r.connected_vehicle_available or False,
                sinal_falha_ativo=r.sinal_falha_ativo or False,
                km_real_odometro=r.km_real_odometro,
            )
            result = calculate_churn_score(v)
            conn.execute(
                text("UPDATE retention_vehicles SET churn_score = :score, score_calculado_em = :scored_at, updated_at = NOW() WHERE vehicle_id = :vehicle_id"),
                {"vehicle_id": result.vehicle_id, "score": result.score, "scored_at": result.scored_at},
            )
            scored += 1
        conn.commit()

    print(f"  Scored {scored} vehicles")
    print("\nDone! Dashboard is ready.")


if __name__ == "__main__":
    main()
