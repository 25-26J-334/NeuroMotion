# Database Migration Instructions

## Why the Error Happened

The errors you're seeing (`Unknown column 'total_squats'` and `Unknown column 'total_pushups'`) happen because:
- The database schema doesn't have these columns yet
- The code is trying to use columns that don't exist
- You need to run the migration scripts to add them

## How to Fix It

### Option 1: Run the Complete Migration Script (Recommended)

```bash
mysql -u root -p athlete_trainer < database_migration_complete.sql
```

When prompted, enter your MySQL root password.

### Option 2: Run Individual Migration Scripts

```bash
# Run squat migration
mysql -u root -p athlete_trainer < database_migration_squats.sql

# Run push-up migration
mysql -u root -p athlete_trainer < database_migration_pushups.sql
```

### Option 3: Run Manually in MySQL

1. Open MySQL command line or phpMyAdmin
2. Select the `athlete_trainer` database
3. Run these SQL commands:

```sql
USE athlete_trainer;

-- Add columns to sessions table
ALTER TABLE sessions ADD COLUMN total_squats INT DEFAULT 0;
ALTER TABLE sessions ADD COLUMN total_pushups INT DEFAULT 0;

-- Create squats table
CREATE TABLE IF NOT EXISTS squats (
    squat_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    squat_number INT NOT NULL,
    points INT DEFAULT 0,
    bad_moves INT DEFAULT 0,
    warnings TEXT,
    has_danger BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_timestamp (timestamp)
);

-- Create pushups table
CREATE TABLE IF NOT EXISTS pushups (
    pushup_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    pushup_number INT NOT NULL,
    points INT DEFAULT 0,
    bad_moves INT DEFAULT 0,
    warnings TEXT,
    has_danger BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_timestamp (timestamp)
);

-- Create indexes
CREATE INDEX idx_squats_session ON squats(session_id, squat_number);
CREATE INDEX idx_pushups_session ON pushups(session_id, pushup_number);
```

## Verify Migration Success

After running the migration, verify it worked:

```sql
USE athlete_trainer;

-- Check if columns exist
SHOW COLUMNS FROM sessions;

-- Check if tables exist
SHOW TABLES;
```

You should see:
- `total_squats` column in `sessions` table
- `total_pushups` column in `sessions` table
- `squats` table exists
- `pushups` table exists

## After Migration

1. **Restart Streamlit** (if it's running):
   - Stop the current app (Ctrl+C)
   - Run: `streamlit run app.py`

2. **Test the Dashboard**:
   - Go to Dashboard page
   - Errors should be gone
   - All charts should load properly

3. **Test Leaderboards**:
   - Go to Leaderboard page
   - Check all 4 tabs (Jumps, Squats, Push-ups, Overall)

## Troubleshooting

### Error: "Column already exists"
- This is okay! It means the column was already added
- You can ignore this error and continue

### Error: "Table already exists"
- This is okay! It means the table was already created
- You can ignore this error and continue

### Error: "Access denied"
- Make sure you're using the correct MySQL username and password
- Try: `mysql -u root -p` (enter password when prompted)

### Still Getting Errors?
1. Make sure MySQL is running
2. Make sure you're connected to the correct database (`athlete_trainer`)
3. Check that the migration script ran successfully
4. Restart Streamlit after migration



