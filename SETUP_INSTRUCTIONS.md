# Setup Instructions - Fix Database Connection

## Quick Fix Steps

### Step 1: Create the Database

Open your terminal/command prompt and run:

```bash
mysql -u root -p < database_setup.sql
```

Or if MySQL root has no password:
```bash
mysql -u root < database_setup.sql
```

**Alternative:** Use the setup script (edit password first):
```bash
# Edit setup_database.py and change the password on line 10
python setup_database.py
```

### Step 2: Create Secrets File

1. Create a folder named `.streamlit` in your project directory:
   ```
   C:\Users\Gunarakulan\Desktop\ai-athlete-trainer\source\.streamlit
   ```

2. Create a file named `secrets.toml` inside the `.streamlit` folder

3. Add this content (replace with your MySQL password):
```toml
[mysql]
host = "localhost"
database = "athlete_trainer"
user = "root"
password = "your_mysql_password_here"
port = 3306
```

**If MySQL root has no password**, use:
```toml
[mysql]
host = "localhost"
database = "athlete_trainer"
user = "root"
password = ""
port = 3306
```

### Step 3: Verify MySQL is Running

```bash
# Windows
net start MySQL80

# Check if running
mysql -u root -p
```

### Step 4: Restart Streamlit

1. Stop the current Streamlit app (Ctrl+C)
2. Run again:
```bash
streamlit run app.py
```

## Troubleshooting

### Error: "Unknown database 'athlete_trainer'"
**Solution:** Run `database_setup.sql` to create the database

### Error: "Access denied for user"
**Solution:** Check your MySQL password in `secrets.toml`

### Error: "Can't connect to MySQL server"
**Solution:** 
- Make sure MySQL service is running
- Check if MySQL is on port 3306
- Verify host is "localhost"

### File Path Issues (Windows)
The secrets file should be at:
```
C:\Users\Gunarakulan\Desktop\ai-athlete-trainer\source\.streamlit\secrets.toml
```

Create the `.streamlit` folder if it doesn't exist!

## Manual Database Creation

If the SQL file doesn't work, create manually:

1. Open MySQL:
```bash
mysql -u root -p
```

2. Run these commands:
```sql
CREATE DATABASE IF NOT EXISTS athlete_trainer;
USE athlete_trainer;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    total_jumps INT DEFAULT 0,
    total_points INT DEFAULT 0,
    total_bad_moves INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS jumps (
    jump_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    jump_number INT NOT NULL,
    points INT DEFAULT 0,
    bad_moves INT DEFAULT 0,
    warnings TEXT,
    has_danger BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);
```

## Still Having Issues?

1. Check MySQL is installed and running
2. Verify database exists: `SHOW DATABASES;`
3. Check tables exist: `USE athlete_trainer; SHOW TABLES;`
4. Verify secrets.toml file location and content
5. Restart Streamlit after making changes









