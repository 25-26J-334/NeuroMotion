from report_generator import ReportGenerator
import os

def test_rich_report():
    print("Testing Rich Report Generation...")
    
    # Mock data
    user_name = "Test Athlete"
    stats = {
        'total_sessions': 15,
        'total_points': 4500,
        'total_exercises': 1200,
        'total_jumps': 200,
        'total_squats': 400,
        'total_pushups': 300,
        'total_burpees': 150,
        'total_stepups': 150
    }
    ai_insights = """
    ## Performance Highlights
    Your jump explosive power is improving! You've shown consistent growth in squat depth.
    
    ## Areas for Improvement
    Focus on maintaining a straight back during push-ups. Your burpee transition speed can be optimized.
    
    ## Recommended Routine
    - 3 sets of 20 explosive jumps
    - 4 sets of 15 deep squats
    """
    
    report_gen = ReportGenerator()
    try:
        filepath, filename = report_gen.create_rich_report(user_name, stats, ai_insights)
        print(f"SUCCESS: Report generated at {filepath}")
        
        if os.path.exists(filepath):
            print(f"Verified: File exists ({os.path.getsize(filepath)} bytes)")
            # In a real test, we would open and check content, but here we just verify creation
        else:
            print("FAILURE: File was not created.")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_rich_report()
