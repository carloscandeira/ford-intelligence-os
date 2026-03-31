"""
Load REAL dealership prices for all pickups into PostgreSQL.
Sources: webmotors.com.br, icarros.com.br, mobiauto.com.br (concessionaria prices, NOT FIPE)
Last updated: 2026-03-31
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from datetime import date
from sqlalchemy import text
from db.connection import engine

# ── FIPE reference prices (tabela de referencia) ──────────────────────────
# Kept for comparison — these are the official FIPE table values
FIPE_PRICES = [
    # Ford Ranger 2025
    ("Ford", "Ranger", "XL", "207545", "https://napista.com.br/tabela-fipe/ford-ranger-2025"),
    ("Ford", "Ranger", "Black", "213966", "https://napista.com.br/tabela-fipe/ford-ranger-2025"),
    ("Ford", "Ranger", "XLS 2.0", "223328", "https://napista.com.br/tabela-fipe/ford-ranger-2025"),
    ("Ford", "Ranger", "XLT", "260865", "https://napista.com.br/tabela-fipe/ford-ranger-2025"),
    ("Ford", "Ranger", "Limited", "307203", "https://napista.com.br/tabela-fipe/ford-ranger-2025"),
    ("Ford", "Ranger", "Raptor", "458491", "https://napista.com.br/tabela-fipe/ford-ranger-2025"),
    # Toyota Hilux 2025
    ("Toyota", "Hilux", "STD Power Pack", "233672", "https://napista.com.br/tabela-fipe/toyota-hilux-2025"),
    ("Toyota", "Hilux", "SR", "261385", "https://napista.com.br/tabela-fipe/toyota-hilux-2025"),
    ("Toyota", "Hilux", "SRV", "277111", "https://napista.com.br/tabela-fipe/toyota-hilux-2025"),
    ("Toyota", "Hilux", "SRX", "305521", "https://napista.com.br/tabela-fipe/toyota-hilux-2025"),
    ("Toyota", "Hilux", "SRX Plus", "317650", "https://napista.com.br/tabela-fipe/toyota-hilux-2025"),
    # Volkswagen Amarok 2025
    ("Volkswagen", "Amarok", "Comfortline V6", "267893", "https://napista.com.br/tabela-fipe/volkswagen-amarok-2025"),
    ("Volkswagen", "Amarok", "Highline V6", "289682", "https://napista.com.br/tabela-fipe/volkswagen-amarok-2025"),
    ("Volkswagen", "Amarok", "Extreme V6", "305937", "https://napista.com.br/tabela-fipe/volkswagen-amarok-2025"),
    # Mitsubishi L200 Triton 2025
    ("Mitsubishi", "L200 Triton", "GLS", "207326", "https://napista.com.br/tabela-fipe/ford-ranger-2025"),
    ("Mitsubishi", "L200 Triton", "HPE", "252990", "https://napista.com.br/tabela-fipe/ford-ranger-2025"),
    ("Mitsubishi", "L200 Triton", "HPE-S", "308990", "https://napista.com.br/tabela-fipe/ford-ranger-2025"),
]

# ── REAL dealership prices (preco de concessionaria / venda) ──────────────
# These are actual 0km selling prices from aggregator sites, NOT FIPE
# Collected 2026-03-31 from webmotors.com.br, icarros.com.br, mobiauto.com.br
PRICES = [
    # Ford Ranger 2025 — source: webmotors.com.br/ford/ranger/2025
    ("Ford", "Ranger", "Black 2.0 4x2", "219990", "https://www.webmotors.com.br/ford/ranger/2025"),
    ("Ford", "Ranger", "XL 2.0 4x4", "247400", "https://www.webmotors.com.br/ford/ranger/2025"),
    ("Ford", "Ranger", "XLS 2.0 4x4", "267000", "https://www.webmotors.com.br/ford/ranger/2025"),
    ("Ford", "Ranger", "XLS V6 4x4", "292900", "https://www.webmotors.com.br/ford/ranger/2025"),
    ("Ford", "Ranger", "XLT V6 4x4", "298700", "https://www.webmotors.com.br/ford/ranger/2025"),
    ("Ford", "Ranger", "Limited V6 4x4", "330300", "https://www.webmotors.com.br/ford/ranger/2025"),
    ("Ford", "Ranger", "Raptor V6", "490000", "https://www.webmotors.com.br/ford/ranger/2025"),

    # Toyota Hilux 2025 — source: webmotors.com.br/toyota/hilux/2025
    ("Toyota", "Hilux", "Power Pack 4x4 MT", "278790", "https://www.webmotors.com.br/toyota/hilux/2025"),
    ("Toyota", "Hilux", "Power Pack 4x4 AT", "288990", "https://www.webmotors.com.br/toyota/hilux/2025"),
    ("Toyota", "Hilux", "SR 4x4 AT", "306090", "https://www.webmotors.com.br/toyota/hilux/2025"),
    ("Toyota", "Hilux", "SRV 4x4 AT", "309590", "https://www.webmotors.com.br/toyota/hilux/2025"),
    ("Toyota", "Hilux", "SRX 4x4 AT", "342390", "https://www.webmotors.com.br/toyota/hilux/2025"),
    ("Toyota", "Hilux", "SRX Plus 4x4 AT", "353290", "https://www.webmotors.com.br/toyota/hilux/2025"),

    # Volkswagen Amarok 2025 — source: mobiauto.com.br/catalogo/carros/volkswagen/amarok/2025
    ("Volkswagen", "Amarok", "Comfortline V6 4x4", "278176", "https://www.mobiauto.com.br/catalogo/carros/volkswagen/amarok/2025"),
    ("Volkswagen", "Amarok", "Highline V6 4x4", "302370", "https://www.mobiauto.com.br/catalogo/carros/volkswagen/amarok/2025"),
    ("Volkswagen", "Amarok", "Extreme V6 4x4", "335500", "https://www.mobiauto.com.br/catalogo/carros/volkswagen/amarok/2025"),

    # Mitsubishi Triton 2025 (nova geracao) — source: webmotors.com.br/mitsubishi/triton/2025
    ("Mitsubishi", "Triton", "GLS 4x4 AT", "265990", "https://www.webmotors.com.br/mitsubishi/triton/2025"),
    ("Mitsubishi", "Triton", "HPE 4x4 AT", "284990", "https://www.webmotors.com.br/mitsubishi/triton/2025"),
    ("Mitsubishi", "Triton", "HPE-S 4x4 AT", "314990", "https://www.webmotors.com.br/mitsubishi/triton/2025"),
    ("Mitsubishi", "Triton", "Katana 4x4 AT", "329990", "https://www.webmotors.com.br/mitsubishi/triton/2025"),

    # Mitsubishi L200 Triton Sport 2025 (geracao anterior, ainda em venda)
    # source: mobiauto.com.br/catalogo/carros/mitsubishi/l200-triton-sport/2025
    ("Mitsubishi", "L200 Triton", "GLS", "238990", "https://www.mobiauto.com.br/catalogo/carros/mitsubishi/l200-triton-sport/2025"),
    ("Mitsubishi", "L200 Triton", "Savana", "245990", "https://www.mobiauto.com.br/catalogo/carros/mitsubishi/l200-triton-savana/2025"),
    ("Mitsubishi", "L200 Triton", "HPE", "279990", "https://www.mobiauto.com.br/catalogo/carros/mitsubishi/l200-triton-sport/2025"),
    ("Mitsubishi", "L200 Triton", "HPE-S", "308990", "https://www.mobiauto.com.br/catalogo/carros/mitsubishi/l200-triton-sport/2025"),
]


def main():
    print("Ford Intelligence OS — Loading REAL Dealership Prices")
    print("Sources: webmotors.com.br, icarros.com.br, mobiauto.com.br")
    print("=" * 60)

    # Remove old price data
    with engine.connect() as conn:
        deleted = conn.execute(text("""
            DELETE FROM vehicle_spec WHERE campo = 'preco_sugerido' AND mercado = 'BR'
        """))
        print(f"Removed {deleted.rowcount} old price entries")

        loaded = 0
        for marca, modelo, versao, preco, fonte in PRICES:
            conn.execute(
                text("""
                    INSERT INTO vehicle_spec (marca, modelo, versao, mercado, campo, valor, unidade, fonte_url, extraido_em, verificado)
                    VALUES (:marca, :modelo, :versao, 'BR', 'preco_sugerido', :valor, 'BRL', :fonte_url, :extraido_em, TRUE)
                    ON CONFLICT (marca, modelo, versao, mercado, campo)
                    DO UPDATE SET valor = EXCLUDED.valor, unidade = EXCLUDED.unidade,
                        fonte_url = EXCLUDED.fonte_url, extraido_em = EXCLUDED.extraido_em,
                        verificado = TRUE, updated_at = NOW()
                """),
                {"marca": marca, "modelo": modelo, "versao": versao,
                 "valor": preco, "fonte_url": fonte, "extraido_em": date.today().isoformat()},
            )
            loaded += 1

        conn.commit()

    print(f"\n✅ Loaded {loaded} prices")
    print()

    # Show results
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT marca, modelo, versao, valor, fonte_url
            FROM vehicle_spec
            WHERE mercado = 'BR' AND campo = 'preco_sugerido'
            ORDER BY marca, CAST(REPLACE(valor, '.', '') AS INTEGER)
        """)).fetchall()

    current = None
    for marca, modelo, versao, valor, fonte in rows:
        if marca != current:
            print(f"\n  {marca}:")
            current = marca
        print(f"    {modelo} {versao}: R$ {int(valor):,}".replace(",", "."))

    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM vehicle_spec WHERE mercado = 'BR'")).scalar()
    print(f"\n{'='*55}")
    print(f"Total no banco: {total} specs")


if __name__ == "__main__":
    main()
