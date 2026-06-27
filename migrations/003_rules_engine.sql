-- Migration: Rules Engine and Dynamic Configuration System

CREATE TABLE IF NOT EXISTS rule_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_code TEXT UNIQUE NOT NULL,
    category_name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rule_configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    rule_code TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    formula TEXT,
    value DECIMAL(18,2),
    min_value DECIMAL(18,2),
    max_value DECIMAL(18,2),
    rate DECIMAL(10,4),
    effective_date DATE NOT NULL,
    expiry_date DATE,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    description TEXT,
    created_by INTEGER,
    updated_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES rule_categories(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id),
    UNIQUE (company_id, rule_code, effective_date)
);

CREATE TABLE IF NOT EXISTS rule_variables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_code TEXT UNIQUE NOT NULL,
    variable_name TEXT NOT NULL,
    variable_type TEXT NOT NULL,
    source_table TEXT,
    source_field TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS rule_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by INTEGER NOT NULL,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    FOREIGN KEY (rule_id) REFERENCES rule_configurations(id),
    FOREIGN KEY (changed_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_rule_configurations_lookup ON rule_configurations(company_id, rule_code, is_active, effective_date, expiry_date);
CREATE INDEX IF NOT EXISTS idx_rule_configurations_category ON rule_configurations(category_id);
CREATE INDEX IF NOT EXISTS idx_rule_audit_logs_rule ON rule_audit_logs(rule_id, changed_at DESC);

-- Seed default categories
INSERT INTO rule_categories (category_code, category_name, description) VALUES
('BPJS', 'BPJS Configuration', 'Rates and ceilings for BPJS Kesehatan, JHT, JP, JKK, JKM'),
('PPH21', 'PPh 21 Configuration', 'Tax brackets, TER brackets, and PTKP values'),
('OVERTIME', 'Overtime Configuration', 'Overtime multipliers and hourly divisor'),
('ALLOWANCE', 'Allowance Configuration', 'Formula-based allowance calculation rules')
ON CONFLICT(category_code) DO NOTHING;

-- Seed default variables
INSERT INTO rule_variables (variable_code, variable_name, variable_type, source_table, source_field, description) VALUES
('basic_salary', 'Basic Salary', 'EMPLOYEE_FIELD', 'employees', 'base_salary', 'Employee base salary'),
('ptkp_status', 'PTKP Status', 'EMPLOYEE_FIELD', 'employees', 'ptkp_status', 'Employee PTKP status'),
('ptkp_value', 'PTKP Value', 'CALCULATED', NULL, NULL, 'Annual PTKP threshold based on ptkp_status'),
('bpjs_base', 'BPJS Base', 'CALCULATED', NULL, NULL, 'BPJS calculation base (salary + eligible allowances)'),
('monthly_gross', 'Monthly Gross Income', 'CALCULATED', NULL, NULL, 'Total monthly gross income')
ON CONFLICT(variable_code) DO NOTHING;
