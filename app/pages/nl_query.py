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
    "Compare todas as versoes do Ranger (preco, potencia e torque)",
    "Qual o preco de todas as pickups?",
    "Compare Ranger Limited vs Hilux SRX vs Amarok Highline",
    "Qual pickup tem maior capacidade de carga?",
    "Mostre todas as specs do Ranger Raptor",
]

DEMO_RESULTS = {
    "Qual a potencia da Ranger Raptor?": {
        "sql": """SELECT marca, modelo, versao, valor AS potencia, unidade, fonte_url, extraido_em
FROM vehicle_spec
WHERE marca = 'Ford' AND modelo = 'Ranger' AND versao = 'Raptor'
  AND campo = 'potencia' AND mercado = 'BR'""",
        "data": [
            {
                "marca": "Ford", "modelo": "Ranger", "versao": "Raptor",
                "potencia": "397", "unidade": "cv",
                "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947",
                "extraido_em": "2026-03-30",
            }
        ],
    },
    "Compare o torque da Hilux SRX com a Ranger Limited": {
        "sql": """SELECT marca, modelo, versao, valor AS torque, unidade, fonte_url, extraido_em
FROM vehicle_spec
WHERE campo = 'torque' AND mercado = 'BR'
AND ((marca = 'Toyota' AND modelo = 'Hilux' AND versao = 'SRX')
  OR (marca = 'Ford' AND modelo = 'Ranger' AND versao = 'Limited'))
ORDER BY marca""",
        "data": [
            {
                "marca": "Ford", "modelo": "Ranger", "versao": "Limited",
                "torque": "61,2", "unidade": "kgfm",
                "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35882",
                "extraido_em": "2026-03-30",
            },
            {
                "marca": "Toyota", "modelo": "Hilux", "versao": "SRX",
                "torque": "50.9", "unidade": "kgfm",
                "fonte_url": "https://www.toyota.com.br/modelos/hilux-cabine-dupla",
                "extraido_em": "2026-03-30",
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

        col_res, col_date = st.columns([1, 2])
        with col_res:
            st.metric("Resultados encontrados", len(data))
        with col_date:
            if "extraido_em" in df.columns:
                datas = df["extraido_em"].dropna().unique()
                if len(datas) > 0:
                    st.metric("Dados capturados em", str(datas[0])[:10])

        # Source attribution
        if "fonte_url" in df.columns:
            fontes = df["fonte_url"].dropna().unique()
            if len(fontes):
                st.caption("**Fontes verificaveis:**")
                for url in fontes:
                    if url:
                        st.caption(f"  🔗 [{url}]({url})")

    else:
        st.warning("Nenhum resultado encontrado para essa consulta.")

    # Disclaimer
    st.divider()
    st.caption(
        "Dados extraidos ao vivo de sites publicos brasileiros. "
        "Ford: carrosnaweb.com.br (ford.com.br bloqueia scraping automatizado via WAF). "
        "VW, Toyota, Mitsubishi: sites oficiais .com.br."
    )
