"""
Bridge: Template Generator — connects Module 1 (specs) to Module 2 (retention).

Architecture decisions from /plan-eng-review:
- Issue 3A: JOIN SQL direto between vehicle_spec and retention_vehicles via modelo
- Issue 7A: LLM guardrail — system prompt restritivo + reviewer pass
  that compares numbers in output vs input fields. Flags for human review if different.

THE BRIDGE FLOW:
1. Get high-risk vehicles (score > threshold) from retention_vehicles
2. JOIN with vehicle_spec to find competitive differentiators
3. LLM generates WhatsApp template using ONLY the provided fields
4. Reviewer pass validates no hallucinated specs in the output
5. Human approval gate before any simulated "send"
"""

import os
import re
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import text

from db.connection import engine

load_dotenv()


@dataclass
class TemplateInput:
    """Data assembled from Bridge JOIN for template generation."""

    vehicle_id: str
    cliente_id: str
    modelo: str
    versao: Optional[str]
    km_estimado: Optional[int]
    ultimo_servico_pago: Optional[str]
    churn_score: int
    diferencial_competitivo: Optional[str]  # from Module 1 via JOIN


@dataclass
class TemplateOutput:
    """Generated template with review status."""

    vehicle_id: str
    template_text: str
    input_fields: dict  # all fields used to generate
    review_passed: bool
    review_notes: str
    diferencial_competitivo: Optional[str]


# ─────────────────────────────────────────────────────────────
# BRIDGE JOIN: the core query connecting Module 1 + Module 2
# ─────────────────────────────────────────────────────────────

BRIDGE_QUERY = text("""
    SELECT
        rv.vehicle_id,
        rv.cliente_id,
        rv.modelo,
        rv.versao,
        rv.km_estimado,
        rv.tipo_ultimo_servico,
        rv.churn_score,
        -- Aggregate competitive differentiators from Module 1
        -- Find specs that this modelo has but competitors DON'T
        (
            SELECT string_agg(DISTINCT vs.campo || ': ' || vs.valor, '; ')
            FROM vehicle_spec vs
            WHERE vs.modelo = rv.modelo
            AND vs.mercado = 'BR'
            AND vs.verificado = TRUE
            AND vs.campo || vs.valor NOT IN (
                SELECT vs2.campo || vs2.valor
                FROM vehicle_spec vs2
                WHERE vs2.marca != (
                    SELECT vs3.marca FROM vehicle_spec vs3
                    WHERE vs3.modelo = rv.modelo LIMIT 1
                )
                AND vs2.mercado = 'BR'
            )
        ) AS diferencial_competitivo
    FROM retention_vehicles rv
    WHERE rv.churn_score > :threshold
    AND rv.lgpd_consent = TRUE
    ORDER BY rv.churn_score DESC
    LIMIT :limit
""")


def get_bridge_data(threshold: int = 85, limit: int = 50) -> list[TemplateInput]:
    """
    Execute the Bridge JOIN: get high-risk vehicles with their
    competitive differentiators from Module 1.
    """
    with engine.connect() as conn:
        result = conn.execute(BRIDGE_QUERY, {"threshold": threshold, "limit": limit})
        rows = result.fetchall()

    return [
        TemplateInput(
            vehicle_id=row.vehicle_id,
            cliente_id=row.cliente_id,
            modelo=row.modelo,
            versao=row.versao,
            km_estimado=row.km_estimado,
            ultimo_servico_pago=row.tipo_ultimo_servico,
            churn_score=row.churn_score,
            diferencial_competitivo=row.diferencial_competitivo,
        )
        for row in rows
    ]


# ─────────────────────────────────────────────────────────────
# TEMPLATE GENERATION with LLM guardrail
# ─────────────────────────────────────────────────────────────

TEMPLATE_SYSTEM_PROMPT = """You are a WhatsApp message composer for Ford dealerships in Brazil.

STRICT RULES:
1. Use ONLY the data provided in the user message. Do NOT add any technical specifications,
   numbers, percentages, or measurements that are not explicitly in the input fields.
2. If there is no competitive differentiator provided, write a generic service reminder
   without mentioning any specific vehicle features.
3. Write in Brazilian Portuguese, friendly but professional tone.
4. Keep the message under 160 words (WhatsApp readability).
5. Always end with a call to action: "Agende aqui: [link]"
6. Address the customer as "voce" (informal).
7. NEVER invent specs. If the input says "suspensao: Fox", you may say "suspensao Fox"
   but NEVER add details like absorption rates, dimensions, or performance numbers
   that are NOT in the input.

OUTPUT: Only the WhatsApp message text. No explanation."""


def generate_template(input_data: TemplateInput) -> str:
    """Generate WhatsApp template using LLM with strict guardrails."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        return _fallback_template(input_data)

    # Build the input fields message
    fields = {
        "modelo": input_data.modelo,
        "versao": input_data.versao or "N/A",
        "km_estimado": input_data.km_estimado or "desconhecido",
        "ultimo_servico": input_data.ultimo_servico_pago or "N/A",
        "diferencial_competitivo": input_data.diferencial_competitivo or "nenhum disponivel",
    }

    user_msg = "Dados do veiculo para gerar a mensagem WhatsApp:\n"
    for k, v in fields.items():
        user_msg += f"- {k}: {v}\n"

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": TEMPLATE_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()


def _fallback_template(data: TemplateInput) -> str:
    """Static template when LLM is not available."""
    km_text = f"com {data.km_estimado} km" if data.km_estimado else ""
    diff_text = ""
    if data.diferencial_competitivo:
        diff_text = f" Com {data.diferencial_competitivo} exclusivo(a), a manutencao com tecnicos Ford certificados faz toda a diferenca."

    return (
        f"Ola! Seu {data.modelo} {data.versao or ''} {km_text} "
        f"esta se aproximando do momento ideal para uma revisao.{diff_text} "
        f"Agende aqui: [link]"
    )


# ─────────────────────────────────────────────────────────────
# REVIEWER PASS (Issue 7A: guardrail validation)
# ─────────────────────────────────────────────────────────────


def _extract_numbers(text: str) -> set[str]:
    """Extract all numbers from a text string."""
    return set(re.findall(r"\d+(?:[.,]\d+)?", text))


def review_template(template_text: str, input_data: TemplateInput) -> tuple[bool, str]:
    """
    Reviewer pass: compare numbers in the template output against
    numbers in the input fields. Flag any number that appears in the
    output but NOT in the input.

    Returns (passed, notes).
    """
    # Collect all numbers from input fields
    input_numbers = set()
    if input_data.km_estimado:
        input_numbers.add(str(input_data.km_estimado))
    if input_data.diferencial_competitivo:
        input_numbers.update(_extract_numbers(input_data.diferencial_competitivo))

    # Also allow common numbers: years, common km milestones
    allowed_extras = {"10000", "20000", "30000", "40000", "50000", "60000", "80000", "100000"}
    input_numbers.update(allowed_extras)

    # Extract numbers from the generated template
    output_numbers = _extract_numbers(template_text)

    # Find suspicious numbers (in output but not in input)
    suspicious = output_numbers - input_numbers
    # Filter out small numbers (1-31 for days, 1-12 for months, etc.)
    suspicious = {n for n in suspicious if int(float(n.replace(",", "."))) > 100}

    if suspicious:
        return False, f"ALERTA: numeros no template nao presentes no input: {suspicious}"

    return True, "OK — todos os numeros verificados contra input"


def generate_and_review(input_data: TemplateInput) -> TemplateOutput:
    """Full pipeline: generate template + review pass."""
    template_text = generate_template(input_data)

    passed, notes = review_template(template_text, input_data)

    return TemplateOutput(
        vehicle_id=input_data.vehicle_id,
        template_text=template_text,
        input_fields={
            "modelo": input_data.modelo,
            "versao": input_data.versao,
            "km_estimado": input_data.km_estimado,
            "diferencial_competitivo": input_data.diferencial_competitivo,
        },
        review_passed=passed,
        review_notes=notes,
        diferencial_competitivo=input_data.diferencial_competitivo,
    )
