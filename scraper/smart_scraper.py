"""
Smart Spec Scraper — extracts specs from page body text via Playwright.

Instead of relying on CSS selectors (which break per-site), this scraper:
1. Loads the full JS-rendered page with Playwright
2. Gets the body text content
3. Uses regex patterns to extract spec values from natural text
4. Works on any site structure (tables, cards, text blocks)

This handles the reality that Brazilian manufacturer sites are SPAs
with different HTML structures and some have anti-bot protection.
"""

import asyncio
import os
import re
import csv
import time
import random
from datetime import date
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
load_dotenv()


@dataclass
class ExtractedSpec:
    marca: str
    modelo: str
    versao: str
    campo: str
    valor: str
    unidade: str
    fonte_url: str
    extraido_em: str = field(default_factory=lambda: date.today().isoformat())


# ─────────────────────────────────────────────────────────────
# Sites to scrape
# ─────────────────────────────────────────────────────────────

SCRAPE_TARGETS = [
    {
        "marca": "Volkswagen",
        "modelo": "Amarok",
        "versao": "Highline V6",
        "url": "https://www.vw.com.br/pt/carros/amarok.html",
    },
    {
        "marca": "Toyota",
        "modelo": "Hilux",
        "versao": "SRX",
        "url": "https://www.toyota.com.br/modelos/hilux-cabine-dupla",
    },
    {
        "marca": "Mitsubishi",
        "modelo": "L200 Triton",
        "versao": "Savana",
        "url": "https://www.mitsubishimotors.com.br/picapes/nova-triton",
    },
    {
        "marca": "Ford",
        "modelo": "Ranger",
        "versao": "Raptor",
        "url": "https://www.ford.com.br/picapes/ranger/",
    },
]

# ─────────────────────────────────────────────────────────────
# Regex extraction patterns (work on body text)
# ─────────────────────────────────────────────────────────────

SPEC_PATTERNS = [
    # Potencia: "258 cv", "400cv", "210 cv"
    {
        "campo": "potencia",
        "patterns": [
            r"(?:pot[eê]ncia|power)[:\s|]*(\d{2,4})\s*(?:cv|CV)",
            r"(\d{2,4})\s*(?:cv|CV)\b",
        ],
        "unidade": "cv",
    },
    # Torque: "59,1 kgfm", "51 kgfm", "500 Nm"
    {
        "campo": "torque",
        "patterns": [
            r"(?:torque)[:\s|]*(\d{2,3}[.,]?\d?)\s*(?:kgf?\.?m|Nm)",
            r"(\d{2,3}[.,]\d)\s*(?:kgf?\.?m)\b",
        ],
        "unidade": "kgfm",
    },
    # Motor: "V6 3.0 TDI", "2.8 Turbo Diesel", "2.0 Turbo"
    {
        "campo": "motor",
        "patterns": [
            r"(?:motor|motoriza[çc][ãa]o)[:\s|]*(V\d\s+\d\.\d[^|,\n]{0,30})",
            r"(?:motor|motoriza[çc][ãa]o)[:\s|]*(\d\.\d[^|,\n]{0,30}(?:Turbo|Diesel|TSI|TDI)[^|,\n]{0,20})",
            r"(V\d\s+\d\.\d\s*(?:T(?:DI|SI|urbo))[^|,\n]{0,20})",
        ],
        "unidade": None,
    },
    # Transmissao: "Automatica 10 velocidades"
    {
        "campo": "transmissao",
        "patterns": [
            r"(?:transmiss[ãa]o|c[aâ]mbio)[:\s|]*((?:autom[aá]tic|manual)[^|,\n]{0,40})",
        ],
        "unidade": None,
    },
    # Tracao: "4x4", "4Motion", "AWD"
    {
        "campo": "tracao",
        "patterns": [
            r"(?:tra[çc][ãa]o)[:\s|]*([^|,\n]{0,40}(?:4x[24]|4Motion|AWD|permanente)[^|,\n]{0,20})",
            r"(?:tra[çc][ãa]o)[:\s|]*(4x[24][^|,\n]{0,30})",
        ],
        "unidade": None,
    },
    # Capacidade de carga: "785 kg", "1.280 litros"
    {
        "campo": "capacidade_carga",
        "patterns": [
            r"(?:capacidade\s+de\s+carga|carga\s+[uú]til)[:\s|]*(\d[\d.]*)\s*(kg|litros)",
        ],
        "unidade": "kg",
    },
    # Entre-eixos: "3270 mm", "3.270 mm"
    {
        "campo": "entre_eixos",
        "patterns": [
            r"(?:entre[\s-]?eixos|dist[aâ]ncia\s+entre[\s-]?eixos)[:\s|]*(\d[\d.]*)\s*(?:mm)",
        ],
        "unidade": "mm",
    },
    # Comprimento: "5381 mm", "5.381 mm"
    {
        "campo": "comprimento",
        "patterns": [
            r"(?:comprimento(?:\s+total)?)[:\s|]*(\d[\d.]*)\s*(?:mm)",
        ],
        "unidade": "mm",
    },
    # Tanque: "80 litros", "80L"
    {
        "campo": "tanque",
        "patterns": [
            r"(?:tanque|combust[ií]vel)[:\s|]*(\d{2,3})\s*(?:litros|[lL]\b)",
        ],
        "unidade": "litros",
    },
]


def extract_specs_from_text(body_text: str, marca: str, modelo: str, versao: str, url: str) -> list[ExtractedSpec]:
    """Extract specs from page body text using regex patterns."""
    specs = []
    found_campos = set()

    for spec_def in SPEC_PATTERNS:
        campo = spec_def["campo"]
        if campo in found_campos:
            continue

        for pattern in spec_def["patterns"]:
            match = re.search(pattern, body_text, re.IGNORECASE)
            if match:
                valor = match.group(1).strip()
                # Clean up value
                valor = re.sub(r"\s+", " ", valor).strip()
                if valor:
                    specs.append(ExtractedSpec(
                        marca=marca,
                        modelo=modelo,
                        versao=versao,
                        campo=campo,
                        valor=valor,
                        unidade=spec_def["unidade"] or "",
                        fonte_url=url,
                    ))
                    found_campos.add(campo)
                    break

    return specs


async def scrape_site(page, target: dict) -> tuple[list[ExtractedSpec], list[str]]:
    """Scrape a single site for specs."""
    marca = target["marca"]
    modelo = target["modelo"]
    versao = target["versao"]
    url = target["url"]
    errors = []
    specs = []

    try:
        print(f"  Loading {marca} {modelo}...")
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        if resp and resp.status == 403:
            errors.append(f"{marca}: 403 Forbidden (anti-bot)")
            return specs, errors

        if resp and resp.status == 404:
            errors.append(f"{marca}: 404 Not Found")
            return specs, errors

        # Wait for dynamic content
        await page.wait_for_timeout(5000)

        # Scroll to load lazy content
        for i in range(5):
            await page.evaluate(f"window.scrollTo(0, {(i+1) * 1500})")
            await page.wait_for_timeout(1000)

        body_text = await page.inner_text("body")
        print(f"  Body: {len(body_text)} chars")

        specs = extract_specs_from_text(body_text, marca, modelo, versao, url)
        print(f"  Extracted: {len(specs)} specs")
        for s in specs:
            print(f"    {s.campo}: {s.valor} {s.unidade}")

        if not specs:
            errors.append(f"{marca}: no specs found in {len(body_text)} chars of body text")

    except Exception as e:
        errors.append(f"{marca}: {type(e).__name__}: {str(e)[:100]}")

    return specs, errors


async def scrape_all():
    """Scrape all target sites."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: playwright not installed")
        return [], []

    all_specs = []
    all_errors = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="pt-BR",
            viewport={"width": 1920, "height": 1080},
        )

        for target in SCRAPE_TARGETS:
            page = await context.new_page()
            specs, errors = await scrape_site(page, target)
            all_specs.extend(specs)
            all_errors.extend(errors)
            await page.close()
            # Delay between sites
            await asyncio.sleep(random.uniform(2, 4))

        await browser.close()

    return all_specs, all_errors


def save_specs_csv(specs: list[ExtractedSpec], output_path: str):
    """Save extracted specs to CSV."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["marca", "modelo", "versao", "mercado", "campo",
                         "valor", "unidade", "fonte_url", "extraido_em"],
        )
        writer.writeheader()
        for s in specs:
            writer.writerow({
                "marca": s.marca, "modelo": s.modelo, "versao": s.versao,
                "mercado": "BR", "campo": s.campo, "valor": s.valor,
                "unidade": s.unidade, "fonte_url": s.fonte_url,
                "extraido_em": s.extraido_em,
            })
    print(f"\nSaved {len(specs)} specs to {output_path}")


def load_into_db(specs: list[ExtractedSpec]):
    """Load scraped specs directly into PostgreSQL."""
    from sqlalchemy import text
    from db.connection import engine

    loaded = 0
    with engine.connect() as conn:
        for s in specs:
            conn.execute(
                text("""
                    INSERT INTO vehicle_spec (marca, modelo, versao, mercado, campo, valor, unidade, fonte_url, extraido_em)
                    VALUES (:marca, :modelo, :versao, 'BR', :campo, :valor, :unidade, :fonte_url, :extraido_em)
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
                    "marca": s.marca, "modelo": s.modelo, "versao": s.versao,
                    "campo": s.campo, "valor": s.valor, "unidade": s.unidade,
                    "fonte_url": s.fonte_url, "extraido_em": s.extraido_em,
                },
            )
            loaded += 1
        conn.commit()
    print(f"Loaded {loaded} specs into database")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    print("Ford Intelligence OS — Smart Spec Scraper")
    print("=" * 50)

    specs, errors = asyncio.run(scrape_all())

    print(f"\n{'='*50}")
    print(f"Total: {len(specs)} specs extracted")
    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")

    if specs:
        # Save to CSV
        output = os.path.join(os.path.dirname(__file__), "..", "data", "scraped")
        os.makedirs(output, exist_ok=True)
        save_specs_csv(specs, os.path.join(output, "scraped_specs.csv"))

        # Load into DB
        if os.getenv("DATABASE_URL"):
            print("\nLoading into database...")
            load_into_db(specs)

    print("\nDone!")
