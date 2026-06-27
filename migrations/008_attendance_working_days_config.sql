CREATE TABLE IF NOT EXISTS attendance_working_days_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    working_days INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_awdc_month CHECK (month >= 1 AND month <= 12),
    CONSTRAINT ck_awdc_working_days CHECK (working_days >= 0 AND working_days <= 31),
    CONSTRAINT uq_awdc_company_year_month UNIQUE (company_id, year, month)
);
