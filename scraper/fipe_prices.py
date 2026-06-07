"""
FIPE price fetcher — preço de referência oficial (Tabela FIPE).

Substitui o passo de preço de concessionária (webmotors.com.br), que é
bloqueado por WAF e retorna 403. A FIPE é a referência oficial de preço
de veículos no Brasil: estável, pública e citável numa apresentação.

Usa a API pública e gratuita "parallelum" (Cantareira) v2, sem token.
Cadeia: brand -> models -> years -> value.

Sem dependências externas: usa apenas a stdlib (urllib + json).
"""

import json
import re
import time
import urllib.error
import urllib.request
from datetime import date

FIPE_BASE = "https://fipe.parallelum.com.br/api/v2/cars"

# Nome da marca (como usado no projeto) -> código FIPE.
# Códigos confirmados em junho/2026 via /cars/brands.
FIPE_BRAND_CODES = {
    "Ford": "22",
    "Toyota": "56",
    "Volkswagen": "59",
    "Mitsubishi": "41",
}

# Só interessam preços do lineup atual (ano-modelo recente).
MIN_MODEL_YEAR = date.today().year - 1
# Código de ano-modelo que a FIPE usa para "Zero KM" (veículo 0km à venda hoje).
ZERO_KM_PREFIX = "32000"
# Teto de versões por modelo, pra não poluir o banco nem martelar a API.
MAX_VERSIONS_PER_MODEL = 6
# Teto de buscas de "anos" por modelo — um nome tipo "Ranger" casa com ~100
# entradas históricas no FIPE; varrer todas seria lento e abusivo com a API.
SCAN_LIMIT = 45
# Pausa entre chamadas — a API gratuita é compartilhada, seja educado.
REQUEST_PAUSE_S = 0.8
# Tentativas em caso de 429 (rate limit), com backoff exponencial.
MAX_RETRIES = 4
RETRY_BACKOFF_S = 3.0
# Preço mínimo plausível pra um veículo novo (descarta ruído).
MIN_PRICE_BRL = 50_000


def _get_json(url: str, timeout: int = 20):
    """GET + parse JSON. Repete em 429 (rate limit) com backoff exponencial."""
    req = urllib.request.Request(url, headers={"User-Agent": "ford-intel-os/1.0"})
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 429 and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_S * (2 ** attempt))
                continue
            raise
    raise last_err  # pragma: no cover


def _parse_year(nome: str) -> int:
    """'2026 Diesel' -> 2026 ; 'Zero KM' -> ano corrente ; senão 0."""
    if "zero" in nome.lower():
        return date.today().year
    m = re.search(r"(?:19|20)\d{2}", nome)
    return int(m.group(0)) if m else 0


def _clean_versao(versao: str, modelo_substr: str) -> str:
    """Remove o nome do modelo da versão pra não duplicar no rótulo.

    'Ranger Raptor 3.0 V6...' + modelo 'Ranger' -> 'Raptor 3.0 V6...'
    (o rótulo final já é 'Ford Ranger {versao}', então repetir polui).
    """
    out = re.sub(rf"\b{re.escape(modelo_substr)}\b", "", versao, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out).strip(" -")
    return out or versao


def _price_to_int(valor_str: str) -> int:
    """'R$ 219.990,00' -> 219990."""
    if not valor_str:
        return 0
    inteiro = valor_str.split(",")[0]
    digits = "".join(c for c in inteiro if c.isdigit())
    return int(digits) if digits else 0


def fetch_fipe_prices(marca: str, modelo_substr: str) -> tuple[list[dict], list[str]]:
    """
    Busca preços FIPE do lineup atual de um modelo.

    Retorna (resultados, erros). Cada resultado é um dict pronto pra virar
    um spec: marca, modelo, versao, campo='preco_fipe', valor, unidade,
    fonte_url (+ codigo_fipe e mes_referencia pra log).
    """
    results: list[dict] = []
    errors: list[str] = []

    code = FIPE_BRAND_CODES.get(marca)
    if not code:
        errors.append(f"FIPE {marca}: marca sem codigo mapeado")
        return results, errors

    try:
        # v2 retorna a lista de modelos direto (sem envelope "modelos").
        models = _get_json(f"{FIPE_BASE}/brands/{code}/models")
    except Exception as e:  # noqa: BLE001 — rede instável é esperado
        errors.append(f"FIPE {marca} modelos: {type(e).__name__}: {str(e)[:60]}")
        return results, errors

    substr = modelo_substr.lower()
    candidates = [m for m in models if substr in m.get("name", "").lower()]
    if not candidates:
        errors.append(f"FIPE {marca} {modelo_substr}: nenhum modelo casou")
        return results, errors

    scanned = 0
    for m in candidates:
        if len(results) >= MAX_VERSIONS_PER_MODEL or scanned >= SCAN_LIMIT:
            break
        model_id = m["code"]

        try:
            anos = _get_json(f"{FIPE_BASE}/brands/{code}/models/{model_id}/years")
            scanned += 1
            time.sleep(REQUEST_PAUSE_S)
        except Exception:  # noqa: BLE001
            continue
        if not anos:
            continue

        ano = anos[0]  # o primeiro é o ano-modelo mais recente
        # A FIPE marca veículos 0km com o código de ano "32000-x". O nome vem
        # como "32000 Diesel", então NÃO dá pra parsear ano do nome (vira 2000).
        # O lineup atual é exatamente o que tem "Zero KM" disponível.
        is_zero_km = str(ano.get("code", "")).startswith(ZERO_KM_PREFIX)
        if not is_zero_km and _parse_year(ano.get("name", "")) < MIN_MODEL_YEAR:
            continue  # versão descontinuada, fora do lineup atual

        try:
            v = _get_json(
                f"{FIPE_BASE}/brands/{code}/models/{model_id}/years/{ano['code']}"
            )
            time.sleep(REQUEST_PAUSE_S)
        except Exception:  # noqa: BLE001
            continue

        preco = _price_to_int(v.get("price", ""))
        if preco < MIN_PRICE_BRL:
            continue

        results.append(
            {
                "marca": marca,
                "modelo": modelo_substr,
                "versao": _clean_versao(
                    v.get("model", m.get("name", "")).strip(), modelo_substr
                ),
                "campo": "preco_fipe",
                "valor": str(preco),
                "unidade": "BRL",
                "fonte_url": (
                    f"{FIPE_BASE}/brands/{code}/models/{model_id}/years/{ano['code']}"
                ),
                "codigo_fipe": v.get("codeFipe", ""),
                "mes_referencia": v.get("referenceMonth", ""),
            }
        )

    if not results and not errors:
        errors.append(
            f"FIPE {marca} {modelo_substr}: 0 precos no lineup atual (>= {MIN_MODEL_YEAR})"
        )
    return results, errors
