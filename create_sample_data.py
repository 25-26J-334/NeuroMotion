#!/usr/bin/env python3
"""
Create sample training data for testing recommendations
"""

import sqlite3
import os
from datetime import datetime, timedelta

def create_sample_data():
    """Create sample training data for testing"""
    
    db_path = os.path.join(os.path.dirname(__file__), "athlete_trainer.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get first user
        cursor.execute("SELECT user_id FROM users LIMIT 1")
        user_result = cursor.fetchone()
        
        if not user_result:
            print("❌ No users found. Please register first.")
            return
        
        user_id = user_result[0]
        print(f"✅ Creating sample data for user ID: {user_id}")
        
        # Create a sample session
        cursor.execute("""
        INSERT INTO sessions (user_id, start_time, end_time, total_jumps, total_squats, total_pushups, total_points, total_bad_moves)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, datetime.now() - timedelta(hours=1), datetime.now() - timedelta(minutes=30), 
              15, 12, 8, 150, 25))
        
        session_id = cursor.lastrowid
        
        # Create sample jumps with various issues
        jump_data = [
            (1, 10, 0, "None", 0),  # Perfect jump
            (2, 10, 1, "LEFT KNEE VALGUS", 0),  # Knee issue
            (3, 8, 2, "FORWARD LEAN, KNEE OVER TOES", 1),  # Multiple issues
            (4, 10, 0, "None", 0),
            (5, 6, 3, "LEFT KNEE VALGUS, FORWARD LEAN", 1),  # Bad form
            (6, 10, 0, "None", 0),
            (7, 9, 1, "KNEE OVER TOES", 0),
            (8, 10, 0, "None", 0),
            (9, 7, 2, "LEFT KNEE VALGUS", 0),
            (10, 10, 0, "None", 0),
            (11, 8, 1, "FORWARD LEAN", 0),
            (12, 10, 0, "None", 0),
            (13, 5, 4, "LEFT KNEE VALGUS, KNEE OVER TOES, FORWARD LEAN", 1),  # Very bad
            (14, 10, 0, "None", 0),
            (15, 10, 0, "None", 0),
        ]
        
        for jump_num, points, bad_moves, warnings, has_danger in jump_data:
            cursor.execute("""
            INSERT INTO jumps (session_id, jump_number, points, bad_moves, warnings, has_danger, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, jump_num, points, bad_moves, warnings, has_danger, 
                  datetime.now() - timedelta(minutes=(60 - jump_num * 2))))
        
        # Create sample squats
        squat_data = [
            (1, 10, 0, "None", 0),
            (2, 8, 1, "BACK ARCH", 0),
            (3, 6, 2, "BACK ARCH, KNEE OVER TOES", 1),
            (4, 10, 0, "None", 0),
            (5, 7, 1, "KNEE OVER TOES", 0),
            (6, 10, 0, "None", 0),
            (7, 5, 3, "BACK ARCH, KNEE OVER TOES, EXCESSIVE BACK ARCH", 1),
            (8, 10, 0, "None", 0),
            (9, 9, 1, "BACK ARCH", 0),
            (10, 10, 0, "None", 0),
            (11, 8, 1, "KNEE OVER TOES", 0),
            (12, 10, 0, "None", 0),
        ]
        
        for squat_num, points, bad_moves, warnings, has_danger in squat_data:
            cursor.execute("""
            INSERT INTO squats (session_id, squat_number, points, bad_moves, warnings, has_danger, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, squat_num, points, bad_moves, warnings, has_danger,
                  datetime.now() - timedelta(minutes=(55 - squat_num * 2))))
        
        # Create sample pushups
        pushup_data = [
            (1, 10, 0, "None", 0),
            (2, 8, 1, "HIP SAGGING", 0),
            (3, 6, 2, "HIP SAGGING, POOR HEAD POSITION", 1),
            (4, 10, 0, "None", 0),
            (5, 7, 1, "POOR HEAD POSITION", 0),
            (6, 10, 0, "None", 0),
            (7, 5, 2, "HIP SAGGING, BACK ARCH", 1),
            (8, 10, 0, "None", 0),
        ]
        
        for pushup_num, points, bad_moves, warnings, has_danger in pushup_data:
            cursor.execute("""
            INSERT INTO pushups (session_id, pushup_number, points, bad_moves, warnings, has_danger, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, pushup_num, points, bad_moves, warnings, has_danger,
                  datetime.now() - timedelta(minutes=(50 - pushup_num * 2))))
        
        conn.commit()
        conn.close()
        
        print("✅ Sample training data created successfully!")
        print("📊 Data summary:")
        print(f"  - Session ID: {session_id}")
        print(f"  - Jumps: 15 (25 bad moves total)")
        print(f"  - Squats: 12 (12 bad moves total)")
        print(f"  - Pushups: 8 (8 bad moves total)")
        print(f"  - Common issues: KNEE VALGUS, BACK ARCH, HIP SAGGING")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")

if __name__ == "__main__":
    create_sample_data()
