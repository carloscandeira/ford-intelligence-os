"""
Ford Intelligence OS — Streamlit Dashboard

This is the main entry point for the demo application.
Runs on Railway/Render, accessible via public URL.

Tabs:
1. Consulta Inteligente (NL Query) — Module 1
2. Ficha Tecnica Comparativa — Module 1
3. Retencao & Churn — Module 2
4. A Ponte — Bridge demo moment

Run: streamlit run app/main.py
"""

import os
import sys
from datetime import datetime

import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.pages import specs_comparison, nl_query, retention, bridge_demo

# ─────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Ford Intelligence OS",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# Ford Brand CSS
# ─────────────────────────────────────────────────────────────

FORD_CSS = """
<style>
/* Ford Brand Colors */
:root {
    --ford-blue: #003478;
    --ford-blue-light: #1B4F9E;
    --ford-blue-dark: #00234D;
    --ford-accent: #00A3E0;
    --ford-silver: #C4C4C4;
    --ford-success: #00B74A;
    --ford-warning: #FFA900;
    --ford-danger: #F93154;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #001F4D 0%, #003478 50%, #001F4D 100%);
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stSidebar"] .stCaption p {
    color: #E0E8F0 !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] .stRadio label span {
    color: #E0E8F0 !important;
}

/* Header accent bar */
.ford-header {
    background: linear-gradient(90deg, #003478 0%, #00A3E0 100%);
    padding: 0.5rem 1.5rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.ford-header h1 {
    color: white !important;
    margin: 0 !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px;
}
.ford-header .ford-subtitle {
    color: #B0D4F1;
    font-size: 0.85rem;
}

/* Primary buttons Ford blue */
.stButton > button[kind="primary"] {
    background-color: #003478 !important;
    border-color: #003478 !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #1B4F9E !important;
    border-color: #1B4F9E !important;
}

/* Metric cards styling */
[data-testid="stMetric"] {
    background: rgba(0, 52, 120, 0.08);
    border: 1px solid rgba(0, 52, 120, 0.15);
    border-radius: 10px;
    padding: 12px 16px;
}
[data-testid="stMetric"] label {
    color: #666 !important;
}

/* Dataframe header Ford blue */
.stDataFrame [data-testid="glideDataEditor"] th {
    background-color: #003478 !important;
    color: white !important;
}

/* Tab styling */
.stTabs [data-baseweb="tab"] {
    border-radius: 4px 4px 0 0;
}
.stTabs [aria-selected="true"] {
    background-color: rgba(0, 52, 120, 0.1);
}

/* Dividers */
hr {
    border-color: rgba(0, 52, 120, 0.15) !important;
}

/* Status badges */
.ford-status-live {
    display: inline-block;
    background: #00B74A;
    color: white;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}
.ford-status-demo {
    display: inline-block;
    background: #00A3E0;
    color: white;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Freshness indicator */
.ford-freshness {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 163, 224, 0.1);
    border: 1px solid rgba(0, 163, 224, 0.3);
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 0.8rem;
    color: #00A3E0;
}
</style>
"""

st.markdown(FORD_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Data freshness helper
# ─────────────────────────────────────────────────────────────

def _get_data_freshness() -> str:
    """Check when data was last updated."""
    try:
        from sqlalchemy import text as sql_text
        from db.connection import engine
        if not os.getenv("DATABASE_URL"):
            return "Demo"
        with engine.connect() as conn:
            row = conn.execute(sql_text(
                "SELECT MAX(extraido_em) FROM vehicle_spec WHERE mercado = 'BR'"
            )).fetchone()
            if row and row[0]:
                last_date = row[0]
                if hasattr(last_date, 'date'):
                    last_date = last_date.date()
                days_ago = (datetime.now().date() - last_date).days
                if days_ago == 0:
                    return "Atualizado hoje"
                elif days_ago == 1:
                    return "Atualizado ontem"
                else:
                    return f"Atualizado ha {days_ago} dias"
        return "Sem dados"
    except Exception:
        return "Demo"


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        '<div style="text-align: center; padding: 0.5rem 0 0.2rem 0;">'
        '<span style="font-size: 2.2rem; font-weight: 800; color: white; letter-spacing: 2px;">FORD</span><br>'
        '<span style="font-size: 1rem; color: #B0D4F1; font-weight: 300;">Intelligence OS</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption("")  # spacer

    # Data freshness badge
    freshness = _get_data_freshness()
    freshness_icon = "🟢" if "hoje" in freshness or "ontem" in freshness else "🔵" if "Demo" in freshness else "🟡"
    st.markdown(
        f'<div style="text-align: center; margin-bottom: 0.5rem;">'
        f'<span class="ford-freshness">{freshness_icon} {freshness}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    page = st.radio(
        "Modulo",
        [
            "Consulta Inteligente",
            "Ficha Tecnica Comparativa",
            "Retencao & Churn",
            "A Ponte (Demo)",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.divider()

    # ─── Fontes dos dados ────────────────────────────────
    st.markdown("**Fontes de dados**")
    st.markdown("""
| Marca | Status |
|---|---|
| VW | ✅ vw.com.br |
| Toyota | ✅ toyota.com.br |
| Mitsubishi | ✅ oficial |
| Ford | ⚠️ carrosnaweb* |
""")
    st.caption("*ford.com.br bloqueia scraping (WAF/Cloudflare)")

    st.divider()
    st.markdown(
        '<div style="text-align: center; font-size: 0.72rem; color: #8899AA;">'
        'Desafio Ford x Universidade 2026<br>'
        'Mercado brasileiro'
        '</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────
# Page routing
# ─────────────────────────────────────────────────────────────

if page == "Consulta Inteligente":
    nl_query.render()
elif page == "Ficha Tecnica Comparativa":
    specs_comparison.render()
elif page == "Retencao & Churn":
    retention.render()
elif page == "A Ponte (Demo)":
    bridge_demo.render()
