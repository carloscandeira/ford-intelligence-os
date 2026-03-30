"""
Retencao & Churn — Churn risk dashboard.

Tab 3 of Ford Intelligence OS dashboard.
Shows churn risk scores, breakdown per vehicle, filters, and batch scoring.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
from typing import Optional

# Try to import real modules
try:
    from sqlalchemy import text
    from db.connection import engine
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False

from scoring.churn_scorer import (
    VehicleData,
    ScoreResult,
    calculate_churn_score,
    score_all_vehicles,
)


# ─────────────────────────────────────────────────────────────
# Demo data (when DB not connected)
# ─────────────────────────────────────────────────────────────

def _generate_demo_vehicles() -> list[VehicleData]:
    """Generate demo vehicles for scoring demonstration."""
    import random
    random.seed(42)

    models = [
        ("Ranger", "Raptor"), ("Ranger", "Limited"), ("Ranger", "XLS"),
        ("Territory", "Titanium"), ("Bronco Sport", "Wildtrak"), ("Maverick", "Lariat"),
    ]

    vehicles = []
    for i in range(20):
        modelo, versao = models[i % len(models)]
        ano = random.randint(2017, 2025)
        had_paid = random.random() > 0.35
        connected = ano >= 2022 and random.random() > 0.3

        vehicles.append(VehicleData(
            vehicle_id=f"VH-{i+1:04d}",
            modelo=modelo,
            ultima_visita_paga=date(2024, random.randint(1, 12), 15) if had_paid else None,
            tipo_ultimo_servico=random.choice(["pago", "garantia", "recall"]),
            ano_fabricacao=ano,
            qtd_visitas_pagas_2_anos=random.randint(0, 5) if had_paid else 0,
            km_estimado=random.randint(5000, 120000),
            connected_vehicle_available=connected,
            sinal_falha_ativo=connected and random.random() > 0.85,
            km_real_odometro=random.randint(5000, 120000) if connected else None,
        ))
    return vehicles


def _load_vehicles_from_db() -> list[VehicleData]:
    """Load vehicles from retention_vehicles table."""
    query = text("""
        SELECT vehicle_id, modelo, ultima_visita_paga, tipo_ultimo_servico,
               ano_fabricacao, qtd_visitas_pagas_2_anos, km_estimado,
               connected_vehicle_available, sinal_falha_ativo, km_real_odometro
        FROM retention_vehicles
        WHERE lgpd_consent = TRUE
        ORDER BY vehicle_id
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


def _score_color(score: int) -> str:
    """Return color indicator for score."""
    if score > 85:
        return "🔴"
    if score > 70:
        return "🟠"
    if score > 40:
        return "🟡"
    return "🟢"


def render():
    """Render the Retencao & Churn tab."""
    st.header("Retencao & Churn")
    st.markdown(
        "Sistema de scoring de risco de churn baseado em regras. "
        "Score de 0-100 com 5 fatores ponderados. "
        "**Alto risco: >70** | **Contatar esta semana: >85**"
    )

    # ─── Load & Score ─────────────────────────────────────────
    if DB_AVAILABLE:
        try:
            vehicles = _load_vehicles_from_db()
            if not vehicles:
                vehicles = _generate_demo_vehicles()
                st.info("Banco vazio — usando dados de demonstracao", icon="🔵")
            else:
                st.success(f"Conectado — {len(vehicles)} veiculos (com LGPD consent)", icon="🟢")
        except Exception:
            vehicles = _generate_demo_vehicles()
            st.info("Modo demonstracao — banco nao conectado", icon="🔵")
    else:
        vehicles = _generate_demo_vehicles()
        st.info("Modo demonstracao — banco nao conectado", icon="🔵")

    results = score_all_vehicles(vehicles)

    # ─── Top Metrics ──────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    high_risk = [r for r in results if r.is_high_risk]
    contact_now = [r for r in results if r.contact_this_week]
    avg_score = sum(r.score for r in results) / len(results) if results else 0

    with col1:
        st.metric("Total Veiculos", len(results))
    with col2:
        st.metric("Alto Risco (>70)", len(high_risk))
    with col3:
        st.metric("Contatar Semana (>85)", len(contact_now))
    with col4:
        st.metric("Score Medio", f"{avg_score:.0f}")

    # ─── Filters ──────────────────────────────────────────────
    st.divider()
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        min_score = st.slider("Score minimo", 0, 100, 0)
    with col_f2:
        modelos = sorted(set(v.modelo for v in vehicles))
        selected_modelos = st.multiselect("Modelo", modelos, default=modelos)
    with col_f3:
        show_connected_only = st.checkbox("Apenas connected vehicles")

    # Apply filters
    filtered = [
        r for r in results
        if r.score >= min_score
        and any(v.modelo in selected_modelos for v in vehicles if v.vehicle_id == r.vehicle_id)
        and (not show_connected_only or any(
            v.connected_vehicle_available for v in vehicles if v.vehicle_id == r.vehicle_id
        ))
    ]

    # ─── Results Table ────────────────────────────────────────
    st.divider()
    st.subheader(f"Veiculos ({len(filtered)} de {len(results)})")

    if not filtered:
        st.warning("Nenhum veiculo encontrado com os filtros selecionados.")
        return

    # Build display dataframe
    vehicle_map = {v.vehicle_id: v for v in vehicles}
    table_rows = []
    for r in filtered:
        v = vehicle_map.get(r.vehicle_id)
        if not v:
            continue
        table_rows.append({
            "Risco": _score_color(r.score),
            "Score": r.score,
            "Vehicle ID": r.vehicle_id,
            "Modelo": v.modelo,
            "Ano": v.ano_fabricacao or "N/D",
            "KM": f"{v.km_estimado:,}" if v.km_estimado else "N/D",
            "Ult. Visita Paga": str(v.ultima_visita_paga) if v.ultima_visita_paga else "Nunca",
            "Visitas 2 anos": v.qtd_visitas_pagas_2_anos,
            "Connected": "Sim" if v.connected_vehicle_available else "Nao",
            "Contatar?": "SIM" if r.contact_this_week else "",
        })

    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ─── Score Breakdown (detail view) ────────────────────────
    st.divider()
    st.subheader("Detalhamento do Score")

    selected_vehicle = st.selectbox(
        "Selecione um veiculo para ver o breakdown:",
        [r.vehicle_id for r in filtered],
        format_func=lambda vid: f"{vid} — {vehicle_map[vid].modelo} (Score: {next(r.score for r in filtered if r.vehicle_id == vid)})",
    )

    if selected_vehicle:
        result = next(r for r in filtered if r.vehicle_id == selected_vehicle)
        vehicle = vehicle_map[selected_vehicle]

        col_d1, col_d2 = st.columns([1, 2])

        with col_d1:
            st.metric("Score Total", result.score)
            if result.contact_this_week:
                st.error("CONTATAR ESTA SEMANA")
            elif result.is_high_risk:
                st.warning("ALTO RISCO")
            else:
                st.info("Risco moderado/baixo")

            if vehicle.connected_vehicle_available and vehicle.sinal_falha_ativo:
                st.error("ALERTA: Falha ativa detectada via connected vehicle")

        with col_d2:
            breakdown_rows = []
            for rule_name, details in result.breakdown.items():
                breakdown_rows.append({
                    "Regra": rule_name,
                    "Pontos": details["points"],
                    "Detalhes": details["reason"],
                })
            df_breakdown = pd.DataFrame(breakdown_rows)
            st.dataframe(df_breakdown, use_container_width=True, hide_index=True)

    # ─── Score Distribution ───────────────────────────────────
    st.divider()
    st.subheader("Distribuicao de Scores")

    score_ranges = {"0-40 (Baixo)": 0, "41-70 (Moderado)": 0, "71-85 (Alto)": 0, "86-100 (Critico)": 0}
    for r in results:
        if r.score <= 40:
            score_ranges["0-40 (Baixo)"] += 1
        elif r.score <= 70:
            score_ranges["41-70 (Moderado)"] += 1
        elif r.score <= 85:
            score_ranges["71-85 (Alto)"] += 1
        else:
            score_ranges["86-100 (Critico)"] += 1

    df_dist = pd.DataFrame(
        {"Faixa": score_ranges.keys(), "Veiculos": score_ranges.values()}
    )
    st.bar_chart(df_dist.set_index("Faixa"))

    # Footer
    st.divider()
    st.caption(
        "Scoring v1: regras baseadas (sem ML). "
        "Pesos: visita paga (40pts), tipo servico (20pts), idade (15pts), "
        "frequencia (15pts), revisao proxima (10pts). "
        "Filtro LGPD aplicado — apenas veiculos com consentimento."
    )
