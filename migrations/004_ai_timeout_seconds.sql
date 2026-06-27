-- Migration: Add configurable timeout for AI provider requests
-- Default 9 seconds keeps calls under Vercel Hobby's 10s serverless limit.

ALTER TABLE ai_settings ADD COLUMN timeout_seconds INTEGER DEFAULT 9;

-- Backfill existing settings to 9 seconds if null.
UPDATE ai_settings SET timeout_seconds = 9 WHERE timeout_seconds IS NULL;
