-- MySQL Command Line Setup Script
-- Copy and paste this entire script into MySQL command line
-- Run: mysql -u root -p < mysql_command_line.sql
-- OR paste directly into MySQL prompt

CREATE DATABASE IF NOT EXISTS athlete_trainer;
USE athlete_trainer;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);

-- Training sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    total_jumps INT DEFAULT 0,
    total_points INT DEFAULT 0,
    total_bad_moves INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_start_time (start_time)
);

-- Individual jumps table
CREATE TABLE IF NOT EXISTS jumps (
    jump_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    jump_number INT NOT NULL,
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
CREATE INDEX idx_sessions_user_time ON sessions(user_id, start_time);
CREATE INDEX idx_jumps_session ON jumps(session_id, jump_number);

-- Verify tables were created
SHOW TABLES;









