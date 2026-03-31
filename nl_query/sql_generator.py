"""
Natural Language Query → SQL Generator.

Architecture decision from /plan-eng-review Issue 2A:
- LLM generates SQL from natural language questions
- Schema injected dynamically via information_schema (TODO 3)
- SQL sanitized before execution (no DDL/DML allowed)
- Response always includes source URL and verification date

Security:
- Only SELECT statements allowed
- DDL (CREATE, DROP, ALTER) blocked
- DML (INSERT, UPDATE, DELETE) blocked
- SQL injection via NL query → blocked by sanitizer
"""

import os
import re
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import text

from db.connection import engine

load_dotenv()


# Dangerous SQL patterns that must never execute
BLOCKED_PATTERNS = [
    r"\b(DROP|CREATE|ALTER|TRUNCATE|INSERT|UPDATE|DELETE|GRANT|REVOKE)\b",
    r";\s*\w",  # multiple statements
    r"--",  # SQL comments (potential injection)
    r"/\*",  # block comments
]


@dataclass
class QueryResult:
    """Result of a natural language query."""

    question: str
    sql_generated: str
    data: list[dict]
    answer_text: str
    error: Optional[str] = None


def get_schema_description() -> str:
    """
    Read current database schema dynamically + sample data.
    Injects both structure AND real data examples so the LLM
    understands how marca/modelo/versao/campo are stored.
    """
    schema_query = text("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)

    with engine.connect() as conn:
        result = conn.execute(schema_query)
        rows = result.fetchall()

    if not rows:
        return _fallback_schema()

    schema_lines = []
    current_table = None
    for table, column, dtype in rows:
        if table != current_table:
            schema_lines.append(f"\nTable: {table}")
            current_table = table
        schema_lines.append(f"  - {column} ({dtype})")

    # Add sample data so LLM understands the data model
    try:
        with engine.connect() as conn:
            # Sample vehicle_spec entries
            sample_specs = conn.execute(text("""
                SELECT DISTINCT marca, modelo, versao FROM vehicle_spec
                WHERE mercado = 'BR' ORDER BY marca, modelo LIMIT 10
            """)).fetchall()

            sample_campos = conn.execute(text("""
                SELECT DISTINCT campo FROM vehicle_spec ORDER BY campo LIMIT 15
            """)).fetchall()

            schema_lines.append("\n\nSAMPLE DATA (vehicle_spec):")
            schema_lines.append("marca/modelo/versao combinations:")
            for row in sample_specs:
                schema_lines.append(f"  - marca='{row[0]}', modelo='{row[1]}', versao='{row[2]}'")
            schema_lines.append("IMPORTANT: 'modelo' and 'versao' are SEPARATE columns.")
            schema_lines.append("Example: 'Ranger Raptor' = modelo='Ranger' AND versao='Raptor'")
            schema_lines.append("Example: 'Hilux SRX' = modelo='Hilux' AND versao='SRX'")

            schema_lines.append("\ncampo values (each is a row, not a column):")
            for row in sample_campos:
                schema_lines.append(f"  - '{row[0]}'")
            schema_lines.append("IMPORTANT: specs are stored as rows (EAV model).")
            schema_lines.append("Each spec is a separate row with campo='potencia', valor='400', unidade='cv'.")
    except Exception:
        pass

    return "\n".join(schema_lines)


def _fallback_schema() -> str:
    """Hardcoded schema for when DB is not available."""
    return """
Table: vehicle_spec
  - id (integer, PK)
  - marca (varchar) -- brand name: "Toyota", "Ford", "Mitsubishi"
  - modelo (varchar) -- model name: "Hilux", "Ranger", "L200 Triton"
  - versao (varchar) -- version: "Raptor", "Limited", "XLS"
  - mercado (varchar) -- always 'BR' for Brazil
  - campo (varchar) -- spec field: "potencia", "torque", "suspensao"
  - valor (text) -- spec value, NULL means not available
  - unidade (varchar) -- unit: "cv", "kgfm", "mm"
  - fonte_url (text) -- source URL
  - extraido_em (timestamp) -- extraction date
  - verificado (boolean) -- false if data > 14 days old

Table: retention_vehicles
  - id (integer, PK)
  - vehicle_id (varchar) -- anonymized VIN
  - cliente_id (varchar)
  - modelo (varchar) -- e.g. "Ranger"
  - versao (varchar)
  - churn_score (integer) -- 0-100
  - lgpd_consent (boolean)
"""


def build_system_prompt(schema: str) -> str:
    """Build the system prompt for SQL generation."""
    return f"""You are a SQL query generator for a Brazilian automotive competitive intelligence database.

DATABASE SCHEMA:
{schema}

CRITICAL — EAV MODEL:
The table vehicle_spec uses an Entity-Attribute-Value (EAV) model.
There are NO columns named potencia, torque, motor, etc.
The columns are: marca, modelo, versao, mercado, campo, valor, unidade, fonte_url, extraido_em.
Each spec is stored as a ROW where campo='potencia' and valor='397'.
To get potencia, you filter WHERE campo = 'potencia' and read the valor column.
NEVER write vs.potencia or vs.torque — those columns DO NOT EXIST.

RULES:
1. Generate ONLY SELECT statements.
2. Always filter by mercado = 'BR'.
3. The only data columns are: marca, modelo, versao, mercado, campo, valor, unidade, fonte_url, extraido_em, verificado.
4. To get a specific spec, use WHERE campo = 'potencia' (or torque, motor, etc.) and SELECT valor.
5. ALWAYS return simple rows. NEVER pivot, crosstab, or create dynamic columns.
6. Always include fonte_url and extraido_em for traceability.
7. Respond ONLY with the SQL query. No explanation. No markdown. No code fences.
8. Use ORDER BY marca, modelo, versao for consistent results.

EXAMPLE — "Qual a potencia da Ranger Raptor?":
SELECT marca, modelo, versao, valor AS potencia, unidade, fonte_url, extraido_em
FROM vehicle_spec
WHERE mercado = 'BR' AND campo = 'potencia'
  AND marca = 'Ford' AND modelo = 'Ranger' AND versao = 'Raptor';

EXAMPLE — "Compare torque do Ranger com Hilux":
SELECT marca, modelo, versao, valor AS torque, unidade, fonte_url, extraido_em
FROM vehicle_spec
WHERE mercado = 'BR' AND campo = 'torque'
  AND ((marca = 'Ford' AND modelo = 'Ranger') OR (marca = 'Toyota' AND modelo = 'Hilux'))
ORDER BY marca, modelo;

EXAMPLE — "Mostre todas as specs do Ranger Raptor":
SELECT marca, modelo, versao, campo, valor, unidade, fonte_url, extraido_em
FROM vehicle_spec
WHERE mercado = 'BR' AND marca = 'Ford' AND modelo = 'Ranger' AND versao = 'Raptor'
ORDER BY campo;

EXAMPLE — "Qual pickup tem maior capacidade de carga?":
SELECT marca, modelo, versao, valor AS capacidade_carga, unidade, fonte_url, extraido_em
FROM vehicle_spec
WHERE mercado = 'BR' AND campo = 'capacidade_carga'
ORDER BY CAST(REPLACE(valor, '.', '') AS INTEGER) DESC;"""


def sanitize_sql(sql: str) -> tuple[bool, str]:
    """
    Validate generated SQL is safe to execute.
    Returns (is_safe, reason).
    """
    sql_upper = sql.upper().strip()

    # Must start with SELECT or WITH (CTE)
    if not sql_upper.startswith(("SELECT", "WITH")):
        return False, f"Query must start with SELECT or WITH, got: {sql_upper[:20]}"

    # Check for blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, sql_upper, re.IGNORECASE):
            return False, f"Blocked pattern detected: {pattern}"

    return True, "OK"


def generate_sql(question: str) -> str:
    """Use LLM to generate SQL from a natural language question."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        return f"-- ERROR: OpenAI client not configured. Set OPENAI_API_KEY in .env"

    schema = get_schema_description()
    system_prompt = build_system_prompt(schema)

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0,
        max_completion_tokens=500,
    )

    sql = response.choices[0].message.content.strip()

    # Remove markdown code fences if present
    sql = re.sub(r"^```\w*\n?", "", sql)
    sql = re.sub(r"\n?```$", "", sql)

    return sql.strip()


def execute_query(question: str) -> QueryResult:
    """
    Full pipeline: question → SQL → execute → format result.
    """
    # Step 1: Generate SQL
    sql = generate_sql(question)

    # Step 2: Sanitize
    is_safe, reason = sanitize_sql(sql)
    if not is_safe:
        return QueryResult(
            question=question,
            sql_generated=sql,
            data=[],
            answer_text=f"Query bloqueada por seguranca: {reason}",
            error=reason,
        )

    # Step 3: Execute
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
    except Exception as e:
        return QueryResult(
            question=question,
            sql_generated=sql,
            data=[],
            answer_text=f"Erro ao executar query: {str(e)}",
            error=str(e),
        )

    # Step 4: Format answer
    if not rows:
        answer = "Nenhum resultado encontrado para essa consulta."
    else:
        answer = f"Encontrados {len(rows)} resultados."

    return QueryResult(
        question=question,
        sql_generated=sql,
        data=rows,
        answer_text=answer,
    )
