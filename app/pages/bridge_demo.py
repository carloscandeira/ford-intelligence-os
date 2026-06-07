"""
A Ponte (Bridge Demo) — connecting competitive intelligence to retention action.

Tab 4 of Ford Intelligence OS dashboard.
THE DEMO MOMENT: shows how Module 1 (specs) feeds Module 2 (retention messaging).

Flow:
1. Select high-risk vehicles (from churn scorer)
2. Show competitive differentiators (from spec intelligence)
3. Generate personalized WhatsApp template
4. Reviewer pass validates no hallucinated specs
5. Human approval gate
"""

import streamlit as st
import pandas as pd
from datetime import date

# Try to import real modules
import os
try:
    from bridge.template_generator import (
        TemplateInput,
        TemplateOutput,
        get_bridge_data,
        generate_and_review,
        _fallback_template,
        review_template,
    )
    BRIDGE_AVAILABLE = bool(os.getenv("DATABASE_URL")) and bool(os.getenv("OPENAI_API_KEY"))
except Exception:
    BRIDGE_AVAILABLE = False

from scoring.churn_scorer import VehicleData, calculate_churn_score


# ─────────────────────────────────────────────────────────────
# Demo data for the bridge demo
# ─────────────────────────────────────────────────────────────

DEMO_BRIDGE_DATA = [
    {
        "vehicle_id": "VH-0012",
        "cliente_id": "CL-0012",
        "modelo": "Ranger",
        "versao": "Limited",
        "km_estimado": 42000,
        "ultimo_servico": "garantia",
        "churn_score": 90,
        "diferencial": "torque: 51 kgfm; capacidade_carga: 785 kg; entre_eixos: 3270 mm",
    },
    {
        "vehicle_id": "VH-0034",
        "cliente_id": "CL-0034",
        "modelo": "Ranger",
        "versao": "Raptor",
        "km_estimado": 28000,
        "ultimo_servico": "recall",
        "churn_score": 87,
        "diferencial": "potencia: 400 cv; motor: V6 3.0 Biturbo; suspensao: Fox 2.5 Live Valve",
    },
    {
        "vehicle_id": "VH-0056",
        "cliente_id": "CL-0056",
        "modelo": "Territory",
        "versao": "Titanium",
        "km_estimado": 61000,
        "ultimo_servico": "garantia",
        "churn_score": 75,
        "diferencial": None,
    },
    {
        "vehicle_id": "VH-0078",
        "cliente_id": "CL-0078",
        "modelo": "Ranger",
        "versao": "XLS",
        "km_estimado": 79000,
        "ultimo_servico": "pago",
        "churn_score": 72,
        "diferencial": "capacidade_carga: 785 kg",
    },
]

DEMO_TEMPLATES = {
    "VH-0012": {
        "text": (
            "Ola! Seu Ranger Limited com 42.000 km esta se aproximando de uma revisao importante. "
            "Com 51 kgfm de torque e 785 kg de capacidade de carga, seu Ranger merece o cuidado "
            "de tecnicos Ford certificados que conhecem cada detalhe do veiculo. "
            "Que tal agendar uma revisao completa? Temos condicoes especiais este mes. "
            "Agende aqui: [link]"
        ),
        "review_passed": True,
        "review_notes": "Todos os numeros verificados contra input",
    },
    "VH-0034": {
        "text": (
            "Ola! Seu Ranger Raptor com motor V6 3.0 Biturbo de 400 cv e suspensao Fox 2.5 Live Valve "
            "precisa de cuidados especializados que so a rede Ford oferece. Com 28.000 km, "
            "esta na hora de uma revisao com tecnicos que entendem a performance unica do Raptor. "
            "Agende aqui: [link]"
        ),
        "review_passed": True,
        "review_notes": "Todos os numeros verificados contra input",
    },
    "VH-0056": {
        "text": (
            "Ola! Seu Territory Titanium com 61.000 km esta proximo de uma revisao importante. "
            "A manutencao na rede Ford garante pecas originais e tecnicos especializados "
            "no seu veiculo. Aproveite nossas condicoes especiais. "
            "Agende aqui: [link]"
        ),
        "review_passed": True,
        "review_notes": "Template generico (sem diferencial competitivo)",
    },
    "VH-0078": {
        "text": (
            "Ola! Seu Ranger XLS com 79.000 km merece atencao especial. "
            "Com 785 kg de capacidade de carga, manter a revisao em dia garante "
            "o desempenho completo do seu veiculo. Tecnicos Ford certificados "
            "cuidam de cada detalhe. "
            "Agende aqui: [link]"
        ),
        "review_passed": True,
        "review_notes": "Todos os numeros verificados contra input",
    },
}


def _step(num, title):
    """Render a numbered step header."""
    st.markdown(
        f'<div class="ford-step-header">'
        f'<span class="ford-step-badge">{num}</span>'
        f'<h3>{title}</h3>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render():
    """Render the A Ponte (Bridge Demo) tab."""
    # Header
    st.markdown(
        '<div class="ford-header" style="background: linear-gradient(135deg, #001A3A 0%, #003478 100%);">'
        '<span class="ford-module-tag">Modulo 1 + 2</span>'
        '<h1>A Ponte</h1>'
        '<span class="ford-subtitle">Inteligencia competitiva alimenta retencao ativa</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Visual pipeline
    st.markdown(
        '<div style="display:flex; align-items:center; justify-content:center; gap:0; '
        'padding:0.75rem 0; flex-wrap:wrap;">'
        '<div style="background:#003478; color:white; padding:8px 16px; border-radius:8px 0 0 8px; '
        'font-size:0.78rem; font-weight:600;">Specs Competitivas</div>'
        '<div style="background:#1B4F9E; color:white; padding:8px 4px; font-size:1rem;">→</div>'
        '<div style="background:#1B4F9E; color:white; padding:8px 16px; '
        'font-size:0.78rem; font-weight:600;">Veiculos Alto Risco</div>'
        '<div style="background:#00A3E0; color:white; padding:8px 4px; font-size:1rem;">→</div>'
        '<div style="background:#00A3E0; color:white; padding:8px 16px; '
        'font-size:0.78rem; font-weight:600;">Template LLM</div>'
        '<div style="background:#0EA47A; color:white; padding:8px 4px; font-size:1rem;">→</div>'
        '<div style="background:#0EA47A; color:white; padding:8px 16px; '
        'font-size:0.78rem; font-weight:600;">Reviewer</div>'
        '<div style="background:#0EA47A; color:white; padding:8px 4px; font-size:1rem;">→</div>'
        '<div style="background:#0EA47A; color:white; padding:8px 16px; border-radius:0 8px 8px 0; '
        'font-size:0.78rem; font-weight:600;">WhatsApp</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Architecture (collapsible)
    with st.expander("Como funciona a Ponte?"):
        col_arch1, col_arch2 = st.columns(2)
        with col_arch1:
            st.markdown(
                "**Bridge JOIN:** conecta `vehicle_spec.modelo = retention_vehicles.modelo` "
                "para encontrar diferenciais competitivos exclusivos do Ford vs concorrentes."
            )
        with col_arch2:
            st.markdown(
                "**Guardrail:** o reviewer compara TODOS os numeros no template gerado "
                "contra os dados de entrada. Numero inventado = template flaggado."
            )

    st.divider()

    # ─── Step 1: Select High-Risk Vehicles ────────────────────
    _step(1, "Veiculos de Alto Risco")

    threshold = st.slider("Threshold de risco", 50, 100, 85)

    # Load data
    bridge_data = DEMO_BRIDGE_DATA
    using_live = False

    if BRIDGE_AVAILABLE:
        try:
            live_data = get_bridge_data(threshold=threshold, limit=20)
            if live_data:
                bridge_data = [
                    {
                        "vehicle_id": d.vehicle_id,
                        "cliente_id": d.cliente_id,
                        "modelo": d.modelo,
                        "versao": d.versao,
                        "km_estimado": d.km_estimado,
                        "ultimo_servico": d.ultimo_servico_pago,
                        "churn_score": d.churn_score,
                        "diferencial": d.diferencial_competitivo,
                    }
                    for d in live_data
                ]
                using_live = True
                st.markdown(
                    f'<span class="ford-badge ford-badge-live">{len(bridge_data)} veiculos acima do threshold</span>',
                    unsafe_allow_html=True,
                )
        except Exception:
            pass

    if not using_live:
        bridge_data = [d for d in DEMO_BRIDGE_DATA if d["churn_score"] >= threshold]
        st.markdown('<span class="ford-badge ford-badge-demo">Dados sinteticos</span>', unsafe_allow_html=True)

    if not bridge_data:
        st.warning(f"Nenhum veiculo com score >= {threshold}. Reduza o threshold.")
        return

    st.write("")

    # Display vehicle cards
    df_vehicles = pd.DataFrame([
        {
            "ID": d["vehicle_id"],
            "Modelo": f"{d['modelo']} {d.get('versao', '')}",
            "KM": f"{d['km_estimado']:,}" if d.get("km_estimado") else "N/D",
            "Score": d["churn_score"],
            "Ult. Servico": d.get("ultimo_servico", "N/D"),
            "Diferencial Ford": d.get("diferencial") or "—",
        }
        for d in bridge_data
    ])
    st.dataframe(df_vehicles, use_container_width=True, hide_index=True)

    # ─── Step 2: Generate Template ────────────────────────────
    st.divider()
    _step(2, "Gerar Template WhatsApp")

    selected_vid = st.selectbox(
        "Selecione um veiculo:",
        [d["vehicle_id"] for d in bridge_data],
        format_func=lambda vid: next(
            f"{d['vehicle_id']} — {d['modelo']} {d.get('versao', '')} (Score: {d['churn_score']})"
            for d in bridge_data if d["vehicle_id"] == vid
        ),
    )

    selected = next(d for d in bridge_data if d["vehicle_id"] == selected_vid)

    # Show input fields
    with st.expander("Dados de entrada para o LLM", expanded=True):
        input_cols = st.columns(3)
        with input_cols[0]:
            st.markdown(f"**Modelo:** {selected['modelo']} {selected.get('versao', '')}")
            st.markdown(f"**KM:** {selected.get('km_estimado', 'N/D'):,}")
        with input_cols[1]:
            st.markdown(f"**Ult. servico:** {selected.get('ultimo_servico', 'N/D')}")
            st.markdown(f"**Churn score:** {selected['churn_score']}")
        with input_cols[2]:
            diff = selected.get('diferencial') or 'Nenhum disponivel'
            st.markdown(f"**Diferencial:** {diff}")

    generate_btn = st.button("Gerar Template", type="primary", use_container_width=True)

    if generate_btn or st.session_state.get(f"generated_{selected_vid}"):
        st.session_state[f"generated_{selected_vid}"] = True

        with st.spinner("Gerando template com guardrails..."):
            if using_live and BRIDGE_AVAILABLE:
                template_input = TemplateInput(
                    vehicle_id=selected["vehicle_id"],
                    cliente_id=selected["cliente_id"],
                    modelo=selected["modelo"],
                    versao=selected.get("versao"),
                    km_estimado=selected.get("km_estimado"),
                    ultimo_servico_pago=selected.get("ultimo_servico"),
                    churn_score=selected["churn_score"],
                    diferencial_competitivo=selected.get("diferencial"),
                )
                output = generate_and_review(template_input)
                template_text = output.template_text
                review_passed = output.review_passed
                review_notes = output.review_notes
            else:
                demo_t = DEMO_TEMPLATES.get(selected_vid)
                if demo_t:
                    template_text = demo_t["text"]
                    review_passed = demo_t["review_passed"]
                    review_notes = demo_t["review_notes"]
                else:
                    template_text = (
                        f"Ola! Seu {selected['modelo']} {selected.get('versao', '')} "
                        f"com {selected.get('km_estimado', 'N/D')} km esta proximo de uma revisao. "
                        f"Agende aqui: [link]"
                    )
                    review_passed = True
                    review_notes = "Template generico"

        # ─── Step 3: Template Output ──────────────────────────
        st.divider()
        _step(3, "Template Gerado")

        # WhatsApp-style preview
        import html as _html
        st.markdown(
            f'<div class="ford-whatsapp">{_html.escape(template_text).replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )

        # ─── Step 4: Review ───────────────────────────────────
        st.write("")
        _step(4, "Reviewer Pass (Guardrail)")

        if review_passed:
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:8px; '
                f'padding:10px 16px; background:rgba(14,164,122,0.08); '
                f'border:1px solid rgba(14,164,122,0.2); border-radius:8px; '
                f'color:#0EA47A; font-size:0.88rem;">'
                f'✅ <strong>Aprovado</strong> — {review_notes}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:8px; '
                f'padding:10px 16px; background:rgba(220,53,69,0.08); '
                f'border:1px solid rgba(220,53,69,0.2); border-radius:8px; '
                f'color:#DC3545; font-size:0.88rem;">'
                f'🚨 <strong>Flaggado</strong> — {review_notes}</div>',
                unsafe_allow_html=True,
            )
            st.warning("Template requer revisao humana antes de envio.")

        # ─── Step 5: Human Approval ──────────────────────────
        st.write("")
        _step(5, "Aprovacao Humana")

        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            if st.button("Aprovar e Enviar", type="primary", use_container_width=True):
                st.balloons()
                st.success(
                    f"Template aprovado para {selected['vehicle_id']}. "
                    f"Em producao: envio via API WhatsApp Business."
                )

        with col_a2:
            if st.button("Editar", use_container_width=True):
                st.session_state[f"editing_{selected_vid}"] = True

        with col_a3:
            if st.button("Rejeitar", use_container_width=True):
                st.warning("Template rejeitado. Sera regenerado.")

        # Edit mode
        if st.session_state.get(f"editing_{selected_vid}"):
            edited = st.text_area("Editar template:", value=template_text, height=150)
            if st.button("Salvar edicao"):
                st.session_state[f"editing_{selected_vid}"] = False
                st.success("Template editado salvo.")

    # Footer
    st.markdown(
        '<div class="ford-footer">'
        'A Ponte conecta inteligencia competitiva (Mod. 1) com retencao (Mod. 2). '
        'Guardrails: prompt restritivo + reviewer numerico + aprovacao humana.'
        '</div>',
        unsafe_allow_html=True,
    )
