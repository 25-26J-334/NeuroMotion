"""
Real-time Biometric Tracking Module for AI Athlete Trainer
Handles heart rate monitoring, calorie burn estimation, exertion tracking, and recovery recommendations
"""

import time
import math
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import streamlit as st


@dataclass
class BiometricData:
    """Container for biometric measurements"""
    timestamp: datetime
    heart_rate: Optional[int] = None
    calories_burned: Optional[float] = None
    exertion_level: Optional[str] = None
    recovery_time: Optional[int] = None
    vo2_max: Optional[float] = None
    respiratory_rate: Optional[int] = None


@dataclass
class UserProfile:
    """User physical profile for biometric calculations"""
    age: int
    weight: float  # kg
    height: float  # cm
    gender: str  # 'male', 'female', 'other'
    fitness_level: str  # 'beginner', 'intermediate', 'advanced'
    resting_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None


class BiometricTracker:
    """Main biometric tracking system"""
    
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
        self.session_data: List[BiometricData] = []
        self.current_session_start = None
        self.last_heart_rate = None
        self.calorie_accumulator = 0.0
        
        # Calculate max heart rate if not provided
        if not user_profile.max_heart_rate:
            self.user_profile.max_heart_rate = self._calculate_max_heart_rate()
    
    def _calculate_max_heart_rate(self) -> int:
        """Calculate estimated maximum heart rate"""
        age = self.user_profile.age
        if self.user_profile.gender.lower() == 'female':
            return int(226 - age)  # Women-specific formula
        else:
            return int(220 - age)  # Standard formula
    
    def start_session(self):
        """Start a new training session"""
        self.current_session_start = datetime.now()
        self.session_data = []
        self.calorie_accumulator = 0.0
        st.session_state.biometric_session_active = True
    
    def end_session(self) -> Dict:
        """End current session and return summary"""
        if not self.current_session_start:
            return {}
        
        session_duration = (datetime.now() - self.current_session_start).total_seconds() / 60  # minutes
        
        summary = {
            'session_duration': session_duration,
            'total_calories': self.calorie_accumulator,
            'avg_heart_rate': self._get_average_heart_rate(),
            'max_heart_rate': self._get_max_heart_rate(),
            'avg_exertion': self._get_average_exertion(),
            'recovery_recommendation': self.calculate_recovery_time(),
            'session_data_points': len(self.session_data)
        }
        
        self.current_session_start = None
        st.session_state.biometric_session_active = False
        
        return summary
    
    def add_heart_rate_reading(self, heart_rate: int, exercise_type: str = 'general'):
        """Add heart rate reading and calculate derived metrics"""
        if not self.current_session_start:
            return
        
        # Validate heart rate
        if heart_rate < 40 or heart_rate > 220:
            return  # Invalid reading
        
        timestamp = datetime.now()
        
        # Calculate exertion level
        exertion = self._calculate_exertion_level(heart_rate)
        
        # Calculate calories burned since last reading
        calories = self._calculate_calories_burned(heart_rate, exercise_type)
        self.calorie_accumulator += calories
        
        # Create biometric data point
        biometric_point = BiometricData(
            timestamp=timestamp,
            heart_rate=heart_rate,
            calories_burned=calories,
            exertion_level=exertion,
            recovery_time=self._calculate_recovery_time(heart_rate)
        )
        
        self.session_data.append(biometric_point)
        self.last_heart_rate = heart_rate
    
    def _calculate_exertion_level(self, heart_rate: int) -> str:
        """Calculate exertion level based on heart rate zones"""
        max_hr = self.user_profile.max_heart_rate
        resting_hr = self.user_profile.resting_heart_rate or 70
        
        # Heart rate reserve method
        hr_reserve = max_hr - resting_hr
        current_hr_reserve = heart_rate - resting_hr
        hr_reserve_percentage = (current_hr_reserve / hr_reserve) * 100 if hr_reserve > 0 else 0
        
        if hr_reserve_percentage < 50:
            return "Very Light"
        elif hr_reserve_percentage < 60:
            return "Light"
        elif hr_reserve_percentage < 70:
            return "Moderate"
        elif hr_reserve_percentage < 80:
            return "Hard"
        elif hr_reserve_percentage < 90:
            return "Very Hard"
        else:
            return "Maximum"
    
    def _calculate_calories_burned(self, heart_rate: int, exercise_type: str) -> float:
        """Calculate calories burned based on heart rate and exercise type"""
        if not self.last_heart_rate:
            return 0.0
        
        # Time since last reading (assume 30 seconds if no previous reading)
        time_minutes = 0.5  # Default to 30 seconds intervals
        
        # MET values for different exercises and intensities
        met_values = {
            'jump': {'Very Light': 3.5, 'Light': 5.0, 'Moderate': 7.0, 'Hard': 8.5, 'Very Hard': 10.0, 'Maximum': 12.0},
            'squat': {'Very Light': 3.0, 'Light': 4.5, 'Moderate': 6.0, 'Hard': 7.5, 'Very Hard': 9.0, 'Maximum': 10.5},
            'pushup': {'Very Light': 2.5, 'Light': 4.0, 'Moderate': 5.5, 'Hard': 7.0, 'Very Hard': 8.5, 'Maximum': 10.0},
            'burpee': {'Very Light': 5.0, 'Light': 7.0, 'Moderate': 9.0, 'Hard': 11.0, 'Very Hard': 13.0, 'Maximum': 15.0},
            'stepup': {'Very Light': 3.0, 'Light': 4.5, 'Moderate': 6.5, 'Hard': 8.0, 'Very Hard': 9.5, 'Maximum': 11.0},
            'general': {'Very Light': 2.0, 'Light': 3.5, 'Moderate': 5.0, 'Hard': 6.5, 'Very Hard': 8.0, 'Maximum': 9.5}
        }
        
        exertion = self._calculate_exertion_level(heart_rate)
        met = met_values.get(exercise_type, met_values['general']).get(exertion, 5.0)
        
        # Calories per minute = MET × weight (kg) × 3.5 / 200
        calories_per_minute = met * self.user_profile.weight * 3.5 / 200
        calories = calories_per_minute * time_minutes
        
        return calories
    
    def _calculate_recovery_time(self, heart_rate: int) -> int:
        """Calculate recommended recovery time in minutes"""
        max_hr = self.user_profile.max_heart_rate
        hr_percentage = (heart_rate / max_hr) * 100
        
        if hr_percentage < 60:
            return 0  # No recovery needed
        elif hr_percentage < 70:
            return 1  # 1 minute
        elif hr_percentage < 80:
            return 2  # 2 minutes
        elif hr_percentage < 90:
            return 3  # 3 minutes
        else:
            return 5  # 5+ minutes
    
    def calculate_recovery_time(self) -> Dict:
        """Calculate comprehensive recovery recommendations"""
        if not self.session_data:
            return {'recovery_time': 0, 'recovery_type': 'None'}
        
        avg_hr = self._get_average_heart_rate()
        max_hr = self._get_max_heart_rate()
        session_duration = (datetime.now() - self.current_session_start).total_seconds() / 60 if self.current_session_start else 0
        
        # Base recovery time on average heart rate
        base_recovery = self._calculate_recovery_time(avg_hr or 100)
        
        # Adjust for session intensity and duration
        if max_hr and max_hr > (self.user_profile.max_heart_rate * 0.85):
            base_recovery += 2  # Extra recovery for high intensity
        
        if session_duration > 30:
            base_recovery += 1  # Extra recovery for long sessions
        
        # Determine recovery type
        if base_recovery <= 2:
            recovery_type = "Active Recovery"
            recommendation = "Light activity like walking or stretching"
        elif base_recovery <= 5:
            recovery_type = "Moderate Recovery"
            recommendation = "Rest with light movement, hydrate well"
        else:
            recovery_type = "Deep Recovery"
            recommendation = "Complete rest, focus on nutrition and sleep"
        
        return {
            'recovery_time': base_recovery,
            'recovery_type': recovery_type,
            'recommendation': recommendation,
            'next_session_ready': datetime.now() + timedelta(minutes=base_recovery)
        }
    
    def _get_average_heart_rate(self) -> Optional[int]:
        """Calculate average heart rate for current session"""
        if not self.session_data:
            return None
        
        heart_rates = [data.heart_rate for data in self.session_data if data.heart_rate]
        return int(statistics.mean(heart_rates)) if heart_rates else None
    
    def _get_max_heart_rate(self) -> Optional[int]:
        """Get maximum heart rate for current session"""
        if not self.session_data:
            return None
        
        heart_rates = [data.heart_rate for data in self.session_data if data.heart_rate]
        return max(heart_rates) if heart_rates else None
    
    def _get_average_exertion(self) -> Optional[str]:
        """Get average exertion level for current session"""
        if not self.session_data:
            return None
        
        exertion_levels = [data.exertion_level for data in self.session_data if data.exertion_level]
        if not exertion_levels:
            return None
        
        # Map exertion levels to numeric values for averaging
        exertion_map = {
            'Very Light': 1,
            'Light': 2,
            'Moderate': 3,
            'Hard': 4,
            'Very Hard': 5,
            'Maximum': 6
        }
        
        numeric_values = [exertion_map.get(level, 3) for level in exertion_levels]
        avg_numeric = statistics.mean(numeric_values)
        
        # Convert back to string
        for level, value in reversed(exertion_map.items()):
            if avg_numeric <= value:
                return level
        
        return 'Moderate'
    
    def get_real_time_metrics(self) -> Dict:
        """Get current real-time biometric metrics"""
        if not self.session_data or not self.current_session_start:
            return {}
        
        latest_data = self.session_data[-1] if self.session_data else None
        session_duration = (datetime.now() - self.current_session_start).total_seconds() / 60
        
        metrics = {
            'session_duration': session_duration,
            'current_heart_rate': latest_data.heart_rate if latest_data else None,
            'current_exertion': latest_data.exertion_level if latest_data else None,
            'total_calories': self.calorie_accumulator,
            'heart_rate_zones': self._get_heart_rate_zone_distribution(),
            'calories_per_minute': self.calorie_accumulator / session_duration if session_duration > 0 else 0
        }
        
        return metrics
    
    def _get_heart_rate_zone_distribution(self) -> Dict:
        """Calculate time spent in each heart rate zone"""
        if not self.session_data:
            return {}
        
        zone_distribution = {
            'Very Light': 0,
            'Light': 0,
            'Moderate': 0,
            'Hard': 0,
            'Very Hard': 0,
            'Maximum': 0
        }
        
        for data in self.session_data:
            if data.exertion_level:
                zone_distribution[data.exertion_level] += 1
        
        total_points = sum(zone_distribution.values())
        if total_points > 0:
            for zone in zone_distribution:
                zone_distribution[zone] = (zone_distribution[zone] / total_points) * 100
        
        return zone_distribution


class HeartRateMonitor:
    """Simulated heart rate monitor for demonstration"""
    
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
        self.base_heart_rate = user_profile.resting_heart_rate or 70
        self.max_heart_rate = user_profile.max_heart_rate or (220 - user_profile.age)
    
    def simulate_heart_rate(self, exercise_type: str, intensity: str = 'moderate') -> int:
        """Simulate heart rate during exercise"""
        intensity_factors = {
            'rest': 0.0,
            'very_light': 0.3,
            'light': 0.5,
            'moderate': 0.65,
            'hard': 0.8,
            'very_hard': 0.9,
            'maximum': 1.0
        }
        
        exercise_factors = {
            'jump': 1.2,
            'burpee': 1.3,
            'squat': 1.1,
            'pushup': 1.0,
            'stepup': 1.05,
            'general': 1.0
        }
        
        intensity_factor = intensity_factors.get(intensity, 0.65)
        exercise_factor = exercise_factors.get(exercise_type, 1.0)
        
        # Calculate target heart rate
        hr_reserve = (self.max_heart_rate - self.base_heart_rate) * intensity_factor * exercise_factor
        target_hr = self.base_heart_rate + hr_reserve
        
        # Add some realistic variation
        variation = math.sin(time.time() * 0.5) * 5 + (random.random() - 0.5) * 10
        simulated_hr = int(target_hr + variation)
        
        # Ensure within realistic bounds
        return max(self.base_heart_rate, min(self.max_heart_rate, simulated_hr))


def create_user_profile(age: int, weight: float, height: float, gender: str, 
                       fitness_level: str, resting_hr: Optional[int] = None) -> UserProfile:
    """Create user profile for biometric tracking"""
    return UserProfile(
        age=age,
        weight=weight,
        height=height,
        gender=gender,
        fitness_level=fitness_level,
        resting_heart_rate=resting_hr
    )


def get_biometric_color_for_value(value: float, metric_type: str) -> str:
    """Get color code for biometric values"""
    if metric_type == 'heart_rate':
        if value < 100:
            return '#00FF00'  # Green
        elif value < 140:
            return '#FFFF00'  # Yellow
        elif value < 170:
            return '#FFA500'  # Orange
        else:
            return '#FF0000'  # Red
    
    elif metric_type == 'exertion':
        exertion_colors = {
            'Very Light': '#00FF00',
            'Light': '#ADFF2F',
            'Moderate': '#FFFF00',
            'Hard': '#FFA500',
            'Very Hard': '#FF6347',
            'Maximum': '#FF0000'
        }
        return exertion_colors.get(value, '#FFFF00')
    
    elif metric_type == 'calories':
        if value < 5:
            return '#00FF00'
        elif value < 10:
            return '#FFFF00'
        elif value < 15:
            return '#FFA500'
        else:
            return '#FF0000'
    
    return '#FFFFFF'  # Default white
