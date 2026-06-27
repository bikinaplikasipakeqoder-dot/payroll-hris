-- Add interest_rate column to kasbon_requests.
-- Existing records default to 0.00% interest.
ALTER TABLE kasbon_requests ADD COLUMN interest_rate NUMERIC(5, 2) NOT NULL DEFAULT 0.00;
