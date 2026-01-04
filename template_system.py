"""
Template System for AI Athlete Trainer
Provides workout templates, training plans, and custom template creation
"""
import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd


class TemplateManager:
    """Manages workout templates and training plans"""
    
    def __init__(self):
        self.templates = self._load_default_templates()
        self.custom_templates = self._load_custom_templates()
    
    def _load_default_templates(self) -> Dict[str, Dict]:
        """Load default workout templates"""
        return {
            'beginner_jump': {
                'id': 'beginner_jump',
                'name': 'Beginner Jump Training',
                'difficulty': 'Beginner',
                'duration_weeks': 4,
                'sessions_per_week': 3,
                'focus_areas': ['jump_technique', 'landing_mechanics', 'basic_plyometrics'],
                'exercises': [
                    {
                        'name': 'Basic Jumps',
                        'type': 'jump',
                        'sets': 3,
                        'reps': 10,
                        'rest_seconds': 60,
                        'notes': 'Focus on soft landing'
                    },
                    {
                        'name': 'Box Step-ups',
                        'type': 'jump',
                        'sets': 3,
                        'reps': 8,
                        'rest_seconds': 45,
                        'notes': 'Use low box (6-12 inches)'
                    }
                ],
                'progression': 'Increase reps by 2 each week'
            },
            'intermediate_squat': {
                'id': 'intermediate_squat',
                'name': 'Intermediate Squat Strength',
                'difficulty': 'Intermediate',
                'duration_weeks': 6,
                'sessions_per_week': 4,
                'focus_areas': ['squat_depth', 'core_stability', 'explosive_power'],
                'exercises': [
                    {
                        'name': 'Bodyweight Squats',
                        'type': 'squat',
                        'sets': 4,
                        'reps': 15,
                        'rest_seconds': 60,
                        'notes': 'Go to parallel or deeper'
                    },
                    {
                        'name': 'Jump Squats',
                        'type': 'squat',
                        'sets': 3,
                        'reps': 8,
                        'rest_seconds': 90,
                        'notes': 'Explosive upward movement'
                    },
                    {
                        'name': 'Pause Squats',
                        'type': 'squat',
                        'sets': 3,
                        'reps': 10,
                        'rest_seconds': 60,
                        'notes': 'Pause 2 seconds at bottom'
                    }
                ],
                'progression': 'Add 1 set each week or increase reps'
            },
            'advanced_pushup': {
                'id': 'advanced_pushup',
                'name': 'Advanced Push-up Challenge',
                'difficulty': 'Advanced',
                'duration_weeks': 8,
                'sessions_per_week': 5,
                'focus_areas': ['upper_body_strength', 'core_endurance', 'explosive_power'],
                'exercises': [
                    {
                        'name': 'Standard Push-ups',
                        'type': 'pushup',
                        'sets': 5,
                        'reps': 20,
                        'rest_seconds': 60,
                        'notes': 'Maintain perfect form'
                    },
                    {
                        'name': 'Diamond Push-ups',
                        'type': 'pushup',
                        'sets': 3,
                        'reps': 10,
                        'rest_seconds': 90,
                        'notes': 'Close grip position'
                    },
                    {
                        'name': 'Clapping Push-ups',
                        'type': 'pushup',
                        'sets': 3,
                        'reps': 5,
                        'rest_seconds': 120,
                        'notes': 'Explosive push with clap'
                    },
                    {
                        'name': 'Decline Push-ups',
                        'type': 'pushup',
                        'sets': 3,
                        'reps': 12,
                        'rest_seconds': 60,
                        'notes': 'Feet elevated on bench'
                    }
                ],
                'progression': 'Increase reps or add difficulty variations'
            },
            'full_body_conditioning': {
                'id': 'full_body_conditioning',
                'name': 'Full Body Conditioning',
                'difficulty': 'Intermediate',
                'duration_weeks': 4,
                'sessions_per_week': 3,
                'focus_areas': ['cardio', 'strength', 'endurance'],
                'exercises': [
                    {
                        'name': 'Jumping Jacks',
                        'type': 'jump',
                        'sets': 3,
                        'reps': 30,
                        'rest_seconds': 45,
                        'notes': 'Full range of motion'
                    },
                    {
                        'name': 'Bodyweight Squats',
                        'type': 'squat',
                        'sets': 3,
                        'reps': 20,
                        'rest_seconds': 60,
                        'notes': 'Controlled movement'
                    },
                    {
                        'name': 'Push-ups',
                        'type': 'pushup',
                        'sets': 3,
                        'reps': 15,
                        'rest_seconds': 60,
                        'notes': 'Modify if needed'
                    },
                    {
                        'name': 'Burpees',
                        'type': 'combined',
                        'sets': 3,
                        'reps': 5,
                        'rest_seconds': 90,
                        'notes': 'Full body exercise'
                    }
                ],
                'progression': 'Increase reps or reduce rest time'
            },
            'power_development': {
                'id': 'power_development',
                'name': 'Power Development Program',
                'difficulty': 'Advanced',
                'duration_weeks': 6,
                'sessions_per_week': 4,
                'focus_areas': ['explosive_power', 'plyometrics', 'rate_of_force_development'],
                'exercises': [
                    {
                        'name': 'Depth Jumps',
                        'type': 'jump',
                        'sets': 4,
                        'reps': 6,
                        'rest_seconds': 120,
                        'notes': 'Step off 18 inch box, jump immediately'
                    },
                    {
                        'name': 'Box Jumps',
                        'type': 'jump',
                        'sets': 4,
                        'reps': 8,
                        'rest_seconds': 90,
                        'notes': 'Maximum height, soft landing'
                    },
                    {
                        'name': 'Jump Squats',
                        'type': 'squat',
                        'sets': 4,
                        'reps': 12,
                        'rest_seconds': 90,
                        'notes': 'Explosive movement'
                    },
                    {
                        'name': 'Plyometric Push-ups',
                        'type': 'pushup',
                        'sets': 3,
                        'reps': 8,
                        'rest_seconds': 120,
                        'notes': 'Hands leave the ground'
                    }
                ],
                'progression': 'Increase box height or reduce ground contact time'
            }
        }
    
    def _load_custom_templates(self) -> Dict[str, Dict]:
        """Load custom user-created templates"""
        # In a real implementation, this would load from database or file
        return {}
    
    def get_all_templates(self) -> Dict[str, Dict]:
        """Get all templates (default + custom)"""
        all_templates = {}
        all_templates.update(self.templates)
        all_templates.update(self.custom_templates)
        return all_templates
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict]:
        """Get specific template by ID"""
        all_templates = self.get_all_templates()
        return all_templates.get(template_id)
    
    def get_templates_by_difficulty(self, difficulty: str) -> List[Dict]:
        """Get templates filtered by difficulty level"""
        all_templates = self.get_all_templates()
        return [t for t in all_templates.values() if t['difficulty'] == difficulty]
    
    def get_templates_by_exercise_type(self, exercise_type: str) -> List[Dict]:
        """Get templates that include specific exercise type"""
        all_templates = self.get_all_templates()
        return [
            t for t in all_templates.values() 
            if any(ex['type'] == exercise_type for ex in t['exercises'])
        ]
    
    def create_custom_template(self, template_data: Dict) -> bool:
        """Create a new custom template"""
        try:
            # Validate required fields
            required_fields = ['name', 'difficulty', 'duration_weeks', 'sessions_per_week', 'exercises']
            for field in required_fields:
                if field not in template_data:
                    return False
            
            # Generate unique ID
            template_id = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            template_data['id'] = template_id
            template_data['created_at'] = datetime.now().isoformat()
            template_data['is_custom'] = True
            
            # Add to custom templates
            self.custom_templates[template_id] = template_data
            
            # Save to file/database (in real implementation)
            self._save_custom_templates()
            
            return True
        except Exception:
            return False
    
    def _save_custom_templates(self):
        """Save custom templates to storage"""
        # In real implementation, save to database or file
        pass
    
    def delete_custom_template(self, template_id: str) -> bool:
        """Delete a custom template"""
        if template_id in self.custom_templates:
            del self.custom_templates[template_id]
            self._save_custom_templates()
            return True
        return False
    
    def generate_workout_schedule(self, template_id: str, start_date: datetime) -> List[Dict]:
        """Generate a workout schedule based on template"""
        template = self.get_template_by_id(template_id)
        if not template:
            return []
        
        schedule = []
        current_date = start_date
        sessions_per_week = template['sessions_per_week']
        
        # Calculate days between sessions
        days_between_sessions = 7 // sessions_per_week
        
        for week in range(template['duration_weeks']):
            for session in range(sessions_per_week):
                # Skip if current_date is in the past
                if current_date.date() < datetime.now().date():
                    current_date += timedelta(days=1)
                    continue
                
                workout_day = {
                    'date': current_date.date(),
                    'week': week + 1,
                    'session': session + 1,
                    'template_name': template['name'],
                    'exercises': template['exercises'].copy(),
                    'focus_areas': template['focus_areas'],
                    'estimated_duration': sum(ex['sets'] * ex['reps'] * 2 + ex['rest_seconds'] 
                                           for ex in template['exercises']) // 60,  # in minutes
                    'completed': False
                }
                
                # Apply progression for later weeks
                if week > 0:
                    for exercise in workout_day['exercises']:
                        # Simple progression: increase reps by 10% each week
                        exercise['reps'] = int(exercise['reps'] * (1 + (week * 0.1)))
                
                schedule.append(workout_day)
                current_date += timedelta(days=days_between_sessions)
        
        return schedule


def template_library_page():
    """Display template library page"""
    st.title("📋 Workout Templates")
    st.markdown("Choose from proven workout templates or create your own custom training plans")
    
    # Initialize template manager
    if 'template_manager' not in st.session_state:
        st.session_state.template_manager = TemplateManager()
    
    manager = st.session_state.template_manager
    
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Template Library", "➕ Create Template", "📅 Schedule Planner", "📊 Progress Tracker"])
    
    with tab1:
        st.markdown("### Browse Workout Templates")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            difficulty_filter = st.selectbox(
                "Filter by Difficulty:",
                ["all", "Beginner", "Intermediate", "Advanced"]
            )
        
        with col2:
            exercise_filter = st.selectbox(
                "Filter by Exercise:",
                ["all", "jump", "squat", "pushup", "combined"]
            )
        
        with col3:
            duration_filter = st.selectbox(
                "Filter by Duration:",
                ["all", "2-4 weeks", "4-6 weeks", "6-8 weeks", "8+ weeks"]
            )
        
        # Get filtered templates
        all_templates = manager.get_all_templates()
        
        # Apply filters
        filtered_templates = []
        for template in all_templates.values():
            if difficulty_filter != "all" and template['difficulty'] != difficulty_filter:
                continue
            if exercise_filter != "all":
                if not any(ex['type'] == exercise_filter for ex in template['exercises']):
                    continue
            if duration_filter != "all":
                weeks = template['duration_weeks']
                if duration_filter == "2-4 weeks" and not (2 <= weeks <= 4):
                    continue
                elif duration_filter == "4-6 weeks" and not (4 <= weeks <= 6):
                    continue
                elif duration_filter == "6-8 weeks" and not (6 <= weeks <= 8):
                    continue
                elif duration_filter == "8+ weeks" and weeks < 8:
                    continue
            
            filtered_templates.append(template)
        
        # Display templates
        if filtered_templates:
            for template in filtered_templates:
                with st.expander(f"{template['name']} ({template['difficulty']}) - {template['duration_weeks']} weeks"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Sessions per week:** {template['sessions_per_week']}")
                        st.markdown(f"**Focus areas:** {', '.join(template['focus_areas'])}")
                        st.markdown(f"**Progression:** {template['progression']}")
                        
                        st.markdown("**Exercises:**")
                        for exercise in template['exercises']:
                            st.markdown(f"• {exercise['name']}: {exercise['sets']} sets × {exercise['reps']} reps")
                    
                    with col2:
                        if st.button(f"Use Template", key=f"use_{template['id']}"):
                            st.session_state.selected_template = template['id']
                            st.session_state.page = 'template_schedule'
                            st.rerun()
                        
                        if template.get('is_custom', False):
                            if st.button(f"Delete", key=f"delete_{template['id']}"):
                                manager.delete_custom_template(template['id'])
                                st.rerun()
        else:
            st.info("No templates found with selected filters.")
    
    with tab2:
        st.markdown("### Create Custom Template")
        
        with st.form("create_template_form"):
            st.markdown("#### Template Information")
            
            col1, col2 = st.columns(2)
            with col1:
                template_name = st.text_input("Template Name*", placeholder="e.g., My Custom Workout")
                difficulty = st.selectbox("Difficulty Level*", ["Beginner", "Intermediate", "Advanced"])
                duration_weeks = st.number_input("Duration (weeks)*", min_value=1, max_value=52, value=4)
            
            with col2:
                sessions_per_week = st.number_input("Sessions per week*", min_value=1, max_value=7, value=3)
                focus_areas = st.text_input("Focus Areas (comma-separated)", 
                                          placeholder="e.g., strength, endurance, flexibility")
            
            st.markdown("#### Exercises")
            
            # Dynamic exercise list
            exercises = []
            exercise_count = st.number_input("Number of Exercises", min_value=1, max_value=10, value=3)
            
            for i in range(exercise_count):
                st.markdown(f"**Exercise {i+1}**")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    name = st.text_input("Name", key=f"ex_name_{i}", placeholder="e.g., Push-ups")
                with col2:
                    ex_type = st.selectbox("Type", ["jump", "squat", "pushup", "combined"], key=f"ex_type_{i}")
                with col3:
                    sets = st.number_input("Sets", min_value=1, max_value=10, value=3, key=f"ex_sets_{i}")
                with col4:
                    reps = st.number_input("Reps", min_value=1, max_value=100, value=10, key=f"ex_reps_{i}")
                
                col1, col2 = st.columns(2)
                with col1:
                    rest = st.number_input("Rest (seconds)", min_value=0, max_value=300, value=60, key=f"ex_rest_{i}")
                with col2:
                    notes = st.text_input("Notes", key=f"ex_notes_{i}", placeholder="Form cues")
                
                if name and sets and reps:
                    exercises.append({
                        'name': name,
                        'type': ex_type,
                        'sets': sets,
                        'reps': reps,
                        'rest_seconds': rest,
                        'notes': notes
                    })
            
            progression = st.text_area("Progression Plan", placeholder="e.g., Increase reps by 2 each week")
            
            submitted = st.form_submit_button("Create Template", use_container_width=True)
            
            if submitted:
                if template_name and difficulty and duration_weeks and sessions_per_week and exercises:
                    template_data = {
                        'name': template_name,
                        'difficulty': difficulty,
                        'duration_weeks': duration_weeks,
                        'sessions_per_week': sessions_per_week,
                        'focus_areas': [area.strip() for area in focus_areas.split(',') if area.strip()],
                        'exercises': exercises,
                        'progression': progression or "Gradually increase intensity"
                    }
                    
                    if manager.create_custom_template(template_data):
                        st.success("✅ Template created successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to create template")
                else:
                    st.error("Please fill in all required fields")
    
    with tab3:
        st.markdown("### Workout Schedule Planner")
        
        if 'selected_template' in st.session_state:
            template = manager.get_template_by_id(st.session_state.selected_template)
            if template:
                st.markdown(f"**Selected Template:** {template['name']}")
                
                start_date = st.date_input("Start Date", value=datetime.now().date())
                
                if st.button("Generate Schedule"):
                    schedule = manager.generate_workout_schedule(template['id'], datetime.combine(start_date, datetime.min.time()))
                    
                    if schedule:
                        st.session_state.workout_schedule = schedule
                        st.success(f"Generated {len(schedule)} workout sessions")
                    else:
                        st.error("Failed to generate schedule")
                
                if 'workout_schedule' in st.session_state:
                    schedule = st.session_state.workout_schedule
                    
                    st.markdown("#### Your Workout Schedule")
                    
                    # Convert to DataFrame for display
                    df_data = []
                    for workout in schedule:
                        df_data.append({
                            'Date': workout['date'],
                            'Week': workout['week'],
                            'Session': workout['session'],
                            'Duration (min)': workout['estimated_duration'],
                            'Exercises': len(workout['exercises']),
                            'Completed': '✅' if workout.get('completed') else '⏳'
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Calendar view
                    st.markdown("#### Calendar View")
                    calendar_data = {}
                    for workout in schedule:
                        date_str = workout['date'].strftime('%Y-%m-%d')
                        calendar_data[date_str] = {
                            'template': template['name'],
                            'exercises': len(workout['exercises']),
                            'duration': workout['estimated_duration']
                        }
                    
                    st.json(calendar_data)
            else:
                st.error("Template not found")
        else:
            st.info("Please select a template from the Template Library tab first")
    
    with tab4:
        st.markdown("### Template Progress Tracker")
        st.info("Progress tracking feature coming soon! This will show your completion rates and improvements for each template.")


def template_schedule_page():
    """Display template schedule page"""
    st.title("📅 Workout Schedule")
    
    if 'selected_template' not in st.session_state:
        st.warning("No template selected. Please choose a template from the library first.")
        if st.button("Go to Template Library"):
            st.session_state.page = 'template_library'
            st.rerun()
        return
    
    manager = st.session_state.template_manager
    template = manager.get_template_by_id(st.session_state.selected_template)
    
    if not template:
        st.error("Template not found")
        return
    
    # Back button
    if st.button("← Back to Templates"):
        st.session_state.page = 'template_library'
        st.rerun()
    
    st.markdown(f"### {template['name']}")
    st.markdown(f"**Difficulty:** {template['difficulty']} | **Duration:** {template['duration_weeks']} weeks")
    
    if 'workout_schedule' not in st.session_state:
        start_date = st.date_input("Start Date", value=datetime.now().date())
        
        if st.button("Generate Schedule", use_container_width=True):
            schedule = manager.generate_workout_schedule(template['id'], datetime.combine(start_date, datetime.min.time()))
            st.session_state.workout_schedule = schedule
            st.rerun()
    else:
        schedule = st.session_state.workout_schedule
        
        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Sessions", len(schedule))
        with col2:
            completed = sum(1 for w in schedule if w.get('completed'))
            st.metric("Completed", completed)
        with col3:
            total_duration = sum(w['estimated_duration'] for w in schedule)
            st.metric("Total Duration (min)", total_duration)
        with col4:
            completion_rate = (completed / len(schedule) * 100) if schedule else 0
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        st.markdown("---")
        
        # Today's workout
        today = datetime.now().date()
        today_workout = next((w for w in schedule if w['date'] == today), None)
        
        if today_workout:
            st.markdown("### 🎯 Today's Workout")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Week {today_workout['week']}, Session {today_workout['session']}**")
                st.markdown(f"**Estimated Duration:** {today_workout['estimated_duration']} minutes")
                st.markdown(f"**Focus Areas:** {', '.join(today_workout['focus_areas'])}")
                
                st.markdown("**Exercises:**")
                for exercise in today_workout['exercises']:
                    st.markdown(f"• {exercise['name']}: {exercise['sets']} sets × {exercise['reps']} reps")
                    if exercise.get('notes'):
                        st.markdown(f"  *Note: {exercise['notes']}*")
            
            with col2:
                if st.button("Start Workout", use_container_width=True, type="primary"):
                    # Navigate to appropriate exercise page
                    exercise_types = list(set(ex['type'] for ex in today_workout['exercises']))
                    if exercise_types:
                        st.session_state.exercise_type = exercise_types[0]
                        st.session_state.page = 'main'
                        st.rerun()
                
                if st.button("Mark Complete", use_container_width=True):
                    today_workout['completed'] = True
                    st.success("Workout marked as complete!")
                    st.rerun()
        else:
            st.info("No workout scheduled for today")
        
        st.markdown("---")
        
        # Full schedule
        st.markdown("### 📋 Full Schedule")
        
        # Group by week
        weeks = {}
        for workout in schedule:
            week_key = f"Week {workout['week']}"
            if week_key not in weeks:
                weeks[week_key] = []
            weeks[week_key].append(workout)
        
        for week_key, week_workouts in weeks.items():
            with st.expander(week_key):
                for workout in week_workouts:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        status = "✅" if workout.get('completed') else "⏳"
                        st.markdown(f"{status} **{workout['date']}** - Session {workout['session']}")
                        st.markdown(f"Exercises: {len(workout['exercises'])} | Duration: {workout['estimated_duration']} min")
                    
                    with col2:
                        if workout['date'] >= today and not workout.get('completed'):
                            if st.button("Start", key=f"start_{workout['date']}"):
                                exercise_types = list(set(ex['type'] for ex in workout['exercises']))
                                if exercise_types:
                                    st.session_state.exercise_type = exercise_types[0]
                                    st.session_state.page = 'main'
                                    st.rerun()
                    
                    with col3:
                        if not workout.get('completed'):
                            if st.button("Complete", key=f"complete_{workout['date']}"):
                                workout['completed'] = True
                                st.rerun()


if __name__ == "__main__":
    # Test the template manager
    manager = TemplateManager()
    print("Template Manager initialized successfully")
    print(f"Loaded {len(manager.get_all_templates())} templates")
