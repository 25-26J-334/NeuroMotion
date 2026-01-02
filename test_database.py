"""
Test script for database.py
Run this to test your database connection and operations
"""
import sys
import os

# Mock Streamlit secrets if running outside Streamlit
if 'streamlit' not in sys.modules:
    class MockSecrets:
        def __getitem__(self, key):
            raise KeyError("No secrets file")
    
    class MockStreamlit:
        def __init__(self):
            self.secrets = MockSecrets()
        
        def error(self, msg):
            print(f"ERROR: {msg}")
    
    import streamlit
    streamlit.st = MockStreamlit()
    sys.modules['streamlit'] = streamlit

from database import Database

def test_database():
    """Test database connection and basic operations"""
    print("🔍 Testing Database Connection...")
    print("-" * 50)
    
    # Initialize database
    db = Database()
    
    # Check connection
    if not db.is_connected():
        print("❌ Database connection failed!")
        print("\nPlease check:")
        print("1. Run: python setup_database.py (to create the database)")
        print("2. Make sure you have write permissions in the directory")
        print("3. Optional: Create .streamlit/secrets.toml with custom database path")
        print("\nExample secrets.toml (optional):")
        print("""
[sqlite]
database_path = "athlete_trainer.db"
        """)
        print(f"\nDefault database path: {db.db_path}")
        return False
    
    print("✅ Database connected successfully!")
    print("-" * 50)
    
    # Test queries
    print("\n📊 Testing database operations...")
    
    # Test: Get overall stats
    print("\n1. Testing get_overall_stats()...")
    stats = db.get_overall_stats()
    if stats:
        print(f"   ✅ Total Participants: {stats['total_participants']}")
        print(f"   ✅ Total Sessions: {stats['total_sessions']}")
        print(f"   ✅ Total Jumps: {stats['total_jumps']}")
        print(f"   ✅ Total Points: {stats['total_points']}")
    else:
        print("   ⚠️  No stats found (database might be empty)")
    
    # Test: Get leaderboard
    print("\n2. Testing get_leaderboard()...")
    leaderboard = db.get_leaderboard(limit=5)
    if leaderboard:
        print(f"   ✅ Found {len(leaderboard)} users in leaderboard")
        for i, user in enumerate(leaderboard[:3], 1):
            print(f"   {i}. {user.get('name', 'Unknown')} - {user.get('total_points', 0)} points")
    else:
        print("   ⚠️  Leaderboard is empty (no users yet)")
    
    # Test: Create a test user (optional)
    print("\n3. Testing create_user()...")
    try:
        test_user_id = db.create_user("Test User", 25)
        if test_user_id:
            print(f"   ✅ Test user created with ID: {test_user_id}")
            
            # Test: Get user stats
            print("\n4. Testing get_user_stats()...")
            user_stats = db.get_user_stats(test_user_id)
            if user_stats:
                print(f"   ✅ User stats retrieved successfully")
                print(f"      Sessions: {user_stats['total_sessions']}")
                print(f"      Jumps: {user_stats['total_jumps']}")
                print(f"      Points: {user_stats['total_points']}")
        else:
            print("   ❌ Failed to create test user")
    except Exception as e:
        print(f"   ⚠️  Could not create test user: {e}")
    
    # Close connection
    db.close()
    print("\n" + "-" * 50)
    print("✅ Database test complete!")
    return True

if __name__ == "__main__":
    try:
        test_database()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

