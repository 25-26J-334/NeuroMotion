from database import Database

db = Database()

print("=== Recent Sessions (All Users) ===")
query = """
SELECT 
    s.session_id,
    u.name,
    s.start_time,
    s.end_time,
    s.total_jumps,
    s.total_squats,
    s.total_pushups,
    s.total_points,
    s.total_bad_moves
FROM sessions s
JOIN users u ON s.user_id = u.user_id
WHERE s.total_squats > 0
ORDER BY s.session_id DESC
LIMIT 10
"""

sessions = db.execute_query(query)
for s in sessions:
    print(f"Session {s['session_id']}: {s['name']} - {s['total_squats']} squats, {s['total_points']} points, {s['total_bad_moves']} bad moves")
    print(f"  Start: {s['start_time']}, End: {s['end_time']}")

print("\n=== Recent Squat Records ===")
query = """
SELECT 
    sq.squat_id,
    sq.session_id,
    u.name,
    sq.squat_number,
    sq.points,
    sq.bad_moves,
    sq.timestamp
FROM squats sq
JOIN sessions s ON sq.session_id = s.session_id
JOIN users u ON s.user_id = u.user_id
ORDER BY sq.squat_id DESC
LIMIT 20
"""

squats = db.execute_query(query)
for sq in squats:
    print(f"Squat {sq['squat_id']}: {sq['name']} - Session {sq['session_id']}, Rep {sq['squat_number']}, {sq['points']} points, {sq['bad_moves']} bad moves")
    print(f"  Time: {sq['timestamp']}")

print("\n=== Check for Incomplete Sessions ===")
query = """
SELECT 
    s.session_id,
    u.name,
    s.start_time,
    s.end_time,
    s.total_squats
FROM sessions s
JOIN users u ON s.user_id = u.user_id
WHERE s.total_squats > 0 AND s.end_time IS NULL
ORDER BY s.session_id DESC
"""

incomplete = db.execute_query(query)
if incomplete:
    print("Found incomplete sessions:")
    for s in incomplete:
        print(f"Session {s['session_id']}: {s['name']} - {s['total_squats']} squats, started {s['start_time']}, no end time")
else:
    print("No incomplete sessions found")
