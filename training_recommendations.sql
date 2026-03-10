-- Training Recommendations Table
CREATE TABLE IF NOT EXISTS training_recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id INTEGER,
    recommendation_type TEXT NOT NULL, -- 'posture_correction', 'endurance', 'strength', 'technique', 'rest'
    priority TEXT NOT NULL, -- 'high', 'medium', 'low'
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    exercise_focus TEXT, -- 'jumps', 'squats', 'pushups', 'all'
    specific_issue TEXT, -- 'knee_valgus', 'forward_lean', 'hip_sag', etc.
    recommendation_text TEXT NOT NULL,
    difficulty_level TEXT, -- 'beginner', 'intermediate', 'advanced'
    estimated_time_minutes INTEGER,
    is_completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_recommendations_user ON training_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_type ON training_recommendations(recommendation_type);
CREATE INDEX IF NOT EXISTS idx_recommendations_priority ON training_recommendations(priority);

-- User Performance Analytics Table
CREATE TABLE IF NOT EXISTS user_performance_analytics (
    analytics_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exercise_type TEXT NOT NULL, -- 'jumps', 'squats', 'pushups'
    total_reps INTEGER DEFAULT 0,
    avg_points_per_rep REAL DEFAULT 0,
    total_bad_moves INTEGER DEFAULT 0,
    bad_move_rate REAL DEFAULT 0, -- percentage
    most_common_issue TEXT,
    improvement_trend TEXT, -- 'improving', 'declining', 'stable'
    performance_score REAL DEFAULT 0, -- 0-100 scale
    recommendations_generated INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_analytics_user_date ON user_performance_analytics(user_id, analysis_date);
