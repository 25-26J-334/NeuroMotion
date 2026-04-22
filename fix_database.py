"""
Quick script to add missing tables to existing database
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "athlete_trainer.db")

if not os.path.exists(db_path):
    print(f"Database not found at: {db_path}")
    exit(1)

print(f"Connecting to: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add training_recommendations table
cursor.execute("""
CREATE TABLE IF NOT EXISTS training_recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id INTEGER,
    recommendation_type TEXT NOT NULL,
    priority TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    exercise_focus TEXT,
    specific_issue TEXT,
    recommendation_text TEXT NOT NULL,
    difficulty_level TEXT,
    estimated_time_minutes INTEGER,
    is_completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE SET NULL
);
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_user ON training_recommendations(user_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_type ON training_recommendations(recommendation_type);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_priority ON training_recommendations(priority);")

# Add user_performance_analytics table
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_performance_analytics (
    analytics_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exercise_type TEXT NOT NULL,
    total_reps INTEGER DEFAULT 0,
    avg_points_per_rep REAL DEFAULT 0,
    total_bad_moves INTEGER DEFAULT 0,
    bad_move_rate REAL DEFAULT 0,
    most_common_issue TEXT,
    improvement_trend TEXT,
    performance_score REAL DEFAULT 0,
    recommendations_generated INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_user_date ON user_performance_analytics(user_id, analysis_date);")

conn.commit()

# Verify
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print(f"\n✅ Tables in database: {', '.join(tables)}")

if 'training_recommendations' in tables and 'user_performance_analytics' in tables:
    print("\n✅ Missing tables added successfully!")
else:
    print("\n❌ Failed to add some tables")

conn.close()
