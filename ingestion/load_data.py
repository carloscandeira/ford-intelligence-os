"""
Data ingestion pipeline for Ford Intelligence OS.

Loads CSV data into PostgreSQL for both Module 1 (specs) and Module 2 (retention).
Handles both synthetic fallback data and real Ford masked data.

Validation rules (from /plan-eng-review Issue 4A):
- Type check: numeric fields must be valid numbers after unit stripping
- Range check: reject obvious outliers (torque > 500 kgfm, etc.)
- NULL normalization: "—", "N/A", "", "-" → NULL
- Source attribution: fonte_url required for every spec row
"""

import csv
import os
from datetime import date, datetime
from typing import Optional

from sqlalchemy import text

from db.connection import get_db, init_db


# NULL values to normalize (Issue 4A)
NULL_VALUES = {"", "-", "—", "N/A", "n/a", "NA", "null", "None", "N/D", "nd"}

# Range checks for numeric spec fields
RANGE_CHECKS = {
    "potencia": (50, 1000),     # cv
    "torque": (10, 500),        # kgfm
    "comprimento": (3000, 7000),  # mm
    "entre_eixos": (2000, 5000),  # mm
    "tanque": (30, 200),        # litros
    "capacidade_carga": (200, 2000),  # kg
    "preco_sugerido": (50000, 2000000),  # BRL
}


def _normalize_null(value: str) -> Optional[str]:
    """Normalize NULL-like values to None."""
    if value is None or value.strip() in NULL_VALUES:
        return None
    return value.strip()


def _validate_numeric(campo: str, valor: str) -> tuple[bool, Optional[str]]:
    """
    Validate a spec value is within expected range.
    Returns (is_valid, cleaned_value or None).
    """
    if valor is None:
        return True, None

    # Strip units and special chars
    cleaned = valor.replace(",", ".").strip()
    # Try to extract numeric part
    numeric_part = ""
    for char in cleaned:
        if char.isdigit() or char == ".":
            numeric_part += char
        elif numeric_part:
            break

    if not numeric_part:
        return True, valor  # non-numeric field, pass through

    try:
        num = float(numeric_part)
    except ValueError:
        return True, valor  # not a number, pass through

    # Range check
    if campo in RANGE_CHECKS:
        lo, hi = RANGE_CHECKS[campo]
        if num < lo or num > hi:
            print(f"  WARNING: {campo}={valor} out of range [{lo}, {hi}] — setting to NULL")
            return False, None

    return True, valor


def load_specs_csv(filepath: str):
    """Load vehicle specs CSV into vehicle_spec table."""
    print(f"\nLoading specs from {filepath}...")
    loaded = 0
    skipped = 0

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with get_db() as db:
            for row in reader:
                valor = _normalize_null(row.get("valor", ""))
                campo = row.get("campo", "")

                # Validate numeric fields
                is_valid, cleaned_valor = _validate_numeric(campo, valor)
                if not is_valid:
                    skipped += 1
                    continue

                # Source URL is mandatory
                fonte_url = row.get("fonte_url", "")
                if not fonte_url:
                    print(f"  WARNING: missing fonte_url for {row.get('marca')}/{row.get('modelo')}/{campo} — skipping")
                    skipped += 1
                    continue

                db.execute(
                    text("""
                        INSERT INTO vehicle_spec (marca, modelo, versao, mercado, campo, valor, unidade, fonte_url, extraido_em)
                        VALUES (:marca, :modelo, :versao, :mercado, :campo, :valor, :unidade, :fonte_url, :extraido_em)
                        ON CONFLICT (marca, modelo, versao, mercado, campo)
                        DO UPDATE SET
                            valor = EXCLUDED.valor,
                            unidade = EXCLUDED.unidade,
                            fonte_url = EXCLUDED.fonte_url,
                            extraido_em = EXCLUDED.extraido_em,
                            verificado = TRUE,
                            updated_at = NOW()
                    """),
                    {
                        "marca": row["marca"],
                        "modelo": row["modelo"],
                        "versao": row["versao"],
                        "mercado": row.get("mercado", "BR"),
                        "campo": campo,
                        "valor": cleaned_valor,
                        "unidade": _normalize_null(row.get("unidade", "")),
                        "fonte_url": fonte_url,
                        "extraido_em": row.get("extraido_em", date.today().isoformat()),
                    },
                )
                loaded += 1

    print(f"  Loaded: {loaded} specs | Skipped: {skipped}")


def load_retention_csv(filepath: str):
    """Load retention vehicles CSV into retention_vehicles table."""
    print(f"\nLoading retention data from {filepath}...")
    loaded = 0

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with get_db() as db:
            for row in reader:
                db.execute(
                    text("""
                        INSERT INTO retention_vehicles (
                            vehicle_id, cliente_id, modelo, versao, ano_fabricacao,
                            data_venda, concessionaria_id, ultima_visita_paga,
                            ultima_visita_qualquer, tipo_ultimo_servico,
                            qtd_visitas_pagas_2_anos, km_estimado,
                            connected_vehicle_available, sinal_falha_ativo,
                            km_real_odometro, lgpd_consent
                        )
                        VALUES (
                            :vehicle_id, :cliente_id, :modelo, :versao, :ano_fabricacao,
                            :data_venda, :concessionaria_id, :ultima_visita_paga,
                            :ultima_visita_qualquer, :tipo_ultimo_servico,
                            :qtd_visitas_pagas_2_anos, :km_estimado,
                            :connected_vehicle_available, :sinal_falha_ativo,
                            :km_real_odometro, :lgpd_consent
                        )
                        ON CONFLICT (vehicle_id) DO UPDATE SET
                            churn_score = NULL,
                            score_calculado_em = NULL,
                            updated_at = NOW()
                    """),
                    {
                        "vehicle_id": row["vehicle_id"],
                        "cliente_id": row["cliente_id"],
                        "modelo": row["modelo"],
                        "versao": _normalize_null(row.get("versao")),
                        "ano_fabricacao": int(row["ano_fabricacao"]) if row.get("ano_fabricacao") else None,
                        "data_venda": row.get("data_venda") or None,
                        "concessionaria_id": row.get("concessionaria_id"),
                        "ultima_visita_paga": row.get("ultima_visita_paga") or None,
                        "ultima_visita_qualquer": row.get("ultima_visita_qualquer") or None,
                        "tipo_ultimo_servico": _normalize_null(row.get("tipo_ultimo_servico")),
                        "qtd_visitas_pagas_2_anos": int(row.get("qtd_visitas_pagas_2_anos", 0)),
                        "km_estimado": int(row["km_estimado"]) if row.get("km_estimado") else None,
                        "connected_vehicle_available": row.get("connected_vehicle_available", "false") == "true",
                        "sinal_falha_ativo": row.get("sinal_falha_ativo", "false") == "true",
                        "km_real_odometro": int(row["km_real_odometro"]) if row.get("km_real_odometro") else None,
                        "lgpd_consent": row.get("lgpd_consent", "false") == "true",
                    },
                )
                loaded += 1

    print(f"  Loaded: {loaded} vehicles")


if __name__ == "__main__":
    print("Ford Intelligence OS — Data Ingestion")
    print("=" * 50)

    # Initialize DB schema
    init_db()

    # Load synthetic data
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic")
    specs_file = os.path.join(data_dir, "vehicle_specs.csv")
    retention_file = os.path.join(data_dir, "retention_vehicles.csv")

    if os.path.exists(specs_file):
        load_specs_csv(specs_file)
    else:
        print(f"  Specs file not found: {specs_file}")
        print("  Run: python -m data.synthetic.generate_synthetic")

    if os.path.exists(retention_file):
        load_retention_csv(retention_file)
    else:
        print(f"  Retention file not found: {retention_file}")

    print("\nDone!")
