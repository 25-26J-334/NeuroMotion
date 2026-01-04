"""
UI Components for displaying training recommendations
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from recommendation_engine import RecommendationEngine
from database import Database

def show_detailed_recommendation_full_page(recommendation: dict):
    """Show detailed information about a recommendation in full page view"""
    
    # Check if this recommendation was marked as complete
    button_key = f"mark_complete_{recommendation.get('recommendation_id', 'unknown')}"
    is_completed = st.session_state.get(button_key, False)
    
    # CSS for red button only for Mark as Complete when completed
    if is_completed:
        st.markdown(f"""
        <style>
        div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {{
            background-color: #FF2E2E !important;
            color: white !important;
            border: 1px solid #FF2E2E !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    
    # Header
    st.markdown(f"# {recommendation.get('title', 'Recommendation Details')}")
    
    st.markdown("---")
    
    # Create a wide layout with better spacing
    # Use wider columns for main content
    main_col1, main_col2 = st.columns([1, 1])
    
    with main_col1:
        st.markdown("## 📋 Recommendation Details")
        st.markdown(f"- **Type:** {recommendation.get('recommendation_type', '').title()}")
        st.markdown(f"- **Priority:** {recommendation.get('priority', '').title()}")
        st.markdown(f"- **Exercise Focus:** {recommendation.get('exercise_focus', '').title()}")
        st.markdown(f"- **Difficulty:** {recommendation.get('difficulty_level', '').title()}")
        st.markdown(f"- **Estimated Time:** {recommendation.get('estimated_time_minutes', 0)} minutes")
    
    with main_col2:
        st.markdown("## 🔍 Issue Analysis")
        if recommendation.get('specific_issue'):
            st.markdown(f"- **Specific Issue:** {recommendation.get('specific_issue')}")
        st.markdown(f"- **Created:** {recommendation.get('created_at', 'N/A')}")
    
    st.markdown("---")
    
    # Full-width description section
    st.markdown("## 📖 Description")
    st.markdown(recommendation.get('description', 'No description available.'))
    
    st.markdown("---")
    
    # Full-width instructions section
    st.markdown("## 📝 Detailed Instructions")
    st.markdown(recommendation.get('recommendation_text', 'No detailed instructions available.'))
    
    st.markdown("---")
    
    # Exercise-specific tips in wider format
    exercise_focus = recommendation.get('exercise_focus', '')
    if exercise_focus == 'jumps':
        st.markdown("## 💡 Jump Training Tips")
        tip_col1, tip_col2, tip_col3 = st.columns(3)
        with tip_col1:
            st.markdown("#### 🚀 Explosive Power")
            st.markdown("Focus on explosive power from your hips")
        with tip_col2:
            st.markdown("#### 🎯 Landing Technique")
            st.markdown("Land softly with bent knees to absorb impact")
        with tip_col3:
            st.markdown("#### 📐 Arm Swing")
            st.markdown("Use your arms to generate momentum and height")
    
    elif exercise_focus == 'squats':
        st.markdown("## 💡 Squat Training Tips")
        tip_col1, tip_col2, tip_col3 = st.columns(3)
        with tip_col1:
            st.markdown("#### 🦵 Knee Position")
            st.markdown("Keep knees aligned with toes, avoid valgus")
        with tip_col2:
            st.markdown("#### 📏 Depth Control")
            st.markdown("Lower to at least parallel position or deeper")
        with tip_col3:
            st.markdown("#### 💪 Core Stability")
            st.markdown("Maintain tight core throughout the movement")
    
    elif exercise_focus == 'pushups':
        st.markdown("## 💡 Push-up Training Tips")
        tip_col1, tip_col2, tip_col3 = st.columns(3)
        with tip_col1:
            st.markdown("#### 📏 Body Alignment")
            st.markdown("Maintain a straight line from head to heels")
        with tip_col2:
            st.markdown("#### 📐 Depth Control")
            st.markdown("Lower your chest to about fist height from the ground")
        with tip_col3:
            st.markdown("#### 🦾 Elbow Position")
            st.markdown("Keep your elbows at about 45 degrees from your body")
    
    st.markdown("---")
    
    # Action buttons at the bottom
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("✅ Mark as Complete", use_container_width=True):
            if recommendation.get('recommendation_id'):
                success = mark_recommendation_completed(recommendation.get('recommendation_id'))
                if success:
                    # Set button to red state
                    st.session_state[button_key] = True
                    st.success("✅ Recommendation marked as completed!")
                    st.rerun()
                else:
                    st.error("❌ Failed to mark as complete")
            else:
                st.error("❌ No recommendation ID found")
    
    with action_col2:
        if st.button("⏰ Remind Later", use_container_width=True):
            st.info("We'll remind you about this in your next session!")
    
    with action_col3:
        if st.button("🔙 Back to List", use_container_width=True):
            st.session_state.show_detailed_recommendation = None
            st.rerun()

def recommendations_page():
    """Display personalized training recommendations page"""
    
    # Initialize session state for detailed recommendation view
    if 'show_detailed_recommendation' not in st.session_state:
        st.session_state.show_detailed_recommendation = None
    
    # Back button at the top
    if st.button("← Back to Training"):
        st.session_state.page = 'main'
        st.rerun()
    
    # Show detailed recommendation if one is selected
    if st.session_state.show_detailed_recommendation:
        show_detailed_recommendation_full_page(st.session_state.show_detailed_recommendation)
        return
    
    st.title("🎯 Personal Training Recommendations")
    st.markdown("---")
    
    # Initialize database and recommendation engine
    db = Database()
    if not db.is_connected():
        st.error("Database connection error. Please check your setup.")
        return
    
    # Get current user
    if 'user_id' not in st.session_state:
        st.error("Please register first to view recommendations.")
        return
    
    user_id = st.session_state.user_id
    recommendation_engine = RecommendationEngine()
    
    # Generate fresh recommendations
    with st.spinner("Analyzing your performance and generating recommendations..."):
        recommendations = recommendation_engine.generate_recommendations(user_id)
    
    # Display recommendations summary
    st.subheader("📊 Your Training Analysis")
    
    # Get performance analytics
    analytics = recommendation_engine.analyze_user_performance(user_id)
    
    if analytics:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            overall_score = sum(perf.get('performance_score', 0) for perf in analytics.values() 
                              if isinstance(perf, dict)) / 3
            st.metric("Overall Performance", f"{overall_score:.1f}/100")
        
        with col2:
            total_recommendations = len(recommendations)
            st.metric("Active Recommendations", total_recommendations)
        
        with col3:
            high_priority = len([r for r in recommendations if r.get('priority') == 'high'])
            st.metric("High Priority", high_priority)
    
    st.markdown("---")
    
    # Filter recommendations
    st.subheader("🔍 Filter Recommendations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_type = st.selectbox(
            "By Type",
            ["All", "posture_correction", "technique", "endurance", "strength", "rest"],
            key="filter_type"
        )
    
    with col2:
        selected_priority = st.selectbox(
            "By Priority", 
            ["All", "high", "medium", "low"],
            key="filter_priority"
        )
    
    with col3:
        selected_exercise = st.selectbox(
            "By Exercise",
            ["All", "jumps", "squats", "pushups", "all"],
            key="filter_exercise"
        )
    
    # Apply filters
    filtered_recommendations = []
    for rec in recommendations:
        if selected_type != "All" and rec.get('recommendation_type') != selected_type:
            continue
        if selected_priority != "All" and rec.get('priority') != selected_priority:
            continue
        if selected_exercise != "All" and rec.get('exercise_focus') != selected_exercise:
            continue
        filtered_recommendations.append(rec)
    
    # Display recommendations
    st.subheader("💡 Your Personalized Recommendations")
    
    if not filtered_recommendations:
        st.info("No recommendations match your current filters. Try adjusting the filters or complete more training sessions.")
        return
    
    # Group recommendations by priority
    high_priority_recs = [r for r in filtered_recommendations if r.get('priority') == 'high']
    medium_priority_recs = [r for r in filtered_recommendations if r.get('priority') == 'medium']
    low_priority_recs = [r for r in filtered_recommendations if r.get('priority') == 'low']
    
    # Display high priority first
    if high_priority_recs:
        st.markdown("### 🔴 High Priority Recommendations")
        for i, rec in enumerate(high_priority_recs, 1):
            display_recommendation_card(rec, i, "high")
    
    if medium_priority_recs:
        st.markdown("### 🟡 Medium Priority Recommendations")
        for i, rec in enumerate(medium_priority_recs, 1):
            display_recommendation_card(rec, i, "medium")
    
    if low_priority_recs:
        st.markdown("### 🟢 Low Priority Recommendations")
        for i, rec in enumerate(low_priority_recs, 1):
            display_recommendation_card(rec, i, "low")
    
    # Performance trends section
    st.markdown("---")
    st.subheader("📈 Performance Trends")
    
    if analytics:
        display_performance_charts(analytics, user_id, db)

def show_detailed_recommendation_callback():
    """Callback function for View More button"""
    # Get the recommendation ID from the button key
    button_key = st.session_state.get('_last_button_clicked', '')
    if 'learn_' in button_key:
        # Extract recommendation ID from button key
        rec_id = button_key.replace('learn_', '')
        # Find the recommendation in the current session
        # For now, just set a test recommendation
        st.session_state.show_detailed_recommendation = {
            'title': 'Test Recommendation',
            'recommendation_text': 'This is a test recommendation',
            'recommendation_type': 'technique',
            'priority': 'medium',
            'exercise_focus': 'jumps',
            'difficulty_level': 'beginner',
            'estimated_time_minutes': 10
        }
        st.toast("📖 Callback worked!", icon="✅")
        st.rerun()

def display_recommendation_card(recommendation: dict, index: int, priority: str):
    """Display a single recommendation as a card"""
    
    # Priority colors (Neon)
    priority_colors = {
        'high': '#FF2E2E',    # Neon Red
        'medium': '#F28500',  # Neon Orange
        'low': '#228B22'      # Neon Green/Cyan
    }
    
    # Exercise icons
    exercise_icons = {
        'jumps': '🏃',
        'squats': '🦵',
        'pushups': '💪',
        'all': '🏋️'
    }
    
    # Type icons
    type_icons = {
        'posture_correction': '🎯',
        'technique': '⚙️',
        'endurance': '⏱️',
        'strength': '💪',
        'rest': '🛌'
    }
    
    with st.container():
        # Card header
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            icon = type_icons.get(recommendation.get('recommendation_type', ''), '💡')
            exercise_icon = exercise_icons.get(recommendation.get('exercise_focus', ''), '🏋️')
            st.markdown(f"#### {icon} {recommendation.get('title', 'Recommendation')} {exercise_icon}")
        
        with col2:
            difficulty = recommendation.get('difficulty_level', 'beginner').title()
            st.markdown(f"**{difficulty}**")
        
        with col3:
            time_minutes = recommendation.get('estimated_time_minutes', 0)
            st.markdown(f"**{time_minutes} min**")
        
        # Card content
        st.markdown(f"**Description:** {recommendation.get('description', '')}")
        st.markdown(f"**Recommendation:** {recommendation.get('recommendation_text', '')}")
        
        # Simple test button with direct action
        if st.button(f"📖 View Details", key=f"direct_test_{index}", use_container_width=True):
            st.session_state.show_detailed_recommendation = recommendation
            st.toast("📖 Loading detailed view...", icon="📚")
            st.rerun()
        
        st.markdown("---")

def display_performance_charts(analytics: dict, user_id: int, db: Database):
    """Display performance trend charts"""
    
    # Get historical data
    historical_data = db.get_user_performance_analytics(user_id, days=30)
    
    if historical_data:
        # Create performance trend chart
        fig = go.Figure()
        
        # Add lines for each exercise type
        exercise_types = ['jumps', 'squats', 'pushups']
        colors = ['#00A8E8', '#F28500', '#228B22']  # Blue, Orange, Green (Neon)
        
        for i, exercise_type in enumerate(exercise_types):
            exercise_data = [d for d in historical_data if d['exercise_type'] == exercise_type]
            if exercise_data:
                dates = [d['analysis_date'] for d in exercise_data]
                scores = [d['performance_score'] for d in exercise_data]
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=scores,
                    mode='lines+markers',
                    name=exercise_type.title(),
                    line=dict(color=colors[i])
                ))
        
        fig.update_layout(
            title="Performance Score Trends (Last 30 Days)",
            xaxis_title="Date",
            yaxis_title="Performance Score (0-100)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True, key="recommendations_trend_chart")
    
    # Current performance radar chart
    if analytics:
        current_scores = {}
        for exercise_type in ['jumps', 'squats', 'pushups']:
            if exercise_type in analytics and isinstance(analytics[exercise_type], dict):
                current_scores[exercise_type] = analytics[exercise_type].get('performance_score', 0)
        
        if current_scores:
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=list(current_scores.values()),
                theta=list(current_scores.keys()),
                fill='toself',
                name='Current Performance'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                title="Current Performance by Exercise Type"
            )
            
            st.plotly_chart(fig, use_container_width=True, key="recommendations_radar_chart")

def mark_recommendation_completed(recommendation_id: int):
    """Mark a recommendation as completed"""
    try:
        db = Database()
        success = db.mark_recommendation_completed(recommendation_id)
        if success:
            return True
    except Exception as e:
        st.error(f"Error marking recommendation as completed: {e}")
    return False

def add_recommendations_to_sidebar():
    """Add recommendations summary to sidebar"""
    
    if 'user_id' not in st.session_state:
        return
    
    db = Database()
    recommendations = db.get_user_recommendations(st.session_state.user_id, limit=5)
    
    if recommendations:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎯 Quick Recommendations")
        
        for i, rec in enumerate(recommendations[:3], 1):
            priority_emoji = "🔴" if rec.get('priority') == 'high' else "🟡" if rec.get('priority') == 'medium' else "🟢"
            st.sidebar.markdown(f"{priority_emoji} **{rec.get('title', 'Recommendation')}**")
            st.sidebar.markdown(f"*{rec.get('recommendation_text', '')[:50]}...*")
            if i < len(recommendations[:3]):
                st.sidebar.markdown("---")
        
        if len(recommendations) > 3:
            st.sidebar.markdown(f"*And {len(recommendations) - 3} more...*")
        
        if st.sidebar.button("View All Recommendations", key="sidebar_view_recs"):
            st.session_state.page = 'recommendations'
            st.rerun()
