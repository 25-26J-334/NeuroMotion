from database import Database

db = Database()

# Get all sessions for debugging
query = """
SELECT 
    s.session_id,
    u.name,
    s.total_jumps,
    s.total_squats, 
    s.total_pushups,
    s.total_points,
    s.total_bad_moves,
    s.start_time,
    s.end_time
FROM sessions s
JOIN users u ON s.user_id = u.user_id
WHERE u.name = 'Leasha'
ORDER BY s.session_id
"""

sessions = db.execute_query(query)
print('All sessions for Leasha:')
for s in sessions:
    print(f"Session {s['session_id']}: Jumps={s['total_jumps']}, Squats={s['total_squats']}, Pushups={s['total_pushups']}, Points={s['total_points']}, Bad={s['total_bad_moves']}")

print("\n" + "="*50)
print("Now checking what each leaderboard sees:")

print("\nJump Leaderboard data:")
jump_lb = db.get_leaderboard(limit=5, exercise_type='jump')
for entry in jump_lb:
    print(f"{entry['name']}: {entry['total_count']} jumps, {entry['total_points']} points, {entry['total_bad_moves']} bad moves, {entry['total_sessions']} sessions")

print("\nSquat Leaderboard data:")
squat_lb = db.get_leaderboard(limit=5, exercise_type='squat')
for entry in squat_lb:
    print(f"{entry['name']}: {entry['total_count']} squats, {entry['total_points']} points, {entry['total_bad_moves']} bad moves, {entry['total_sessions']} sessions")
