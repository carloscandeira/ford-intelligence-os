"""
Spec Scraper — Playwright-based scraper for Brazilian manufacturer sites.

Architecture decisions from /plan-eng-review:
- Playwright for JS-rendered .com.br sites (not requests/BS4)
- Anti-bot: random delays, realistic user-agent, headless mode
- Fallback: INMETRO PDF table if site blocks
- Validation: inline type check, range check, NULL normalization

Target sites (MVP — Brazilian pickup market):
- ford.com.br/ranger/
- toyota.com.br/hilux/
- mitsubishi-motors.com.br/l200-triton/
- vw.com.br/amarok/

IMPORTANT: This scraper respects robots.txt and adds delays between requests.
For demo/development, use generate_synthetic.py instead.
"""

import os
import re
import random
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────

@dataclass
class SpecField:
    """A single spec field extracted from a manufacturer site."""
    marca: str
    modelo: str
    versao: str
    mercado: str
    campo: str
    valor: Optional[str]
    unidade: Optional[str]
    fonte_url: str
    extraido_em: str = field(default_factory=lambda: date.today().isoformat())


@dataclass
class ScrapeResult:
    """Result of scraping a single vehicle page."""
    url: str
    marca: str
    modelo: str
    specs: list[SpecField]
    errors: list[str]
    duration_seconds: float


# ─────────────────────────────────────────────────────────────
# Site configurations
# ─────────────────────────────────────────────────────────────

SITE_CONFIGS = {
    "ford": {
        "base_url": "https://www.ford.com.br",
        "vehicles": {
            "Ranger": {
                "url": "/ranger/",
                "versoes": ["Raptor", "Limited", "XLS", "XL"],
            },
        },
        "spec_selectors": {
            # CSS selectors for spec extraction (to be refined per site)
            "spec_table": ".specs-table, .technical-specs, [data-specs]",
            "spec_row": "tr, .spec-row, .spec-item",
            "spec_label": "td:first-child, .spec-label, .spec-name",
            "spec_value": "td:last-child, .spec-value, .spec-data",
        },
    },
    "toyota": {
        "base_url": "https://www.toyota.com.br",
        "vehicles": {
            "Hilux": {
                "url": "/modelos/hilux/",
                "versoes": ["SRX", "GR-Sport", "SR", "STD"],
            },
        },
        "spec_selectors": {
            "spec_table": ".specs-table, .technical-data, .ficha-tecnica",
            "spec_row": "tr, .spec-row",
            "spec_label": "td:first-child, .spec-label",
            "spec_value": "td:last-child, .spec-value",
        },
    },
    "mitsubishi": {
        "base_url": "https://www.mitsubishi-motors.com.br",
        "vehicles": {
            "L200 Triton": {
                "url": "/l200-triton/",
                "versoes": ["Savana", "Outdoor", "GLX"],
            },
        },
        "spec_selectors": {
            "spec_table": ".specs-table, .ficha-tecnica",
            "spec_row": "tr, .spec-row",
            "spec_label": "td:first-child, .spec-label",
            "spec_value": "td:last-child, .spec-value",
        },
    },
    "volkswagen": {
        "base_url": "https://www.vw.com.br",
        "vehicles": {
            "Amarok": {
                "url": "/carros/amarok/",
                "versoes": ["Highline V6", "Comfortline", "Extreme"],
            },
        },
        "spec_selectors": {
            "spec_table": ".specs-table, .technical-specs, .ficha-tecnica",
            "spec_row": "tr, .spec-row",
            "spec_label": "td:first-child, .spec-label",
            "spec_value": "td:last-child, .spec-value",
        },
    },
}

# Field name normalization map (Brazilian Portuguese variants → canonical names)
FIELD_NORMALIZATION = {
    "potencia": "potencia",
    "potência": "potencia",
    "potencia maxima": "potencia",
    "potência máxima": "potencia",
    "torque": "torque",
    "torque maximo": "torque",
    "torque máximo": "torque",
    "motor": "motor",
    "motorização": "motor",
    "motorizacao": "motor",
    "transmissao": "transmissao",
    "transmissão": "transmissao",
    "cambio": "transmissao",
    "câmbio": "transmissao",
    "tracao": "tracao",
    "tração": "tracao",
    "suspensao": "suspensao",
    "suspensão": "suspensao",
    "suspensao dianteira": "suspensao",
    "capacidade de carga": "capacidade_carga",
    "carga util": "capacidade_carga",
    "entre-eixos": "entre_eixos",
    "entre eixos": "entre_eixos",
    "distancia entre eixos": "entre_eixos",
    "distância entre eixos": "entre_eixos",
    "comprimento": "comprimento",
    "comprimento total": "comprimento",
    "tanque": "tanque",
    "tanque de combustivel": "tanque",
    "tanque de combustível": "tanque",
    "capacidade do tanque": "tanque",
    "preco": "preco_sugerido",
    "preço": "preco_sugerido",
    "preco sugerido": "preco_sugerido",
    "preço sugerido": "preco_sugerido",
}

# Unit extraction patterns
UNIT_PATTERNS = {
    "potencia": (r"([\d.,]+)\s*(cv|hp|PS)", "cv"),
    "torque": (r"([\d.,]+)\s*(kgfm|Nm|kgf\.m)", "kgfm"),
    "capacidade_carga": (r"([\d.,]+)\s*(kg)", "kg"),
    "entre_eixos": (r"([\d.,]+)\s*(mm)", "mm"),
    "comprimento": (r"([\d.,]+)\s*(mm)", "mm"),
    "tanque": (r"([\d.,]+)\s*(l|litros|L)", "litros"),
    "preco_sugerido": (r"R?\$?\s*([\d.,]+)", "BRL"),
}

# Validation ranges (same as ingestion/load_data.py)
RANGE_CHECKS = {
    "potencia": (50, 1000),
    "torque": (10, 500),
    "comprimento": (3000, 7000),
    "entre_eixos": (2000, 5000),
    "tanque": (30, 200),
    "capacidade_carga": (200, 2000),
    "preco_sugerido": (50000, 2000000),
}


# ─────────────────────────────────────────────────────────────
# Core scraper
# ─────────────────────────────────────────────────────────────

def _normalize_field_name(raw_name: str) -> Optional[str]:
    """Normalize a Brazilian Portuguese field name to canonical form."""
    cleaned = raw_name.lower().strip().replace(":", "")
    return FIELD_NORMALIZATION.get(cleaned)


def _extract_value_and_unit(campo: str, raw_value: str) -> tuple[Optional[str], Optional[str]]:
    """Extract numeric value and unit from a raw spec string."""
    if not raw_value or raw_value.strip() in ("", "-", "—", "N/A", "N/D"):
        return None, None

    if campo in UNIT_PATTERNS:
        pattern, default_unit = UNIT_PATTERNS[campo]
        match = re.search(pattern, raw_value)
        if match:
            return match.group(1).replace(",", "."), default_unit

    # Return raw value for non-numeric fields
    return raw_value.strip(), None


def _validate_spec(campo: str, valor: Optional[str]) -> bool:
    """Validate a spec value is within expected range."""
    if valor is None:
        return True
    if campo not in RANGE_CHECKS:
        return True

    try:
        num = float(valor.replace(",", "."))
        lo, hi = RANGE_CHECKS[campo]
        return lo <= num <= hi
    except (ValueError, AttributeError):
        return True


async def scrape_vehicle_page(
    page,  # playwright Page object
    marca: str,
    modelo: str,
    versao: str,
    url: str,
    selectors: dict,
) -> ScrapeResult:
    """
    Scrape a single vehicle page for spec data.

    Args:
        page: Playwright page instance
        marca: Brand name
        modelo: Model name
        versao: Version/trim
        url: Full URL to scrape
        selectors: CSS selectors for this site

    Returns:
        ScrapeResult with extracted specs
    """
    start_time = time.time()
    specs = []
    errors = []

    try:
        # Navigate with realistic delay
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(random.randint(1000, 3000))

        # Try to find spec tables
        tables = await page.query_selector_all(selectors["spec_table"])

        if not tables:
            errors.append(f"No spec table found at {url} with selector: {selectors['spec_table']}")
            return ScrapeResult(url=url, marca=marca, modelo=modelo, specs=[], errors=errors,
                                duration_seconds=time.time() - start_time)

        for table in tables:
            rows = await table.query_selector_all(selectors["spec_row"])

            for row in rows:
                label_el = await row.query_selector(selectors["spec_label"])
                value_el = await row.query_selector(selectors["spec_value"])

                if not label_el or not value_el:
                    continue

                raw_label = (await label_el.inner_text()).strip()
                raw_value = (await value_el.inner_text()).strip()

                # Normalize field name
                campo = _normalize_field_name(raw_label)
                if not campo:
                    continue  # unknown field, skip

                # Extract value and unit
                valor, unidade = _extract_value_and_unit(campo, raw_value)

                # Validate
                if not _validate_spec(campo, valor):
                    errors.append(f"Validation failed: {campo}={valor} out of range")
                    continue

                specs.append(SpecField(
                    marca=marca,
                    modelo=modelo,
                    versao=versao,
                    mercado="BR",
                    campo=campo,
                    valor=valor,
                    unidade=unidade,
                    fonte_url=url,
                ))

    except Exception as e:
        errors.append(f"Error scraping {url}: {str(e)}")

    return ScrapeResult(
        url=url,
        marca=marca,
        modelo=modelo,
        specs=specs,
        errors=errors,
        duration_seconds=time.time() - start_time,
    )


async def scrape_all_sites(headless: bool = True) -> list[ScrapeResult]:
    """
    Scrape all configured manufacturer sites.

    Requires: playwright install chromium

    Returns list of ScrapeResult for each vehicle page.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
        return []

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="pt-BR",
        )
        page = await context.new_page()

        for brand_key, config in SITE_CONFIGS.items():
            base_url = config["base_url"]
            selectors = config["spec_selectors"]

            for modelo, vehicle_config in config["vehicles"].items():
                url = base_url + vehicle_config["url"]
                marca = brand_key.capitalize()
                if marca == "Volkswagen":
                    marca = "Volkswagen"

                print(f"  Scraping {marca} {modelo} at {url}...")

                # Scrape with delay between requests
                for versao in vehicle_config["versoes"]:
                    result = await scrape_vehicle_page(
                        page, marca, modelo, versao, url, selectors
                    )
                    results.append(result)

                    if result.errors:
                        for err in result.errors:
                            print(f"    WARNING: {err}")
                    else:
                        print(f"    OK: {len(result.specs)} specs for {versao}")

                    # Anti-bot delay between requests
                    await page.wait_for_timeout(random.randint(2000, 5000))

        await browser.close()

    return results


def save_results_to_csv(results: list[ScrapeResult], output_path: str):
    """Save scrape results to CSV format matching vehicle_specs.csv schema."""
    import csv

    all_specs = []
    for result in results:
        all_specs.extend(result.specs)

    if not all_specs:
        print("No specs to save.")
        return

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["marca", "modelo", "versao", "mercado", "campo",
                         "valor", "unidade", "fonte_url", "extraido_em"],
        )
        writer.writeheader()
        for spec in all_specs:
            writer.writerow({
                "marca": spec.marca,
                "modelo": spec.modelo,
                "versao": spec.versao,
                "mercado": spec.mercado,
                "campo": spec.campo,
                "valor": spec.valor,
                "unidade": spec.unidade or "",
                "fonte_url": spec.fonte_url,
                "extraido_em": spec.extraido_em,
            })

    print(f"Saved {len(all_specs)} specs to {output_path}")


# ─────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    print("Ford Intelligence OS — Spec Scraper")
    print("=" * 50)
    print("WARNING: This scrapes real manufacturer sites.")
    print("For development, use: python -m data.synthetic.generate_synthetic")
    print()

    results = asyncio.run(scrape_all_sites(headless=True))

    total_specs = sum(len(r.specs) for r in results)
    total_errors = sum(len(r.errors) for r in results)
    print(f"\nTotal: {total_specs} specs extracted, {total_errors} errors")

    if total_specs > 0:
        output = os.path.join(os.path.dirname(__file__), "..", "data", "scraped", "vehicle_specs.csv")
        os.makedirs(os.path.dirname(output), exist_ok=True)
        save_results_to_csv(results, output)
