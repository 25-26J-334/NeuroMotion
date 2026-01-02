#!/usr/bin/env python3
"""
Check database tables
"""

import sqlite3
import os

def check_database():
    """Check what tables exist in the database"""
    
    db_path = os.path.join(os.path.dirname(__file__), "athlete_trainer.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📊 Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if jumps table exists and get its structure
        if any('jumps' in table[0] for table in tables):
            print("\n✅ Jumps table found!")
            cursor.execute("PRAGMA table_info(jumps)")
            columns = cursor.fetchall()
            print("Jumps table structure:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("\n❌ Jumps table NOT found!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_database()
