"""
Load REAL Ford Ranger specs into PostgreSQL.
Data sourced from carrosnaweb.com.br, garagem360.com.br, carro.blog.br, icarros.com.br.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from db.connection import engine

FORD_REAL_SPECS = [
    # ─── Ranger Raptor (V6 3.0 EcoBoost Gasolina Biturbo) ───
    ("Ford", "Ranger", "Raptor", "potencia", "397", "cv", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947"),
    ("Ford", "Ranger", "Raptor", "torque", "59,4", "kgfm", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947"),
    ("Ford", "Ranger", "Raptor", "motor", "V6 3.0 EcoBoost Gasolina Biturbo", "", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947"),
    ("Ford", "Ranger", "Raptor", "transmissao", "Automatica 10 velocidades", "", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947"),
    ("Ford", "Ranger", "Raptor", "tracao", "4x4 integral sob demanda", "", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947"),
    ("Ford", "Ranger", "Raptor", "capacidade_carga", "736", "kg", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947"),
    ("Ford", "Ranger", "Raptor", "entre_eixos", "3270", "mm", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947"),
    ("Ford", "Ranger", "Raptor", "comprimento", "5360", "mm", "https://carro.blog.br/ficha-tecnica/ford/ford-ranger/ford-ranger-2025/ford-ranger-raptor-3-0-v6-2025-ficha-tecnica-preco-consumo-equipamentos-e-fotos-picape-de-397-cv-para-uso-pesado"),
    ("Ford", "Ranger", "Raptor", "tanque", "82", "litros", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35947"),

    # ─── Ranger Limited (V6 3.0 Turbo Diesel) ───
    ("Ford", "Ranger", "Limited", "potencia", "250", "cv", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35882"),
    ("Ford", "Ranger", "Limited", "torque", "61,2", "kgfm", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35882"),
    ("Ford", "Ranger", "Limited", "motor", "V6 3.0 Turbo Diesel", "", "https://garagem360.com.br/ford-ranger-limited-2025-conheca-a-picape-de-aspectos-exclusivos/"),
    ("Ford", "Ranger", "Limited", "transmissao", "Automatica 10 velocidades", "", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35882"),
    ("Ford", "Ranger", "Limited", "tracao", "4x4 integral temporaria", "", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35882"),
    ("Ford", "Ranger", "Limited", "capacidade_carga", "1023", "kg", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35882"),
    ("Ford", "Ranger", "Limited", "entre_eixos", "3270", "mm", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35882"),
    ("Ford", "Ranger", "Limited", "comprimento", "5360", "mm", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35882"),
    ("Ford", "Ranger", "Limited", "tanque", "80", "litros", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35882"),

    # ─── Ranger XLS (2.0 Turbo Diesel 4x4) ───
    ("Ford", "Ranger", "XLS", "potencia", "170", "cv", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35868"),
    ("Ford", "Ranger", "XLS", "torque", "41,3", "kgfm", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35868"),
    ("Ford", "Ranger", "XLS", "motor", "2.0 Turbo Diesel 4 cilindros", "", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35868"),
    ("Ford", "Ranger", "XLS", "transmissao", "Automatica 6 velocidades", "", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35868"),
    ("Ford", "Ranger", "XLS", "tracao", "4x4 integral temporaria", "", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35868"),
    ("Ford", "Ranger", "XLS", "capacidade_carga", "1037", "kg", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35868"),
    ("Ford", "Ranger", "XLS", "entre_eixos", "3270", "mm", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35868"),
    ("Ford", "Ranger", "XLS", "comprimento", "5370", "mm", "https://garagem360.com.br/ford-ranger-xls-2025/"),
    ("Ford", "Ranger", "XLS", "tanque", "80", "litros", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=35868"),

    # ─── Ranger Black (2.0 Turbo Diesel 4x2) ───
    ("Ford", "Ranger", "Black", "potencia", "170", "cv", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=37251"),
    ("Ford", "Ranger", "Black", "torque", "41,3", "kgfm", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=37251"),
    ("Ford", "Ranger", "Black", "motor", "2.0 Turbo Diesel 4 cilindros", "", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=37251"),
    ("Ford", "Ranger", "Black", "transmissao", "Automatica 6 velocidades", "", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=37251"),
    ("Ford", "Ranger", "Black", "tracao", "4x2 traseira", "", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=37251"),
    ("Ford", "Ranger", "Black", "capacidade_carga", "1031", "kg", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=37251"),
    ("Ford", "Ranger", "Black", "entre_eixos", "3270", "mm", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=37251"),
    ("Ford", "Ranger", "Black", "comprimento", "5382", "mm", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=37251"),
    ("Ford", "Ranger", "Black", "tanque", "80", "litros", "https://www.carrosnaweb.com.br/fichadetalhe.asp?codigo=37251"),
]


def main():
    from datetime import date

    print("Ford Intelligence OS — Loading REAL Ford Ranger Specs")
    print("=" * 55)
    print(f"Source: carrosnaweb.com.br, garagem360.com.br, carro.blog.br, icarros.com.br")
    print(f"Specs to load: {len(FORD_REAL_SPECS)}")
    print()

    # First, remove old synthetic Ford data
    with engine.connect() as conn:
        deleted = conn.execute(text("""
            DELETE FROM vehicle_spec
            WHERE marca = 'Ford' AND mercado = 'BR'
        """))
        print(f"Removed {deleted.rowcount} old Ford specs (synthetic + scraped)")

        # Insert real data
        loaded = 0
        for marca, modelo, versao, campo, valor, unidade, fonte_url in FORD_REAL_SPECS:
            conn.execute(
                text("""
                    INSERT INTO vehicle_spec (marca, modelo, versao, mercado, campo, valor, unidade, fonte_url, extraido_em, verificado)
                    VALUES (:marca, :modelo, :versao, 'BR', :campo, :valor, :unidade, :fonte_url, :extraido_em, TRUE)
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
                    "marca": marca, "modelo": modelo, "versao": versao,
                    "campo": campo, "valor": valor, "unidade": unidade,
                    "fonte_url": fonte_url, "extraido_em": date.today().isoformat(),
                },
            )
            loaded += 1

        conn.commit()

    print(f"\n✅ Loaded {loaded} REAL Ford specs into database")
    print()

    # Show what's in the DB now
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT marca, modelo, versao, campo, valor, unidade
            FROM vehicle_spec
            WHERE marca = 'Ford' AND mercado = 'BR'
            ORDER BY versao, campo
        """))
        rows = result.fetchall()

    current_versao = None
    for marca, modelo, versao, campo, valor, unidade in rows:
        if versao != current_versao:
            print(f"\n  {modelo} {versao}:")
            current_versao = versao
        print(f"    {campo}: {valor} {unidade}")

    # Total count
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM vehicle_spec WHERE mercado = 'BR'")).scalar()
        ford_total = conn.execute(text("SELECT COUNT(*) FROM vehicle_spec WHERE marca = 'Ford' AND mercado = 'BR'")).scalar()
    print(f"\n{'='*55}")
    print(f"Total no banco: {total} specs ({ford_total} Ford)")


if __name__ == "__main__":
    main()
