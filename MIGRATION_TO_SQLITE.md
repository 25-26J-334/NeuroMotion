# Migration from MySQL to SQLite

This document summarizes the migration from MySQL to SQLite database.

## What Changed

### 1. Database Module (`database.py`)
- **Before**: Used `mysql.connector` to connect to MySQL server
- **After**: Uses built-in `sqlite3` module (no external dependencies)
- **Changes**:
  - Parameter placeholders changed from `%s` to `?` (SQLite syntax)
  - Connection method changed to file-based SQLite connection
  - Date functions updated (DATE_SUB replaced with Python timedelta)
  - Boolean values converted to integers (0/1) for SQLite compatibility
  - Row factory set to return dictionary-like results

### 2. Database Setup
- **Before**: `database_setup.sql` (MySQL syntax)
- **After**: `database_setup_sqlite.sql` (SQLite syntax)
- **Changes**:
  - `AUTO_INCREMENT` → `INTEGER PRIMARY KEY AUTOINCREMENT`
  - `VARCHAR` → `TEXT`
  - `BOOLEAN` → `INTEGER` (0/1)
  - `TIMESTAMP` → `TIMESTAMP` (SQLite compatible)
  - Removed `USE DATABASE` (not needed in SQLite)
  - Foreign keys enabled via `PRAGMA foreign_keys = ON`

### 3. Setup Script (`setup_database.py`)
- **Before**: Required MySQL server connection
- **After**: Creates SQLite database file directly
- **Changes**:
  - No server required - creates local `.db` file
  - Simpler setup process
  - No credentials needed

### 4. Configuration
- **Before**: Required MySQL credentials in `.streamlit/secrets.toml`
- **After**: Optional - database path can be specified, defaults to `athlete_trainer.db` in source directory
- **Changes**:
  - Secrets file is now optional
  - Default database location: `source/athlete_trainer.db`
  - Custom path can be set via secrets file if needed

### 5. Dependencies (`requirements.txt`)
- **Removed**: `mysql-connector-python>=8.2.0`
- **Added**: Nothing (SQLite is built into Python)

### 6. Helper Scripts
- **`create_secrets.py`**: Updated to create SQLite configuration (optional)
- **`test_database.py`**: Updated error messages for SQLite

## Benefits of SQLite

1. **No Server Required**: SQLite is file-based, no database server needed
2. **Simpler Setup**: Just run `python setup_database.py` - no MySQL installation
3. **Portable**: Database is a single file that can be easily backed up or moved
4. **Zero Configuration**: Works out of the box with default settings
5. **Perfect for Development**: Ideal for local development and testing
6. **Built-in**: No additional dependencies required

## Migration Steps

If you have existing MySQL data, you would need to:
1. Export data from MySQL
2. Convert data format (if needed)
3. Import into SQLite

However, for a fresh start:
1. Run `python setup_database.py` to create the SQLite database
2. Start using the application - no other setup needed!

## File Locations

- **Database file**: `source/athlete_trainer.db` (created automatically)
- **Schema file**: `source/database_setup_sqlite.sql`
- **Setup script**: `source/setup_database.py`

## Notes

- SQLite is perfect for single-user or small-scale applications
- For production with high concurrency, consider PostgreSQL or MySQL
- Database file can be easily backed up by copying the `.db` file
- All existing functionality remains the same - only the database backend changed

