#!/usr/bin/env python3
"""
Test script for the recommendation system
"""

from recommendation_engine import RecommendationEngine
from database import Database

def test_recommendation_system():
    """Test the recommendation system with sample data"""
    
    print("🧪 Testing Recommendation System...")
    
    # Initialize database
    db = Database()
    if not db.is_connected():
        print("❌ Database connection failed")
        return
    
    # Get a test user (first user in database)
    users = db.execute_query("SELECT user_id, name FROM users LIMIT 1")
    if not users:
        print("❌ No users found in database. Please register first.")
        return
    
    test_user = users[0]
    user_id = test_user['user_id']
    user_name = test_user['name']
    
    print(f"✅ Testing with user: {user_name} (ID: {user_id})")
    
    # Initialize recommendation engine
    engine = RecommendationEngine()
    
    # Analyze user performance
    print("📊 Analyzing user performance...")
    performance = engine.analyze_user_performance(user_id)
    
    if performance:
        print("✅ Performance analysis completed:")
        for exercise_type, data in performance.items():
            if isinstance(data, dict) and 'total_reps' in data:
                print(f"  - {exercise_type.title()}: {data['total_reps']} reps, "
                      f"Score: {data.get('performance_score', 0):.1f}")
                if data.get('most_common_issue'):
                    print(f"    Common issue: {data['most_common_issue']}")
    else:
        print("ℹ️ No performance data found (user hasn't trained yet)")
    
    # Generate recommendations
    print("\n🎯 Generating recommendations...")
    recommendations = engine.generate_recommendations(user_id)
    
    if recommendations:
        print(f"✅ Generated {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations[:5], 1):  # Show first 5
            priority_emoji = "🔴" if rec.get('priority') == 'high' else "🟡" if rec.get('priority') == 'medium' else "🟢"
            print(f"  {i}. {priority_emoji} {rec.get('title', 'No title')}")
            print(f"     Type: {rec.get('recommendation_type', 'N/A')}")
            print(f"     Exercise: {rec.get('exercise_focus', 'N/A')}")
            print(f"     Description: {rec.get('description', 'N/A')[:80]}...")
            print()
    else:
        print("ℹ️ No recommendations generated (need more training data)")
    
    # Test database retrieval
    print("💾 Testing database retrieval...")
    db_recommendations = db.get_user_recommendations(user_id)
    
    if db_recommendations:
        print(f"✅ Retrieved {len(db_recommendations)} recommendations from database")
    else:
        print("ℹ️ No recommendations found in database")
    
    print("\n🎉 Recommendation system test completed!")

if __name__ == "__main__":
    test_recommendation_system()
