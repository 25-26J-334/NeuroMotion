-- Database setup script for AI Athlete Trainer (SQLite)
-- Run this script to create the database and tables

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_name ON users(name);

-- Training sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    total_jumps INTEGER DEFAULT 0,
    total_squats INTEGER DEFAULT 0,
    total_pushups INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    total_bad_moves INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_start_time ON sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_sessions_user_time ON sessions(user_id, start_time);

-- Individual jumps table
CREATE TABLE IF NOT EXISTS jumps (
    jump_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    jump_number INTEGER NOT NULL,
    points INTEGER DEFAULT 0,
    bad_moves INTEGER DEFAULT 0,
    warnings TEXT,
    has_danger INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_session_id ON jumps(session_id);
CREATE INDEX IF NOT EXISTS idx_timestamp ON jumps(timestamp);
CREATE INDEX IF NOT EXISTS idx_jumps_session ON jumps(session_id, jump_number);

-- Squats table
CREATE TABLE IF NOT EXISTS squats (
    squat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    squat_number INTEGER NOT NULL,
    points INTEGER DEFAULT 0,
    bad_moves INTEGER DEFAULT 0,
    warnings TEXT,
    has_danger INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_squats_session_id ON squats(session_id);
CREATE INDEX IF NOT EXISTS idx_squats_timestamp ON squats(timestamp);
CREATE INDEX IF NOT EXISTS idx_squats_session ON squats(session_id, squat_number);

-- Pushups table
CREATE TABLE IF NOT EXISTS pushups (
    pushup_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    pushup_number INTEGER NOT NULL,
    points INTEGER DEFAULT 0,
    bad_moves INTEGER DEFAULT 0,
    warnings TEXT,
    has_danger INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pushups_session_id ON pushups(session_id);
CREATE INDEX IF NOT EXISTS idx_pushups_timestamp ON pushups(timestamp);
CREATE INDEX IF NOT EXISTS idx_pushups_session ON pushups(session_id, pushup_number);

