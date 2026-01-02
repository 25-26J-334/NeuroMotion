-- Complete database migration script for AI Athlete Trainer
-- This adds support for squats and push-ups
-- Run: mysql -u root -p athlete_trainer < database_migration_complete.sql

USE athlete_trainer;

-- Add total_squats column to sessions table (if not exists)
-- Note: If column already exists, you'll get an error - that's okay, just ignore it
ALTER TABLE sessions 
ADD COLUMN total_squats INT DEFAULT 0;

-- Add total_pushups column to sessions table (if not exists)
ALTER TABLE sessions 
ADD COLUMN total_pushups INT DEFAULT 0;

-- Create squats table (if not exists)
CREATE TABLE IF NOT EXISTS squats (
    squat_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    squat_number INT NOT NULL,
    points INT DEFAULT 0,
    bad_moves INT DEFAULT 0,
    warnings TEXT,
    has_danger BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_timestamp (timestamp)
);

-- Create pushups table (if not exists)
CREATE TABLE IF NOT EXISTS pushups (
    pushup_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    pushup_number INT NOT NULL,
    points INT DEFAULT 0,
    bad_moves INT DEFAULT 0,
    warnings TEXT,
    has_danger BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_timestamp (timestamp)
);

-- Create indexes for better query performance
CREATE INDEX idx_squats_session ON squats(session_id, squat_number);
CREATE INDEX idx_pushups_session ON pushups(session_id, pushup_number);

-- Verify the changes
SELECT 'Migration completed successfully!' as status;
SHOW COLUMNS FROM sessions LIKE 'total_%';
SHOW TABLES LIKE '%squat%' OR '%pushup%';



