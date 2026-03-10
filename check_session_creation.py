from database import Database
from datetime import datetime, timedelta

db = Database()

print("=== All Recent Sessions (Last 24 Hours) ===")
cutoff_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
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
    s.total_bad_moves,
    CASE 
        WHEN s.end_time IS NULL THEN 'INCOMPLETE'
        WHEN s.total_jumps = 0 AND s.total_squats = 0 AND s.total_pushups = 0 THEN 'EMPTY'
        ELSE 'COMPLETE'
    END as status
FROM sessions s
JOIN users u ON s.user_id = u.user_id
WHERE s.start_time >= ?
ORDER BY s.session_id DESC
"""

sessions = db.execute_query(query, (cutoff_time,))
for s in sessions:
    print(f"Session {s['session_id']}: {s['name']} - Status: {s['status']}")
    print(f"  Exercises: J={s['total_jumps']}, S={s['total_squats']}, P={s['total_pushups']}")
    print(f"  Points: {s['total_points']}, Bad: {s['total_bad_moves']}")
    print(f"  Start: {s['start_time']}")
    if s['end_time']:
        print(f"  End: {s['end_time']}")
    else:
        print(f"  End: NOT SET")
    print()

print("=== Sessions with Zero Exercises (Possible Failed Attempts) ===")
query = """
SELECT 
    s.session_id,
    u.name,
    s.start_time,
    s.end_time
FROM sessions s
JOIN users u ON s.user_id = u.user_id
WHERE s.start_time >= ?
AND s.total_jumps = 0 
AND s.total_squats = 0 
AND s.total_pushups = 0
ORDER BY s.session_id DESC
"""

empty_sessions = db.execute_query(query, (cutoff_time,))
if empty_sessions:
    for s in empty_sessions:
        print(f"Empty Session {s['session_id']}: {s['name']} - Start: {s['start_time']}, End: {s['end_time'] or 'NOT SET'}")
else:
    print("No empty sessions found")

print("\n=== User Activity Summary ===")
query = """
SELECT 
    u.name,
    COUNT(s.session_id) as total_sessions,
    COUNT(CASE WHEN s.total_squats > 0 THEN 1 END) as squat_sessions,
    SUM(s.total_squats) as total_squats
FROM users u
LEFT JOIN sessions s ON u.user_id = s.user_id AND s.start_time >= ?
GROUP BY u.user_id, u.name
ORDER BY total_squats DESC
"""

users = db.execute_query(query, (cutoff_time,))
for u in users:
    if u['total_sessions'] > 0:
        print(f"{u['name']}: {u['total_sessions']} sessions, {u['squat_sessions']} squat sessions, {u['total_squats']} total squats")
