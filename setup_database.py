"""
Database setup helper script for SQLite
Run this to create the database and tables
"""
import sqlite3
import sys
import time
import os

def print_step(message):
    """Print a step message with timestamp"""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")
    sys.stdout.flush()

def setup_database():
    """Create database and tables"""
    try:
        print_step("=" * 60)
        print_step("AI Athlete Trainer - SQLite Database Setup")
        print_step("=" * 60)
        
        # Determine database path
        db_path = os.path.join(os.path.dirname(__file__), "athlete_trainer.db")
        print_step(f"Step 1/4: Database will be created at: {db_path}")
        
        # Connect to SQLite (creates file if it doesn't exist)
        print_step("Step 2/4: Connecting to SQLite database...")
        connection = sqlite3.connect(db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        
        if connection:
            print_step("✓ Connected to SQLite database successfully")
            cursor = connection.cursor()
            
            # Read SQL file
            print_step("Step 3/4: Reading database_setup_sqlite.sql file...")
            sql_file = os.path.join(os.path.dirname(__file__), 'database_setup_sqlite.sql')
            try:
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                print_step("✓ SQL file loaded successfully")
            except FileNotFoundError:
                print_step("❌ ERROR: database_setup_sqlite.sql file not found!")
                print_step("Make sure database_setup_sqlite.sql is in the same directory")
                return
            except Exception as e:
                print_step(f"❌ ERROR reading SQL file: {e}")
                return
            
            # Execute SQL statements
            print_step("Step 4/4: Creating tables and indexes...")
            
            # Split script into individual statements
            statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
            
            executed = 0
            skipped = 0
            
            for statement in statements:
                try:
                    cursor.execute(statement)
                    executed += 1
                except sqlite3.OperationalError as e:
                    error_msg = str(e).lower()
                    if "already exists" in error_msg or "duplicate" in error_msg:
                        skipped += 1
                    else:
                        print_step(f"    ⚠ Warning: {e}")
                        skipped += 1
                except Exception as e:
                    print_step(f"    ⚠ Warning: {e}")
                    skipped += 1
            
            # Commit changes
            connection.commit()
            print_step(f"✓ Successfully executed {executed} operations")
            if skipped > 0:
                print_step(f"⚠ Skipped {skipped} operations (already exist)")
            
            # Verify tables
            print_step("\nVerifying database structure...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            print_step(f"✓ Found {len(table_names)} tables: {', '.join(table_names)}")
            
            # Check sessions table columns
            cursor.execute("PRAGMA table_info(sessions)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            print_step(f"✓ Sessions table has {len(column_names)} columns")
            if 'total_squats' in column_names and 'total_pushups' in column_names:
                print_step("✓ Squat and push-up columns present")
            
            cursor.close()
            connection.close()
            
            print_step("=" * 60)
            print_step("✅ Database setup complete!")
            print_step("=" * 60)
            print_step(f"\nDatabase file: {db_path}")
            print_step("\nYou can now run: streamlit run app.py")
            
    except sqlite3.Error as e:
        print_step("=" * 60)
        print_step(f"❌ SQLite Error: {e}")
        print_step("=" * 60)
        print_step("\nTroubleshooting:")
        print_step("1. Make sure you have write permissions in the directory")
        print_step("2. Check if the database file is locked by another process")
    except FileNotFoundError as e:
        print_step("=" * 60)
        print_step(f"❌ File Error: {e}")
        print_step("=" * 60)
        print_step("Make sure database_setup_sqlite.sql is in the same directory")
    except Exception as e:
        print_step("=" * 60)
        print_step(f"❌ Unexpected Error: {e}")
        print_step("=" * 60)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_database()
