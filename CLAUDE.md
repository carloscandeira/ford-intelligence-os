# Ford Intelligence OS

## What is this
Platform that connects competitive vehicle intelligence (Module 1) with customer retention (Module 2) for Ford Brazil. Built for the Ford x Universidade 2026 challenge.

## Architecture
- **Module 1 (Competitive Radar):** Scrapes Brazilian manufacturer sites (.com.br) for pickup specs, stores in PostgreSQL `vehicle_spec` table, exposes via NL-to-SQL query interface
- **Module 2 (Retention Engine):** Rule-based churn scoring (0-100) on Ford vehicle fleet, generates personalized WhatsApp templates
- **The Bridge:** JOIN between `vehicle_spec` and `retention_vehicles` via `modelo` field — competitive intelligence feeds retention messaging

## Key commands
```bash
# Generate synthetic data + load into DB + score
python scripts/generate_and_load.py

# Run dashboard
streamlit run app/main.py

# Run tests
pytest tests/ -v

# Run scraper (real sites — use synthetic for dev)
python -m scraper.spec_scraper

# Score vehicles only
python scripts/run_churn_scorer.py --threshold 70
```

## Project structure
```
app/           → Streamlit dashboard (main.py + pages/)
bridge/        → Template generator connecting Module 1 + 2
db/            → PostgreSQL schema + connection
ingestion/     → CSV → PostgreSQL pipeline
nl_query/      → NL question → SQL → execute
scoring/       → Churn risk scorer (rule-based v1)
scraper/       → Playwright-based spec scraper
data/synthetic → Synthetic dataset generator
scripts/       → CLI utilities
tests/         → pytest test suite
```

## Environment
Requires `.env` with: `DATABASE_URL`, `OPENAI_API_KEY`, `LLM_MODEL`
Copy from `.env.example`.

## Database
PostgreSQL with 4 tables: `vehicle_spec`, `spec_changes`, `retention_vehicles`, `templates_gerados`.
Schema at `db/schema.sql`.

## Important constraints
- LGPD: always filter `lgpd_consent = TRUE` on retention queries
- NULL handling: `ultima_visita_paga = NULL` means max churn risk (+40pts)
- SQL sanitizer: only SELECT/WITH allowed, blocks DDL/DML/injection
- Template reviewer: compares numbers in LLM output vs input fields
- Market filter: always `mercado = 'BR'` on spec queries
