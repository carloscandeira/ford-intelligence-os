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
# Ford Professional CSS
# ─────────────────────────────────────────────────────────────

FORD_CSS = """
<style>
/* ── Reset & Base ──────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --ford-blue: #003478;
    --ford-blue-mid: #1B4F9E;
    --ford-blue-dark: #001A3A;
    --ford-accent: #00A3E0;
    --ford-accent-soft: rgba(0, 163, 224, 0.12);
    --ford-surface: #FAFBFD;
    --ford-card: #FFFFFF;
    --ford-border: #E8ECF1;
    --ford-text: #1A1A2E;
    --ford-text-secondary: #5A6275;
    --ford-success: #0EA47A;
    --ford-warning: #E5960A;
    --ford-danger: #DC3545;
    --radius: 12px;
    --shadow-sm: 0 1px 3px rgba(0,20,60,0.06), 0 1px 2px rgba(0,20,60,0.04);
    --shadow-md: 0 4px 12px rgba(0,20,60,0.08), 0 2px 4px rgba(0,20,60,0.04);
    --shadow-lg: 0 8px 24px rgba(0,20,60,0.10), 0 4px 8px rgba(0,20,60,0.04);
}

/* ── Sidebar ───────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--ford-blue-dark) !important;
    border-right: none !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: rgba(255,255,255,0.65) !important;
    font-size: 0.82rem;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 0.8rem 0 !important;
}
[data-testid="stSidebar"] .stRadio label {
    padding: 0.45rem 0.75rem !important;
    border-radius: 8px !important;
    transition: all 0.15s ease !important;
    margin-bottom: 2px !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] .stRadio label span {
    color: rgba(255,255,255,0.85) !important;
    font-weight: 400 !important;
    font-size: 0.88rem !important;
}
[data-testid="stSidebar"] .stRadio [data-checked="true"] label {
    background: rgba(0, 163, 224, 0.15) !important;
    border-left: 3px solid var(--ford-accent) !important;
}
[data-testid="stSidebar"] .stRadio [data-checked="true"] label span {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* ── Page Header ───────────────────────────────────────── */
.ford-header {
    background: var(--ford-blue);
    padding: 1.25rem 1.75rem;
    border-radius: var(--radius);
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-md);
    position: relative;
    overflow: hidden;
}
.ford-header::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 200px; height: 100%;
    background: linear-gradient(135deg, transparent 0%, rgba(0,163,224,0.15) 100%);
    border-radius: 0 var(--radius) var(--radius) 0;
}
.ford-header h1 {
    color: white !important;
    margin: 0 !important;
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px;
    position: relative;
    z-index: 1;
}
.ford-header .ford-subtitle {
    color: rgba(255,255,255,0.55);
    font-size: 0.82rem;
    font-weight: 400;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    position: relative;
    z-index: 1;
}
.ford-header .ford-module-tag {
    display: inline-block;
    background: rgba(0,163,224,0.2);
    color: var(--ford-accent);
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 4px;
    position: relative;
    z-index: 1;
}

/* ── Metrics ───────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--ford-card);
    border: 1px solid var(--ford-border);
    border-radius: var(--radius);
    padding: 16px 20px;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
    box-shadow: var(--shadow-md);
}
[data-testid="stMetric"] label {
    color: var(--ford-text-secondary) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-weight: 700 !important;
    color: var(--ford-text) !important;
}

/* ── Buttons ───────────────────────────────────────────── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    border: 1px solid var(--ford-border) !important;
}
.stButton > button[kind="primary"] {
    background: var(--ford-blue) !important;
    border-color: var(--ford-blue) !important;
    color: white !important;
    box-shadow: 0 2px 4px rgba(0,52,120,0.25) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--ford-blue-mid) !important;
    border-color: var(--ford-blue-mid) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 8px rgba(0,52,120,0.3) !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--ford-accent) !important;
    color: var(--ford-accent) !important;
}

/* ── Data Tables ───────────────────────────────────────── */
.stDataFrame {
    border-radius: var(--radius) !important;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--ford-border) !important;
}

/* ── Expanders ─────────────────────────────────────────── */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    color: var(--ford-text) !important;
    border-radius: 8px !important;
}

/* ── Dividers ──────────────────────────────────────────── */
hr {
    border-color: var(--ford-border) !important;
    margin: 1.2rem 0 !important;
}

/* ── Custom Components ─────────────────────────────────── */
.ford-card {
    background: var(--ford-card);
    border: 1px solid var(--ford-border);
    border-radius: var(--radius);
    padding: 1.25rem;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.ford-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}

.ford-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.ford-badge-live {
    background: rgba(14, 164, 122, 0.1);
    color: #0EA47A;
    border: 1px solid rgba(14, 164, 122, 0.2);
}
.ford-badge-demo {
    background: rgba(0, 163, 224, 0.1);
    color: #00A3E0;
    border: 1px solid rgba(0, 163, 224, 0.2);
}
.ford-badge-warn {
    background: rgba(229, 150, 10, 0.1);
    color: #E5960A;
    border: 1px solid rgba(229, 150, 10, 0.2);
}

.ford-step-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px; height: 28px;
    border-radius: 50%;
    background: var(--ford-blue);
    color: white;
    font-size: 0.82rem;
    font-weight: 700;
    margin-right: 8px;
    flex-shrink: 0;
}

.ford-step-header {
    display: flex;
    align-items: center;
    margin-bottom: 0.75rem;
}
.ford-step-header h3 {
    margin: 0 !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: var(--ford-text) !important;
}

.ford-whatsapp {
    background: #E7FFDB;
    padding: 14px 18px;
    border-radius: 0 12px 12px 12px;
    max-width: 420px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: #111;
    font-size: 0.88rem;
    line-height: 1.55;
    box-shadow: 0 1px 2px rgba(0,0,0,0.08);
    position: relative;
    margin: 0.5rem 0;
}
.ford-whatsapp::before {
    content: '';
    position: absolute;
    left: -8px; top: 0;
    border-width: 0 8px 10px 0;
    border-style: solid;
    border-color: transparent #E7FFDB transparent transparent;
}

.ford-source-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 500;
    background: rgba(0, 52, 120, 0.06);
    color: var(--ford-text-secondary);
    border: 1px solid rgba(0, 52, 120, 0.08);
    text-decoration: none;
}

/* ── Status Alerts ─────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}

/* ── Subheader ─────────────────────────────────────────── */
.ford-section-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--ford-text);
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--ford-blue);
    display: inline-block;
    margin-bottom: 1rem;
}

/* ── Footer ────────────────────────────────────────────── */
.ford-footer {
    padding: 0.75rem 0;
    margin-top: 1rem;
    border-top: 1px solid var(--ford-border);
    color: var(--ford-text-secondary);
    font-size: 0.75rem;
}

/* ── Plotly chart backgrounds ──────────────────────────── */
.js-plotly-plot .plotly .main-svg {
    background: transparent !important;
}
</style>
"""

st.markdown(FORD_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Data freshness helper
# ─────────────────────────────────────────────────────────────

def _get_data_freshness():
    """Check when data was last updated. Returns (label, badge_class)."""
    try:
        from sqlalchemy import text as sql_text
        from db.connection import engine
        if not os.getenv("DATABASE_URL"):
            return "Modo demo", "ford-badge-demo"
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
                    return "Atualizado hoje", "ford-badge-live"
                elif days_ago == 1:
                    return "Atualizado ontem", "ford-badge-live"
                elif days_ago <= 7:
                    return f"Ha {days_ago} dias", "ford-badge-warn"
                else:
                    return f"Ha {days_ago} dias", "ford-badge-warn"
        return "Sem dados", "ford-badge-warn"
    except Exception:
        return "Modo demo", "ford-badge-demo"


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────

NAV_ITEMS = {
    "Consulta Inteligente": "search",
    "Ficha Tecnica Comparativa": "compare_arrows",
    "Retencao & Churn": "trending_down",
    "A Ponte (Demo)": "link",
}

with st.sidebar:
    # Brand mark
    st.markdown(
        '<div style="text-align:center; padding: 1.2rem 0 0.4rem 0;">'
        '<div style="font-size: 1.8rem; font-weight: 800; color: white; '
        'letter-spacing: 3px; line-height: 1;">FORD</div>'
        '<div style="font-size: 0.7rem; color: rgba(255,255,255,0.45); '
        'letter-spacing: 3px; text-transform: uppercase; margin-top: 4px;">Intelligence OS</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Freshness badge
    freshness_label, freshness_class = _get_data_freshness()
    st.markdown(
        f'<div style="text-align: center; margin: 0.6rem 0 0.3rem 0;">'
        f'<span class="ford-badge {freshness_class}">{freshness_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    page = st.radio(
        "Navegacao",
        list(NAV_ITEMS.keys()),
        index=0,
        label_visibility="collapsed",
    )

    st.divider()

    # Data sources — compact
    st.markdown(
        '<div style="font-size: 0.72rem; color: rgba(255,255,255,0.4); '
        'text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; '
        'font-weight: 600;">Fontes de dados</div>',
        unsafe_allow_html=True,
    )

    sources = [
        ("VW", "vw.com.br", True),
        ("Toyota", "toyota.com.br", True),
        ("Mitsubishi", "oficial", True),
        ("Ford", "carrosnaweb*", False),
    ]
    for brand, source, ok in sources:
        icon = "check_circle" if ok else "warning"
        color = "rgba(14,164,122,0.8)" if ok else "rgba(229,150,10,0.8)"
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:6px; '
            f'padding:2px 0; font-size:0.78rem; color:rgba(255,255,255,0.6);">'
            f'<span style="color:{color}; font-size:0.65rem;">{"✓" if ok else "!"}</span>'
            f'<span style="font-weight:500; color:rgba(255,255,255,0.8); width:70px;">{brand}</span>'
            f'<span>{source}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="font-size:0.65rem; color:rgba(255,255,255,0.3); margin-top:6px;">'
        '*ford.com.br bloqueia scraping (WAF)</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown(
        '<div style="text-align: center; padding: 0.3rem 0;">'
        '<div style="font-size: 0.68rem; color: rgba(255,255,255,0.3);">'
        'Desafio Ford x Universidade 2026</div>'
        '<div style="font-size: 0.62rem; color: rgba(255,255,255,0.2); margin-top:2px;">'
        'Mercado brasileiro</div>'
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
