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

import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.pages import specs_comparison, nl_query, retention, bridge_demo

# ─────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Ford Intelligence OS",
    page_icon="🚙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Ford Intelligence OS")
    st.caption("Inteligencia competitiva + Retencao de clientes")
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
    )

    st.divider()
    st.caption("Desafio Ford x Universidade 2026")
    st.caption("Dados: mercado brasileiro")

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
