# Ford Intelligence OS

## What is this
Platform that connects competitive vehicle intelligence (Module 1) with customer retention (Module 2) for Ford Brazil. Built for the Ford x Universidade 2026 challenge.

## Architecture
- **Module 1 (Competitive Radar):** Dynamic scraper discovers current models from manufacturer sites (.com.br), stores in PostgreSQL `vehicle_spec` table (EAV model), exposes via NL-to-SQL query interface
- **Module 2 (Retention Engine):** Rule-based churn scoring (0-100) on Ford vehicle fleet, generates personalized WhatsApp templates
- **The Bridge:** JOIN between `vehicle_spec` and `retention_vehicles` via `modelo` field — competitive intelligence feeds retention messaging

## Key commands
```bash
# Run dashboard
python3 -m streamlit run app/main.py

# Run scraper (discovers current models dynamically — no year hardcoded)
python3 -m scraper.smart_scraper

# Generate synthetic data + load into DB + score
python3 scripts/generate_and_load.py

# Run tests
python3 -m pytest tests/ -v

# Score vehicles only
python3 scripts/run_churn_scorer.py --threshold 70
```

## Project structure
```
app/           → Streamlit dashboard (main.py + pages/)
bridge/        → Template generator connecting Module 1 + 2
db/            → PostgreSQL schema + connection
ingestion/     → CSV → PostgreSQL pipeline
nl_query/      → NL question → SQL → execute
scoring/       → Churn risk scorer (rule-based v1)
scraper/       → smart_scraper.py — dynamic 2-step scraper
data/synthetic → Synthetic dataset generator
scripts/       → CLI utilities
tests/         → pytest test suite (97 tests)
```

## Scraper — how it works
Two-step dynamic scraper (`scraper/smart_scraper.py`):
1. **Discovery:** fetches catalog page of each brand, finds all current model URLs via regex
2. **Extraction:** for each discovered model, extracts specs via regex from body text

Brands covered: VW (11 models), Toyota (15 models), Mitsubishi (1), Ford (blocked — see below)

**Ford.com.br anti-bot:** ford.com.br uses Cloudflare WAF that returns 403 for all headless browsers. Ford data is sourced from carrosnaweb.com.br (public FIPE ficha tecnica). In production, use Ford Developer Portal API instead.

## Environment
Requires `.env` with: `DATABASE_URL`, `OPENAI_API_KEY`, `LLM_MODEL`
Copy from `.env.example`.

LLM_MODEL=gpt-5.4-nano

## Database
PostgreSQL with 4 tables: `vehicle_spec`, `spec_changes`, `retention_vehicles`, `templates_gerados`.
Schema at `db/schema.sql`.

Current state: ~94 specs (Ford 36 real + scraped VW/Toyota/Mitsubishi), 100 retention vehicles.

## NL Query — EAV model (IMPORTANT)
The vehicle_spec table uses Entity-Attribute-Value model.
There are NO columns named potencia, torque, etc.
Columns are: marca, modelo, versao, mercado, campo, valor, unidade, fonte_url, extraido_em.
To get potencia: WHERE campo = 'potencia' → read valor column.
The system prompt explicitly explains this to prevent LLM from generating vs.potencia errors.

## Important constraints
- LGPD: always filter `lgpd_consent = TRUE` on retention queries
- NULL handling: `ultima_visita_paga = NULL` means max churn risk (+40pts)
- SQL sanitizer: only SELECT/WITH allowed, blocks DDL/DML/injection
- Template reviewer: compares numbers in LLM output vs input fields
- Market filter: always `mercado = 'BR'` on spec queries
- NL→SQL: always use simple row-based results, never pivot/crosstab

## Deployment
- GitHub: https://github.com/carloscandeira/ford-intelligence-os
- Streamlit Cloud: https://carloscandeira-ford-intelligence-os-appmain-uykdq8.streamlit.app
