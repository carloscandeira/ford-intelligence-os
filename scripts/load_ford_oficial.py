"""
Load OFFICIAL Ford Ranger specs into vehicle_spec.

Source: ficha técnica oficial Ford Ranger MY2026 (PDF publicado pela Ford no
CDN de assets do ford.com.br — o site HTML é bloqueado por WAF, mas o PDF
oficial é público e indexado pelo Google).

Dados transcritos da tabela "Performance / Dimensões e capacidades" do PDF
(6 versões). Torque convertido de Nm para kgfm (1 kgfm = 9.80665 Nm) para
manter a unidade consistente com o restante do banco:
  405 Nm -> 41,3 kgfm | 600 Nm -> 61,2 kgfm

Usage: python3 scripts/load_ford_oficial.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

FONTE_OFICIAL = (
    "https://weupreviewimagesprd.blob.core.windows.net/br1001/siteassets/"
    "250516-nova-geracao-ford-ranger-ficha-tecnica.pdf"
)

# (versao, motor, potencia cv, torque kgfm, tracao, transmissao, carga kg)
RANGER_VERSOES = [
    ("XL 4x4",  "2.0 Turbo Diesel",    "170", "41,3", "4x4", "Manual 6 velocidades",     "1071"),
    ("XLS 4x4", "2.0 Turbo Diesel",    "170", "41,3", "4x4", "Automatica 6 velocidades", "1037"),
    ("Black",   "2.0 Turbo Diesel",    "170", "41,3", "4x2", "Automatica 6 velocidades", "1005"),
    ("XLS 4WD", "3.0 V6 Turbo Diesel", "250", "61,2", "4WD", "Automatica 10 velocidades", "1054"),
    ("XLT 4WD", "3.0 V6 Turbo Diesel", "250", "61,2", "4WD", "Automatica 10 velocidades", "1037"),
    ("Limited", "3.0 V6 Turbo Diesel", "250", "61,2", "4WD", "Automatica 10 velocidades", "1023"),
]

# Dimensões iguais para todas as versões (tabela oficial)
DIMENSOES_COMUNS = [
    ("tanque", "80", "litros"),
    ("comprimento", "5370", "mm"),
    ("entre_eixos", "3270", "mm"),
]


def main():
    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL nao setado.")
        return

    from scraper.smart_scraper import ExtractedSpec, load_into_db

    specs = []
    for versao, motor, potencia, torque, tracao, transmissao, carga in RANGER_VERSOES:
        campos = [
            ("motor", motor, ""),
            ("potencia", potencia, "cv"),
            ("torque", torque, "kgfm"),
            ("tracao", tracao, ""),
            ("transmissao", transmissao, ""),
            ("capacidade_carga", carga, "kg"),
        ] + DIMENSOES_COMUNS
        for campo, valor, unidade in campos:
            specs.append(ExtractedSpec(
                marca="Ford", modelo="Ranger", versao=versao,
                campo=campo, valor=valor, unidade=unidade,
                fonte_url=FONTE_OFICIAL,
            ))

    print(f"Ford Ranger MY2026 — ficha tecnica OFICIAL: {len(specs)} specs "
          f"({len(RANGER_VERSOES)} versoes x {6 + len(DIMENSOES_COMUNS)} campos)")
    load_into_db(specs)
    print("Fonte:", FONTE_OFICIAL)


if __name__ == "__main__":
    main()
