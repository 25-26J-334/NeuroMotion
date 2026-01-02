# Quick Start Guide

## Step 1: Install MySQL

If you don't have MySQL installed:
- **Windows**: Download from [MySQL Downloads](https://dev.mysql.com/downloads/installer/)
- **Mac**: `brew install mysql` or download installer
- **Linux**: `sudo apt-get install mysql-server` (Ubuntu/Debian)

Start MySQL service:
```bash
# Windows (as Administrator)
net start MySQL80

# Mac/Linux
sudo systemctl start mysql
# or
sudo service mysql start
```

## Step 2: Create Database

**Option A: Using the setup script**
```bash
# Edit setup_database.py and update MySQL password
python setup_database.py
```

**Option B: Manual setup**
```bash
mysql -u root -p < database_setup.sql
```

## Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Configure Database Connection

Create `.streamlit` folder in your project directory:
```bash
mkdir .streamlit
```

Create `.streamlit/secrets.toml` file:
```toml
[mysql]
host = "localhost"
database = "athlete_trainer"
user = "root"
password = "your_mysql_password"
port = 3306
```

**Note**: Replace `your_mysql_password` with your actual MySQL root password.

## Step 5: Run the Application

```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

## First Time Usage

1. Enter your **name** and **age** when prompted
2. Choose **Upload Video** or **Use Camera**
3. For video: Upload a video file and click "Start Processing"
4. For camera: Click "Start Camera" and allow browser permissions
5. Wait for calibration (30 frames)
6. Start jumping!

## Troubleshooting

### Database Connection Error
- Verify MySQL is running: `mysql -u root -p`
- Check credentials in `.streamlit/secrets.toml`
- Ensure database exists: `SHOW DATABASES;`

### Camera Not Working
- Grant browser camera permissions
- Try a different browser (Chrome/Firefox recommended)
- Check if camera is used by another app

### Video Upload Issues
- Supported formats: MP4, AVI, MOV, MKV
- Ensure video shows person clearly
- Try smaller video files first

### Import Errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

## Next Steps

- View **Leaderboard** to see top performers
- Check **Dashboard** for statistics and charts
- Start a new session anytime from the sidebar
- All your data is automatically saved to the database!









