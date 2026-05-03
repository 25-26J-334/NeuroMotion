"""
Biometric UI Components for AI Athlete Trainer
Real-time biometric tracking interface components
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from biometric_tracker import BiometricTracker, HeartRateMonitor, create_user_profile, get_biometric_color_for_value
from database import Database


def biometric_profile_setup_page():
    """Biometric profile setup page for users"""
    st.title("🔬 Biometric Profile Setup")
    st.markdown("Set up your biometric profile for accurate tracking and personalized recommendations")
    
    # Initialize session state for biometric setup
    if 'biometric_setup_step' not in st.session_state:
        st.session_state.biometric_setup_step = 1
    
    db = Database()
    user_id = st.session_state.user_id
    
    # Check if user already has a profile
    existing_profile = db.get_user_biometric_profile(user_id)
    
    if existing_profile and st.session_state.biometric_setup_step == 1:
        st.success("✅ You already have a biometric profile set up!")
        st.write("You can update your profile information below:")
    
    # Profile setup form
    with st.form("biometric_profile_form"):
        st.subheader("📊 Physical Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.number_input(
                "Age", 
                min_value=10, 
                max_value=100, 
                value=existing_profile['age'] if existing_profile else 25,
                help="Your current age"
            )
            
            weight = st.number_input(
                "Weight (kg)", 
                min_value=30.0, 
                max_value=200.0, 
                value=existing_profile['weight'] if existing_profile else 70.0,
                step=0.1,
                help="Your current weight in kilograms"
            )
            
            height = st.number_input(
                "Height (cm)", 
                min_value=100.0, 
                max_value=250.0, 
                value=existing_profile['height'] if existing_profile else 175.0,
                step=0.1,
                help="Your height in centimeters"
            )
        
        with col2:
            gender = st.selectbox(
                "Gender",
                options=['male', 'female', 'other'],
                index=['male', 'female', 'other'].index(existing_profile['gender']) if existing_profile else 0,
                help="Biological gender for accurate calculations"
            )
            
            fitness_level = st.selectbox(
                "Fitness Level",
                options=['beginner', 'intermediate', 'advanced'],
                index=['beginner', 'intermediate', 'advanced'].index(existing_profile['fitness_level']) if existing_profile else 1,
                help="Your current fitness level"
            )
            
            resting_hr = st.number_input(
                "Resting Heart Rate (optional)",
                min_value=40,
                max_value=100,
                value=existing_profile['resting_heart_rate'] if existing_profile else 70,
                help="Your resting heart rate (beats per minute)"
            )
        
        max_hr = st.number_input(
            "Maximum Heart Rate (optional)",
            min_value=120,
            max_value=220,
            value=existing_profile['max_heart_rate'] if existing_profile else None,
            help="Your maximum heart rate (will be calculated if not provided)"
        )
        
        submitted = st.form_submit_button("Save Biometric Profile", use_container_width=True, type="primary")
        
        if submitted:
            # Validate inputs
            if age and weight and height and gender and fitness_level:
                success = db.save_user_biometric_profile(
                    user_id, age, weight, height, gender, fitness_level, resting_hr, max_hr
                )
                
                if success:
                    st.success("✅ Biometric profile saved successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to save biometric profile. Please try again.")
            else:
                st.error("Please fill in all required fields.")


def biometric_dashboard_page():
    """Main biometric tracking dashboard"""
    st.title("💓 Biometric Tracking Dashboard")
    st.markdown("Real-time monitoring of your heart rate, calories, and performance metrics")
    
    db = Database()
    user_id = st.session_state.user_id
    
    # Check if user has biometric profile
    profile = db.get_user_biometric_profile(user_id)
    if not profile:
        st.warning("⚠️ Please set up your biometric profile first")
        if st.button("Set Up Profile", use_container_width=True):
            st.session_state.page = 'biometric_setup'
            st.rerun()
        return
    
    # Initialize biometric tracker
    if 'biometric_tracker' not in st.session_state:
        user_profile = create_user_profile(
            profile['age'], profile['weight'], profile['height'], 
            profile['gender'], profile['fitness_level'], profile['resting_heart_rate']
        )
        st.session_state.biometric_tracker = BiometricTracker(user_profile)
        st.session_state.heart_rate_monitor = HeartRateMonitor(user_profile)
    
    tracker = st.session_state.biometric_tracker
    monitor = st.session_state.heart_rate_monitor
    
    # Session controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not st.session_state.get('biometric_session_active', False):
            if st.button("🚀 Start Tracking", use_container_width=True, type="primary"):
                tracker.start_session()
                st.session_state.biometric_session_id = db.create_biometric_session(user_id)
                st.rerun()
        else:
            if st.button("⏹️ Stop Tracking", use_container_width=True, type="secondary"):
                session_summary = tracker.end_session()
                if st.session_state.get('biometric_session_id'):
                    db.end_biometric_session(st.session_state.biometric_session_id, session_summary)
                    del st.session_state.biometric_session_id
                st.success("✅ Session ended successfully!")
                st.rerun()
    
    with col2:
        if st.session_state.get('biometric_session_active', False):
            exercise_type = st.selectbox(
                "Exercise Type",
                options=['general', 'jump', 'squat', 'pushup', 'burpee', 'stepup'],
                help="Select your current exercise type"
            )
    
    with col3:
        if st.session_state.get('biometric_session_active', False):
            intensity = st.selectbox(
                "Intensity",
                options=['very_light', 'light', 'moderate', 'hard', 'very_hard', 'maximum'],
                index=2,
                help="Select your exercise intensity"
            )
    
    # Real-time metrics display
    if st.session_state.get('biometric_session_active', False):
        st.markdown("---")
        st.subheader("📊 Real-time Metrics")
        
        # Simulate heart rate reading (in real implementation, this would come from a device)
        simulated_hr = monitor.simulate_heart_rate(exercise_type, intensity)
        tracker.add_heart_rate_reading(simulated_hr, exercise_type)
        
        # Get current metrics
        metrics = tracker.get_real_time_metrics()
        
        # Display metrics in columns
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            current_hr = metrics.get('current_heart_rate', simulated_hr)
            hr_color = get_biometric_color_for_value(current_hr, 'heart_rate')
            st.metric(
                "❤️ Heart Rate",
                f"{current_hr} bpm",
                delta=None,
                delta_color="normal"
            )
            st.markdown(f'<div style="background-color: {hr_color}; height: 5px; border-radius: 3px;"></div>', unsafe_allow_html=True)
        
        with metric_col2:
            exertion = metrics.get('current_exertion', 'Moderate')
            exertion_color = get_biometric_color_for_value(exertion, 'exertion')
            st.metric(
                "💪 Exertion Level",
                exertion.title(),
                delta=None
            )
            st.markdown(f'<div style="background-color: {exertion_color}; height: 5px; border-radius: 3px;"></div>', unsafe_allow_html=True)
        
        with metric_col3:
            calories = metrics.get('total_calories', 0)
            calories_color = get_biometric_color_for_value(calories, 'calories')
            st.metric(
                "🔥 Calories Burned",
                f"{calories:.1f}",
                delta=None
            )
            st.markdown(f'<div style="background-color: {calories_color}; height: 5px; border-radius: 3px;"></div>', unsafe_allow_html=True)
        
        with metric_col4:
            duration = metrics.get('session_duration', 0)
            st.metric(
                "⏱️ Duration",
                f"{duration:.1f} min",
                delta=None
            )
        
        # Heart rate zones chart
        if metrics.get('heart_rate_zones'):
            st.markdown("---")
            st.subheader("📈 Heart Rate Zones Distribution")
            
            zones = metrics['heart_rate_zones']
            zone_labels = list(zones.keys())
            zone_values = list(zones.values())
            zone_colors = ['#00FF00', '#ADFF2F', '#FFFF00', '#FFA500', '#FF6347', '#FF0000']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=zone_labels,
                    y=zone_values,
                    marker_color=zone_colors,
                    text=[f"{v:.1f}%" for v in zone_values],
                    textposition='auto',
                )
            ])
            
            fig.update_layout(
                title="Time Spent in Each Heart Rate Zone",
                xaxis_title="Heart Rate Zone",
                yaxis_title="Percentage of Time",
                template="plotly_dark",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Recovery recommendations
        recovery = tracker.calculate_recovery_time()
        st.markdown("---")
        st.subheader("🔄 Recovery Recommendations")
        
        recovery_col1, recovery_col2, recovery_col3 = st.columns(3)
        
        with recovery_col1:
            st.metric(
                "Recovery Time",
                f"{recovery['recovery_time']} min",
                delta=None
            )
        
        with recovery_col2:
            st.metric(
                "Recovery Type",
                recovery['recovery_type'],
                delta=None
            )
        
        with recovery_col3:
            next_ready = recovery.get('next_session_ready')
            if next_ready:
                time_until = next_ready - datetime.now()
                if time_until.total_seconds() > 0:
                    minutes_until = int(time_until.total_seconds() / 60)
                    st.metric(
                        "Next Session Ready",
                        f"In {minutes_until} min",
                        delta=None
                    )
                else:
                    st.metric(
                        "Next Session Ready",
                        "Ready Now!",
                        delta=None
                    )
        
        st.info(f"💡 **Recommendation:** {recovery['recommendation']}")
    
    # Historical data
    st.markdown("---")
    st.subheader("📅 Historical Biometric Data")
    
    # Get recent sessions
    recent_sessions = db.get_user_biometric_sessions(user_id, limit=10)
    
    if recent_sessions:
        # Create DataFrame for visualization
        df = pd.DataFrame(recent_sessions)
        df['start_time'] = pd.to_datetime(df['start_time'])
        
        # Session trends
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🔥 Calories Burned Trend")
            fig_calories = px.line(
                df, 
                x='start_time', 
                y='total_calories_burned',
                title="Calories Burned Per Session",
                markers=True,
                template="plotly_dark"
            )
            fig_calories.update_layout(height=300)
            st.plotly_chart(fig_calories, use_container_width=True)
        
        with col2:
            st.markdown("##### ❤️ Average Heart Rate Trend")
            fig_hr = px.line(
                df, 
                x='start_time', 
                y='avg_heart_rate',
                title="Average Heart Rate Per Session",
                markers=True,
                template="plotly_dark"
            )
            fig_hr.update_layout(height=300)
            st.plotly_chart(fig_hr, use_container_width=True)
        
        # Recent sessions table
        st.markdown("##### 📋 Recent Sessions")
        
        # Format the data for display
        display_df = df[['start_time', 'duration_minutes', 'total_calories_burned', 'avg_heart_rate', 'max_heart_rate', 'recovery_type']].copy()
        display_df['start_time'] = display_df['start_time'].dt.strftime('%Y-%m-%d %H:%M')
        display_df.columns = ['Date', 'Duration (min)', 'Calories', 'Avg HR', 'Max HR', 'Recovery Type']
        
        st.dataframe(display_df, use_container_width=True)
        
    else:
        st.info("📈 No biometric sessions recorded yet. Start tracking to see your data here!")
    
    # Biometric analytics
    analytics = db.get_biometric_analytics(user_id, days=30)
    if analytics and analytics.get('total_sessions', 0) > 0:
        st.markdown("---")
        st.subheader("📊 30-Day Analytics")
        
        analytics_col1, analytics_col2, analytics_col3 = st.columns(3)
        
        with analytics_col1:
            st.metric("Total Sessions", analytics['total_sessions'])
        
        with analytics_col2:
            avg_calories = analytics.get('avg_calories')
            st.metric("Avg Calories/Session", f"{avg_calories:.1f}" if avg_calories is not None else "N/A")
        
        with analytics_col3:
            avg_recovery = analytics.get('avg_recovery_time')
            st.metric("Avg Recovery Time", f"{avg_recovery:.1f} min" if avg_recovery is not None else "N/A")


def add_biometric_widgets_to_sidebar():
    """Add biometric status widgets to the sidebar"""
    db = Database()
    user_id = st.session_state.user_id
    
    # Check if user has biometric profile
    profile = db.get_user_biometric_profile(user_id)
    
    if profile:
        st.markdown("---")
        st.markdown("### 💓 Biometric Status")
        
        # Session status
        if st.session_state.get('biometric_session_active', False):
            st.success("🟢 Tracking Active")
            
            if 'biometric_tracker' in st.session_state:
                metrics = st.session_state.biometric_tracker.get_real_time_metrics()
                
                if metrics.get('current_heart_rate'):
                    st.metric("Heart Rate", f"{metrics['current_heart_rate']} bpm")
                
                if metrics.get('total_calories'):
                    st.metric("Calories", f"{metrics['total_calories']:.1f}")
                
                if metrics.get('session_duration'):
                    st.metric("Duration", f"{metrics['session_duration']:.1f} min")
        else:
            st.info("⚪ Not Tracking")
            
            # Quick start button
            if st.button("🚀 Quick Start", use_container_width=True, key="sidebar_biometric_start"):
                if 'biometric_tracker' not in st.session_state:
                    user_profile = create_user_profile(
                        profile['age'], profile['weight'], profile['height'], 
                        profile['gender'], profile['fitness_level'], profile['resting_heart_rate']
                    )
                    st.session_state.biometric_tracker = BiometricTracker(user_profile)
                    st.session_state.heart_rate_monitor = HeartRateMonitor(user_profile)
                
                st.session_state.biometric_tracker.start_session()
                st.session_state.biometric_session_id = db.create_biometric_session(user_id)
                st.rerun()
        
        # Recent session summary
        recent_sessions = db.get_user_biometric_sessions(user_id, limit=1)
        if recent_sessions:
            last_session = recent_sessions[0]
            st.markdown("**Last Session:**")
            st.markdown(f"- Calories: {last_session['total_calories_burned']:.1f}")
            st.markdown(f"- Duration: {last_session['duration_minutes']:.1f} min")
            st.markdown(f"- Avg HR: {last_session['avg_heart_rate']} bpm")
    else:
        st.markdown("---")
        st.markdown("### 💓 Biometric Setup")
        st.info("Profile not set up")
        if st.button("Set Up Now", use_container_width=True, key="sidebar_biometric_setup"):
            st.session_state.page = 'biometric_setup'
            st.rerun()
