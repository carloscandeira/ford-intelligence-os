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
    "potencia": "Potencia", "torque": "Torque", "motor": "Motor",
    "transmissao": "Transmissao", "tracao": "Tracao", "capacidade_carga": "Cap. Carga",
    "entre_eixos": "Entre-eixos", "comprimento": "Comprimento",
    "tanque": "Tanque", "preco_sugerido": "Preco (R$)",
    "preco_concessionaria": "Preco Concessionaria (R$)",
    "autonomia_eletrica": "Autonomia",
}

FIELD_UNITS = {
    "potencia": "cv", "torque": "kgfm", "capacidade_carga": "kg",
    "entre_eixos": "mm", "comprimento": "mm", "tanque": "L",
    "preco_sugerido": "R$", "autonomia_eletrica": "km",
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
    # Header
    st.markdown(
        '<div class="ford-header">'
        '<span class="ford-module-tag">Modulo 1</span>'
        '<h1>Ficha Tecnica Comparativa</h1>'
        '<span class="ford-subtitle">Comparacao lado a lado com dados ao vivo</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Load data
    if LIVE_MODE:
        try:
            specs = _load_live_data()
            if not specs:
                specs = SPECS_DATA
                st.markdown('<span class="ford-badge ford-badge-demo">Banco vazio — dados demo</span>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<span class="ford-badge ford-badge-live">{len(specs)} versoes disponiveis</span>',
                    unsafe_allow_html=True,
                )
        except Exception:
            specs = SPECS_DATA
            st.markdown('<span class="ford-badge ford-badge-demo">Modo demonstracao</span>', unsafe_allow_html=True)
    else:
        specs = SPECS_DATA
        st.markdown('<span class="ford-badge ford-badge-demo">Modo demonstracao</span>', unsafe_allow_html=True)

    st.write("")

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
            "Filtrar marca",
            ["Todas"] + sorted(set(m for m, _, _ in all_vehicles)),
        )

    filtered_vehicles = all_vehicles if marca_filter == "Todas" else \
        [v for v in all_vehicles if v[0] == marca_filter]
    filtered_labels = [f"{m} {mod} {v}" for m, mod, v in filtered_vehicles]

    with col_sel:
        selected_labels = st.multiselect(
            "Veiculos para comparar",
            options=filtered_labels,
            default=[vehicle_labels[i] for i in default_idx
                     if vehicle_labels[i] in filtered_labels][:4],
        )

    if len(selected_labels) < 2:
        st.info("Selecione pelo menos 2 veiculos para comparar.")
        return

    selected_vehicles = [filtered_vehicles[filtered_labels.index(l)] for l in selected_labels]
    selected_specs = {k: specs[k] for k in selected_vehicles}

    # ─── Price chart ──────────────────────────────────────────
    price_data = {}
    for (marca, modelo, versao), vspecs in selected_specs.items():
        if "preco_sugerido" in vspecs:
            val = _to_float(vspecs["preco_sugerido"][0])
            if val:
                label = f"{marca} {modelo} {versao}"
                price_data[label] = val / 1000

    if price_data:
        st.write("")
        st.markdown('<span class="ford-section-title">Comparacao de Preco</span>', unsafe_allow_html=True)

        df_price = pd.DataFrame({
            "Veiculo": list(price_data.keys()),
            "Preco (R$ mil)": list(price_data.values()),
        }).sort_values("Preco (R$ mil)")

        colors = ["#003478" if "Ford" in v else "#CBD5E1" for v in df_price["Veiculo"]]

        try:
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(
                x=df_price["Preco (R$ mil)"],
                y=df_price["Veiculo"],
                orientation="h",
                marker_color=colors,
                text=[f"R$ {v:,.0f}k".replace(",", ".") for v in df_price["Preco (R$ mil)"]],
                textposition="outside",
                textfont=dict(size=12, color="#334155"),
            ))
            fig.update_layout(
                height=max(180, len(price_data) * 55),
                margin=dict(l=10, r=60, t=8, b=8),
                xaxis=dict(
                    title="R$ mil",
                    gridcolor="rgba(0,0,0,0.06)",
                    title_font_color="#94A3B8",
                    tickfont_color="#94A3B8",
                ),
                yaxis=dict(tickfont=dict(size=11, color="#334155")),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.bar_chart(df_price.set_index("Veiculo"))

    # ─── Comparison table ─────────────────────────────────────
    st.markdown('<span class="ford-section-title">Especificacoes Tecnicas</span>', unsafe_allow_html=True)

    all_campos = set()
    for vspecs in selected_specs.values():
        all_campos.update(vspecs.keys())

    ordered_campos = [c for c in FIELD_ORDER if c in all_campos] + \
                     [c for c in all_campos if c not in FIELD_ORDER]

    rows = []
    for campo in ordered_campos:
        label = FIELD_LABELS.get(campo, campo)
        unit = FIELD_UNITS.get(campo, "")
        if unit and unit != "R$":
            label = f"{label} ({unit})"

        row = {"Especificacao": label}
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
    st.markdown('<span class="ford-section-title">Resumo Competitivo</span>', unsafe_allow_html=True)

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
                    f"{count} {'vitorias' if count > 1 else 'vitoria'}",
                    delta="Ford" if is_ford else None,
                    delta_color="normal" if is_ford else "off",
                )

    # Footer
    st.markdown(
        '<div class="ford-footer">'
        'Fontes: vw.com.br, toyota.com.br, mitsubishimotors.com.br (oficiais) | '
        'Ford: carrosnaweb.com.br | ✓ = melhor valor na categoria'
        '</div>',
        unsafe_allow_html=True,
    )
