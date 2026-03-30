"""
Generate synthetic datasets for Ford Intelligence OS demo.

Creates:
1. vehicle_specs.csv — competitive spec data for Module 1
2. retention_vehicles.csv — vehicle/customer data for Module 2

This is the FALLBACK dataset (outside voice recommendation from eng review).
Use this for development and demo rehearsal. Replace with real Ford data
when Renato delivers the masked dataset.
"""

import csv
import os
import random
from datetime import date, timedelta

OUTPUT_DIR = os.path.dirname(__file__)

# ─────────────────────────────────────────────────────────────
# MODULE 1: Competitive Spec Data (Brazilian market)
# ─────────────────────────────────────────────────────────────

# Real-ish specs for Brazilian pickup market (publicly available data)
VEHICLES = {
    ("Ford", "Ranger", "Raptor"): {
        "potencia": ("400", "cv"),
        "torque": ("59.2", "kgfm"),
        "motor": ("V6 3.0 Biturbo", None),
        "transmissao": ("Automatica 10 velocidades", None),
        "tracao": ("4x4", None),
        "suspensao": ("Fox 2.5 Live Valve", None),
        "capacidade_carga": ("620", "kg"),
        "entre_eixos": ("3270", "mm"),
        "comprimento": ("5381", "mm"),
        "tanque": ("80", "litros"),
        "preco_sugerido": ("449990", "BRL"),
    },
    ("Ford", "Ranger", "Limited"): {
        "potencia": ("210", "cv"),
        "torque": ("51", "kgfm"),
        "motor": ("2.0 Turbo Diesel", None),
        "transmissao": ("Automatica 6 velocidades", None),
        "tracao": ("4x4", None),
        "suspensao": ("Independente dianteira / Rigida traseira", None),
        "capacidade_carga": ("785", "kg"),
        "entre_eixos": ("3270", "mm"),
        "comprimento": ("5381", "mm"),
        "tanque": ("80", "litros"),
        "preco_sugerido": ("289990", "BRL"),
    },
    ("Toyota", "Hilux", "SRX"): {
        "potencia": ("204", "cv"),
        "torque": ("50.9", "kgfm"),
        "motor": ("2.8 Turbo Diesel", None),
        "transmissao": ("Automatica 6 velocidades", None),
        "tracao": ("4x4", None),
        "suspensao": ("Independente dianteira / Rigida traseira com molas", None),
        "capacidade_carga": ("720", "kg"),
        "entre_eixos": ("3085", "mm"),
        "comprimento": ("5325", "mm"),
        "tanque": ("80", "litros"),
        "preco_sugerido": ("299990", "BRL"),
    },
    ("Toyota", "Hilux", "GR-Sport"): {
        "potencia": ("224", "cv"),
        "torque": ("55.1", "kgfm"),
        "motor": ("2.8 Turbo Diesel", None),
        "transmissao": ("Automatica 6 velocidades", None),
        "tracao": ("4x4", None),
        "suspensao": ("Monotube com reservatorio remoto", None),
        "capacidade_carga": ("680", "kg"),
        "entre_eixos": ("3085", "mm"),
        "comprimento": ("5325", "mm"),
        "tanque": ("80", "litros"),
        "preco_sugerido": ("369990", "BRL"),
    },
    ("Mitsubishi", "L200 Triton", "Savana"): {
        "potencia": ("190", "cv"),
        "torque": ("43.9", "kgfm"),
        "motor": ("2.4 Turbo Diesel", None),
        "transmissao": ("Automatica 6 velocidades", None),
        "tracao": ("4x4", None),
        "suspensao": ("Independente dianteira / Rigida traseira", None),
        "capacidade_carga": ("715", "kg"),
        "entre_eixos": ("3000", "mm"),
        "comprimento": ("5305", "mm"),
        "tanque": ("75", "litros"),
        "preco_sugerido": ("279990", "BRL"),
    },
    ("Volkswagen", "Amarok", "Highline V6"): {
        "potencia": ("258", "cv"),
        "torque": ("59.1", "kgfm"),
        "motor": ("V6 3.0 Turbo Diesel", None),
        "transmissao": ("Automatica 10 velocidades", None),
        "tracao": ("4x4 permanente", None),
        "suspensao": ("Independente nas 4 rodas", None),
        "capacidade_carga": ("710", "kg"),
        "entre_eixos": ("3270", "mm"),
        "comprimento": ("5350", "mm"),
        "tanque": ("80", "litros"),
        "preco_sugerido": ("339990", "BRL"),
    },
}


def generate_specs_csv():
    """Generate vehicle_specs.csv for Module 1."""
    filepath = os.path.join(OUTPUT_DIR, "vehicle_specs.csv")
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "marca", "modelo", "versao", "mercado", "campo",
                "valor", "unidade", "fonte_url", "extraido_em",
            ],
        )
        writer.writeheader()

        for (marca, modelo, versao), specs in VEHICLES.items():
            for campo, (valor, unidade) in specs.items():
                writer.writerow({
                    "marca": marca,
                    "modelo": modelo,
                    "versao": versao,
                    "mercado": "BR",
                    "campo": campo,
                    "valor": valor,
                    "unidade": unidade or "",
                    "fonte_url": f"https://www.{marca.lower()}.com.br/{modelo.lower()}/",
                    "extraido_em": date.today().isoformat(),
                })

    print(f"Generated {filepath} ({sum(len(s) for s in VEHICLES.values())} specs)")


# ─────────────────────────────────────────────────────────────
# MODULE 2: Retention Vehicle Data (100 synthetic vehicles)
# ─────────────────────────────────────────────────────────────

FORD_MODELS = [
    ("Ranger", "Raptor"),
    ("Ranger", "Limited"),
    ("Ranger", "XLS"),
    ("Ranger", "XL"),
    ("Territory", "Titanium"),
    ("Territory", "SEL"),
    ("Bronco Sport", "Wildtrak"),
    ("Maverick", "Lariat"),
]

CONCESSIONARIAS = ["SP001", "SP002", "SP003", "RJ001", "MG001"]
SERVICO_TIPOS = ["pago", "garantia", "recall"]


def _random_date(start_year: int, end_year: int) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_retention_csv():
    """Generate retention_vehicles.csv for Module 2."""
    filepath = os.path.join(OUTPUT_DIR, "retention_vehicles.csv")
    vehicles = []

    for i in range(100):
        modelo, versao = random.choice(FORD_MODELS)
        ano_fab = random.randint(2016, 2025)
        data_venda = _random_date(ano_fab, min(ano_fab + 1, 2025))

        # Simulate service history
        had_paid_visit = random.random() > 0.35  # 65% had at least one paid visit
        if had_paid_visit:
            ultima_visita_paga = _random_date(2023, 2026)
            qtd_pagas = random.randint(1, 8)
        else:
            ultima_visita_paga = None
            qtd_pagas = 0

        tipo_ultimo = random.choice(SERVICO_TIPOS)
        km = random.randint(5_000, 120_000)

        # Connected vehicle: newer cars more likely
        connected = ano_fab >= 2022 and random.random() > 0.3
        falha_ativa = connected and random.random() > 0.85

        # LGPD: 80% consented
        lgpd = random.random() > 0.2

        vehicles.append({
            "vehicle_id": f"VH-{i+1:04d}",
            "cliente_id": f"CL-{i+1:04d}",
            "modelo": modelo,
            "versao": versao,
            "ano_fabricacao": ano_fab,
            "data_venda": data_venda.isoformat(),
            "concessionaria_id": random.choice(CONCESSIONARIAS),
            "ultima_visita_paga": ultima_visita_paga.isoformat() if ultima_visita_paga else "",
            "ultima_visita_qualquer": _random_date(2024, 2026).isoformat(),
            "tipo_ultimo_servico": tipo_ultimo,
            "qtd_visitas_pagas_2_anos": qtd_pagas,
            "km_estimado": km,
            "connected_vehicle_available": str(connected).lower(),
            "sinal_falha_ativo": str(falha_ativa).lower(),
            "km_real_odometro": km + random.randint(-500, 500) if connected else "",
            "lgpd_consent": str(lgpd).lower(),
        })

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=vehicles[0].keys())
        writer.writeheader()
        writer.writerows(vehicles)

    print(f"Generated {filepath} (100 vehicles)")


if __name__ == "__main__":
    random.seed(42)  # reproducible for demo
    generate_specs_csv()
    generate_retention_csv()
    print("\nSynthetic data ready. Load into PostgreSQL with: python -m ingestion.load_data")
