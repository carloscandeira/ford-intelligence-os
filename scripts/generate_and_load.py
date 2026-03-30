"""
One-command setup: generate synthetic data + load into PostgreSQL.

Usage: python scripts/generate_and_load.py

This is the quickest way to get a working demo:
1. Generates synthetic CSVs (vehicle_specs.csv + retention_vehicles.csv)
2. Initializes the database schema
3. Loads data into PostgreSQL
4. Runs churn scoring on all vehicles
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def main():
    print("Ford Intelligence OS — Full Setup")
    print("=" * 50)

    # Step 1: Generate synthetic data
    print("\n[1/4] Generating synthetic data...")
    import random
    random.seed(42)
    from data.synthetic.generate_synthetic import generate_specs_csv, generate_retention_csv
    generate_specs_csv()
    generate_retention_csv()

    # Step 2: Initialize DB
    print("\n[2/4] Initializing database...")
    from db.connection import init_db
    init_db()

    # Step 3: Load data
    print("\n[3/4] Loading data into PostgreSQL...")
    from ingestion.load_data import load_specs_csv, load_retention_csv

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic")
    load_specs_csv(os.path.join(data_dir, "vehicle_specs.csv"))
    load_retention_csv(os.path.join(data_dir, "retention_vehicles.csv"))

    # Step 4: Run churn scorer
    print("\n[4/4] Running churn scorer...")
    from scoring.churn_scorer import VehicleData, calculate_churn_score
    from sqlalchemy import text
    from db.connection import engine

    # Load vehicles
    query = text("""
        SELECT vehicle_id, modelo, ultima_visita_paga, tipo_ultimo_servico,
               ano_fabricacao, qtd_visitas_pagas_2_anos, km_estimado,
               connected_vehicle_available, sinal_falha_ativo, km_real_odometro
        FROM retention_vehicles
        WHERE lgpd_consent = TRUE
    """)
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    scored = 0
    with engine.connect() as conn:
        for r in rows:
            v = VehicleData(
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
            result = calculate_churn_score(v)
            conn.execute(
                text("""
                    UPDATE retention_vehicles
                    SET churn_score = :score, score_calculado_em = :scored_at, updated_at = NOW()
                    WHERE vehicle_id = :vehicle_id
                """),
                {"vehicle_id": result.vehicle_id, "score": result.score, "scored_at": result.scored_at},
            )
            scored += 1
        conn.commit()

    print(f"  Scored {scored} vehicles")

    print("\n" + "=" * 50)
    print("Setup complete! Run the dashboard:")
    print("  streamlit run app/main.py")


if __name__ == "__main__":
    main()
