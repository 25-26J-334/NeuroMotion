"""
Database connection and operations for AI Athlete Trainer
SQLite version
"""
import sqlite3
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import streamlit as st
import os

class Database:
    def __init__(self, db_path: str = None):
        """Initialize database connection using SQLite"""
        self.connection = None
        self.db_path = db_path or self._get_db_path()
        if self.connect():
            self._migrate_users_table()
            self._migrate_exercises_tables()
    
    def _get_db_path(self) -> str:
        """Get database path from secrets or use default"""
        try:
            # Try to get path from Streamlit secrets
            return st.secrets.get("sqlite", {}).get("database_path", "athlete_trainer.db")
        except (KeyError, FileNotFoundError, AttributeError):
            # Fallback to default path in source directory
            return os.path.join(os.path.dirname(__file__), "athlete_trainer.db")
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Use row factory to get dictionary-like results
            self.connection.row_factory = sqlite3.Row
            return True
        except Exception as e:
            self.connection = None
            return False
    
    def is_connected(self):
        """Check if database is connected"""
        return self.connection is not None
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        """Execute a query and return results"""
        if not self.is_connected():
            return None
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            
            # Only commit for INSERT/UPDATE/DELETE queries
            query_upper = query.strip().upper()
            if any(query_upper.startswith(cmd) for cmd in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']):
                self.connection.commit()
            
            # Fetch results if needed
            if fetch:
                results = cursor.fetchall()
                # Convert Row objects to dictionaries
                return [dict(row) for row in results]
            else:
                return cursor.rowcount
        except Exception as e:
            try:
                st.error(f"Query execution error: {e}")
            except:
                print(f"Query execution error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def _migrate_exercises_tables(self):
        """Add columns and tables for new exercises dynamically"""
        if not self.is_connected():
            return
        
        cursor = self.connection.cursor()
        
        # 1. Add total_burpees to sessions
        cursor.execute("PRAGMA table_info(sessions)")
        session_columns = [row[1] for row in cursor.fetchall()]
        if 'total_burpees' not in session_columns:
            self.execute_query("ALTER TABLE sessions ADD COLUMN total_burpees INTEGER DEFAULT 0", fetch=False)
            
        # 2. Create burpees table if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='burpees'")
        if not cursor.fetchone():
            burpee_sql = """
            CREATE TABLE burpees (
                burpee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                burpee_number INTEGER NOT NULL,
                points INTEGER DEFAULT 0,
                bad_moves INTEGER DEFAULT 0,
                warnings TEXT,
                has_danger INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
            CREATE INDEX idx_burpees_session_id ON burpees(session_id);
            CREATE INDEX idx_burpees_timestamp ON burpees(timestamp);
            CREATE INDEX idx_burpees_session ON burpees(session_id, burpee_number);
            """
            self.connection.executescript(burpee_sql)
            
        # 3. Add total_stepups to sessions
        if 'total_stepups' not in session_columns:
            self.execute_query("ALTER TABLE sessions ADD COLUMN total_stepups INTEGER DEFAULT 0", fetch=False)
            
        # 4. Create stepups table if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stepups'")
        if not cursor.fetchone():
            stepup_sql = """
            CREATE TABLE stepups (
                stepup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                stepup_number INTEGER NOT NULL,
                points INTEGER DEFAULT 0,
                bad_moves INTEGER DEFAULT 0,
                warnings TEXT,
                has_danger INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
            CREATE INDEX idx_stepups_session_id ON stepups(session_id);
            CREATE INDEX idx_stepups_timestamp ON stepups(timestamp);
            CREATE INDEX idx_stepups_session ON stepups(session_id, stepup_number);
            """
            self.connection.executescript(stepup_sql)
            
        # 5. Create biometric tracking tables
        self._create_biometric_tables()
            
        if self.connection:
            self.connection.commit()
    
    def _create_biometric_tables(self):
        """Create tables for biometric tracking data"""
        if not self.is_connected():
            return
        
        cursor = self.connection.cursor()
        
        # Create user biometric profiles table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_biometric_profiles'")
        if not cursor.fetchone():
            # Create table first
            self.connection.execute("""
            CREATE TABLE user_biometric_profiles (
                profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                age INTEGER NOT NULL,
                weight REAL NOT NULL,
                height REAL NOT NULL,
                gender TEXT NOT NULL,
                fitness_level TEXT NOT NULL,
                resting_heart_rate INTEGER,
                max_heart_rate INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            """)
            # Then create index
            self.connection.execute("CREATE INDEX idx_biometric_profiles_user_id ON user_biometric_profiles(user_id)")
        
        # Create biometric sessions table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='biometric_sessions'")
        if not cursor.fetchone():
            # Create table first
            self.connection.execute("""
            CREATE TABLE biometric_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                training_session_id INTEGER,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_minutes REAL,
                total_calories_burned REAL DEFAULT 0,
                avg_heart_rate INTEGER,
                max_heart_rate INTEGER,
                avg_exertion_level TEXT,
                recovery_time_minutes INTEGER,
                recovery_type TEXT,
                recovery_recommendation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (training_session_id) REFERENCES sessions(session_id) ON DELETE SET NULL
            )
            """)
            # Then create indexes
            self.connection.execute("CREATE INDEX idx_biometric_sessions_user_id ON biometric_sessions(user_id)")
            self.connection.execute("CREATE INDEX idx_biometric_sessions_training_id ON biometric_sessions(training_session_id)")
        
        # Create biometric readings table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='biometric_readings'")
        if not cursor.fetchone():
            # Create table first
            self.connection.execute("""
            CREATE TABLE biometric_readings (
                reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
                biometric_session_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                heart_rate INTEGER,
                calories_burned REAL,
                exertion_level TEXT,
                recovery_time_minutes INTEGER,
                vo2_max_estimated REAL,
                respiratory_rate INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (biometric_session_id) REFERENCES biometric_sessions(session_id) ON DELETE CASCADE
            )
            """)
            # Then create indexes
            self.connection.execute("CREATE INDEX idx_biometric_readings_session_id ON biometric_readings(biometric_session_id)")
            self.connection.execute("CREATE INDEX idx_biometric_readings_timestamp ON biometric_readings(timestamp)")
        
        # Add biometric columns to existing sessions table
        cursor.execute("PRAGMA table_info(sessions)")
        session_columns = [column[1] for column in cursor.fetchall()]
        
        if 'biometric_session_id' not in session_columns:
            self.execute_query("ALTER TABLE sessions ADD COLUMN biometric_session_id INTEGER", fetch=False)
            self.execute_query("ALTER TABLE sessions ADD COLUMN biometric_data_available INTEGER DEFAULT 0", fetch=False)
    
    def _migrate_users_table(self):
        """Create tables if they don't exist, then add username, email, and password_hash columns"""
        if not self.is_connected():
            return

        cursor = self.connection.cursor()

        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()

        if not table_exists:
            # Create base tables from schema
            self._create_base_tables()

        # Check current columns for migration
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add auth-related columns if missing
        changes_made = False
        if 'username' not in columns:
            self.execute_query("ALTER TABLE users ADD COLUMN username TEXT", fetch=False)
            self.execute_query("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)", fetch=False)
            changes_made = True
        if 'email' not in columns:
            self.execute_query("ALTER TABLE users ADD COLUMN email TEXT", fetch=False)
            self.execute_query("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)", fetch=False)
            changes_made = True
        if 'password_hash' not in columns:
            self.execute_query("ALTER TABLE users ADD COLUMN password_hash TEXT", fetch=False)
            changes_made = True
        if 'role' not in columns:
            self.execute_query("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'athlete'", fetch=False)
            changes_made = True

        if changes_made and self.connection:
            self.connection.commit()

    def _create_base_tables(self):
        """Create all base tables if they don't exist"""
        if not self.is_connected():
            return

        schema_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            username TEXT,
            email TEXT,
            password_hash TEXT,
            role TEXT DEFAULT 'athlete',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_name ON users(name);

        -- Training sessions table
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP NULL,
            total_jumps INTEGER DEFAULT 0,
            total_squats INTEGER DEFAULT 0,
            total_pushups INTEGER DEFAULT 0,
            total_burpees INTEGER DEFAULT 0,
            total_points INTEGER DEFAULT 0,
            total_bad_moves INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_user_id ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_start_time ON sessions(start_time);
        CREATE INDEX IF NOT EXISTS idx_sessions_user_time ON sessions(user_id, start_time);

        -- Individual jumps table
        CREATE TABLE IF NOT EXISTS jumps (
            jump_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            jump_number INTEGER NOT NULL,
            points INTEGER DEFAULT 0,
            bad_moves INTEGER DEFAULT 0,
            warnings TEXT,
            has_danger INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_session_id ON jumps(session_id);
        CREATE INDEX IF NOT EXISTS idx_timestamp ON jumps(timestamp);
        CREATE INDEX IF NOT EXISTS idx_jumps_session ON jumps(session_id, jump_number);

        -- Squats table
        CREATE TABLE IF NOT EXISTS squats (
            squat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            squat_number INTEGER NOT NULL,
            points INTEGER DEFAULT 0,
            bad_moves INTEGER DEFAULT 0,
            warnings TEXT,
            has_danger INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_squats_session_id ON squats(session_id);
        CREATE INDEX IF NOT EXISTS idx_squats_timestamp ON squats(timestamp);
        CREATE INDEX IF NOT EXISTS idx_squats_session ON squats(session_id, squat_number);

        -- Pushups table
        CREATE TABLE IF NOT EXISTS pushups (
            pushup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            pushup_number INTEGER NOT NULL,
            points INTEGER DEFAULT 0,
            bad_moves INTEGER DEFAULT 0,
            warnings TEXT,
            has_danger INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_pushups_session_id ON pushups(session_id);
        CREATE INDEX IF NOT EXISTS idx_pushups_timestamp ON pushups(timestamp);
        CREATE INDEX IF NOT EXISTS idx_pushups_session ON pushups(session_id, pushup_number);

        -- Burpees table
        CREATE TABLE IF NOT EXISTS burpees (
            burpee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            burpee_number INTEGER NOT NULL,
            points INTEGER DEFAULT 0,
            bad_moves INTEGER DEFAULT 0,
            warnings TEXT,
            has_danger INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_burpees_session_id ON burpees(session_id);
        CREATE INDEX IF NOT EXISTS idx_burpees_timestamp ON burpees(timestamp);
        CREATE INDEX IF NOT EXISTS idx_burpees_session ON burpees(session_id, burpee_number);

        -- Training recommendations table
        CREATE TABLE IF NOT EXISTS training_recommendations (
            recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id INTEGER,
            recommendation_type TEXT NOT NULL,
            priority TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            exercise_focus TEXT,
            specific_issue TEXT,
            recommendation_text TEXT NOT NULL,
            difficulty_level TEXT,
            estimated_time_minutes INTEGER,
            is_completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_recommendations_user ON training_recommendations(user_id);
        CREATE INDEX IF NOT EXISTS idx_recommendations_type ON training_recommendations(recommendation_type);
        CREATE INDEX IF NOT EXISTS idx_recommendations_priority ON training_recommendations(priority);

        -- User performance analytics table
        CREATE TABLE IF NOT EXISTS user_performance_analytics (
            analytics_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exercise_type TEXT NOT NULL,
            total_reps INTEGER DEFAULT 0,
            avg_points_per_rep REAL DEFAULT 0,
            total_bad_moves INTEGER DEFAULT 0,
            bad_move_rate REAL DEFAULT 0,
            most_common_issue TEXT,
            improvement_trend TEXT,
            performance_score REAL DEFAULT 0,
            recommendations_generated INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_analytics_user_date ON user_performance_analytics(user_id, analysis_date);
        """

        try:
            self.connection.executescript(schema_sql)
            self.connection.commit()
        except Exception as e:
            print(f"Error creating base tables: {e}")
    
    def register_user(self, username: str, email: str, password: str, name: str, age: int, role: str = 'athlete') -> Optional[int]:
        """Register a new user with hashed password"""
        if not self.is_connected():
            return None
            
        # Check if username or email exists
        check_query = "SELECT user_id FROM users WHERE username = ? OR email = ?"
        existing = self.execute_query(check_query, (username, email))
        if existing:
            return None
            
        # Hash password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        query = """
        INSERT INTO users (username, email, password_hash, name, age, role, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (username, email, password_hash, name, age, role, datetime.now()))
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            st.error(f"Error registering user: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def authenticate_user(self, username_or_email: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data if successful"""
        if not self.is_connected():
            return None
            
        query = "SELECT * FROM users WHERE username = ? OR email = ?"
        result = self.execute_query(query, (username_or_email, username_or_email))
        
        if not result:
            return None
            
        user = result[0]
        if not user.get('password_hash'):
            # Legacy user without password
            return None
            
        # Verify password
        stored_hash = user['password_hash'].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return user
        return None
    
    def create_user(self, name: str, age: int) -> Optional[int]:
        """Create a new user and return user_id"""
        if not self.is_connected():
            return None
        query = """
        INSERT INTO users (name, age, created_at) 
        VALUES (?, ?, ?)
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (name, age, datetime.now()))
            self.connection.commit()
            user_id = cursor.lastrowid
            return user_id
        except Exception as e:
            try:
                st.error(f"Error creating user: {e}")
            except:
                print(f"Error creating user: {e}")
            if cursor:
                cursor.close()
            return None
    
    def get_user_by_name_age(self, name: str, age: int) -> Optional[Dict]:
        """Get existing user by name and age"""
        if not self.is_connected():
            return None
        query = """
        SELECT user_id, name, age, created_at 
        FROM users 
        WHERE name = ? AND age = ?
        ORDER BY created_at DESC
        LIMIT 1
        """
        result = self.execute_query(query, (name, age))
        return result[0] if result else None
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE user_id = ?"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def create_session(self, user_id: int) -> Optional[int]:
        """Create a new training session and return session_id"""
        if not self.is_connected():
            return None
        query = """
        INSERT INTO sessions (user_id, start_time) 
        VALUES (?, ?)
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (user_id, datetime.now()))
            self.connection.commit()
            session_id = cursor.lastrowid
            return session_id
        except Exception as e:
            try:
                st.error(f"Error creating session: {e}")
            except:
                print(f"Error creating session: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def update_session_totals(self, session_id: int, total_jumps: int, total_points: int, total_bad_moves: int, total_squats: int = 0, total_pushups: int = 0, total_burpees: int = 0, total_stepups: int = 0):
        """Update session totals in real-time (without ending the session)"""
        query = """
        UPDATE sessions 
        SET total_jumps = ?, total_points = ?, total_bad_moves = ?, total_squats = ?, total_pushups = ?, total_burpees = ?, total_stepups = ?
        WHERE session_id = ?
        """
        self.execute_query(query, (total_jumps, total_points, total_bad_moves, total_squats, total_pushups, total_burpees, total_stepups, session_id), fetch=False)
        # Force immediate commit to ensure real-time updates
        if self.connection:
            try:
                self.connection.commit()
            except:
                pass
    
    def end_session(self, session_id: int, total_jumps: int, total_points: int, total_bad_moves: int, total_squats: int = 0, total_pushups: int = 0, total_burpees: int = 0, total_stepups: int = 0):
        """End a training session"""
        query = """
        UPDATE sessions 
        SET end_time = ?, total_jumps = ?, total_points = ?, total_bad_moves = ?, total_squats = ?, total_pushups = ?, total_burpees = ?, total_stepups = ?
        WHERE session_id = ?
        """
        self.execute_query(query, (datetime.now(), total_jumps, total_points, total_bad_moves, total_squats, total_pushups, total_burpees, total_stepups, session_id), fetch=False)

    def record_stepup(self, session_id: int, stepup_number: int, points: int, 
                     bad_moves: int, warnings: str, has_danger: bool):
        """Record a single stepup rep"""
        if not self.is_connected():
            return
        query = """
        INSERT INTO stepups (session_id, stepup_number, points, bad_moves, warnings, has_danger, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.execute_query(query, (session_id, stepup_number, points, bad_moves, warnings, 1 if has_danger else 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')), fetch=False)

    def record_burpee(self, session_id: int, burpee_number: int, points: int, 
                     bad_moves: int, warnings: str, has_danger: bool):
        """Record a single burpee"""
        if not self.is_connected():
            return
        query = """
        INSERT INTO burpees (session_id, burpee_number, points, bad_moves, warnings, has_danger, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.execute_query(query, (session_id, burpee_number, points, bad_moves, warnings, 1 if has_danger else 0, datetime.now()), fetch=False)
        # Force immediate commit to ensure real-time updates
        if self.connection:
            try:
                self.connection.commit()
            except:
                pass
    
    def record_jump(self, session_id: int, jump_number: int, points: int, 
                   bad_moves: int, warnings: str, has_danger: bool):
        """Record a single jump"""
        if not self.is_connected():
            return
        query = """
        INSERT INTO jumps (session_id, jump_number, points, bad_moves, warnings, has_danger, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.execute_query(query, (session_id, jump_number, points, bad_moves, warnings, 1 if has_danger else 0, datetime.now()), fetch=False)
        # Force immediate commit to ensure real-time updates
        if self.connection:
            try:
                self.connection.commit()
            except:
                pass
    
    def record_squat(self, session_id: int, squat_number: int, points: int, 
                    bad_moves: int, warnings: str, has_danger: bool):
        """Record a single squat"""
        if not self.is_connected():
            return
        query = """
        INSERT INTO squats (session_id, squat_number, points, bad_moves, warnings, has_danger, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.execute_query(query, (session_id, squat_number, points, bad_moves, warnings, 1 if has_danger else 0, datetime.now()), fetch=False)
        # Force immediate commit to ensure real-time updates
        if self.connection:
            try:
                self.connection.commit()
            except:
                pass
    
    def record_pushup(self, session_id: int, pushup_number: int, points: int, 
                     bad_moves: int, warnings: str, has_danger: bool):
        """Record a single push-up"""
        if not self.is_connected():
            return
        query = """
        INSERT INTO pushups (session_id, pushup_number, points, bad_moves, warnings, has_danger, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.execute_query(query, (session_id, pushup_number, points, bad_moves, warnings, 1 if has_danger else 0, datetime.now()), fetch=False)
        # Force immediate commit to ensure real-time updates
        if self.connection:
            try:
                self.connection.commit()
            except:
                pass
    
    def get_leaderboard(self, limit: int = 10, exercise_type: str = 'all') -> List[Dict]:
        """Get top performers leaderboard for specific exercise type or all"""
        if exercise_type == 'jump':
            query = """
            SELECT 
                u.name,
                u.age,
                COUNT(DISTINCT s.session_id) as total_sessions,
                COUNT(j.jump_id) as total_count,
                COALESCE(SUM(j.points), 0) as total_points,
                COALESCE(SUM(j.bad_moves), 0) as total_bad_moves,
                MAX(s.end_time) as last_session
            FROM users u
            JOIN sessions s ON u.user_id = s.user_id
            JOIN jumps j ON s.session_id = j.session_id
            WHERE s.total_jumps > 0
            GROUP BY u.user_id, u.name, u.age
            ORDER BY total_points DESC, total_count DESC
            LIMIT ?
            """
        elif exercise_type == 'squat':
            query = """
            SELECT 
                u.name,
                u.age,
                COUNT(DISTINCT s.session_id) as total_sessions,
                COUNT(sq.squat_id) as total_count,
                COALESCE(SUM(sq.points), 0) as total_points,
                COALESCE(SUM(sq.bad_moves), 0) as total_bad_moves,
                MAX(s.end_time) as last_session
            FROM users u
            JOIN sessions s ON u.user_id = s.user_id
            JOIN squats sq ON s.session_id = sq.session_id
            WHERE s.total_squats > 0
            GROUP BY u.user_id, u.name, u.age
            ORDER BY total_points DESC, total_count DESC
            LIMIT ?
            """
        elif exercise_type == 'pushup':
            query = """
            SELECT 
                u.name,
                u.age,
                COUNT(DISTINCT s.session_id) as total_sessions,
                COUNT(p.pushup_id) as total_count,
                COALESCE(SUM(p.points), 0) as total_points,
                COALESCE(SUM(p.bad_moves), 0) as total_bad_moves,
                MAX(s.end_time) as last_session
            FROM users u
            JOIN sessions s ON u.user_id = s.user_id
            JOIN pushups p ON s.session_id = p.session_id
            WHERE s.total_pushups > 0
            GROUP BY u.user_id, u.name, u.age
            ORDER BY total_points DESC, total_count DESC
            LIMIT ?
            """
        elif exercise_type == 'burpee':
            query = """
            SELECT 
                u.name,
                u.age,
                COUNT(DISTINCT s.session_id) as total_sessions,
                COUNT(b.burpee_id) as total_count,
                COALESCE(SUM(b.points), 0) as total_points,
                COALESCE(SUM(b.bad_moves), 0) as total_bad_moves,
                MAX(s.end_time) as last_session
            FROM users u
            JOIN sessions s ON u.user_id = s.user_id
            JOIN burpees b ON s.session_id = b.session_id
            WHERE s.total_burpees > 0
            GROUP BY u.user_id, u.name, u.age
            ORDER BY total_points DESC, total_count DESC
            LIMIT ?
            """
        elif exercise_type == 'stepup':
            query = """
            SELECT 
                u.name,
                u.age,
                COUNT(DISTINCT s.session_id) as total_sessions,
                COUNT(st.stepup_id) as total_count,
                COALESCE(SUM(st.points), 0) as total_points,
                COALESCE(SUM(st.bad_moves), 0) as total_bad_moves,
                MAX(s.end_time) as last_session
            FROM users u
            JOIN sessions s ON u.user_id = s.user_id
            JOIN stepups st ON s.session_id = st.session_id
            WHERE s.total_stepups > 0
            GROUP BY u.user_id, u.name, u.age
            ORDER BY total_points DESC, total_count DESC
            LIMIT ?
            """
        else:  # all
            query = """
            SELECT 
                u.name,
                u.age,
                SUM(s.total_jumps + s.total_squats + s.total_pushups + s.total_burpees + s.total_stepups) as total_count,
                SUM(s.total_points) as total_points,
                SUM(s.total_bad_moves) as total_bad_moves,
                COUNT(DISTINCT s.session_id) as total_sessions,
                MAX(s.end_time) as last_session
            FROM users u
            JOIN sessions s ON u.user_id = s.user_id
            WHERE s.total_points > 0 OR s.total_squats > 0 OR s.total_pushups > 0 OR s.total_burpees > 0 OR s.total_stepups > 0
            GROUP BY u.user_id, u.name, u.age
            ORDER BY total_points DESC, total_count DESC
            LIMIT ?
            """
        return self.execute_query(query, (limit,)) or []
    
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Get statistics for a specific user"""
        query = """
        SELECT 
            COUNT(DISTINCT s.session_id) as total_sessions,
            SUM(s.total_jumps) as total_jumps,
            SUM(s.total_squats) as total_squats,
            SUM(s.total_pushups) as total_pushups,
            SUM(s.total_burpees) as total_burpees,
            SUM(s.total_stepups) as total_stepups,
            SUM(s.total_points) as total_points,
            SUM(s.total_bad_moves) as total_bad_moves,
            AVG(s.total_points) as avg_points_per_session,
            MAX(s.end_time) as last_session
        FROM sessions s
        WHERE s.user_id = ? AND (s.total_jumps > 0 OR s.total_squats > 0 OR s.total_pushups > 0 OR s.total_burpees > 0 OR s.total_stepups > 0)
        """
        result = self.execute_query(query, (user_id,))
        if result and len(result) > 0:
            stats = result[0]
            # Ensure all values are properly converted (handle None)
            return {
                'total_sessions': int(stats.get('total_sessions') or 0),
                'total_jumps': int(stats.get('total_jumps') or 0),
                'total_squats': int(stats.get('total_squats') or 0),
                'total_pushups': int(stats.get('total_pushups') or 0),
                'total_burpees': int(stats.get('total_burpees') or 0),
                'total_stepups': int(stats.get('total_stepups') or 0),
                'total_points': int(stats.get('total_points') or 0),
                'total_bad_moves': int(stats.get('total_bad_moves') or 0),
                'avg_points_per_session': float(stats.get('avg_points_per_session') or 0.0),
                'last_session': stats.get('last_session')
            }
        return None
    
    def get_recent_sessions(self, user_id: int, exercise_type: str = 'all', limit: int = 20) -> List[Dict]:
        if exercise_type == 'jump':
            where_clause = "s.total_jumps > 0"
        elif exercise_type == 'squat':
            where_clause = "s.total_squats > 0"
        elif exercise_type == 'pushup':
            where_clause = "s.total_pushups > 0"
        elif exercise_type == 'burpee':
            where_clause = "s.total_burpees > 0"
        elif exercise_type == 'stepup':
            where_clause = "s.total_stepups > 0"
        else:
            where_clause = "(s.total_jumps > 0 OR s.total_squats > 0 OR s.total_pushups > 0 OR s.total_burpees > 0 OR s.total_stepups > 0)"

        query = f"""
        SELECT 
            s.session_id,
            s.user_id,
            s.start_time,
            s.end_time,
            s.total_jumps,
            s.total_squats,
            s.total_pushups,
            s.total_burpees,
            s.total_stepups,
            s.total_points,
            s.total_bad_moves
        FROM sessions s
        WHERE s.user_id = ? AND s.end_time IS NOT NULL AND {where_clause}
        ORDER BY s.end_time DESC
        LIMIT ?
        """
        return self.execute_query(query, (user_id, limit)) or []
    
    def get_overall_stats(self) -> Dict:
        """Get overall statistics for dashboard"""
        stats = {}
        
        # Total participants
        query = "SELECT COUNT(DISTINCT user_id) as count FROM sessions WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0 OR total_burpees > 0 OR total_stepups > 0"
        result = self.execute_query(query)
        stats['total_participants'] = result[0]['count'] if result and len(result) > 0 and result[0]['count'] is not None else 0
        
        # Total sessions
        query = "SELECT COUNT(*) as count FROM sessions WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0 OR total_burpees > 0 OR total_stepups > 0"
        result = self.execute_query(query)
        stats['total_sessions'] = result[0]['count'] if result and len(result) > 0 and result[0]['count'] is not None else 0
        
        # Total jumps
        query = "SELECT SUM(total_jumps) as total FROM sessions WHERE total_jumps > 0"
        result = self.execute_query(query)
        stats['total_jumps'] = int(result[0]['total']) if result and len(result) > 0 and result[0]['total'] is not None else 0
        
        # Total squats
        query = "SELECT SUM(total_squats) as total FROM sessions WHERE total_squats > 0"
        result = self.execute_query(query)
        stats['total_squats'] = int(result[0]['total']) if result and len(result) > 0 and result[0]['total'] is not None else 0
        
        # Total push-ups
        query = "SELECT SUM(total_pushups) as total FROM sessions WHERE total_pushups > 0"
        result = self.execute_query(query)
        stats['total_pushups'] = int(result[0]['total']) if result and len(result) > 0 and result[0]['total'] is not None else 0
        
        # Total burpees
        query = "SELECT SUM(total_burpees) as total FROM sessions WHERE total_burpees > 0"
        result = self.execute_query(query)
        stats['total_burpees'] = int(result[0]['total']) if result and len(result) > 0 and result[0]['total'] is not None else 0
        
        # Total step-ups
        query = "SELECT SUM(total_stepups) as total FROM sessions WHERE total_stepups > 0"
        result = self.execute_query(query)
        stats['total_stepups'] = int(result[0]['total']) if result and len(result) > 0 and result[0]['total'] is not None else 0
        
        # Total exercises (all combined)
        stats['total_exercises'] = stats['total_jumps'] + stats['total_squats'] + stats['total_pushups'] + stats['total_burpees'] + stats['total_stepups']
        
        # Total points
        query = "SELECT SUM(total_points) as total FROM sessions WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0 OR total_burpees > 0 OR total_stepups > 0"
        result = self.execute_query(query)
        stats['total_points'] = int(result[0]['total']) if result and len(result) > 0 and result[0]['total'] is not None else 0
        
        # Total bad moves
        query = "SELECT SUM(total_bad_moves) as total FROM sessions WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0 OR total_burpees > 0 OR total_stepups > 0"
        result = self.execute_query(query)
        stats['total_bad_moves'] = int(result[0]['total']) if result and len(result) > 0 and result[0]['total'] is not None else 0
        
        # Average exercises per session
        query = "SELECT AVG(total_jumps + total_squats + total_pushups + total_burpees + total_stepups) as avg FROM sessions WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0 OR total_burpees > 0 OR total_stepups > 0"
        result = self.execute_query(query)
        stats['avg_exercises_per_session'] = float(result[0]['avg']) if result and len(result) > 0 and result[0]['avg'] is not None else 0.0
        
        # Average points per session
        query = "SELECT AVG(total_points) as avg FROM sessions WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0 OR total_burpees > 0 OR total_stepups > 0"
        result = self.execute_query(query)
        stats['avg_points_per_session'] = float(result[0]['avg']) if result and len(result) > 0 and result[0]['avg'] is not None else 0.0
        
        return stats
    
    def get_all_athletes_stats(self) -> List[Dict]:
        """Get summary statistics for all athletes for the Coach Dashboard"""
        if not self.is_connected():
            return []
        
        query = """
        SELECT 
            u.user_id,
            u.name,
            u.age,
            u.email,
            COUNT(DISTINCT s.session_id) as total_sessions,
            SUM(s.total_jumps + s.total_squats + s.total_pushups + s.total_burpees + s.total_stepups) as total_reps,
            SUM(s.total_points) as total_points,
            SUM(s.total_bad_moves) as total_bad_moves,
            MAX(s.end_time) as last_active
        FROM users u
        LEFT JOIN sessions s ON u.user_id = s.user_id
        WHERE u.role = 'athlete' OR u.role IS NULL
        GROUP BY u.user_id, u.name, u.age, u.email
        ORDER BY total_points DESC
        """
        return self.execute_query(query) or []

    def get_daily_stats(self, days: int = 30) -> List[Dict]:
        """Get daily statistics for charts"""
        # SQLite date arithmetic
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        query = """
        SELECT 
            DATE(s.start_time) as date,
            COUNT(DISTINCT s.user_id) as participants,
            COUNT(s.session_id) as sessions,
            SUM(s.total_jumps) as jumps,
            SUM(s.total_squats) as squats,
            SUM(s.total_pushups) as pushups,
            SUM(s.total_burpees) as burpees,
            SUM(s.total_stepups) as stepups,
            SUM(s.total_points) as points
        FROM sessions s
        WHERE (s.total_jumps > 0 OR s.total_squats > 0 OR s.total_pushups > 0 OR s.total_burpees > 0 OR s.total_stepups > 0)
        AND s.start_time >= ?
        GROUP BY DATE(s.start_time)
        ORDER BY date ASC
        """
        return self.execute_query(query, (cutoff_date,)) or []
    
    def get_exercise_distribution(self) -> Dict:
        """Get distribution of exercises (for pie chart)"""
        query = """
        SELECT 
            SUM(total_jumps) as jumps,
            SUM(total_squats) as squats,
            SUM(total_pushups) as pushups,
            SUM(total_burpees) as burpees,
            SUM(total_stepups) as stepups
        FROM sessions
        WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0 OR total_burpees > 0 OR total_stepups > 0
        """
        result = self.execute_query(query)
        if result and len(result) > 0:
            return {
                'jumps': int(result[0].get('jumps') or 0),
                'squats': int(result[0].get('squats') or 0),
                'pushups': int(result[0].get('pushups') or 0),
                'burpees': int(result[0].get('burpees') or 0),
                'stepups': int(result[0].get('stepups') or 0)
            }
        return {'jumps': 0, 'squats': 0, 'pushups': 0, 'burpees': 0, 'stepups': 0}
    
    def get_daily_exercise_stats(self, days: int = 30) -> List[Dict]:
        """Get daily statistics for each exercise type"""
        # SQLite date arithmetic
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        query = """
        SELECT 
            DATE(s.start_time) as date,
            SUM(s.total_jumps) as jumps,
            SUM(s.total_squats) as squats,
            SUM(s.total_pushups) as pushups,
            SUM(s.total_burpees) as burpees,
            SUM(s.total_stepups) as stepups,
            SUM(s.total_points) as points,
            COUNT(DISTINCT s.user_id) as participants,
            COUNT(s.session_id) as sessions
        FROM sessions s
        WHERE (s.total_jumps > 0 OR s.total_squats > 0 OR s.total_pushups > 0 OR s.total_burpees > 0 OR s.total_stepups > 0)
        AND s.start_time >= ?
        GROUP BY DATE(s.start_time)
        ORDER BY date ASC
        """
        return self.execute_query(query, (cutoff_date,)) or []

    def get_hourly_exercise_stats(self, hours: int = 24) -> List[Dict]:
        """Get hourly statistics for each exercise type"""
        cutoff_date = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = """
        SELECT 
            strftime('%Y-%m-%d %H:00:00', s.start_time) as hour,
            SUM(s.total_jumps) as jumps,
            SUM(s.total_squats) as squats,
            SUM(s.total_pushups) as pushups,
            SUM(s.total_burpees) as burpees,
            SUM(s.total_stepups) as stepups,
            SUM(s.total_points) as points,
            COUNT(DISTINCT s.user_id) as participants,
            COUNT(s.session_id) as sessions
        FROM sessions s
        WHERE (s.total_jumps > 0 OR s.total_squats > 0 OR s.total_pushups > 0 OR s.total_burpees > 0 OR s.total_stepups > 0)
        AND s.start_time >= ?
        GROUP BY strftime('%Y-%m-%d %H', s.start_time)
        ORDER BY hour ASC
        """
        return self.execute_query(query, (cutoff_date,)) or []
    
    def get_top_performers_by_exercise(self, exercise_type: str, limit: int = 5) -> List[Dict]:
        """Get top performers for specific exercise type"""
        if exercise_type == 'jump':
            query = """
            SELECT 
                u.name,
                SUM(s.total_jumps) as count,
                SUM(s.total_points) as points
            FROM users u
            JOIN sessions s ON u.user_id = s.user_id
            WHERE s.total_jumps > 0
            GROUP BY u.user_id, u.name
            ORDER BY count DESC
            LIMIT ?
            """
        elif exercise_type == 'squat':
            query = """
            SELECT 
                u.name,
                SUM(s.total_squats) as count,
                SUM(s.total_points) as points
            FROM users u
            JOIN sessions s ON u.user_id = s.user_id
            WHERE s.total_squats > 0
            GROUP BY u.user_id, u.name
            ORDER BY count DESC
            LIMIT ?
            """
        elif exercise_type == 'pushup':
            query = """
            SELECT 
                u.name,
                SUM(s.total_pushups) as count,
                SUM(s.total_points) as points
            FROM users u
            JOIN sessions s ON u.user_id = s.user_id
            WHERE s.total_pushups > 0
            GROUP BY u.user_id, u.name
            ORDER BY count DESC
            LIMIT ?
            """
        else:  # burpee
            query = """
            SELECT 
                u.name,
                SUM(s.total_burpees) as count,
                SUM(s.total_points) as points
            FROM users u
            JOIN sessions s ON u.user_id = s.user_id
            WHERE s.total_burpees > 0
            GROUP BY u.user_id, u.name
            ORDER BY count DESC
            LIMIT ?
            """
        return self.execute_query(query, (limit,)) or []
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    # ==================== TRAINING RECOMMENDATIONS ====================
    
    def get_user_recommendations(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's training recommendations sorted by priority"""
        query = """
        SELECT * FROM training_recommendations 
        WHERE user_id = ? AND is_completed = 0
        ORDER BY 
            CASE priority 
                WHEN 'high' THEN 1 
                WHEN 'medium' THEN 2 
                WHEN 'low' THEN 3 
            END,
            created_at DESC
        LIMIT ?
        """
        return self.execute_query(query, (user_id, limit)) or []
    
    def mark_recommendation_completed(self, recommendation_id: int) -> bool:
        """Mark a recommendation as completed"""
        query = """
        UPDATE training_recommendations 
        SET is_completed = 1, completed_at = ?
        WHERE recommendation_id = ?
        """
        result = self.execute_query(query, (datetime.now(), recommendation_id), fetch=False)
        return result is not None and result > 0
    
    def get_user_performance_analytics(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get user's performance analytics for the last N days"""
        query = """
        SELECT * FROM user_performance_analytics 
        WHERE user_id = ? AND analysis_date >= datetime('now', '-{} days')
        ORDER BY analysis_date DESC
        """.format(days)
        return self.execute_query(query, (user_id,)) or []
    
    def get_recommendations_by_type(self, user_id: int, rec_type: str) -> List[Dict]:
        """Get recommendations by type for a user"""
        query = """
        SELECT * FROM training_recommendations 
        WHERE user_id = ? AND recommendation_type = ? AND is_completed = 0
        ORDER BY priority DESC, created_at DESC
        """
        return self.execute_query(query, (user_id, rec_type)) or []
    
    # ==================== BIOMETRIC DATA METHODS ====================
    
    def save_user_biometric_profile(self, user_id: int, age: int, weight: float, height: float, 
                                   gender: str, fitness_level: str, resting_hr: int = None, max_hr: int = None) -> bool:
        """Save or update user biometric profile"""
        try:
            # Check if profile exists
            existing = self.execute_query(
                "SELECT profile_id FROM user_biometric_profiles WHERE user_id = ?", 
                (user_id,)
            )
            
            if existing:
                # Update existing profile
                query = """
                UPDATE user_biometric_profiles 
                SET age = ?, weight = ?, height = ?, gender = ?, fitness_level = ?, 
                    resting_heart_rate = ?, max_heart_rate = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """
                self.execute_query(query, (age, weight, height, gender, fitness_level, resting_hr, max_hr, user_id), fetch=False)
            else:
                # Insert new profile
                query = """
                INSERT INTO user_biometric_profiles 
                (user_id, age, weight, height, gender, fitness_level, resting_heart_rate, max_heart_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                self.execute_query(query, (user_id, age, weight, height, gender, fitness_level, resting_hr, max_hr), fetch=False)
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error saving biometric profile: {e}")
            return False
    
    def get_user_biometric_profile(self, user_id: int) -> Optional[Dict]:
        """Get user biometric profile"""
        query = """
        SELECT * FROM user_biometric_profiles WHERE user_id = ?
        """
        result = self.execute_query(query, (user_id,))
        return dict(result[0]) if result else None
    
    def create_biometric_session(self, user_id: int, training_session_id: int = None) -> Optional[int]:
        """Create a new biometric tracking session"""
        try:
            query = """
            INSERT INTO biometric_sessions 
            (user_id, training_session_id, start_time)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """
            cursor = self.connection.execute(query, (user_id, training_session_id))
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating biometric session: {e}")
            return None
    
    def end_biometric_session(self, biometric_session_id: int, session_summary: Dict) -> bool:
        """End a biometric session with summary data"""
        try:
            query = """
            UPDATE biometric_sessions 
            SET end_time = CURRENT_TIMESTAMP,
                duration_minutes = ?,
                total_calories_burned = ?,
                avg_heart_rate = ?,
                max_heart_rate = ?,
                avg_exertion_level = ?,
                recovery_time_minutes = ?,
                recovery_type = ?,
                recovery_recommendation = ?
            WHERE session_id = ?
            """
            params = (
                session_summary.get('session_duration', 0),
                session_summary.get('total_calories', 0),
                session_summary.get('avg_heart_rate'),
                session_summary.get('max_heart_rate'),
                session_summary.get('avg_exertion'),
                session_summary.get('recovery_recommendation', {}).get('recovery_time', 0),
                session_summary.get('recovery_recommendation', {}).get('recovery_type', 'None'),
                session_summary.get('recovery_recommendation', {}).get('recommendation', ''),
                biometric_session_id
            )
            
            self.execute_query(query, params, fetch=False)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error ending biometric session: {e}")
            return False
    
    def add_biometric_reading(self, biometric_session_id: int, reading_data: Dict) -> bool:
        """Add a biometric reading to a session"""
        try:
            query = """
            INSERT INTO biometric_readings 
            (biometric_session_id, timestamp, heart_rate, calories_burned, exertion_level, 
             recovery_time_minutes, vo2_max_estimated, respiratory_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                biometric_session_id,
                reading_data.get('timestamp', datetime.now()),
                reading_data.get('heart_rate'),
                reading_data.get('calories_burned'),
                reading_data.get('exertion_level'),
                reading_data.get('recovery_time'),
                reading_data.get('vo2_max'),
                reading_data.get('respiratory_rate')
            )
            
            self.execute_query(query, params, fetch=False)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error adding biometric reading: {e}")
            return False
    
    def get_user_biometric_sessions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's biometric session history"""
        query = """
        SELECT * FROM biometric_sessions 
        WHERE user_id = ? AND end_time IS NOT NULL
        ORDER BY start_time DESC
        LIMIT ?
        """
        result = self.execute_query(query, (user_id, limit))
        return [dict(row) for row in result] if result else []
    
    def get_biometric_session_details(self, session_id: int) -> List[Dict]:
        """Get detailed readings for a biometric session"""
        query = """
        SELECT * FROM biometric_readings 
        WHERE biometric_session_id = ?
        ORDER BY timestamp ASC
        """
        result = self.execute_query(query, (session_id,))
        return [dict(row) for row in result] if result else []
    
    def get_biometric_analytics(self, user_id: int, days: int = 30) -> Dict:
        """Get biometric analytics for a user over specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT 
            COUNT(*) as total_sessions,
            AVG(duration_minutes) as avg_duration,
            AVG(total_calories_burned) as avg_calories,
            AVG(avg_heart_rate) as avg_heart_rate,
            MAX(max_heart_rate) as max_heart_rate,
            AVG(recovery_time_minutes) as avg_recovery_time
        FROM biometric_sessions
        WHERE user_id = ? AND start_time >= ?
        """
        
        result = self.execute_query(query, (user_id, cutoff_date))
        return dict(result[0]) if result else {}
    
    def update_training_session_biometric_link(self, training_session_id: int, biometric_session_id: int) -> bool:
        """Link training session with biometric session"""
        try:
            query = """
            UPDATE sessions 
            SET biometric_session_id = ?, biometric_data_available = 1
            WHERE session_id = ?
            """
            self.execute_query(query, (biometric_session_id, training_session_id), fetch=False)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error linking biometric session: {e}")
            return False
