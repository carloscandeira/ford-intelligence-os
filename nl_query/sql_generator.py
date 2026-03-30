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
    Read current database schema dynamically.
    TODO 3 from /plan-eng-review: inject schema dynamically via information_schema
    so the LLM always sees the real structure, even after changes.
    """
    query = text("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        rows = result.fetchall()

    if not rows:
        # Fallback to hardcoded schema if DB not initialized
        return _fallback_schema()

    schema_lines = []
    current_table = None
    for table, column, dtype in rows:
        if table != current_table:
            schema_lines.append(f"\nTable: {table}")
            current_table = table
        schema_lines.append(f"  - {column} ({dtype})")

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

RULES:
1. Generate ONLY SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP, CREATE, or ALTER.
2. Always filter by mercado = 'BR' when querying vehicle_spec.
3. When comparing brands, use the 'campo' column to match equivalent fields.
4. Return well-formatted SQL with proper aliases.
5. If the question is unclear, generate a query that returns the most relevant data.
6. For comparison questions ("what does X have that Y doesn't"), use set difference (EXCEPT or LEFT JOIN WHERE NULL).
7. Always include fonte_url and extraido_em in the output for traceability.
8. Respond ONLY with the SQL query. No explanation. No markdown. No code fences.
9. Use Portuguese column aliases matching the campo values in the database."""


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
        max_tokens=500,
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
