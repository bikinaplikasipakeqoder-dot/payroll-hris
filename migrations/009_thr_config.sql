-- THR company configuration and join-date calculation support

CREATE TABLE IF NOT EXISTS thr_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL UNIQUE,
    payment_mode VARCHAR(20) NOT NULL DEFAULT 'BY_RELIGION',
    unified_holiday VARCHAR(20) NOT NULL DEFAULT 'IDUL_FITRI',
    full_tenure_months INTEGER NOT NULL DEFAULT 12,
    min_tenure_months INTEGER NOT NULL DEFAULT 1,
    prorate_partial_months BOOLEAN NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id),
    CONSTRAINT ck_thr_configs_payment_mode CHECK (payment_mode IN ('BY_RELIGION', 'UNIFIED')),
    CONSTRAINT ck_thr_configs_unified_holiday CHECK (unified_holiday IN ('IDUL_FITRI', 'CHRISTMAS', 'NYEPI', 'WAISAK')),
    CONSTRAINT ck_thr_configs_full_tenure CHECK (full_tenure_months >= 1),
    CONSTRAINT ck_thr_configs_min_tenure CHECK (min_tenure_months >= 0)
);

-- Insert default config for company 1 if not exists
INSERT OR IGNORE INTO thr_configs (company_id, payment_mode, unified_holiday)
SELECT 1, 'BY_RELIGION', 'IDUL_FITRI'
WHERE EXISTS (SELECT 1 FROM companies WHERE id = 1);
