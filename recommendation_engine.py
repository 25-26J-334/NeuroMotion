"""
Adaptive Training Recommendation Engine for AI Athlete Trainer
Analyzes user performance and generates personalized training recommendations
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import re

class RecommendationEngine:
    def __init__(self, db_path: str = None):
        """Initialize the recommendation engine"""
        self.db_path = db_path or "athlete_trainer.db"
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False
    
    def analyze_user_performance(self, user_id: int) -> Dict:
        """Analyze user's recent performance across all exercises"""
        if not self.connection:
            return {}
        
        # Get user's recent sessions (last 10 sessions)
        query = """
        SELECT * FROM sessions 
        WHERE user_id = ? 
        ORDER BY start_time DESC 
        LIMIT 10
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (user_id,))
        sessions = [dict(row) for row in cursor.fetchall()]
        
        if not sessions:
            return {}
        
        # Analyze performance for each exercise type
        performance = {
            'user_id': user_id,
            'analysis_date': datetime.now(),
            'jumps': self._analyze_exercise_performance(user_id, 'jumps', sessions),
            'squats': self._analyze_exercise_performance(user_id, 'squats', sessions),
            'pushups': self._analyze_exercise_performance(user_id, 'pushups', sessions)
        }
        
        return performance
    
    def _analyze_exercise_performance(self, user_id: int, exercise_type: str, sessions: List[Dict]) -> Dict:
        """Analyze performance for a specific exercise type"""
        table_name = exercise_type  # Use the exercise type directly (jumps, squats, pushups)
        
        # Get exercise data
        query = f"""
        SELECT e.*, s.start_time 
        FROM {table_name} e
        JOIN sessions s ON e.session_id = s.session_id
        WHERE s.user_id = ?
        ORDER BY e.timestamp DESC
        LIMIT 100
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (user_id,))
        exercises = [dict(row) for row in cursor.fetchall()]
        
        if not exercises:
            return {'total_reps': 0, 'avg_points': 0, 'bad_move_rate': 0, 'most_common_issue': None, 'trend': 'insufficient_data', 'performance_score': 0}
        
        # Calculate metrics
        total_reps = len(exercises)
        total_points = sum(e['points'] for e in exercises)
        total_bad_moves = sum(e['bad_moves'] for e in exercises)
        avg_points = total_points / total_reps if total_reps > 0 else 0
        bad_move_rate = (total_bad_moves / (total_reps * 10)) * 100 if total_reps > 0 else 0  # Assuming 10 points per rep
        
        # Find most common issue
        most_common_issue = self._find_most_common_issue(exercises)
        
        # Calculate trend
        trend = self._calculate_performance_trend(exercises)
        
        # Calculate performance score (0-100)
        performance_score = max(0, min(100, (avg_points / 10) * 100 - (bad_move_rate * 2)))
        
        return {
            'total_reps': total_reps,
            'avg_points': avg_points,
            'bad_move_rate': bad_move_rate,
            'most_common_issue': most_common_issue,
            'trend': trend,
            'performance_score': performance_score
        }
    
    def _find_most_common_issue(self, exercises: List[Dict]) -> Optional[str]:
        """Find the most common posture issue from warnings"""
        issue_counts = {}
        
        for exercise in exercises:
            if exercise['warnings']:
                # Parse warnings (they're stored as comma-separated strings)
                warnings = str(exercise['warnings']).split(', ')
                for warning in warnings:
                    warning = warning.strip()
                    if warning and warning != 'None':
                        # Extract the issue type (e.g., "KNEE VALGUS" from "LEFT KNEE VALGUS")
                        issue_words = warning.split()
                        if len(issue_words) >= 2:
                            issue = ' '.join(issue_words[-2:])  # Take last 2 words
                            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        if issue_counts:
            return max(issue_counts, key=issue_counts.get)
        return None
    
    def _calculate_performance_trend(self, exercises: List[Dict]) -> str:
        """Calculate performance trend over time"""
        if len(exercises) < 10:
            return 'insufficient_data'
        
        # Split into first half and second half
        mid_point = len(exercises) // 2
        first_half = exercises[mid_point:]
        second_half = exercises[:mid_point]
        
        # Calculate average points for each half
        first_half_avg = sum(e['points'] for e in first_half) / len(first_half)
        second_half_avg = sum(e['points'] for e in second_half) / len(second_half)
        
        # Determine trend
        if second_half_avg > first_half_avg * 1.1:
            return 'improving'
        elif second_half_avg < first_half_avg * 0.9:
            return 'declining'
        else:
            return 'stable'
    
    def generate_recommendations(self, user_id: int, session_id: Optional[int] = None) -> List[Dict]:
        """Generate personalized training recommendations based on user performance"""
        performance = self.analyze_user_performance(user_id)
        
        if not performance:
            return []
        
        recommendations = []
        
        # Generate recommendations for each exercise type
        for exercise_type in ['jumps', 'squats', 'pushups']:
            exercise_perf = performance[exercise_type]
            
            if exercise_perf['total_reps'] > 0:
                recommendations.extend(
                    self._generate_exercise_recommendations(user_id, session_id, exercise_type, exercise_perf)
                )
        
        # Generate overall recommendations
        recommendations.extend(
            self._generate_overall_recommendations(user_id, session_id, performance)
        )
        
        # Sort by priority and save to database
        recommendations.sort(key=lambda x: self._priority_value(x['priority']), reverse=True)
        self._save_recommendations(recommendations)
        
        # Save performance analytics for tracking historical trends
        self.save_performance_analytics(user_id, performance)
        
        return recommendations
    
    def _generate_exercise_recommendations(self, user_id: int, session_id: Optional[int], 
                                         exercise_type: str, performance: Dict) -> List[Dict]:
        """Generate recommendations for a specific exercise type"""
        recommendations = []
        
        # Posture correction recommendations
        if performance['most_common_issue']:
            recommendations.append({
                'user_id': user_id,
                'session_id': session_id,
                'recommendation_type': 'posture_correction',
                'priority': 'high',
                'title': f'Fix {performance["most_common_issue"]} in {exercise_type.title()}',
                'description': f'You frequently have {performance["most_common_issue"]} issues during {exercise_type}.',
                'exercise_focus': exercise_type,
                'specific_issue': performance['most_common_issue'],
                'recommendation_text': self._get_posture_correction_recommendation(performance['most_common_issue'], exercise_type),
                'difficulty_level': 'beginner',
                'estimated_time_minutes': 10
            })
        
        # Performance improvement recommendations
        if performance['bad_move_rate'] > 30:
            recommendations.append({
                'user_id': user_id,
                'session_id': session_id,
                'recommendation_type': 'technique',
                'priority': 'high',
                'title': f'Improve {exercise_type.title()} Technique',
                'description': f'Your bad move rate is {performance["bad_move_rate"]:.1f}%. Focus on form.',
                'exercise_focus': exercise_type,
                'specific_issue': 'high_bad_move_rate',
                'recommendation_text': self._get_technique_recommendation(exercise_type, performance['bad_move_rate']),
                'difficulty_level': 'intermediate',
                'estimated_time_minutes': 15
            })
        
        # Endurance recommendations
        if performance['total_reps'] < 50 and performance['performance_score'] > 70:
            recommendations.append({
                'user_id': user_id,
                'session_id': session_id,
                'recommendation_type': 'endurance',
                'priority': 'medium',
                'title': f'Build {exercise_type.title()} Endurance',
                'description': f'You have good form but need more volume. Try increasing reps.',
                'exercise_focus': exercise_type,
                'specific_issue': 'low_volume',
                'recommendation_text': self._get_endurance_recommendation(exercise_type),
                'difficulty_level': 'intermediate',
                'estimated_time_minutes': 20
            })
        
        return recommendations
    
    def _generate_overall_recommendations(self, user_id: int, session_id: Optional[int], 
                                        performance: Dict) -> List[Dict]:
        """Generate overall training recommendations"""
        recommendations = []
        
        # Calculate overall performance
        total_score = sum(perf.get('performance_score', 0) for perf in performance.values() if isinstance(perf, dict))
        avg_score = total_score / 3
        
        # Rest and recovery recommendation
        if avg_score < 50:
            recommendations.append({
                'user_id': user_id,
                'session_id': session_id,
                'recommendation_type': 'rest',
                'priority': 'high',
                'title': 'Focus on Recovery',
                'description': 'Your overall performance suggests you may need more recovery time.',
                'exercise_focus': 'all',
                'specific_issue': 'fatigue',
                'recommendation_text': 'Take 1-2 days rest, focus on stretching and light cardio. Return when refreshed.',
                'difficulty_level': 'beginner',
                'estimated_time_minutes': 30
            })
        
        # Strength training recommendation
        if avg_score > 80:
            recommendations.append({
                'user_id': user_id,
                'session_id': session_id,
                'recommendation_type': 'strength',
                'priority': 'medium',
                'title': 'Increase Training Intensity',
                'description': 'Your form is excellent! Ready for more challenging workouts.',
                'exercise_focus': 'all',
                'specific_issue': 'need_challenge',
                'recommendation_text': 'Add resistance bands, increase speed, or try advanced variations. Consider interval training.',
                'difficulty_level': 'advanced',
                'estimated_time_minutes': 25
            })
        
        return recommendations
    
    def _get_posture_correction_recommendation(self, issue: str, exercise_type: str) -> str:
        """Get specific posture correction recommendations"""
        recommendations = {
            'KNEE VALGUS': f'Focus on pushing knees outward during {exercise_type}. Place a resistance band around knees to maintain proper alignment. Keep weight on heels.',
            'FORWARD LEAN': f'Keep chest up and back straight during {exercise_type}. Engage core muscles. Practice in front of mirror to check posture.',
            'KNEE OVER TOES': f'Sit hips back more during {exercise_type}. Keep knees behind toes by hinging at hips. Practice box squats.',
            'BACK ARCH': f'Engage core and keep back neutral during {exercise_type}. Think about bracing your stomach. Avoid hyperextending.',
            'HIP SAGGING': f'Maintain plank position during {exercise_type}. Engage glutes and core. Keep body in straight line from head to heels.',
            'HEAD POSITION': f'Keep head in neutral position during {exercise_type}. Look at floor slightly ahead. Avoid tucking chin or looking up.',
            'ARM ANGLE': f'Maintain proper arm positioning during {exercise_type}. Keep elbows at appropriate angle. Focus on controlled movement.'
        }
        
        return recommendations.get(issue, f'Focus on proper form during {exercise_type}. Practice slowly and mindfully.')
    
    def _get_technique_recommendation(self, exercise_type: str, bad_move_rate: float) -> str:
        """Get technique improvement recommendations"""
        base_text = f'Slow down your {exercise_type} and focus on quality over quantity.'
        
        if exercise_type == 'jumps':
            return f'{base_text} Practice landing softly with bent knees. Focus on explosive upward movement and controlled landing.'
        elif exercise_type == 'squats':
            return f'{base_text} Use a chair as a guide for depth. Keep weight on heels and chest up. Film yourself to check form.'
        elif exercise_type == 'pushups':
            return f'{base_text} Start with knee pushups if needed. Keep core tight and body straight. Lower chest to floor height.'
        
        return base_text
    
    def _get_endurance_recommendation(self, exercise_type: str) -> str:
        """Get endurance building recommendations"""
        if exercise_type == 'jumps':
            return 'Try interval training: 30 seconds of jumping followed by 30 seconds rest. Gradually increase work periods.'
        elif exercise_type == 'squats':
            return 'Increase reps gradually. Try bodyweight squat circuits: 20 reps, rest 30s, repeat 3-5 times.'
        elif exercise_type == 'pushups':
            return 'Build volume with pyramid sets: 5-10-15-10-5 reps with minimal rest. Focus on maintaining form.'
        
        return 'Gradually increase training volume while maintaining good form.'
    
    def _priority_value(self, priority: str) -> int:
        """Convert priority string to numeric value for sorting"""
        priority_values = {'high': 3, 'medium': 2, 'low': 1}
        return priority_values.get(priority, 0)
    
    def _save_recommendations(self, recommendations: List[Dict]):
        """Save recommendations to database"""
        if not self.connection or not recommendations:
            return
        
        cursor = self.connection.cursor()
        
        # Check for existing recommendations today to avoid duplicates
        today = datetime.now().strftime('%Y-%m-%d')
        
        for rec in recommendations:
            # Check if similar recommendation already exists for this user today
            check_query = """
            SELECT recommendation_id FROM training_recommendations
            WHERE user_id = ? AND title = ? AND DATE(created_at) = ?
            LIMIT 1
            """
            cursor.execute(check_query, (rec['user_id'], rec['title'], today))
            if cursor.fetchone():
                continue

            query = """
            INSERT INTO training_recommendations 
            (user_id, session_id, recommendation_type, priority, title, description, 
             exercise_focus, specific_issue, recommendation_text, difficulty_level, 
             estimated_time_minutes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                rec['user_id'], rec['session_id'], rec['recommendation_type'],
                rec['priority'], rec['title'], rec['description'], rec['exercise_focus'],
                rec['specific_issue'], rec['recommendation_text'], rec['difficulty_level'],
                rec['estimated_time_minutes'], datetime.now()
            ))
            
            # Update the recommendation with the database ID
            rec['recommendation_id'] = cursor.lastrowid
        
        self.connection.commit()
    
    def get_user_recommendations(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's recommendations sorted by priority"""
        if not self.connection:
            return []
        
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
        
        cursor = self.connection.cursor()
        cursor.execute(query, (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def mark_recommendation_completed(self, recommendation_id: int):
        """Mark a recommendation as completed"""
        if not self.connection:
            return
        
        query = """
        UPDATE training_recommendations 
        SET is_completed = 1, completed_at = ?
        WHERE recommendation_id = ?
        """
        
        cursor = self.connection.cursor()
        cursor.execute(query, (datetime.now(), recommendation_id))
        self.connection.commit()
    
    def save_performance_analytics(self, user_id: int, performance: Dict):
        """Save performance analytics to database"""
        if not self.connection:
            return
        
        cursor = self.connection.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        for exercise_type, perf_data in performance.items():
            if isinstance(perf_data, dict) and 'total_reps' in perf_data:
                # Check for existing analytics today
                check_query = """
                SELECT analytics_id FROM user_performance_analytics
                WHERE user_id = ? AND exercise_type = ? AND DATE(analysis_date) = ?
                LIMIT 1
                """
                cursor.execute(check_query, (user_id, exercise_type, today))
                if cursor.fetchone():
                    continue

                query = """
                INSERT INTO user_performance_analytics 
                (user_id, analysis_date, exercise_type, total_reps, avg_points_per_rep,
                 total_bad_moves, bad_move_rate, most_common_issue, improvement_trend,
                 performance_score, recommendations_generated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(query, (
                    user_id, datetime.now(), exercise_type,
                    perf_data.get('total_reps', 0),
                    perf_data.get('avg_points', 0),
                    perf_data.get('total_reps', 0) * (perf_data.get('bad_move_rate', 0) / 100),
                    perf_data.get('bad_move_rate', 0),
                    perf_data.get('most_common_issue'),
                    perf_data.get('trend'),
                    perf_data.get('performance_score', 0),
                    len(self.get_user_recommendations(user_id))
                ))
        
        self.connection.commit()
