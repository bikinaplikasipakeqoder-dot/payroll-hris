-- Migration: Add audit columns to employee_salary_history
-- Tracks who created/updated each salary record and when.

ALTER TABLE employee_salary_history ADD COLUMN created_by INTEGER REFERENCES users(id);
ALTER TABLE employee_salary_history ADD COLUMN updated_by INTEGER REFERENCES users(id);

-- Backfill existing migration records with a default system user if desired.
-- (Leaves NULL if no user is available; UI will display '-'.)
