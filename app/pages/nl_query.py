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
    "Compare todas as versoes do Ranger",
    "Qual o preco de todas as pickups?",
    "Ranger vs Hilux vs Amarok",
    "Maior capacidade de carga?",
    "Specs do Ranger Raptor",
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
    # Header
    st.markdown(
        '<div class="ford-header">'
        '<span class="ford-module-tag">Modulo 1</span>'
        '<h1>Consulta Inteligente</h1>'
        '<span class="ford-subtitle">Pergunte em portugues, receba dados com rastreabilidade</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Status
    if LIVE_MODE:
        st.markdown(
            '<span class="ford-badge ford-badge-live">Banco conectado — consultas ao vivo</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="ford-badge ford-badge-demo">Modo demonstracao</span>',
            unsafe_allow_html=True,
        )

    st.write("")  # spacer

    # ─── Input ────────────────────────────────────────────────
    question = st.text_input(
        "Sua pergunta sobre veiculos:",
        placeholder="Ex: Qual a potencia da Ranger Raptor?",
        label_visibility="collapsed",
    )

    # Example pills
    cols = st.columns(len(EXAMPLE_QUESTIONS))
    for i, ex in enumerate(EXAMPLE_QUESTIONS):
        with cols[i]:
            if st.button(ex, key=f"ex_{i}", use_container_width=True):
                question = ex

    if not question:
        st.markdown(
            '<div style="text-align:center; padding:2rem; color: var(--ford-text-secondary);">'
            'Digite uma pergunta acima ou clique em um exemplo para comecar.'
            '</div>',
            unsafe_allow_html=True,
        )
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
                st.markdown(
                    '<span class="ford-badge ford-badge-live">SQL seguro (apenas SELECT)</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.warning(f"Validacao: {reason}")

    # Show results
    if error:
        st.error(f"Erro: {error}")
    elif data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Metrics row
        col_res, col_date, col_space = st.columns([1, 1, 2])
        with col_res:
            st.metric("Resultados", len(data))
        with col_date:
            if "extraido_em" in df.columns:
                datas = df["extraido_em"].dropna().unique()
                if len(datas) > 0:
                    st.metric("Capturado em", str(datas[0])[:10])

        # Source attribution
        if "fonte_url" in df.columns:
            fontes = df["fonte_url"].dropna().unique()
            if len(fontes):
                st.write("")
                st.markdown(
                    '<span class="ford-section-title">Fontes verificaveis</span>',
                    unsafe_allow_html=True,
                )
                for url in fontes:
                    if url:
                        st.markdown(
                            f'<a href="{url}" target="_blank" class="ford-source-tag">'
                            f'🔗 {url}</a>',
                            unsafe_allow_html=True,
                        )
    else:
        st.warning("Nenhum resultado encontrado para essa consulta.")

    # Footer
    st.markdown(
        '<div class="ford-footer">'
        'Dados extraidos ao vivo de sites publicos brasileiros. '
        'Ford: carrosnaweb.com.br | VW, Toyota, Mitsubishi: sites oficiais .com.br'
        '</div>',
        unsafe_allow_html=True,
    )
