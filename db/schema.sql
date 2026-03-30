-- Ford Intelligence OS - Database Schema
-- Decisions from /plan-eng-review 2026-03-28
--
-- DATA FLOW:
-- .com.br sites → scraper → vehicle_spec (Module 1)
-- Ford CSV       → ETL    → retention_vehicles (Module 2)
-- Bridge: JOIN vehicle_spec + retention_vehicles via modelo

-- ============================================================
-- MODULE 1: Competitive Radar
-- ============================================================

CREATE TABLE IF NOT EXISTS vehicle_spec (
    id              SERIAL PRIMARY KEY,
    marca           VARCHAR(100) NOT NULL,   -- ex: "Toyota", "Ford", "Mitsubishi"
    modelo          VARCHAR(100) NOT NULL,   -- ex: "Hilux", "Ranger", "L200 Triton"
    versao          VARCHAR(200) NOT NULL,   -- ex: "Raptor", "Limited", "XLS"
    mercado         VARCHAR(10) NOT NULL DEFAULT 'BR',  -- always 'BR' for MVP
    campo           VARCHAR(200) NOT NULL,   -- ex: "potencia", "torque", "suspensao"
    valor           TEXT,                    -- NULL means "data not available"
    unidade         VARCHAR(50),             -- ex: "cv", "kgfm", "mm"
    fonte_url       TEXT NOT NULL,           -- source URL (mandatory)
    extraido_em     TIMESTAMP NOT NULL DEFAULT NOW(),
    verificado      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Prevent duplicate entries for same spec
    UNIQUE(marca, modelo, versao, mercado, campo)
);

-- Spec change history (for change alerts)
CREATE TABLE IF NOT EXISTS spec_changes (
    id              SERIAL PRIMARY KEY,
    spec_id         INTEGER REFERENCES vehicle_spec(id),
    campo           VARCHAR(200) NOT NULL,
    valor_anterior  TEXT,
    valor_novo      TEXT,
    detectado_em    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- MODULE 2: Retention Engine
-- ============================================================

CREATE TABLE IF NOT EXISTS retention_vehicles (
    id                          SERIAL PRIMARY KEY,
    vehicle_id                  VARCHAR(100) NOT NULL UNIQUE,  -- anonymized VIN
    cliente_id                  VARCHAR(100) NOT NULL,         -- synthetic customer ID
    modelo                      VARCHAR(100) NOT NULL,         -- ex: "Ranger"
    versao                      VARCHAR(200),                  -- ex: "Raptor"
    ano_fabricacao               INTEGER,
    data_venda                  DATE,
    concessionaria_id           VARCHAR(50),

    -- Service history (aggregated)
    ultima_visita_paga          DATE,            -- NULL = never had paid service
    ultima_visita_qualquer      DATE,            -- includes warranty/recall
    tipo_ultimo_servico         VARCHAR(50),     -- 'pago', 'garantia', 'recall'
    qtd_visitas_pagas_2_anos    INTEGER DEFAULT 0,
    km_estimado                 INTEGER,         -- estimated from service records

    -- Connected vehicle (conditional)
    connected_vehicle_available BOOLEAN DEFAULT FALSE,
    sinal_falha_ativo           BOOLEAN DEFAULT FALSE,
    km_real_odometro            INTEGER,

    -- LGPD
    lgpd_consent                BOOLEAN NOT NULL DEFAULT FALSE,

    -- Churn score (calculated)
    churn_score                 INTEGER,         -- 0-100, calculated by scorer
    score_calculado_em          TIMESTAMP,

    created_at                  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Template history
CREATE TABLE IF NOT EXISTS templates_gerados (
    id              SERIAL PRIMARY KEY,
    vehicle_id      VARCHAR(100) REFERENCES retention_vehicles(vehicle_id),
    template_texto  TEXT NOT NULL,
    diferencial_competitivo TEXT,  -- from Module 1 via bridge JOIN
    aprovado        BOOLEAN DEFAULT FALSE,
    aprovado_em     TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEXES (from /plan-eng-review Issue 5A)
-- ============================================================

-- Module 1: fast spec lookups
CREATE INDEX IF NOT EXISTS idx_spec_marca_modelo
    ON vehicle_spec(marca, modelo, versao, mercado);

CREATE INDEX IF NOT EXISTS idx_spec_modelo_campo
    ON vehicle_spec(modelo, campo);

-- Module 2: fast retention queries
CREATE INDEX IF NOT EXISTS idx_retention_score
    ON retention_vehicles(churn_score DESC);

CREATE INDEX IF NOT EXISTS idx_retention_modelo
    ON retention_vehicles(modelo);

CREATE INDEX IF NOT EXISTS idx_retention_consent
    ON retention_vehicles(lgpd_consent) WHERE lgpd_consent = TRUE;

-- Change alerts
CREATE INDEX IF NOT EXISTS idx_changes_date
    ON spec_changes(detectado_em DESC);

-- ============================================================
-- STALENESS CHECK (from /plan-eng-review Issue 4A)
-- Records with extraido_em > 14 days → verificado = false
-- Run as a scheduled job or trigger
-- ============================================================

CREATE OR REPLACE FUNCTION mark_stale_specs() RETURNS void AS $$
BEGIN
    UPDATE vehicle_spec
    SET verificado = FALSE, updated_at = NOW()
    WHERE extraido_em < NOW() - INTERVAL '14 days'
    AND verificado = TRUE;
END;
$$ LANGUAGE plpgsql;
