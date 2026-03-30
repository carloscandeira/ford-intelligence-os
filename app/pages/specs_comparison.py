"""
Ficha Tecnica Comparativa — Side-by-side spec comparison.

Tab 2 of Ford Intelligence OS dashboard.
Visual comparison table: Ford Ranger vs competitors (Hilux, Amarok, L200 Triton).
Highlights where Ford wins/loses on each spec field.
"""

import streamlit as st
import pandas as pd

# Try to import DB connection for live data
import os
try:
    from sqlalchemy import text
    from db.connection import engine
    LIVE_MODE = bool(os.getenv("DATABASE_URL"))
except Exception:
    LIVE_MODE = False


# ─────────────────────────────────────────────────────────────
# Demo data (matches generate_synthetic.py exactly)
# ─────────────────────────────────────────────────────────────

SPECS_DATA = {
    ("Ford", "Ranger", "Raptor"): {
        "potencia": ("400", "cv"),
        "torque": ("59.2", "kgfm"),
        "motor": ("V6 3.0 Biturbo", ""),
        "transmissao": ("Automatica 10 velocidades", ""),
        "tracao": ("4x4", ""),
        "capacidade_carga": ("620", "kg"),
        "entre_eixos": ("3270", "mm"),
        "comprimento": ("5381", "mm"),
        "tanque": ("80", "litros"),
        "preco_sugerido": ("449990", "BRL"),
    },
    ("Ford", "Ranger", "Limited"): {
        "potencia": ("210", "cv"),
        "torque": ("51", "kgfm"),
        "motor": ("2.0 Turbo Diesel", ""),
        "transmissao": ("Automatica 6 velocidades", ""),
        "tracao": ("4x4", ""),
        "capacidade_carga": ("785", "kg"),
        "entre_eixos": ("3270", "mm"),
        "comprimento": ("5381", "mm"),
        "tanque": ("80", "litros"),
        "preco_sugerido": ("289990", "BRL"),
    },
    ("Toyota", "Hilux", "SRX"): {
        "potencia": ("204", "cv"),
        "torque": ("50.9", "kgfm"),
        "motor": ("2.8 Turbo Diesel", ""),
        "transmissao": ("Automatica 6 velocidades", ""),
        "tracao": ("4x4", ""),
        "capacidade_carga": ("720", "kg"),
        "entre_eixos": ("3085", "mm"),
        "comprimento": ("5325", "mm"),
        "tanque": ("80", "litros"),
        "preco_sugerido": ("299990", "BRL"),
    },
    ("Toyota", "Hilux", "GR-Sport"): {
        "potencia": ("224", "cv"),
        "torque": ("55.1", "kgfm"),
        "motor": ("2.8 Turbo Diesel", ""),
        "transmissao": ("Automatica 6 velocidades", ""),
        "tracao": ("4x4", ""),
        "capacidade_carga": ("680", "kg"),
        "entre_eixos": ("3085", "mm"),
        "comprimento": ("5325", "mm"),
        "tanque": ("80", "litros"),
        "preco_sugerido": ("369990", "BRL"),
    },
    ("Mitsubishi", "L200 Triton", "Savana"): {
        "potencia": ("190", "cv"),
        "torque": ("43.9", "kgfm"),
        "motor": ("2.4 Turbo Diesel", ""),
        "transmissao": ("Automatica 6 velocidades", ""),
        "tracao": ("4x4", ""),
        "capacidade_carga": ("715", "kg"),
        "entre_eixos": ("3000", "mm"),
        "comprimento": ("5305", "mm"),
        "tanque": ("75", "litros"),
        "preco_sugerido": ("279990", "BRL"),
    },
    ("Volkswagen", "Amarok", "Highline V6"): {
        "potencia": ("258", "cv"),
        "torque": ("59.1", "kgfm"),
        "motor": ("V6 3.0 Turbo Diesel", ""),
        "transmissao": ("Automatica 10 velocidades", ""),
        "tracao": ("4x4 permanente", ""),
        "capacidade_carga": ("710", "kg"),
        "entre_eixos": ("3270", "mm"),
        "comprimento": ("5350", "mm"),
        "tanque": ("80", "litros"),
        "preco_sugerido": ("339990", "BRL"),
    },
}

# Fields that should be compared numerically (higher is better / lower is better)
NUMERIC_FIELDS = {
    "potencia": "higher",
    "torque": "higher",
    "capacidade_carga": "higher",
    "entre_eixos": "higher",
    "comprimento": "higher",
    "tanque": "higher",
    "preco_sugerido": "lower",
}

FIELD_LABELS = {
    "potencia": "Potencia",
    "torque": "Torque",
    "motor": "Motor",
    "transmissao": "Transmissao",
    "tracao": "Tracao",
    "capacidade_carga": "Capacidade de Carga",
    "entre_eixos": "Entre-eixos",
    "comprimento": "Comprimento",
    "tanque": "Tanque",
    "preco_sugerido": "Preco Sugerido",
}


def _load_live_data() -> dict:
    """Load spec data from database."""
    query = text("""
        SELECT marca, modelo, versao, campo, valor, unidade
        FROM vehicle_spec
        WHERE mercado = 'BR' AND verificado = TRUE
        ORDER BY marca, modelo, versao
    """)
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    data = {}
    for row in rows:
        key = (row.marca, row.modelo, row.versao)
        if key not in data:
            data[key] = {}
        data[key][row.campo] = (row.valor or "N/D", row.unidade or "")
    return data


def _format_value(valor: str, unidade: str) -> str:
    """Format a spec value with its unit."""
    if not valor or valor == "N/D":
        return "N/D"
    if unidade == "BRL":
        try:
            return f"R$ {int(valor):,.0f}".replace(",", ".")
        except ValueError:
            return valor
    if unidade:
        return f"{valor} {unidade}"
    return valor


def _highlight_best(values: dict[str, float], direction: str) -> str:
    """Return the key of the best value."""
    if not values:
        return ""
    if direction == "higher":
        return max(values, key=values.get)
    return min(values, key=values.get)


def render():
    """Render the Ficha Tecnica Comparativa tab."""
    st.header("Ficha Tecnica Comparativa")
    st.markdown(
        "Comparacao lado a lado das especificacoes tecnicas de pickups no mercado brasileiro. "
        "Dados extraidos automaticamente dos sites oficiais dos fabricantes."
    )

    # Load data
    if LIVE_MODE:
        try:
            specs = _load_live_data()
            if not specs:
                specs = SPECS_DATA
                st.info("Banco vazio — usando dados de demonstracao", icon="🔵")
        except Exception:
            specs = SPECS_DATA
            st.info("Modo demonstracao — banco nao conectado", icon="🔵")
    else:
        specs = SPECS_DATA
        st.info("Modo demonstracao — banco nao conectado", icon="🔵")

    # Vehicle selector
    all_vehicles = list(specs.keys())
    vehicle_labels = [f"{m} {mod} {v}" for m, mod, v in all_vehicles]

    selected = st.multiselect(
        "Selecione veiculos para comparar:",
        options=range(len(all_vehicles)),
        format_func=lambda i: vehicle_labels[i],
        default=list(range(min(4, len(all_vehicles)))),
    )

    if len(selected) < 2:
        st.warning("Selecione pelo menos 2 veiculos para comparar.")
        return

    selected_vehicles = [all_vehicles[i] for i in selected]
    selected_specs = {k: specs[k] for k in selected_vehicles}

    # ─── Comparison Table ─────────────────────────────────────
    st.divider()

    # Get all unique fields
    all_fields = []
    seen = set()
    for vehicle_specs in selected_specs.values():
        for campo in vehicle_specs:
            if campo not in seen:
                all_fields.append(campo)
                seen.add(campo)

    # Build comparison dataframe
    rows = []
    for campo in all_fields:
        row = {"Especificacao": FIELD_LABELS.get(campo, campo)}

        # Collect numeric values for highlighting
        numeric_vals = {}

        for (marca, modelo, versao), vehicle_specs in selected_specs.items():
            col_name = f"{marca} {modelo} {versao}"
            if campo in vehicle_specs:
                valor, unidade = vehicle_specs[campo]
                row[col_name] = _format_value(valor, unidade)

                # Track numeric value for highlighting
                if campo in NUMERIC_FIELDS:
                    try:
                        numeric_vals[col_name] = float(valor.replace(",", "."))
                    except (ValueError, AttributeError):
                        pass
            else:
                row[col_name] = "N/D"

        # Mark best value
        if campo in NUMERIC_FIELDS and numeric_vals:
            best_col = _highlight_best(numeric_vals, NUMERIC_FIELDS[campo])
            if best_col in row:
                row[best_col] = row[best_col] + " ✓"

        rows.append(row)

    df = pd.DataFrame(rows)

    # Style: highlight Ford columns
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=len(rows) * 40 + 40,
    )

    # ─── Summary Metrics ──────────────────────────────────────
    st.divider()
    st.subheader("Resumo Competitivo")

    # Count wins per vehicle
    wins = {}
    for campo in all_fields:
        if campo not in NUMERIC_FIELDS:
            continue
        numeric_vals = {}
        for (marca, modelo, versao), vehicle_specs in selected_specs.items():
            col_name = f"{marca} {modelo} {versao}"
            if campo in vehicle_specs:
                try:
                    numeric_vals[col_name] = float(
                        vehicle_specs[campo][0].replace(",", ".")
                    )
                except (ValueError, AttributeError):
                    pass
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
                st.metric(
                    vehicle,
                    f"{count} melhor(es)",
                    delta="Ford" if is_ford else None,
                    delta_color="normal" if is_ford else "off",
                )

    # Source attribution
    st.divider()
    st.caption("Dados extraidos de: ford.com.br, toyota.com.br, mitsubishi-motors.com.br, vw.com.br")
    st.caption("Atualizacao: verificar campo 'extraido_em' de cada registro no banco de dados.")
