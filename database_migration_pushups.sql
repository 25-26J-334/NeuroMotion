-- Database migration script to add push-up support
-- Run this script to add pushups table and update sessions table
-- Run: mysql -u root -p athlete_trainer < database_migration_pushups.sql

USE athlete_trainer;

-- Add total_pushups column to sessions table
-- Note: IF NOT EXISTS is not supported in ALTER TABLE for MySQL < 8.0
-- If column already exists, you'll get an error - that's okay, just ignore it
ALTER TABLE sessions 
ADD COLUMN total_pushups INT DEFAULT 0;

-- Create pushups table (similar to jumps and squats tables)
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

-- Create index for better query performance
-- Note: IF NOT EXISTS is not supported in CREATE INDEX for MySQL < 8.0
-- If index already exists, you'll get an error - that's okay, just ignore it
CREATE INDEX idx_pushups_session ON pushups(session_id, pushup_number);




