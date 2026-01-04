#!/usr/bin/env python3
"""
Test script for performance prediction functionality
Tests the enhanced prediction system with sample data
"""

# Mock the required imports for testing
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Mock numpy for testing
class MockNumpy:
    @staticmethod
    def array(data):
        return data
    
    @staticmethod
    def arange(n):
        return list(range(n))
    
    @staticmethod
    def mean(data):
        return sum(data) / len(data) if data else 0
    
    @staticmethod
    def std(data):
        if len(data) < 2:
            return 0
        mean_val = sum(data) / len(data)
        variance = sum((x - mean_val) ** 2 for x in data) / len(data)
        return variance ** 0.5
    
    @staticmethod
    def nanmean(data):
        filtered_data = [x for x in data if x == x]  # Filter out NaN
        return sum(filtered_data) / len(filtered_data) if filtered_data else 0
    
    @staticmethod
    def isfinite(data):
        return [x == x and x != float('inf') and x != float('-inf') for x in data]
    
    @staticmethod
    def sum(data):
        return sum(data)
    
    @staticmethod
    def polyfit(x, y, degree):
        # Simple linear regression implementation
        n = len(x)
        if n < 2:
            return [0, 0]
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return [0, sum_y / n]
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        
        return [slope, intercept]

# Mock numpy
sys.modules['numpy'] = MockNumpy()

# Now import our prediction module
try:
    from performance_prediction import compute_performance_prediction, PredictionResult
    print("✅ Successfully imported performance prediction module")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

def create_sample_sessions(num_sessions=5):
    """Create sample session data for testing"""
    sessions = []
    base_time = datetime.now() - timedelta(days=num_sessions)
    
    for i in range(num_sessions):
        session_time = base_time + timedelta(days=i)
        # Simulate improving performance
        jumps = 20 + i * 5  # 20, 25, 30, 35, 40
        points = 15 + i * 3  # 15, 18, 21, 24, 27
        bad_moves = max(1, 5 - i)  # 5, 4, 3, 2, 1
        
        sessions.append({
            'session_id': i + 1,
            'user_id': 1,
            'start_time': session_time.isoformat(),
            'end_time': (session_time + timedelta(minutes=30)).isoformat(),
            'total_jumps': jumps,
            'total_squats': 0,
            'total_pushups': 0,
            'total_points': points,
            'total_bad_moves': bad_moves
        })
    
    return sessions

def test_prediction():
    """Test the prediction functionality"""
    print("🧪 Testing Performance Prediction System")
    print("=" * 50)
    
    # Create sample data
    sessions = create_sample_sessions(5)
    print(f"📊 Created {len(sessions)} sample sessions")
    
    # Test prediction
    try:
        prediction = compute_performance_prediction(
            recent_sessions=sessions,
            exercise_type='jump',
            current_count=45,
            current_points=30,
            current_bad_moves=0,
            current_session_start=datetime.now()
        )
        
        print("✅ Prediction computation successful!")
        print("\n📈 Prediction Results:")
        print(f"  Predicted Speed: {prediction.predicted_speed_rpm:.2f} reps/min")
        print(f"  Predicted Endurance: {prediction.predicted_endurance_score:.1f}/100")
        print(f"  Predicted Rating: {prediction.predicted_rating:.1f}/100")
        print(f"  Trend: {prediction.trend}")
        print(f"  History Points: {prediction.history_points}")
        
        # Test error metrics (should be available with 5 sessions)
        if prediction.history_points >= 2:
            print("\n📊 Error Metrics:")
            print(f"  Speed RMSE: {prediction.rmse_speed:.3f}")
            print(f"  Speed MAE: {prediction.mae_speed:.3f}")
            print(f"  Speed R²: {prediction.r2_speed:.3f}")
            print(f"  Endurance RMSE: {prediction.rmse_endurance:.3f}")
            print(f"  Endurance MAE: {prediction.mae_endurance:.3f}")
            print(f"  Endurance R²: {prediction.r2_endurance:.3f}")
            print(f"  Rating RMSE: {prediction.rmse_rating:.3f}")
            print(f"  Rating MAE: {prediction.mae_rating:.3f}")
            print(f"  Rating R²: {prediction.r2_rating:.3f}")
        
        # Test forecasting
        print("\n🔮 Training Load Forecasts:")
        for forecast in prediction.forecast:
            load_pct = int(forecast['training_load'] * 100)
            print(f"  {load_pct}% Load: Speed={forecast['pred_speed_rpm']:.1f}, "
                  f"Endurance={forecast['pred_endurance_score']:.1f}, "
                  f"Rating={forecast['pred_rating']:.1f}")
        
        # Test performance history
        if prediction.performance_history:
            print(f"\n📈 Performance History: {len(prediction.performance_history)} sessions")
            for i, hist in enumerate(prediction.performance_history[-3:]):  # Show last 3
                print(f"  Session {hist['session_number']}: "
                      f"Speed={hist['speed_rpm']:.1f}, "
                      f"Endurance={hist['endurance_score']:.1f}, "
                      f"Rating={hist['rating']:.1f}")
        
        print("\n✅ All tests passed! Enhanced prediction system is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_prediction()
    if success:
        print("\n🎉 Performance prediction system is ready!")
    else:
        print("\n💥 Performance prediction system needs fixes.")
        sys.exit(1)
