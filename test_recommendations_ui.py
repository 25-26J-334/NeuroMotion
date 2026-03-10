#!/usr/bin/env python3
"""
Test the recommendations UI directly
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from recommendations_ui import recommendations_page
from database import Database

def test_recommendations_ui():
    """Test the recommendations UI"""
    
    print("🧪 Testing Recommendations UI...")
    
    # Initialize database
    db = Database()
    if not db.is_connected():
        print("❌ Database connection failed")
        return
    
    # Get a test user
    users = db.execute_query("SELECT user_id, name FROM users LIMIT 1")
    if not users:
        print("❌ No users found in database. Please register first.")
        return
    
    test_user = users[0]
    user_id = test_user['user_id']
    user_name = test_user['name']
    
    print(f"✅ Testing with user: {user_name} (ID: {user_id})")
    
    # Set up session state (simulating Streamlit)
    class MockSessionState:
        def __init__(self):
            self.user_id = user_id
            self.user_name = user_name
            self.page = 'recommendations'
    
    # Mock streamlit
    import streamlit as st
    st.session_state = MockSessionState()
    
    try:
        # Test getting recommendations (without rendering UI)
        from recommendation_engine import RecommendationEngine
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(user_id)
        
        print(f"✅ Generated {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            priority_emoji = "🔴" if rec.get('priority') == 'high' else "🟡" if rec.get('priority') == 'medium' else "🟢"
            print(f"  {i}. {priority_emoji} {rec.get('title', 'No title')}")
        
        print("✅ Recommendations UI test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing recommendations UI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_recommendations_ui()
