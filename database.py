"""
Database module for AI Athlete Trainer
Handles all database operations for users, sessions, and exercises
"""
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st


class Database:
    """Database connection and operations class"""
    
    def __init__(self, db_path: str = None):
        """Initialize database connection"""
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "athlete_trainer.db")
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.execute("PRAGMA foreign_keys = ON")
            return True
        except sqlite3.Error as e:
            st.error(f"Database connection error: {e}")
            return False
    
    def is_connected(self):
        """Check if database is connected"""
        return self.connection is not None
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results as list of dictionaries"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Fetch all rows and convert to list of dictionaries
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))
            
            return result
        except sqlite3.Error as e:
            st.error(f"Query execution error: {e}")
            return []
    
    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Execute an INSERT, UPDATE, or DELETE query"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            st.error(f"Update execution error: {e}")
            return False
    
    def create_user(self, name: str, age: int) -> Optional[int]:
        """Create a new user and return user_id"""
        query = "INSERT INTO users (name, age) VALUES (?, ?)"
        if self.execute_update(query, (name, age)):
            cursor = self.connection.cursor()
            cursor.execute("SELECT last_insert_rowid()")
            return cursor.fetchone()[0]
        return None
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE user_id = ?"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def get_user_by_name(self, name: str) -> Optional[Dict]:
        """Get user by name"""
        query = "SELECT * FROM users WHERE name = ?"
        result = self.execute_query(query, (name,))
        return result[0] if result else None
    
    def create_session(self, user_id: int) -> Optional[int]:
        """Create a new training session and return session_id"""
        query = "INSERT INTO sessions (user_id) VALUES (?)"
        if self.execute_update(query, (user_id,)):
            cursor = self.connection.cursor()
            cursor.execute("SELECT last_insert_rowid()")
            return cursor.fetchone()[0]
        return None
    
    def end_session(self, session_id: int, total_jumps: int, total_points: int, 
                   total_bad_moves: int, total_squats: int = 0, total_pushups: int = 0):
        """End a training session and update totals"""
        query = """
        UPDATE sessions 
        SET end_time = CURRENT_TIMESTAMP, 
            total_jumps = ?, 
            total_squats = ?,
            total_pushups = ?,
            total_points = ?, 
            total_bad_moves = ?
        WHERE session_id = ?
        """
        return self.execute_update(query, (total_jumps, total_squats, total_pushups, total_points, total_bad_moves, session_id))
    
    def update_session_totals(self, session_id: int, total_jumps: int, total_points: int, 
                           total_bad_moves: int, total_squats: int = 0, total_pushups: int = 0):
        """Update session totals in real-time"""
        query = """
        UPDATE sessions 
        SET total_jumps = ?, 
            total_squats = ?,
            total_pushups = ?,
            total_points = ?, 
            total_bad_moves = ?
        WHERE session_id = ?
        """
        return self.execute_update(query, (total_jumps, total_squats, total_pushups, total_points, total_bad_moves, session_id))
    
    def record_jump(self, session_id: int, jump_number: int, points: int, 
                   bad_moves: int, warnings: str, has_danger: bool):
        """Record a single jump"""
        query = """
        INSERT INTO jumps (session_id, jump_number, points, bad_moves, warnings, has_danger)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute_update(query, (session_id, jump_number, points, bad_moves, warnings, int(has_danger)))
    
    def record_squat(self, session_id: int, squat_number: int, points: int, 
                    bad_moves: int, warnings: str, has_danger: bool):
        """Record a single squat"""
        query = """
        INSERT INTO squats (session_id, squat_number, points, bad_moves, warnings, has_danger)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute_update(query, (session_id, squat_number, points, bad_moves, warnings, int(has_danger)))
    
    def record_pushup(self, session_id: int, pushup_number: int, points: int, 
                    bad_moves: int, warnings: str, has_danger: bool):
        """Record a single push-up"""
        query = """
        INSERT INTO pushups (session_id, pushup_number, points, bad_moves, warnings, has_danger)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute_update(query, (session_id, pushup_number, points, bad_moves, warnings, int(has_danger)))
    
    def get_recent_sessions(self, user_id: int, exercise_type: str = 'all', limit: int = 20) -> List[Dict]:
        """Get recent completed sessions for a user"""
        if exercise_type == 'jump':
            where_clause = "s.total_jumps > 0"
        elif exercise_type == 'squat':
            where_clause = "s.total_squats > 0"
        elif exercise_type == 'pushup':
            where_clause = "s.total_pushups > 0"
        else:
            where_clause = "(s.total_jumps > 0 OR s.total_squats > 0 OR s.total_pushups > 0)"

        query = f"""
        SELECT 
            s.session_id,
            s.user_id,
            s.start_time,
            s.end_time,
            s.total_jumps,
            s.total_squats,
            s.total_pushups,
            s.total_points,
            s.total_bad_moves
        FROM sessions s
        WHERE s.user_id = ? AND s.end_time IS NOT NULL AND {where_clause}
        ORDER BY s.end_time DESC
        LIMIT ?
        """
        return self.execute_query(query, (user_id, limit)) or []
    
    def get_leaderboard(self, limit: int = 20, exercise_type: str = 'all') -> List[Dict]:
        """Get leaderboard data"""
        if exercise_type == 'jump':
            count_col = "SUM(s.total_jumps)"
            where_clause = "s.total_jumps > 0"
        elif exercise_type == 'squat':
            count_col = "SUM(s.total_squats)"
            where_clause = "s.total_squats > 0"
        elif exercise_type == 'pushup':
            count_col = "SUM(s.total_pushups)"
            where_clause = "s.total_pushups > 0"
        else:
            count_col = "(SUM(s.total_jumps) + SUM(s.total_squats) + SUM(s.total_pushups))"
            where_clause = "(s.total_jumps > 0 OR s.total_squats > 0 OR s.total_pushups > 0)"

        query = f"""
        SELECT 
            u.user_id,
            u.name,
            u.age,
            {count_col} as total_count,
            SUM(s.total_points) as total_points,
            SUM(s.total_bad_moves) as total_bad_moves,
            COUNT(s.session_id) as total_sessions,
            MAX(s.end_time) as last_session
        FROM users u
        JOIN sessions s ON u.user_id = s.user_id
        WHERE s.end_time IS NOT NULL AND {where_clause}
        GROUP BY u.user_id, u.name, u.age
        HAVING total_count > 0
        ORDER BY total_points DESC
        LIMIT ?
        """
        return self.execute_query(query, (limit,))
    
    def get_overall_stats(self) -> Dict:
        """Get overall statistics for dashboard"""
        query = """
        SELECT 
            COUNT(DISTINCT u.user_id) as total_participants,
            COUNT(s.session_id) as total_sessions,
            SUM(s.total_jumps + s.total_squats + s.total_pushups) as total_exercises,
            SUM(s.total_points) as total_points,
            SUM(s.total_bad_moves) as total_bad_moves,
            AVG(s.total_jumps + s.total_squats + s.total_pushups) as avg_exercises_per_session,
            SUM(s.total_jumps) as total_jumps,
            SUM(s.total_squats) as total_squats,
            SUM(s.total_pushups) as total_pushups
        FROM users u
        JOIN sessions s ON u.user_id = s.user_id
        WHERE s.end_time IS NOT NULL
        """
        result = self.execute_query(query)
        return result[0] if result else {}
    
    def get_daily_exercise_stats(self, days: int = 30) -> List[Dict]:
        """Get daily exercise statistics for the last N days"""
        query = """
        SELECT 
            DATE(s.end_time) as date,
            SUM(s.total_jumps + s.total_squats + s.total_pushups) as total_exercises,
            SUM(s.total_points) as total_points,
            COUNT(s.session_id) as total_sessions
        FROM sessions s
        WHERE s.end_time IS NOT NULL 
            AND s.end_time >= DATE('now', '-{} days')
        GROUP BY DATE(s.end_time)
        ORDER BY date DESC
        """.format(days)
        return self.execute_query(query)
    
    def get_exercise_distribution(self) -> Dict:
        """Get distribution of exercise types"""
        query = """
        SELECT 
            SUM(s.total_jumps) as jumps,
            SUM(s.total_squats) as squats,
            SUM(s.total_pushups) as pushups
        FROM sessions s
        WHERE s.end_time IS NOT NULL
        """
        result = self.execute_query(query)
        if result:
            return {
                'jumps': result[0]['jumps'] or 0,
                'squats': result[0]['squats'] or 0,
                'pushups': result[0]['pushups'] or 0
            }
        return {'jumps': 0, 'squats': 0, 'pushups': 0}
    
    def add_athlete_performance(self, user_id: int, performance_data: Dict[str, Any]) -> bool:
        """
        Add new athlete performance data
        
        Args:
            user_id: ID of the athlete
            performance_data: Dictionary containing performance metrics with keys:
                - session_date: Date of the performance (YYYY-MM-DD format or datetime)
                - exercise_type: Type of exercise ('jump', 'squat', 'pushup', or 'combined')
                - total_reps: Total repetitions completed
                - total_points: Points earned
                - total_bad_moves: Number of bad moves
                - duration_minutes: Duration in minutes
                - notes: Optional notes about the performance
                - predicted_speed: Optional predicted speed (reps/min)
                - endurance_score: Optional endurance score (0-100)
                - performance_rating: Optional performance rating (0-100)
        
        Returns:
            bool: True if successfully added, False otherwise
        """
        try:
            # Create a new session for this performance data
            session_id = self.create_session(user_id)
            if not session_id:
                return False
            
            # Parse session date
            if isinstance(performance_data.get('session_date'), str):
                session_date = performance_data['session_date']
            elif isinstance(performance_data.get('session_date'), datetime):
                session_date = performance_data['session_date'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                session_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Update session with start time
            update_query = "UPDATE sessions SET start_time = ? WHERE session_id = ?"
            self.execute_update(update_query, (session_date, session_id))
            
            # Extract performance metrics
            exercise_type = performance_data.get('exercise_type', 'combined')
            total_reps = performance_data.get('total_reps', 0)
            total_points = performance_data.get('total_points', 0)
            total_bad_moves = performance_data.get('total_bad_moves', 0)
            duration_minutes = performance_data.get('duration_minutes', 0)
            notes = performance_data.get('notes', '')
            
            # Initialize exercise totals
            total_jumps = 0
            total_squats = 0
            total_pushups = 0
            
            # Distribute reps based on exercise type
            if exercise_type == 'jump':
                total_jumps = total_reps
            elif exercise_type == 'squat':
                total_squats = total_reps
            elif exercise_type == 'pushup':
                total_pushups = total_reps
            elif exercise_type == 'combined':
                # For combined, distribute evenly or use provided breakdown
                total_jumps = performance_data.get('total_jumps', total_reps // 3)
                total_squats = performance_data.get('total_squats', total_reps // 3)
                total_pushups = performance_data.get('total_pushups', total_reps // 3)
            
            # End the session with the performance data
            self.end_session(
                session_id=session_id,
                total_jumps=total_jumps,
                total_squats=total_squats,
                total_pushups=total_pushups,
                total_points=total_points,
                total_bad_moves=total_bad_moves
            )
            
            # Add individual exercise records if detailed data is provided
            if total_jumps > 0:
                for i in range(1, total_jumps + 1):
                    points_per_rep = total_points // total_reps if total_reps > 0 else 1
                    self.record_jump(
                        session_id=session_id,
                        jump_number=i,
                        points=points_per_rep,
                        bad_moves=0,
                        warnings=notes,
                        has_danger=False
                    )
            
            if total_squats > 0:
                for i in range(1, total_squats + 1):
                    points_per_rep = total_points // total_reps if total_reps > 0 else 1
                    self.record_squat(
                        session_id=session_id,
                        squat_number=i,
                        points=points_per_rep,
                        bad_moves=0,
                        warnings=notes,
                        has_danger=False
                    )
            
            if total_pushups > 0:
                for i in range(1, total_pushups + 1):
                    points_per_rep = total_points // total_reps if total_reps > 0 else 1
                    self.record_pushup(
                        session_id=session_id,
                        pushup_number=i,
                        points=points_per_rep,
                        bad_moves=0,
                        warnings=notes,
                        has_danger=False
                    )
            
            return True
            
        except Exception as e:
            st.error(f"Error adding athlete performance: {e}")
            return False
    
    def get_athlete_performance_history(self, user_id: int, exercise_type: str = 'all', 
                                    limit: int = 50) -> List[Dict]:
        """
        Get performance history for an athlete
        
        Args:
            user_id: ID of the athlete
            exercise_type: Filter by exercise type ('jump', 'squat', 'pushup', or 'all')
            limit: Maximum number of records to return
            
        Returns:
            List of dictionaries with performance data
        """
        if exercise_type == 'jump':
            where_clause = "s.total_jumps > 0"
        elif exercise_type == 'squat':
            where_clause = "s.total_squats > 0"
        elif exercise_type == 'pushup':
            where_clause = "s.total_pushups > 0"
        else:
            where_clause = "(s.total_jumps > 0 OR s.total_squats > 0 OR s.total_pushups > 0)"
        
        query = f"""
        SELECT 
            s.session_id,
            s.start_time,
            s.end_time,
            s.total_jumps,
            s.total_squats,
            s.total_pushups,
            s.total_points,
            s.total_bad_moves,
            (julianday(s.end_time) - julianday(s.start_time)) * 24 * 60 as duration_minutes
        FROM sessions s
        WHERE s.user_id = ? AND s.end_time IS NOT NULL AND {where_clause}
        ORDER BY s.end_time DESC
        LIMIT ?
        """
        
        results = self.execute_query(query, (user_id, limit))
        
        # Calculate additional metrics for each session
        for result in results:
            total_exercises = result['total_jumps'] + result['total_squats'] + result['total_pushups']
            result['total_exercises'] = total_exercises
            result['points_per_exercise'] = result['total_points'] / total_exercises if total_exercises > 0 else 0
            result['exercises_per_minute'] = total_exercises / result['duration_minutes'] if result['duration_minutes'] > 0 else 0
        
        return results
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __del__(self):
        """Destructor to ensure connection is closed"""
        self.close()
