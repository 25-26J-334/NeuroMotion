import sys
import os
from database import Database
import bcrypt

def verify_auth():
    print("🔍 Verifying Authentication Logic...")
    db = Database()
    
    if not db.is_connected():
        print("❌ Database connection failed!")
        return
    
    test_user = "tester_" + os.urandom(4).hex()
    test_pass = "password123"
    test_email = f"{test_user}@example.com"
    
    print(f"\n1. Testing Registration for {test_user}...")
    user_id = db.register_user(test_user, test_email, test_pass, "Test User", 25)
    
    if user_id:
        print(f"   ✅ Registered with ID: {user_id}")
    else:
        print("   ❌ Registration failed!")
        return

    print("\n2. Testing Authentication with correct credentials...")
    user = db.authenticate_user(test_user, test_pass)
    if user and user['user_id'] == user_id:
        print("   ✅ Authentication successful!")
    else:
        print("   ❌ Authentication failed!")

    print("\n3. Testing Authentication with incorrect password...")
    user_wrong = db.authenticate_user(test_user, "wrongpass")
    if user_wrong is None:
        print("   ✅ Rejected incorrect password!")
    else:
        print("   ❌ Accepted incorrect password!")

    print("\n4. Testing duplicate registration...")
    dup_id = db.register_user(test_user, test_email, "anotherpass", "Dup User", 30)
    if dup_id is None:
        print("   ✅ Rejected duplicate registration!")
    else:
        print("   ❌ Allowed duplicate registration!")

    db.close()
    print("\nVerification Complete!")

if __name__ == "__main__":
    # Mock streamlit st.error
    import streamlit as st
    st.error = lambda x: print(f"ST_ERROR: {x}")
    
    verify_auth()
