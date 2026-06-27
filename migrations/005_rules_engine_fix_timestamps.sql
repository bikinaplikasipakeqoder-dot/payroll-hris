-- Migration: Fix rule_variables missing timestamp columns
-- Recreate the table because SQLite/Turso does not support adding columns
-- with CURRENT_TIMESTAMP default on ALTER TABLE.

CREATE TABLE IF NOT EXISTS rule_variables_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_code TEXT UNIQUE NOT NULL,
    variable_name TEXT NOT NULL,
    variable_type TEXT NOT NULL,
    source_table TEXT,
    source_field TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_rule_variables_variable_type CHECK (variable_type IN ('EMPLOYEE_FIELD', 'CALCULATED', 'SYSTEM_CONSTANT'))
);

INSERT INTO rule_variables_new (
    id, variable_code, variable_name, variable_type, source_table, source_field, description, is_active
)
SELECT
    id, variable_code, variable_name, variable_type, source_table, source_field, description, is_active
FROM rule_variables;

DROP TABLE rule_variables;

ALTER TABLE rule_variables_new RENAME TO rule_variables;
-- Migration: Add missing timestamp columns to rule_variables
-- The RuleVariable model inherits from TimestampMixin and expects created_at/updated_at.

ALTER TABLE rule_variables ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE rule_variables ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;
