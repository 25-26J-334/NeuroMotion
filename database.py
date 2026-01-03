"""
Database connection and operations for AI Athlete Trainer
SQLite version
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import streamlit as st
import os

class Database:
    def __init__(self, db_path: str = None):
        """Initialize database connection using SQLite"""
        self.connection = None
        self.db_path = db_path or self._get_db_path()
        self.connect()
    
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
    
    def update_session_totals(self, session_id: int, total_jumps: int, total_points: int, total_bad_moves: int, total_squats: int = 0, total_pushups: int = 0):
        """Update session totals in real-time (without ending the session)"""
        query = """
        UPDATE sessions 
        SET total_jumps = ?, total_points = ?, total_bad_moves = ?, total_squats = ?, total_pushups = ?
        WHERE session_id = ?
        """
        self.execute_query(query, (total_jumps, total_points, total_bad_moves, total_squats, total_pushups, session_id), fetch=False)
        # Force immediate commit to ensure real-time updates
        if self.connection:
            try:
                self.connection.commit()
            except:
                pass
    
    def end_session(self, session_id: int, total_jumps: int, total_points: int, total_bad_moves: int, total_squats: int = 0, total_pushups: int = 0):
        """End a training session"""
        query = """
        UPDATE sessions 
        SET end_time = ?, total_jumps = ?, total_points = ?, total_bad_moves = ?, total_squats = ?, total_pushups = ?
        WHERE session_id = ?
        """
        self.execute_query(query, (datetime.now(), total_jumps, total_points, total_bad_moves, total_squats, total_pushups, session_id), fetch=False)
    
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
        else:  # all
            query = """
            SELECT 
                u.name,
                u.age,
                SUM(s.total_jumps + s.total_squats + s.total_pushups) as total_count,
                SUM(s.total_points) as total_points,
                SUM(s.total_bad_moves) as total_bad_moves,
                COUNT(DISTINCT s.session_id) as total_sessions,
                MAX(s.end_time) as last_session
            FROM users u
            JOIN sessions s ON u.user_id = s.user_id
            WHERE s.total_points > 0 OR s.total_squats > 0 OR s.total_pushups > 0
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
            SUM(s.total_points) as total_points,
            SUM(s.total_bad_moves) as total_bad_moves,
            AVG(s.total_points) as avg_points_per_session,
            MAX(s.end_time) as last_session
        FROM sessions s
        WHERE s.user_id = ? AND (s.total_jumps > 0 OR s.total_squats > 0 OR s.total_pushups > 0)
        """
        result = self.execute_query(query, (user_id,))
        if result and len(result) > 0:
            stats = result[0]
            # Ensure all values are properly converted (handle None)
            return {
                'total_sessions': int(stats.get('total_sessions') or 0),
                'total_jumps': int(stats.get('total_jumps') or 0),
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
    
    def get_overall_stats(self) -> Dict:
        """Get overall statistics for dashboard"""
        stats = {}
        
        # Total participants
        query = "SELECT COUNT(DISTINCT user_id) as count FROM sessions WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0"
        result = self.execute_query(query)
        stats['total_participants'] = result[0]['count'] if result and len(result) > 0 and result[0]['count'] is not None else 0
        
        # Total sessions
        query = "SELECT COUNT(*) as count FROM sessions WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0"
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
        
        # Total exercises (all combined)
        stats['total_exercises'] = stats['total_jumps'] + stats['total_squats'] + stats['total_pushups']
        
        # Total points
        query = "SELECT SUM(total_points) as total FROM sessions WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0"
        result = self.execute_query(query)
        stats['total_points'] = int(result[0]['total']) if result and len(result) > 0 and result[0]['total'] is not None else 0
        
        # Total bad moves
        query = "SELECT SUM(total_bad_moves) as total FROM sessions WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0"
        result = self.execute_query(query)
        stats['total_bad_moves'] = int(result[0]['total']) if result and len(result) > 0 and result[0]['total'] is not None else 0
        
        # Average exercises per session
        query = "SELECT AVG(total_jumps + total_squats + total_pushups) as avg FROM sessions WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0"
        result = self.execute_query(query)
        stats['avg_exercises_per_session'] = float(result[0]['avg']) if result and len(result) > 0 and result[0]['avg'] is not None else 0.0
        
        # Average points per session
        query = "SELECT AVG(total_points) as avg FROM sessions WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0"
        result = self.execute_query(query)
        stats['avg_points_per_session'] = float(result[0]['avg']) if result and len(result) > 0 and result[0]['avg'] is not None else 0.0
        
        return stats
    
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
            SUM(s.total_points) as points
        FROM sessions s
        WHERE (s.total_jumps > 0 OR s.total_squats > 0 OR s.total_pushups > 0)
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
            SUM(total_pushups) as pushups
        FROM sessions
        WHERE total_jumps > 0 OR total_squats > 0 OR total_pushups > 0
        """
        result = self.execute_query(query)
        if result and len(result) > 0:
            return {
                'jumps': int(result[0].get('jumps') or 0),
                'squats': int(result[0].get('squats') or 0),
                'pushups': int(result[0].get('pushups') or 0)
            }
        return {'jumps': 0, 'squats': 0, 'pushups': 0}
    
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
            SUM(s.total_points) as points,
            COUNT(DISTINCT s.user_id) as participants,
            COUNT(s.session_id) as sessions
        FROM sessions s
        WHERE (s.total_jumps > 0 OR s.total_squats > 0 OR s.total_pushups > 0)
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
            SUM(s.total_points) as points,
            COUNT(DISTINCT s.user_id) as participants,
            COUNT(s.session_id) as sessions
        FROM sessions s
        WHERE (s.total_jumps > 0 OR s.total_squats > 0 OR s.total_pushups > 0)
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
        else:  # pushup
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
