#!/usr/bin/env python3
"""
Setup training recommendations tables in the database
"""

import sqlite3
import os

def setup_recommendations_tables():
    """Create training recommendations and analytics tables"""
    
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), "athlete_trainer.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Read and execute the SQL file
        sql_file = os.path.join(os.path.dirname(__file__), "training_recommendations.sql")
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        # Execute all SQL statements
        cursor.executescript(sql_script)
        conn.commit()
        
        print("✅ Training recommendations tables created successfully!")
        print("📊 Tables added:")
        print("   - training_recommendations")
        print("   - user_performance_analytics")
        
    except Exception as e:
        print(f"❌ Error setting up recommendations tables: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_recommendations_tables()
