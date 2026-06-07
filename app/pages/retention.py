"""
Retencao & Churn — Churn risk dashboard.

Tab 3 of Ford Intelligence OS dashboard.
Shows churn risk scores, breakdown per vehicle, filters, and batch scoring.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime

# Try to import real modules
import os
try:
    from sqlalchemy import text
    from db.connection import engine
    DB_AVAILABLE = bool(os.getenv("DATABASE_URL"))
except Exception:
    DB_AVAILABLE = False

from scoring.churn_scorer import (
    VehicleData,
    score_all_vehicles,
)


# ─────────────────────────────────────────────────────────────
# Demo data (when DB not connected)
# ─────────────────────────────────────────────────────────────

def _generate_demo_vehicles():
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


def _load_vehicles_from_db():
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


def _score_badge(score: int) -> str:
    """Return HTML badge for score level."""
    if score > 85:
        return '<span class="ford-badge" style="background:rgba(220,53,69,0.1);color:#DC3545;border:1px solid rgba(220,53,69,0.2);">CRITICO</span>'
    if score > 70:
        return '<span class="ford-badge" style="background:rgba(229,150,10,0.1);color:#E5960A;border:1px solid rgba(229,150,10,0.2);">ALTO</span>'
    if score > 40:
        return '<span class="ford-badge" style="background:rgba(0,163,224,0.1);color:#00A3E0;border:1px solid rgba(0,163,224,0.2);">MODERADO</span>'
    return '<span class="ford-badge" style="background:rgba(14,164,122,0.1);color:#0EA47A;border:1px solid rgba(14,164,122,0.2);">BAIXO</span>'


def _score_color_emoji(score: int) -> str:
    if score > 85:
        return "🔴"
    if score > 70:
        return "🟠"
    if score > 40:
        return "🟡"
    return "🟢"


def render():
    """Render the Retencao & Churn tab."""
    # Header
    st.markdown(
        '<div class="ford-header">'
        '<span class="ford-module-tag">Modulo 2</span>'
        '<h1>Retencao & Churn</h1>'
        '<span class="ford-subtitle">Identifique clientes em risco antes que migrem</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ─── Load & Score ─────────────────────────────────────────
    if DB_AVAILABLE:
        try:
            vehicles = _load_vehicles_from_db()
            if not vehicles:
                vehicles = _generate_demo_vehicles()
                st.markdown('<span class="ford-badge ford-badge-demo">Dados demo</span>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<span class="ford-badge ford-badge-live">{len(vehicles)} veiculos (LGPD consent)</span>',
                    unsafe_allow_html=True,
                )
        except Exception:
            vehicles = _generate_demo_vehicles()
            st.markdown('<span class="ford-badge ford-badge-demo">Modo demonstracao</span>', unsafe_allow_html=True)
    else:
        vehicles = _generate_demo_vehicles()
        st.markdown('<span class="ford-badge ford-badge-demo">Modo demonstracao</span>', unsafe_allow_html=True)

    results = score_all_vehicles(vehicles)
    vehicle_map = {v.vehicle_id: v for v in vehicles}

    # ─── PDF Export ───────────────────────────────────────────
    try:
        from app.pdf_report import generate_retention_pdf
        pdf_bytes = generate_retention_pdf(results, vehicles, vehicle_map)
        st.download_button(
            "Exportar PDF",
            data=pdf_bytes,
            file_name=f"retencao_churn_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            type="primary",
        )
    except Exception:
        st.caption("Exportacao em PDF temporariamente indisponivel.")

    st.write("")

    # ─── Top Metrics ──────────────────────────────────────────
    high_risk = [r for r in results if r.is_high_risk]
    contact_now = [r for r in results if r.contact_this_week]
    avg_score = sum(r.score for r in results) / len(results) if results else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Frota", len(results))
    with col2:
        st.metric("Alto Risco (>70)", len(high_risk))
    with col3:
        st.metric("Contatar Urgente", len(contact_now))
    with col4:
        st.metric("Score Medio", f"{avg_score:.0f}/100")

    # ─── Distribution chart + Filters in columns ──────────────
    st.write("")
    col_chart, col_filters = st.columns([2, 1])

    with col_chart:
        st.markdown('<span class="ford-section-title">Distribuicao de Risco</span>', unsafe_allow_html=True)

        score_ranges = {
            "Baixo\n0-40": 0,
            "Moderado\n41-70": 0,
            "Alto\n71-85": 0,
            "Critico\n86-100": 0,
        }
        for r in results:
            if r.score <= 40:
                score_ranges["Baixo\n0-40"] += 1
            elif r.score <= 70:
                score_ranges["Moderado\n41-70"] += 1
            elif r.score <= 85:
                score_ranges["Alto\n71-85"] += 1
            else:
                score_ranges["Critico\n86-100"] += 1

        range_colors = ["#0EA47A", "#00A3E0", "#E5960A", "#DC3545"]

        try:
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(
                x=list(score_ranges.keys()),
                y=list(score_ranges.values()),
                marker_color=range_colors,
                text=list(score_ranges.values()),
                textposition="outside",
                textfont=dict(size=13, color="#334155"),
            ))
            fig.update_layout(
                height=250,
                margin=dict(l=0, r=0, t=8, b=0),
                yaxis=dict(
                    gridcolor="rgba(0,0,0,0.05)",
                    tickfont_color="#94A3B8",
                ),
                xaxis=dict(tickfont=dict(size=11, color="#64748B")),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                bargap=0.35,
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            df_dist = pd.DataFrame(
                {"Faixa": score_ranges.keys(), "Veiculos": score_ranges.values()}
            )
            st.bar_chart(df_dist.set_index("Faixa"))

    with col_filters:
        st.markdown('<span class="ford-section-title">Filtros</span>', unsafe_allow_html=True)
        min_score = st.slider("Score minimo", 0, 100, 0)
        modelos = sorted(set(v.modelo for v in vehicles))
        selected_modelos = st.multiselect("Modelo", modelos, default=modelos)
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
    st.markdown(
        f'<span class="ford-section-title">Veiculos ({len(filtered)} de {len(results)})</span>',
        unsafe_allow_html=True,
    )

    if not filtered:
        st.warning("Nenhum veiculo encontrado com os filtros selecionados.")
        return

    # Build display dataframe
    table_rows = []
    for r in filtered:
        v = vehicle_map.get(r.vehicle_id)
        if not v:
            continue
        table_rows.append({
            "Risco": _score_color_emoji(r.score),
            "Score": r.score,
            "ID": r.vehicle_id,
            "Modelo": v.modelo,
            "Ano": v.ano_fabricacao or "N/D",
            "KM": f"{v.km_estimado:,}" if v.km_estimado else "N/D",
            "Ult. Visita": str(v.ultima_visita_paga) if v.ultima_visita_paga else "Nunca",
            "Visitas 2a": v.qtd_visitas_pagas_2_anos,
            "Connected": "Sim" if v.connected_vehicle_available else "—",
            "Acao": "CONTATAR" if r.contact_this_week else "",
        })

    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ─── Score Breakdown (detail view) ────────────────────────
    st.write("")
    st.markdown('<span class="ford-section-title">Detalhamento do Score</span>', unsafe_allow_html=True)

    selected_vehicle = st.selectbox(
        "Selecione um veiculo:",
        [r.vehicle_id for r in filtered],
        format_func=lambda vid: f"{vid} — {vehicle_map[vid].modelo} (Score: {next(r.score for r in filtered if r.vehicle_id == vid)})",
    )

    if selected_vehicle:
        result = next(r for r in filtered if r.vehicle_id == selected_vehicle)
        vehicle = vehicle_map[selected_vehicle]

        col_d1, col_d2 = st.columns([1, 3])

        with col_d1:
            # Score gauge
            score = result.score
            score_color = "#DC3545" if score > 85 else "#E5960A" if score > 70 else "#00A3E0" if score > 40 else "#0EA47A"

            st.markdown(
                f'<div style="text-align:center; padding:1rem;">'
                f'<div style="font-size:2.5rem; font-weight:800; color:{score_color};">{score}</div>'
                f'<div style="font-size:0.8rem; color:var(--ford-text-secondary);">de 100</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown(_score_badge(score), unsafe_allow_html=True)

            if vehicle.connected_vehicle_available and vehicle.sinal_falha_ativo:
                st.error("Falha ativa detectada")

        with col_d2:
            breakdown_rows = []
            for rule_name, details in result.breakdown.items():
                pts = details["points"]
                breakdown_rows.append({
                    "Regra": rule_name,
                    "Pontos": pts,
                    "Max": details.get("max", 0),
                    "Detalhes": details["reason"],
                })
            df_breakdown = pd.DataFrame(breakdown_rows)
            st.dataframe(df_breakdown, use_container_width=True, hide_index=True)

    # Footer
    st.markdown(
        '<div class="ford-footer">'
        'Scoring v1: regras ponderadas (visita 40pts, servico 20pts, idade 15pts, '
        'frequencia 15pts, revisao 10pts). Filtro LGPD aplicado.'
        '</div>',
        unsafe_allow_html=True,
    )
