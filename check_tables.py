from database import Database

db = Database()
print('Checking database tables...')
tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
for table in tables:
    print(f'Table: {table["name"]}')

print('\nChecking if there are separate exercise tables...')
# Check if jumps, squats, pushups tables exist
for exercise in ['jumps', 'squats', 'pushups']:
    result = db.execute_query(f"SELECT COUNT(*) as count FROM {exercise} LIMIT 1")
    if result:
        print(f'{exercise} table exists with {result[0]["count"]}+ records')
