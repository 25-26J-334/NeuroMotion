from database import Database

db = Database()

session_id = 57

print(f"=== Checking Session {session_id} Details ===")

# Check session details
session = db.execute_query("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
if session:
    s = session[0]
    print(f"Session {s['session_id']}: User ID {s['user_id']}")
    print(f"  Totals: J={s['total_jumps']}, S={s['total_squats']}, P={s['total_pushups']}")
    print(f"  Points: {s['total_points']}, Bad: {s['total_bad_moves']}")
    print(f"  Start: {s['start_time']}, End: {s['end_time'] or 'NOT SET'}")

# Check what's actually in exercise tables
print(f"\n=== Exercise Records for Session {session_id} ===")

jumps = db.execute_query("SELECT COUNT(*) as count, SUM(points) as points, SUM(bad_moves) as bad FROM jumps WHERE session_id = ?", (session_id,))
squats = db.execute_query("SELECT COUNT(*) as count, SUM(points) as points, SUM(bad_moves) as bad FROM squats WHERE session_id = ?", (session_id,))
pushups = db.execute_query("SELECT COUNT(*) as count, SUM(points) as points, SUM(bad_moves) as bad FROM pushups WHERE session_id = ?", (session_id,))

print(f"Jumps table: {jumps[0]['count'] or 0} records, {jumps[0]['points'] or 0} points, {jumps[0]['bad'] or 0} bad moves")
print(f"Squats table: {squats[0]['count'] or 0} records, {squats[0]['points'] or 0} points, {squats[0]['bad'] or 0} bad moves")
print(f"Pushups table: {pushups[0]['count'] or 0} records, {pushups[0]['points'] or 0} points, {pushups[0]['bad'] or 0} bad moves")

# Show individual records if any exist
if jumps[0]['count'] > 0:
    print(f"\nJump records:")
    jump_records = db.execute_query("SELECT jump_number, points, bad_moves, timestamp FROM jumps WHERE session_id = ? ORDER BY jump_number", (session_id,))
    for j in jump_records:
        print(f"  Jump {j['jump_number']}: {j['points']} points, {j['bad_moves']} bad moves at {j['timestamp']}")

if squats[0]['count'] > 0:
    print(f"\nSquat records:")
    squat_records = db.execute_query("SELECT squat_number, points, bad_moves, timestamp FROM squats WHERE session_id = ? ORDER BY squat_number", (session_id,))
    for s in squat_records:
        print(f"  Squat {s['squat_number']}: {s['points']} points, {s['bad_moves']} bad moves at {s['timestamp']}")

if pushups[0]['count'] > 0:
    print(f"\nPushup records:")
    pushup_records = db.execute_query("SELECT pushup_number, points, bad_moves, timestamp FROM pushups WHERE session_id = ? ORDER BY pushup_number", (session_id,))
    for p in pushup_records:
        print(f"  Pushup {p['pushup_number']}: {p['points']} points, {p['bad_moves']} bad moves at {p['timestamp']}")
