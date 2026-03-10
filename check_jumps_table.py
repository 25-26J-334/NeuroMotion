from database import Database

db = Database()

print('Jumps table structure:')
jumps_sample = db.execute_query('SELECT * FROM jumps LIMIT 3')
if jumps_sample:
    print('Columns:', list(jumps_sample[0].keys()))
    for jump in jumps_sample:
        print(f'Jump: {jump}')

print('\nSquats table structure:')
squats_sample = db.execute_query('SELECT * FROM squats LIMIT 3')
if squats_sample:
    print('Columns:', list(squats_sample[0].keys()))
    for squat in squats_sample:
        print(f'Squat: {squat}')

print('\nSession 51 jumps details:')
session_51_jumps = db.execute_query('SELECT * FROM jumps WHERE session_id = 51')
for jump in session_51_jumps:
    print(f'Jump {jump["jump_number"]}: {jump["points"]} points, {jump["bad_moves"]} bad moves')

print('\nSession 52 squats details:')
session_52_squats = db.execute_query('SELECT * FROM squats WHERE session_id = 52')
for squat in session_52_squats:
    print(f'Squat {squat["squat_number"]}: {squat["points"]} points, {squat["bad_moves"]} bad moves')
