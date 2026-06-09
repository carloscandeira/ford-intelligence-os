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
                "extraido_em": "2026-03-31",
            },
            {
                "marca": "Toyota", "modelo": "Hilux", "versao": "SRX",
                "torque": "42,8", "unidade": "kgfm",
                "fonte_url": "https://www.toyota.com.br/modelos/hilux-cabine-dupla",
                "extraido_em": "2026-06-03",
            },
        ],
    },
    # ── Botões de exemplo (EXAMPLE_QUESTIONS) — dados reais do banco ──
    "Compare todas as versoes do Ranger": {
        "sql": """SELECT versao, valor AS potencia, unidade, fonte_url, extraido_em
FROM vehicle_spec
WHERE marca = 'Ford' AND modelo = 'Ranger' AND campo = 'potencia' AND mercado = 'BR'
ORDER BY CAST(valor AS INTEGER)""",
        "data": [
            {"marca": "Ford", "modelo": "Ranger", "versao": "Black", "potencia (cv)": "170", "torque (kgfm)": "41,3", "preco (R$)": "219.990", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=37251", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "XLS", "potencia (cv)": "170", "torque (kgfm)": "41,3", "preco (R$)": "267.000", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35868", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "Limited", "potencia (cv)": "250", "torque (kgfm)": "61,2", "preco (R$)": "330.300", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35882", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor", "potencia (cv)": "397", "torque (kgfm)": "59,4", "preco (R$)": "490.000", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947", "extraido_em": "2026-03-31"},
        ],
    },
    "Qual o preco de todas as pickups?": {
        "sql": """SELECT marca, modelo, versao, valor AS preco, unidade, fonte_url, extraido_em
FROM vehicle_spec
WHERE campo = 'preco_fipe' AND mercado = 'BR'
ORDER BY CAST(valor AS INTEGER) DESC""",
        "data": [
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor 3.0 V6 Bi-Turbo 4WD", "preco (R$)": "495.991", "fonte": "Tabela FIPE", "fonte_url": "https://veiculos.fipe.org.br", "extraido_em": "2026-06-03"},
            {"marca": "Volkswagen", "modelo": "Amarok", "versao": "Highline CD 3.0 4x4 TB Diesel", "preco (R$)": "371.748", "fonte": "Tabela FIPE", "fonte_url": "https://veiculos.fipe.org.br", "extraido_em": "2026-06-03"},
            {"marca": "Toyota", "modelo": "Hilux", "versao": "CD SRX Plus 4x4 2.8 TDI", "preco (R$)": "348.475", "fonte": "Tabela FIPE", "fonte_url": "https://veiculos.fipe.org.br", "extraido_em": "2026-06-03"},
            {"marca": "Mitsubishi", "modelo": "Triton", "versao": "L200 Sport GLS 2.4 CD Diesel", "preco (R$)": "205.918", "fonte": "Tabela FIPE", "fonte_url": "https://veiculos.fipe.org.br", "extraido_em": "2026-06-03"},
        ],
    },
    "Ranger vs Hilux vs Amarok": {
        "sql": """SELECT marca, modelo, versao, campo, valor, unidade, fonte_url, extraido_em
FROM vehicle_spec
WHERE campo IN ('potencia', 'torque') AND mercado = 'BR'
AND ((marca='Ford' AND modelo='Ranger') OR (marca='Toyota' AND modelo='Hilux')
  OR (marca='Volkswagen' AND modelo='Amarok'))
ORDER BY marca""",
        "data": [
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor", "potencia (cv)": "397", "torque (kgfm)": "59,4", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947", "extraido_em": "2026-03-31"},
            {"marca": "Toyota", "modelo": "Hilux", "versao": "SRX", "potencia (cv)": "204", "torque (kgfm)": "42,8", "fonte_url": "https://www.toyota.com.br/modelos/hilux-cabine-dupla", "extraido_em": "2026-06-03"},
            {"marca": "Volkswagen", "modelo": "Amarok", "versao": "Highline V6", "potencia (cv)": "258", "torque (kgfm)": "59,1", "fonte_url": "https://www.vw.com.br/pt/carros/amarok.html", "extraido_em": "2026-06-03"},
        ],
    },
    "Maior capacidade de carga?": {
        "sql": """SELECT marca, modelo, versao, valor AS capacidade_carga, unidade, fonte_url, extraido_em
FROM vehicle_spec
WHERE campo = 'capacidade_carga' AND mercado = 'BR'
ORDER BY CAST(REPLACE(valor, '.', '') AS INTEGER) DESC""",
        "data": [
            {"marca": "Volkswagen", "modelo": "Amarok", "versao": "Highline V6", "capacidade_carga (kg)": "1.280", "fonte_url": "https://www.vw.com.br/pt/carros/amarok.html", "extraido_em": "2026-06-03"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "XLS", "capacidade_carga (kg)": "1.037", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35868", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "Limited", "capacidade_carga (kg)": "1.023", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35882", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor", "capacidade_carga (kg)": "736", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947", "extraido_em": "2026-03-31"},
            {"marca": "Toyota", "modelo": "Hilux", "versao": "STD Power Pack", "capacidade_carga (kg)": "720", "fonte_url": "https://www.toyota.com.br/modelos/hilux-cabine-dupla", "extraido_em": "2026-06-03"},
        ],
    },
    "Specs do Ranger Raptor": {
        "sql": """SELECT marca, modelo, versao, campo, valor, unidade, fonte_url, extraido_em
FROM vehicle_spec
WHERE marca = 'Ford' AND modelo = 'Ranger' AND versao = 'Raptor' AND mercado = 'BR'
ORDER BY campo""",
        "data": [
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor", "campo": "potencia", "valor": "397", "unidade": "cv", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor", "campo": "torque", "valor": "59,4", "unidade": "kgfm", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor", "campo": "motor", "valor": "V6 3.0 EcoBoost Gasolina Biturbo", "unidade": "", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor", "campo": "transmissao", "valor": "Automatica 10 velocidades", "unidade": "", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor", "campo": "tracao", "valor": "4x4 integral sob demanda", "unidade": "", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor", "campo": "capacidade_carga", "valor": "736", "unidade": "kg", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor", "campo": "tanque", "valor": "82", "unidade": "litros", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor", "campo": "entre_eixos", "valor": "3270", "unidade": "mm", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947", "extraido_em": "2026-03-31"},
            {"marca": "Ford", "modelo": "Ranger", "versao": "Raptor", "campo": "comprimento", "valor": "5360", "unidade": "mm", "fonte_url": "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947", "extraido_em": "2026-03-31"},
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
                error = (
                    "Modo demonstracao: respostas pre-carregadas apenas para as "
                    "perguntas de exemplo acima. Conecte o banco (DATABASE_URL) e a "
                    "OPENAI_API_KEY para consultar qualquer pergunta ao vivo."
                )

    # ─── Results ──────────────────────────────────────────────
    st.divider()

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
                    if url and str(url).startswith(("http://", "https://")):
                        import html as _html
                        safe_url = _html.escape(str(url))
                        st.markdown(
                            f'<a href="{safe_url}" target="_blank" class="ford-source-tag">'
                            f'🔗 {safe_url}</a>',
                            unsafe_allow_html=True,
                        )

        # Technical detail: generated SQL, hidden behind a discreet toggle so the
        # default view stays clean. Off by default.
        st.write("")
        if st.toggle("Ver SQL tecnico", value=False, key="show_sql"):
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
