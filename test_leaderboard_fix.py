from database import Database

db = Database()

print("=== Testing Fixed Leaderboard Logic ===\n")

# Test jump leaderboard
print("Jump Leaderboard (should only show users who did jumps):")
jump_leaderboard = db.get_leaderboard(limit=5, exercise_type='jump')
for entry in jump_leaderboard:
    print(f"  {entry['name']}: {entry['total_count']} jumps, {entry['total_points']} points")

print("\nSquat Leaderboard (should only show users who did squats):")
squat_leaderboard = db.get_leaderboard(limit=5, exercise_type='squat')
for entry in squat_leaderboard:
    print(f"  {entry['name']}: {entry['total_count']} squats, {entry['total_points']} points")

print("\nPushup Leaderboard (should only show users who did pushups):")
pushup_leaderboard = db.get_leaderboard(limit=5, exercise_type='pushup')
for entry in pushup_leaderboard:
    print(f"  {entry['name']}: {entry['total_count']} pushups, {entry['total_points']} points")

print("\nOverall Leaderboard (should show all users):")
overall_leaderboard = db.get_leaderboard(limit=5, exercise_type='all')
for entry in overall_leaderboard:
    print(f"  {entry['name']}: {entry['total_count']} total exercises, {entry['total_points']} points")
