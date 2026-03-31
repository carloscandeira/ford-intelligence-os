"""
Smart Spec Scraper — descobre e extrai specs ATUAIS de sites oficiais.

Fluxo em 2 etapas:
1. DESCOBERTA: acessa a página de catálogo de cada marca e descobre
   todos os modelos disponíveis hoje (sem hardcodar nomes/anos)
2. EXTRAÇÃO: para cada modelo descoberto, acessa a página de specs
   e extrai dados via regex do body text

Resultado: banco sempre atualizado com os modelos que EXISTEM HOJE,
independente do ano. Quando a Ford lançar um modelo novo ou descontinuar
um antigo, o scraper reflete isso automaticamente na próxima execução.
"""

import asyncio
import os
import re
import csv
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
# CATÁLOGOS — páginas que listam TODOS os modelos atuais de cada marca
# O scraper lê estas páginas para descobrir os modelos dinamicamente
# ─────────────────────────────────────────────────────────────

CATALOGS = [
    # Ford — lista todos os carros/SUVs/picapes/elétricos/comerciais
    {
        "marca": "Ford",
        "url": "https://www.ford.com.br/carros/",
        "needs_stealth": True,
        "link_patterns": [
            # URLs como /picapes/ranger/, /suvs/territory/, /eletricos/mustang-mach-e/
            r'href="(https://www\.ford\.com\.br/(?:carros|suvs|picapes|eletricos|comerciais)/[^/"]+/)"',
            r'href="(/(?:carros|suvs|picapes|eletricos|comerciais)/[^/"]+/)"',
        ],
        "base_url": "https://www.ford.com.br",
    },
    # Volkswagen
    {
        "marca": "Volkswagen",
        "url": "https://www.vw.com.br/pt/carros.html",
        "link_patterns": [
            r'href="(https://www\.vw\.com\.br/pt/carros/[^/"]+\.html)"',
            r'href="(/pt/carros/[^/"]+\.html)"',
        ],
        "base_url": "https://www.vw.com.br",
    },
    # Toyota
    {
        "marca": "Toyota",
        "url": "https://www.toyota.com.br/modelos",
        "link_patterns": [
            r'href="(https://www\.toyota\.com\.br/modelos/[^/"]+)"',
            r'href="(/modelos/[^/"]+)"',
        ],
        "base_url": "https://www.toyota.com.br",
    },
    # Mitsubishi
    {
        "marca": "Mitsubishi",
        "url": "https://www.mitsubishimotors.com.br/",
        "link_patterns": [
            r'href="(https://www\.mitsubishimotors\.com\.br/(?:suvs|picapes|sedans)/[^/"]+)"',
            r'href="(/(?:suvs|picapes|sedans)/[^/"]+)"',
        ],
        "base_url": "https://www.mitsubishimotors.com.br",
    },
    # Honda
    {
        "marca": "Honda",
        "url": "https://www.honda.com.br/carros/todos-os-modelos",
        "link_patterns": [
            r'href="(https://www\.honda\.com\.br/carros/[a-z][^/"]+)"',
            r'href="(/carros/[a-z][^/"]+)"',
        ],
        "base_url": "https://www.honda.com.br",
    },
    # Chevrolet
    {
        "marca": "Chevrolet",
        "url": "https://www.chevrolet.com.br/todos-os-veiculos",
        "link_patterns": [
            r'href="(https://www\.chevrolet\.com\.br/(?:suv|hatchback|sedan|picape|van)/[^/"]+)"',
            r'href="(/(?:suv|hatchback|sedan|picape|van)/[^/"]+)"',
        ],
        "base_url": "https://www.chevrolet.com.br",
    },
    # Jeep
    {
        "marca": "Jeep",
        "url": "https://www.jeep.com.br/veiculos",
        "link_patterns": [
            r'href="(https://www\.jeep\.com\.br/(?:compass|renegade|commander|wrangler|avenger)[^"]*)"',
            r'href="(/(?:compass|renegade|commander|wrangler|avenger)[^"]*)"',
        ],
        "base_url": "https://www.jeep.com.br",
    },
    # Nissan
    {
        "marca": "Nissan",
        "url": "https://www.nissan.com.br/carros/",
        "link_patterns": [
            r'href="(https://www\.nissan\.com\.br/carros/[^/"]+)"',
            r'href="(/carros/[^/"]+/)"',
        ],
        "base_url": "https://www.nissan.com.br",
    },
]

# Modelos a EXCLUIR da descoberta (utilitários, caminhões pesados, fora de escopo)
EXCLUDE_PATTERNS = [
    r"transit-custom", r"f-350", r"f-4000", r"cargo",
    r"agile", r"vectra",          # descontinuados
    r"seminovos", r"usados",      # não são modelos novos
    r"acessorios", r"pecas",      # não são veículos
    r"lp-gr",                     # landing page, não modelo
    r"#", r"javascript", r"mailto",
]

# ─────────────────────────────────────────────────────────────
# Regex de extração de specs (do body text da página do modelo)
# ─────────────────────────────────────────────────────────────

SPEC_PATTERNS = [
    {
        "campo": "preco_sugerido",
        "patterns": [
            r"(?:pre[çc]o|partir\s+de|FIPE|tabela)[:\s]*R?\$?\s*([\d.]+(?:,\d{2})?)",
            r"R\$\s*([\d.]{7,}(?:,\d{2})?)\b",
        ],
        "unidade": "BRL",
    },
    {
        "campo": "potencia",
        "patterns": [
            r"(?:pot[eê]ncia|power)[:\s|]*(\d{2,4})\s*(?:cv|CV)",
            r"(\d{2,4})\s*(?:cv|CV)\b",
        ],
        "unidade": "cv",
    },
    {
        "campo": "torque",
        "patterns": [
            r"(?:torque)[:\s|]*(\d{2,3}[.,]?\d?)\s*(?:kgf?\.?m|Nm)",
            r"(\d{2,3}[.,]\d)\s*(?:kgf?\.?m)\b",
        ],
        "unidade": "kgfm",
    },
    {
        "campo": "motor",
        "patterns": [
            r"(?:motor|motoriza[çc][ãa]o)[:\s|]*(V\d\s+\d\.\d[^|,\n]{0,30})",
            r"(?:motor|motoriza[çc][ãa]o)[:\s|]*(\d\.\d[^|,\n]{0,30}(?:Turbo|Diesel|TSI|TDI|EcoBoost|Flex)[^|,\n]{0,20})",
            r"(V\d\s+\d\.\d\s*(?:T(?:DI|SI|urbo)|EcoBoost)[^|,\n]{0,20})",
        ],
        "unidade": None,
    },
    {
        "campo": "transmissao",
        "patterns": [
            r"(?:transmiss[ãa]o|c[aâ]mbio)[:\s|]*((?:autom[aá]tic|manual)[^|,\n]{0,40})",
        ],
        "unidade": None,
    },
    {
        "campo": "tracao",
        "patterns": [
            r"(?:tra[çc][ãa]o)[:\s|]*([^|,\n]{0,40}(?:4x[24]|4Motion|AWD|permanente|dianteira|traseira)[^|,\n]{0,20})",
            r"(4x[24])\b",
        ],
        "unidade": None,
    },
    {
        "campo": "capacidade_carga",
        "patterns": [
            r"(?:capacidade\s+de\s+carga|carga\s+[uú]til)[:\s|]*(\d[\d.]*)\s*(kg)",
        ],
        "unidade": "kg",
    },
    {
        "campo": "entre_eixos",
        "patterns": [
            r"(?:entre[\s-]?eixos)[:\s|]*(\d[\d.]*)\s*mm",
        ],
        "unidade": "mm",
    },
    {
        "campo": "comprimento",
        "patterns": [
            r"(?:comprimento(?:\s+total)?)[:\s|]*(\d[\d.]*)\s*mm",
        ],
        "unidade": "mm",
    },
    {
        "campo": "tanque",
        "patterns": [
            r"(?:tanque|combust[ií]vel)[:\s|]*(\d{2,3})\s*(?:litros|[lL]\b)",
        ],
        "unidade": "litros",
    },
    {
        "campo": "autonomia_eletrica",
        "patterns": [
            r"(?:autonomia)[:\s|]*(\d{2,4})\s*(?:km)\b",
            r"(\d{3,4})\s*km\s*(?:de autonomia|WLTP)",
        ],
        "unidade": "km",
    },
]


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def extract_modelo_from_url(url: str, marca: str) -> str:
    """Extrai nome do modelo a partir da URL."""
    path = re.sub(r"https?://[^/]+", "", url).strip("/")
    parts = [p for p in path.split("/") if p]
    name = parts[-1] if parts else "desconhecido"
    # Remove extensão .html
    name = re.sub(r"\.html?$", "", name, flags=re.IGNORECASE)
    # ranger-raptor → Ranger Raptor
    return name.replace("-", " ").title()


def should_exclude(url: str) -> bool:
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, url, re.IGNORECASE):
            return True
    return False


def extract_specs_from_text(body_text: str, marca: str, modelo: str, versao: str, url: str) -> list[ExtractedSpec]:
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
                valor = re.sub(r"\s+", " ", valor).strip()
                if campo == "preco_sugerido":
                    valor = valor.replace(".", "").replace(",00", "")
                    if not valor.isdigit() or int(valor) < 50000:
                        continue
                if valor:
                    specs.append(ExtractedSpec(
                        marca=marca, modelo=modelo, versao=versao,
                        campo=campo, valor=valor,
                        unidade=spec_def["unidade"] or "",
                        fonte_url=url,
                    ))
                    found_campos.add(campo)
                    break
    return specs


# ─────────────────────────────────────────────────────────────
# ETAPA 1 — Descoberta de modelos
# ─────────────────────────────────────────────────────────────

async def discover_models(page, catalog: dict) -> list[dict]:
    """Acessa a página de catálogo e descobre todos os modelos atuais."""
    marca = catalog["marca"]
    url = catalog["url"]
    base_url = catalog.get("base_url", "")
    discovered = []

    try:
        print(f"\n  🔍 Descobrindo modelos {marca} em {url}")
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        if resp and resp.status in (403, 404):
            print(f"     ⚠ {resp.status} — impossível descobrir modelos de {marca}")
            return discovered

        await page.wait_for_timeout(4000)
        # Scroll para carregar lazy content
        for i in range(4):
            await page.evaluate(f"window.scrollTo(0, {(i+1)*1500})")
            await page.wait_for_timeout(800)

        # Pega HTML completo para extrair links
        html = await page.content()
        body_text = await page.inner_text("body")
        print(f"     Body: {len(body_text)} chars")

        found_urls = set()
        for pattern in catalog["link_patterns"]:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                href = match if match.startswith("http") else base_url + match
                href = href.rstrip("/") + "/"
                if not should_exclude(href) and href not in found_urls:
                    found_urls.add(href)
                    modelo = extract_modelo_from_url(href, marca)
                    discovered.append({
                        "marca": marca,
                        "modelo": modelo,
                        "versao": "Principal",  # versão padrão; pode haver subpáginas
                        "url": href,
                        "needs_stealth": catalog.get("needs_stealth", False),
                    })

        print(f"     ✅ {len(discovered)} modelos descobertos")
        for d in discovered:
            print(f"        → {d['modelo']} ({d['url']})")

    except Exception as e:
        print(f"     ❌ Erro: {e}")

    return discovered


# ─────────────────────────────────────────────────────────────
# ETAPA 2 — Extração de specs por modelo
# ─────────────────────────────────────────────────────────────

async def scrape_model(page, target: dict) -> tuple[list[ExtractedSpec], list[str]]:
    """Acessa a página de um modelo e extrai specs."""
    marca = target["marca"]
    modelo = target["modelo"]
    versao = target["versao"]
    url = target["url"]
    errors = []
    specs = []

    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        status = resp.status if resp else 0

        if status == 403:
            errors.append(f"{marca} {modelo}: 403 Forbidden — {url}")
            return specs, errors
        if status == 404:
            errors.append(f"{marca} {modelo}: 404 Not Found — {url}")
            return specs, errors

        await page.wait_for_timeout(5000)
        for i in range(5):
            await page.evaluate(f"window.scrollTo(0, {(i+1)*1500})")
            await page.wait_for_timeout(800)

        body_text = await page.inner_text("body")
        specs = extract_specs_from_text(body_text, marca, modelo, versao, url)

        if specs:
            campos = ", ".join(s.campo for s in specs)
            print(f"     ✅ {marca} {modelo}: {len(specs)} specs ({campos})")
        else:
            errors.append(f"{marca} {modelo}: 0 specs em {len(body_text)} chars — {url}")
            print(f"     ⚠ {marca} {modelo}: 0 specs ({len(body_text)} chars)")

    except Exception as e:
        errors.append(f"{marca} {modelo}: {type(e).__name__}: {str(e)[:80]}")

    return specs, errors


# ─────────────────────────────────────────────────────────────
# MAIN — descobre + extrai
# ─────────────────────────────────────────────────────────────

async def scrape_all():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: pip3 install playwright && python3 -m playwright install chromium")
        return [], []

    try:
        from playwright_stealth import Stealth
        HAS_STEALTH = True
        print("✅ playwright-stealth v2 carregado")
    except ImportError:
        HAS_STEALTH = False
        Stealth = None

    all_specs = []
    all_errors = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        regular_ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="pt-BR",
            viewport={"width": 1920, "height": 1080},
        )

        # Contexto stealth para sites com WAF (Ford)
        stealth_ctx = None
        if HAS_STEALTH:
            stealth_browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            stealth_ctx = await stealth_browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                ),
                locale="pt-BR",
                viewport={"width": 1920, "height": 1080},
            )
            stealth_obj = Stealth()
            await stealth_obj.apply_stealth_async(stealth_ctx)
            print("🛡 Stealth aplicado ao contexto Ford")

        # ── ETAPA 1: Descoberta ──────────────────────────────
        print("\n" + "="*55)
        print("ETAPA 1 — Descoberta de modelos atuais")
        print("="*55)

        all_targets = []
        for catalog in CATALOGS:
            needs_stealth = catalog.get("needs_stealth", False)
            ctx = stealth_ctx if (needs_stealth and stealth_ctx) else regular_ctx
            page = await ctx.new_page()
            targets = await discover_models(page, catalog)
            all_targets.extend(targets)
            await page.close()
            await asyncio.sleep(random.uniform(1, 2))

        print(f"\nTotal descobertos: {len(all_targets)} modelos/versões")

        # ── ETAPA 2: Extração de specs ───────────────────────
        print("\n" + "="*55)
        print("ETAPA 2 — Extração de specs por modelo")
        print("="*55)

        for target in all_targets:
            needs_stealth = target.get("needs_stealth", False)
            ctx = stealth_ctx if (needs_stealth and stealth_ctx) else regular_ctx
            page = await ctx.new_page()
            specs, errors = await scrape_model(page, target)
            all_specs.extend(specs)
            all_errors.extend(errors)
            await page.close()
            await asyncio.sleep(random.uniform(1, 3))

        await browser.close()
        if HAS_STEALTH:
            await stealth_browser.close()

    return all_specs, all_errors


# ─────────────────────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────────────────────

def load_into_db(specs: list[ExtractedSpec]):
    from sqlalchemy import text
    from db.connection import engine

    loaded = 0
    with engine.connect() as conn:
        for s in specs:
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
                {"marca": s.marca, "modelo": s.modelo, "versao": s.versao,
                 "campo": s.campo, "valor": s.valor, "unidade": s.unidade,
                 "fonte_url": s.fonte_url, "extraido_em": s.extraido_em},
            )
            loaded += 1
        conn.commit()
    print(f"✅ {loaded} specs salvos no banco (data: {date.today().isoformat()})")


def save_specs_csv(specs: list[ExtractedSpec], output_path: str):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "marca", "modelo", "versao", "mercado", "campo", "valor", "unidade", "fonte_url", "extraido_em"
        ])
        writer.writeheader()
        for s in specs:
            writer.writerow({
                "marca": s.marca, "modelo": s.modelo, "versao": s.versao,
                "mercado": "BR", "campo": s.campo, "valor": s.valor,
                "unidade": s.unidade, "fonte_url": s.fonte_url, "extraido_em": s.extraido_em,
            })
    print(f"CSV salvo: {output_path}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    print("Ford Intelligence OS — Smart Spec Scraper (DINÂMICO)")
    print("=" * 55)
    print(f"Data: {date.today().isoformat()}")
    print(f"Modo: descobre modelos ATUAIS automaticamente (sem hardcode de ano)")
    print(f"Marcas: {len(CATALOGS)} catálogos para varrer")
    print()

    specs, errors = asyncio.run(scrape_all())

    print(f"\n{'='*55}")
    print(f"RESULTADO FINAL: {len(specs)} specs extraídos ao vivo")

    if errors:
        print(f"\nErros ({len(errors)}):")
        for e in errors[:10]:
            print(f"  ⚠ {e}")

    if specs:
        output = os.path.join(os.path.dirname(__file__), "..", "data", "scraped")
        os.makedirs(output, exist_ok=True)
        save_specs_csv(specs, os.path.join(output, "scraped_specs.csv"))
        if os.getenv("DATABASE_URL"):
            load_into_db(specs)

    # Resumo por marca
    print(f"\n{'='*55}")
    print("Resumo por marca:")
    from collections import defaultdict
    by_marca = defaultdict(set)
    for s in specs:
        by_marca[s.marca].add(s.modelo)
    for marca, modelos in sorted(by_marca.items()):
        print(f"  {marca}: {', '.join(sorted(modelos))}")

    print("\nDone!")
