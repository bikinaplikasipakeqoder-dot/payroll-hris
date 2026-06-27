-- Migration: Employee base salary history (Effective Date pattern)
-- Creates history table and seeds existing employee base salaries as initial records.

CREATE TABLE IF NOT EXISTS employee_salary_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    base_salary NUMERIC(15, 2) NOT NULL,
    effective_date DATE NOT NULL,
    end_date DATE,
    notes TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    CONSTRAINT ck_employee_salary_history_amount CHECK (base_salary >= 0),
    CONSTRAINT ck_employee_salary_history_dates CHECK (end_date IS NULL OR end_date >= effective_date),
    CONSTRAINT uq_employee_salary_history_emp_date UNIQUE (employee_id, effective_date)
);

CREATE INDEX IF NOT EXISTS idx_employee_salary_history_employee ON employee_salary_history(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_salary_history_effective ON employee_salary_history(employee_id, effective_date);

-- Seed existing employee base salaries as history records effective from date_joined.
-- If date_joined is missing, fall back to 2024-01-01.
INSERT INTO employee_salary_history (employee_id, base_salary, effective_date, notes, is_active)
SELECT
    id,
    COALESCE(base_salary, 0),
    COALESCE(date_joined, '2024-01-01'),
    'Gaji pokok awal (migrasi)',
    1
FROM employees
WHERE base_salary IS NOT NULL
ON CONFLICT(employee_id, effective_date) DO UPDATE SET
    base_salary = excluded.base_salary,
    notes = excluded.notes,
    is_active = excluded.is_active;
