"""
Ficha Tecnica Comparativa — Side-by-side spec comparison.

Tab 2 of Ford Intelligence OS dashboard.
Visual comparison table: any vehicle from DB vs competitors.
Highlights where Ford wins/loses on each spec field.
Includes price comparison bar chart.
"""

import streamlit as st
import pandas as pd

import os
from typing import Optional
try:
    from sqlalchemy import text
    from db.connection import engine
    LIVE_MODE = bool(os.getenv("DATABASE_URL"))
except Exception:
    LIVE_MODE = False


# ─────────────────────────────────────────────────────────────
# Demo data fallback
# ─────────────────────────────────────────────────────────────

SPECS_DATA = {
    ("Ford", "Ranger", "Raptor"): {
        "potencia": ("397", "cv"), "torque": ("59,4", "kgfm"),
        "motor": ("V6 3.0 EcoBoost Biturbo", ""), "transmissao": ("Automatica 10 velocidades", ""),
        "tracao": ("4x4 integral sob demanda", ""), "capacidade_carga": ("736", "kg"),
        "entre_eixos": ("3270", "mm"), "comprimento": ("5360", "mm"),
        "tanque": ("82", "litros"), "preco_sugerido": ("458491", "BRL"),
    },
    ("Ford", "Ranger", "Limited"): {
        "potencia": ("250", "cv"), "torque": ("61,2", "kgfm"),
        "motor": ("V6 3.0 Turbo Diesel", ""), "transmissao": ("Automatica 10 velocidades", ""),
        "tracao": ("4x4 integral temporaria", ""), "capacidade_carga": ("1023", "kg"),
        "entre_eixos": ("3270", "mm"), "comprimento": ("5360", "mm"),
        "tanque": ("80", "litros"), "preco_sugerido": ("307203", "BRL"),
    },
    ("Toyota", "Hilux", "SRX"): {
        "potencia": ("204", "cv"), "torque": ("42,8", "kgfm"),
        "motor": ("2.8L Turbo Diesel", ""), "transmissao": ("Automatica 6 velocidades", ""),
        "tracao": ("4x4", ""), "capacidade_carga": ("720", "kg"),
        "entre_eixos": ("3085", "mm"), "comprimento": ("5325", "mm"),
        "tanque": ("80", "litros"), "preco_sugerido": ("305521", "BRL"),
    },
    ("Mitsubishi", "L200 Triton", "Savana"): {
        "potencia": ("205", "cv"), "torque": ("47,9", "kgfm"),
        "motor": ("2.4 Bi-Turbo Diesel", ""), "transmissao": ("Automatica 6 velocidades", ""),
        "tracao": ("4x4 Super Select II", ""), "capacidade_carga": ("715", "kg"),
        "entre_eixos": ("3000", "mm"), "comprimento": ("5305", "mm"),
        "tanque": ("75", "litros"), "preco_sugerido": ("279990", "BRL"),
    },
    ("Volkswagen", "Amarok", "Highline V6"): {
        "potencia": ("258", "cv"), "torque": ("59,1", "kgfm"),
        "motor": ("V6 3.0 TDI", ""), "transmissao": ("Automatica 8 velocidades", ""),
        "tracao": ("4Motion (4x4 Permanente)", ""), "capacidade_carga": ("1280", "kg"),
        "entre_eixos": ("3270", "mm"), "comprimento": ("5350", "mm"),
        "tanque": ("80", "litros"), "preco_sugerido": ("289682", "BRL"),
    },
}

NUMERIC_FIELDS = {
    "potencia": "higher", "torque": "higher", "capacidade_carga": "higher",
    "entre_eixos": "higher", "comprimento": "higher", "tanque": "higher",
    "preco_sugerido": "lower",
}

FIELD_LABELS = {
    "potencia": "Potencia (cv)", "torque": "Torque (kgfm)", "motor": "Motor",
    "transmissao": "Transmissao", "tracao": "Tracao", "capacidade_carga": "Cap. Carga (kg)",
    "entre_eixos": "Entre-eixos (mm)", "comprimento": "Comprimento (mm)",
    "tanque": "Tanque (L)", "preco_sugerido": "Preco FIPE (R$)",
    "autonomia_eletrica": "Autonomia (km)",
}

FIELD_ORDER = [
    "preco_sugerido", "potencia", "torque", "motor", "transmissao",
    "tracao", "capacidade_carga", "tanque", "entre_eixos", "comprimento",
    "autonomia_eletrica",
]


def _load_live_data() -> dict:
    """Load all verified specs from database."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT marca, modelo, versao, campo, valor, unidade
            FROM vehicle_spec
            WHERE mercado = 'BR'
            ORDER BY marca, modelo, versao, campo
        """)).fetchall()

    data = {}
    for row in rows:
        key = (row.marca, row.modelo, row.versao)
        if key not in data:
            data[key] = {}
        data[key][row.campo] = (row.valor or "N/D", row.unidade or "")
    return data


def _format_value(valor: str, unidade: str) -> str:
    if not valor or valor == "N/D":
        return "—"
    if unidade == "BRL":
        try:
            return f"R$ {int(valor):,}".replace(",", ".")
        except ValueError:
            return valor
    if unidade:
        return f"{valor} {unidade}"
    return valor


def _to_float(valor: str) -> Optional[float]:
    try:
        return float(str(valor).replace(",", ".").replace(".", "", str(valor).count(".") - 1))
    except Exception:
        return None


def _highlight_best(values: dict, direction: str) -> str:
    if not values:
        return ""
    return max(values, key=values.get) if direction == "higher" else min(values, key=values.get)


def render():
    st.header("Ficha Tecnica Comparativa")
    st.markdown(
        "Compare qualquer veiculo do banco de dados lado a lado. "
        "Dados extraidos automaticamente dos sites oficiais dos fabricantes. "
        "**✓** indica o melhor valor em cada categoria."
    )

    # Load data
    if LIVE_MODE:
        try:
            specs = _load_live_data()
            if not specs:
                specs = SPECS_DATA
                st.info("Banco vazio — usando dados de demonstracao", icon="🔵")
            else:
                st.success(f"Banco conectado — {len(specs)} versoes disponiveis", icon="🟢")
        except Exception as e:
            specs = SPECS_DATA
            st.info("Modo demonstracao", icon="🔵")
    else:
        specs = SPECS_DATA
        st.info("Modo demonstracao — banco nao conectado", icon="🔵")

    # ─── Vehicle selector ─────────────────────────────────────
    all_vehicles = sorted(specs.keys(), key=lambda x: (x[0] != "Ford", x[0], x[1], x[2]))
    vehicle_labels = [f"{m} {mod} {v}" for m, mod, v in all_vehicles]

    # Smart defaults: Ford Ranger Raptor + 3 main competitors
    default_labels = ["Ford Ranger Raptor", "Toyota Hilux SRX",
                      "Volkswagen Amarok Highline V6", "Mitsubishi L200 Triton Savana"]
    default_idx = [i for i, l in enumerate(vehicle_labels)
                   if any(d in l for d in default_labels)][:4]
    if len(default_idx) < 2:
        default_idx = list(range(min(4, len(all_vehicles))))

    col_sel, col_filter = st.columns([3, 1])
    with col_filter:
        marca_filter = st.selectbox(
            "Filtrar por marca:",
            ["Todas"] + sorted(set(m for m, _, _ in all_vehicles)),
        )

    filtered_vehicles = all_vehicles if marca_filter == "Todas" else \
        [v for v in all_vehicles if v[0] == marca_filter]
    filtered_labels = [f"{m} {mod} {v}" for m, mod, v in filtered_vehicles]

    with col_sel:
        selected_labels = st.multiselect(
            "Selecione veiculos para comparar:",
            options=filtered_labels,
            default=[vehicle_labels[i] for i in default_idx
                     if vehicle_labels[i] in filtered_labels][:4],
        )

    if len(selected_labels) < 2:
        st.warning("Selecione pelo menos 2 veiculos para comparar.")
        return

    selected_vehicles = [filtered_vehicles[filtered_labels.index(l)] for l in selected_labels]
    selected_specs = {k: specs[k] for k in selected_vehicles}

    # ─── Price chart ──────────────────────────────────────────
    price_data = {}
    for (marca, modelo, versao), vspecs in selected_specs.items():
        if "preco_sugerido" in vspecs:
            val = _to_float(vspecs["preco_sugerido"][0])
            if val:
                label = f"{marca}\n{modelo} {versao}"
                price_data[label] = val / 1000  # em mil R$

    if price_data:
        st.divider()
        st.subheader("Comparacao de Preco (R$ mil — FIPE)")
        df_price = pd.DataFrame({
            "Veiculo": list(price_data.keys()),
            "Preco (R$ mil)": list(price_data.values()),
        }).sort_values("Preco (R$ mil)")

        # Color Ford bars differently
        colors = ["#003478" if "Ford" in v else "#888888" for v in df_price["Veiculo"]]

        try:
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(
                x=df_price["Preco (R$ mil)"],
                y=df_price["Veiculo"],
                orientation="h",
                marker_color=colors,
                text=[f"R$ {v:,.0f}k".replace(",", ".") for v in df_price["Preco (R$ mil)"]],
                textposition="outside",
            ))
            fig.update_layout(
                height=max(200, len(price_data) * 60),
                margin=dict(l=0, r=80, t=10, b=10),
                xaxis_title="R$ mil",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white",
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.bar_chart(df_price.set_index("Veiculo"))

    # ─── Comparison table ─────────────────────────────────────
    st.divider()
    st.subheader("Especificacoes Tecnicas")

    all_campos = set()
    for vspecs in selected_specs.values():
        all_campos.update(vspecs.keys())

    ordered_campos = [c for c in FIELD_ORDER if c in all_campos] + \
                     [c for c in all_campos if c not in FIELD_ORDER]

    rows = []
    for campo in ordered_campos:
        row = {"Especificacao": FIELD_LABELS.get(campo, campo)}
        numeric_vals = {}

        for (marca, modelo, versao), vspecs in selected_specs.items():
            col_name = f"{marca} {modelo} {versao}"
            if campo in vspecs:
                valor, unidade = vspecs[campo]
                row[col_name] = _format_value(valor, unidade)
                if campo in NUMERIC_FIELDS:
                    fval = _to_float(valor)
                    if fval is not None:
                        numeric_vals[col_name] = fval
            else:
                row[col_name] = "—"

        if campo in NUMERIC_FIELDS and numeric_vals:
            best = _highlight_best(numeric_vals, NUMERIC_FIELDS[campo])
            if best in row and row[best] != "—":
                row[best] = row[best] + " ✓"

        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True,
                 height=min(len(rows) * 38 + 40, 600))

    # ─── Win summary ──────────────────────────────────────────
    st.divider()
    st.subheader("Resumo Competitivo")

    wins = {}
    for campo in ordered_campos:
        if campo not in NUMERIC_FIELDS:
            continue
        numeric_vals = {}
        for (marca, modelo, versao), vspecs in selected_specs.items():
            col_name = f"{marca} {modelo} {versao}"
            if campo in vspecs:
                fval = _to_float(vspecs[campo][0])
                if fval is not None:
                    numeric_vals[col_name] = fval
        if numeric_vals:
            best = _highlight_best(numeric_vals, NUMERIC_FIELDS[campo])
            wins[best] = wins.get(best, 0) + 1

    if wins:
        cols = st.columns(len(wins))
        for i, (vehicle, count) in enumerate(
            sorted(wins.items(), key=lambda x: x[1], reverse=True)
        ):
            with cols[i]:
                is_ford = "Ford" in vehicle
                short = vehicle.replace("Ford ", "").replace("Toyota ", "").replace(
                    "Volkswagen ", "VW ").replace("Mitsubishi ", "")
                st.metric(
                    short,
                    f"{count} lider(es)",
                    delta="Ford" if is_ford else None,
                    delta_color="normal" if is_ford else "off",
                )

    st.divider()
    st.caption(
        "Fontes: vw.com.br, toyota.com.br, mitsubishimotors.com.br (oficiais) | "
        "Ford: carrosnaweb.com.br (ford.com.br bloqueia scraping). "
        "Precos: Tabela FIPE."
    )
