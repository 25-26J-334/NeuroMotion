-- Database migration script to add squat support
-- Run this script to add squats table and update sessions table
-- Run: mysql -u root -p athlete_trainer < database_migration_squats.sql

USE athlete_trainer;

-- Add total_squats column to sessions table
-- Note: IF NOT EXISTS is not supported in ALTER TABLE for MySQL < 8.0
-- If column already exists, you'll get an error - that's okay, just ignore it
ALTER TABLE sessions 
ADD COLUMN total_squats INT DEFAULT 0;

-- Create squats table (similar to jumps table)
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

-- Create index for better query performance
-- Note: IF NOT EXISTS is not supported in CREATE INDEX for MySQL < 8.0
-- If index already exists, you'll get an error - that's okay, just ignore it
CREATE INDEX idx_squats_session ON squats(session_id, squat_number);

