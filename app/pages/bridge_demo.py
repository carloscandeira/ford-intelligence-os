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
try:
    from bridge.template_generator import (
        TemplateInput,
        TemplateOutput,
        get_bridge_data,
        generate_and_review,
        _fallback_template,
        review_template,
    )
    BRIDGE_AVAILABLE = True
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
        "review_notes": "OK — todos os numeros verificados contra input",
    },
    "VH-0034": {
        "text": (
            "Ola! Seu Ranger Raptor com motor V6 3.0 Biturbo de 400 cv e suspensao Fox 2.5 Live Valve "
            "precisa de cuidados especializados que so a rede Ford oferece. Com 28.000 km, "
            "esta na hora de uma revisao com tecnicos que entendem a performance unica do Raptor. "
            "Agende aqui: [link]"
        ),
        "review_passed": True,
        "review_notes": "OK — todos os numeros verificados contra input",
    },
    "VH-0056": {
        "text": (
            "Ola! Seu Territory Titanium com 61.000 km esta proximo de uma revisao importante. "
            "A manutencao na rede Ford garante pecas originais e tecnicos especializados "
            "no seu veiculo. Aproveite nossas condicoes especiais. "
            "Agende aqui: [link]"
        ),
        "review_passed": True,
        "review_notes": "OK — template generico (sem diferencial competitivo)",
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
        "review_notes": "OK — todos os numeros verificados contra input",
    },
}


def render():
    """Render the A Ponte (Bridge Demo) tab."""
    st.header("A Ponte")
    st.markdown(
        "**O momento de demonstracao.** Aqui os dois modulos se conectam: "
        "a inteligencia competitiva do Modulo 1 alimenta as mensagens de retencao do Modulo 2."
    )

    # Architecture explanation
    with st.expander("Como funciona a Ponte?", expanded=False):
        st.markdown("""
        ```
        Modulo 1 (Specs)          Modulo 2 (Retencao)
        vehicle_spec     ──JOIN──  retention_vehicles
             │                          │
             ▼                          ▼
        Diferenciais             Veiculos alto risco
        competitivos             (score > threshold)
             │                          │
             └──────────┬───────────────┘
                        ▼
                  Template LLM
                  (com guardrails)
                        │
                        ▼
                  Reviewer Pass
                  (valida numeros)
                        │
                        ▼
                  Aprovacao Humana
                        │
                        ▼
                  WhatsApp (simulado)
        ```

        **Bridge JOIN:** conecta `vehicle_spec.modelo = retention_vehicles.modelo`
        para encontrar diferenciais competitivos que so o Ford tem vs concorrentes.

        **Guardrail:** o reviewer pass compara TODOS os numeros no template gerado
        contra os numeros no input. Se aparecer um numero que nao estava no input,
        o template e flaggado para revisao humana.
        """)

    st.divider()

    # ─── Step 1: Select High-Risk Vehicles ────────────────────
    st.subheader("1. Veiculos de Alto Risco")

    threshold = st.slider("Threshold de risco", 50, 100, 85)

    # Load data
    bridge_data = DEMO_BRIDGE_DATA  # default to demo
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
                st.success(f"Dados ao vivo — {len(bridge_data)} veiculos acima do threshold", icon="🟢")
        except Exception:
            pass

    if not using_live:
        # Filter demo data by threshold
        bridge_data = [d for d in DEMO_BRIDGE_DATA if d["churn_score"] >= threshold]
        st.info("Modo demonstracao — dados sinteticos", icon="🔵")

    if not bridge_data:
        st.warning(f"Nenhum veiculo com score >= {threshold}. Reduza o threshold.")
        return

    # Display vehicle cards
    df_vehicles = pd.DataFrame([
        {
            "Vehicle ID": d["vehicle_id"],
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
    st.subheader("2. Gerar Template WhatsApp")

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
    with st.expander("Campos de entrada para o LLM", expanded=True):
        st.json({
            "modelo": selected["modelo"],
            "versao": selected.get("versao", "N/D"),
            "km_estimado": selected.get("km_estimado"),
            "ultimo_servico": selected.get("ultimo_servico"),
            "diferencial_competitivo": selected.get("diferencial") or "nenhum disponivel",
        })

    generate_btn = st.button("Gerar Template", type="primary", use_container_width=True)

    if generate_btn or st.session_state.get(f"generated_{selected_vid}"):
        st.session_state[f"generated_{selected_vid}"] = True

        with st.spinner("Gerando template com guardrails..."):
            if using_live and BRIDGE_AVAILABLE:
                # Use real LLM generation
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
                # Demo mode
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
                    review_notes = "OK — template generico"

        # ─── Step 3: Template Output + Review ─────────────────
        st.divider()
        st.subheader("3. Template Gerado")

        # WhatsApp-style preview
        st.markdown(
            f"""
            <div style="background-color: #DCF8C6; padding: 16px; border-radius: 12px;
                        max-width: 400px; font-family: sans-serif; color: #000;
                        font-size: 14px; line-height: 1.5;">
                {template_text}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Review status
        st.divider()
        st.subheader("4. Reviewer Pass (Guardrail)")

        if review_passed:
            st.success(f"Reviewer: {review_notes}", icon="✅")
        else:
            st.error(f"Reviewer: {review_notes}", icon="🚨")
            st.warning(
                "Template com numeros nao verificados. "
                "Necessita revisao humana antes de enviar."
            )

        # ─── Step 4: Human Approval ──────────────────────────
        st.divider()
        st.subheader("5. Aprovacao Humana")

        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            if st.button("Aprovar e Enviar (simulado)", type="primary"):
                st.balloons()
                st.success(
                    f"Template aprovado para {selected['vehicle_id']}. "
                    f"Em producao, seria enviado via API WhatsApp Business."
                )

        with col_a2:
            if st.button("Editar Template"):
                st.session_state[f"editing_{selected_vid}"] = True

        with col_a3:
            if st.button("Rejeitar"):
                st.warning("Template rejeitado. Sera regenerado com parametros ajustados.")

        # Edit mode
        if st.session_state.get(f"editing_{selected_vid}"):
            edited = st.text_area("Editar template:", value=template_text, height=200)
            if st.button("Salvar edicao"):
                st.session_state[f"editing_{selected_vid}"] = False
                st.success("Template editado salvo.")

    # ─── Footer ───────────────────────────────────────────────
    st.divider()
    st.caption(
        "A Ponte conecta inteligencia competitiva (Modulo 1) com retencao (Modulo 2). "
        "Guardrails: system prompt restritivo + reviewer pass que compara numeros input vs output. "
        "Envio real via WhatsApp Business API fora do escopo do MVP."
    )
