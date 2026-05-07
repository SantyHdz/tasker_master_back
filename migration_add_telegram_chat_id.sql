-- Migration to add telegram_chat_id column to users table
-- Run this script using: psql DATABASE_URL -f migration_add_telegram_chat_id.sql

-- Add telegram_chat_id column to users table
ALTER TABLE users
ADD COLUMN telegram_chat_id VARCHAR(100) NULL;

-- Create index for faster lookups by telegram_chat_id
CREATE INDEX idx_users_telegram_chat_id ON users(telegram_chat_id)
WHERE telegram_chat_id IS NOT NULL;

-- Comment the column for documentation
COMMENT ON COLUMN users.telegram_chat_id IS 'Telegram chat ID for sending notifications to this user';