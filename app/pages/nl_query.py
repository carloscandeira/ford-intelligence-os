"""
Consulta Inteligente — Natural Language Query interface.

Tab 1 of Ford Intelligence OS dashboard.
User types a question in Portuguese, LLM generates SQL,
executes against vehicle_spec table, shows results with source attribution.
"""

import streamlit as st
import pandas as pd

# Try to import the real query engine; fall back to demo mode
# Requires both sqlalchemy (DB) AND OPENAI_API_KEY (LLM) to be live
import os
try:
    from nl_query.sql_generator import execute_query, sanitize_sql
    LIVE_MODE = bool(os.getenv("OPENAI_API_KEY")) and bool(os.getenv("DATABASE_URL"))
except Exception:
    LIVE_MODE = False


# ─────────────────────────────────────────────────────────────
# Demo data for when DB is not connected
# ─────────────────────────────────────────────────────────────

EXAMPLE_QUESTIONS = [
    "Qual a potencia da Ranger Raptor?",
    "Compare o torque da Hilux SRX com a Ranger Limited",
    "Quais pickups tem tracao 4x4?",
    "Qual o preco da Amarok V6 vs Ranger Raptor?",
    "Qual pickup tem maior capacidade de carga?",
]

DEMO_RESULTS = {
    "Qual a potencia da Ranger Raptor?": {
        "sql": """SELECT marca, modelo, versao, valor, unidade, fonte_url, extraido_em
FROM vehicle_spec
WHERE modelo = 'Ranger' AND versao = 'Raptor' AND campo = 'potencia' AND mercado = 'BR'""",
        "data": [
            {
                "marca": "Ford", "modelo": "Ranger", "versao": "Raptor",
                "valor": "400", "unidade": "cv",
                "fonte_url": "https://www.ford.com.br/ranger/",
                "extraido_em": "2026-03-28",
            }
        ],
    },
    "Compare o torque da Hilux SRX com a Ranger Limited": {
        "sql": """SELECT marca, modelo, versao, valor AS torque, unidade, fonte_url
FROM vehicle_spec
WHERE campo = 'torque' AND mercado = 'BR'
AND (
    (modelo = 'Hilux' AND versao = 'SRX')
    OR (modelo = 'Ranger' AND versao = 'Limited')
)""",
        "data": [
            {
                "marca": "Toyota", "modelo": "Hilux", "versao": "SRX",
                "torque": "50.9", "unidade": "kgfm",
                "fonte_url": "https://www.toyota.com.br/hilux/",
            },
            {
                "marca": "Ford", "modelo": "Ranger", "versao": "Limited",
                "torque": "51", "unidade": "kgfm",
                "fonte_url": "https://www.ford.com.br/ranger/",
            },
        ],
    },
}


def render():
    """Render the Consulta Inteligente tab."""
    st.header("Consulta Inteligente")
    st.markdown(
        "Faca perguntas em linguagem natural sobre especificacoes de veiculos "
        "no mercado brasileiro. A IA gera SQL, executa a consulta, e mostra os "
        "resultados com **rastreabilidade completa** (fonte + data de extracao)."
    )

    # Status indicator
    if LIVE_MODE:
        st.success("Conectado ao banco de dados", icon="🟢")
    else:
        st.info("Modo demonstracao — banco de dados nao conectado", icon="🔵")

    # ─── Input ────────────────────────────────────────────────
    col1, col2 = st.columns([3, 1])

    with col1:
        question = st.text_input(
            "Sua pergunta:",
            placeholder="Ex: Qual a potencia da Ranger Raptor?",
        )

    with col2:
        st.markdown("##### Exemplos")
        for ex in EXAMPLE_QUESTIONS:
            if st.button(ex, key=f"ex_{ex[:20]}", use_container_width=True):
                question = ex

    if not question:
        st.caption("Digite uma pergunta acima ou clique em um exemplo.")
        return

    # ─── Execute ──────────────────────────────────────────────
    with st.spinner("Gerando SQL e executando consulta..."):
        if LIVE_MODE:
            result = execute_query(question)
            sql = result.sql_generated
            data = result.data
            error = result.error
        else:
            # Demo mode: use pre-built results or show generic
            if question in DEMO_RESULTS:
                demo = DEMO_RESULTS[question]
                sql = demo["sql"]
                data = demo["data"]
                error = None
            else:
                sql = f"-- [DEMO] SQL seria gerado pelo LLM para: {question}"
                data = []
                error = None

    # ─── Results ──────────────────────────────────────────────
    st.divider()

    # Show generated SQL (collapsible)
    with st.expander("SQL Gerado", expanded=False):
        st.code(sql, language="sql")
        if LIVE_MODE:
            is_safe, reason = sanitize_sql(sql)
            if is_safe:
                st.caption("Validacao: SQL seguro (apenas SELECT)")
            else:
                st.warning(f"Validacao: {reason}")

    # Show results
    if error:
        st.error(f"Erro: {error}")
    elif data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        # Source attribution
        if "fonte_url" in df.columns:
            st.caption("**Fontes:**")
            for url in df["fonte_url"].unique():
                st.caption(f"  - {url}")
        if "extraido_em" in df.columns:
            st.caption(f"Dados extraidos em: {df['extraido_em'].iloc[0]}")

        st.metric("Resultados encontrados", len(data))
    else:
        st.warning("Nenhum resultado encontrado para essa consulta.")

    # Disclaimer
    st.divider()
    st.caption(
        "Os dados sao extraidos de fontes publicas (.com.br dos fabricantes). "
        "Sempre verifique com a fonte original antes de usar em decisoes comerciais."
    )
