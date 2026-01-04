def performance_page():
    """Display performance analytics and predictions"""
    # Back button at the top
    if st.button("← Back to Training"):
        st.session_state.page = 'main'
        st.rerun()
    
    st.title("📈 Performance Analytics")
    
    db = initialize_database()
    if db is None:
        st.error("Database connection failed. Please check your setup.")
        return
    
    if not st.session_state.user_id:
        st.error("Please log in to view performance analytics.")
        return
    
    # Fetch recent sessions for the user
    recent_sessions = db.get_recent_sessions(st.session_state.user_id, exercise_type='all', limit=50)
    
    if not recent_sessions:
        st.info("No training sessions found. Start training to see your performance analytics!")
        return
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(recent_sessions)
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    df['duration_minutes'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 60
    df['total_exercises'] = df['total_jumps'] + df['total_squats'] + df['total_pushups']
    
    # Overall performance metrics
    st.markdown("### 📊 Overall Performance")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sessions", len(df))
    with col2:
        st.metric("Total Exercises", df['total_exercises'].sum())
    with col3:
        st.metric("Total Points", df['total_points'].sum())
    with col4:
        st.metric("Avg Points/Session", f"{df['total_points'].mean():.1f}")
    
    st.markdown("---")
    
    # Performance trends over time
    st.markdown("### 📈 Performance Trends")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📅 Over Time", "🏋️ By Exercise", "⚡ Efficiency"])
    
    with tab1:
        # Performance over time
        df_sorted = df.sort_values('end_time')
        fig_time = px.line(
            df_sorted, 
            x='end_time', 
            y='total_points',
            title='Points Over Time',
            labels={'end_time': 'Session Date', 'total_points': 'Points Earned'},
            markers=True
        )
        fig_time.add_scatter(
            x=df_sorted['end_time'], 
            y=df_sorted['total_exercises'],
            mode='lines+markers',
            name='Total Exercises',
            yaxis='y2'
        )
        fig_time.update_layout(
            yaxis2=dict(title='Total Exercises', overlaying='y', side='right'),
            title='Performance Over Time'
        )
        st.plotly_chart(fig_time, use_container_width=True, key="performance_over_time")
    
    with tab2:
        # Performance by exercise type
        exercise_data = {
            'Jumps': df['total_jumps'].sum(),
            'Squats': df['total_squats'].sum(),
            'Push-ups': df['total_pushups'].sum()
        }
        
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(
                values=list(exercise_data.values()),
                names=list(exercise_data.keys()),
                title="Exercise Distribution"
            )
            st.plotly_chart(fig_pie, use_container_width=True, key="performance_exercise_pie")
        
        with col2:
            fig_bar = px.bar(
                x=list(exercise_data.keys()),
                y=list(exercise_data.values()),
                title="Total Reps by Exercise",
                labels={'x': 'Exercise', 'y': 'Total Reps'}
            )
            st.plotly_chart(fig_bar, use_container_width=True, key="performance_exercise_bar")
    
    with tab3:
        # Efficiency metrics
        df['points_per_exercise'] = df['total_points'] / df['total_exercises'].replace(0, 1)
        df['exercises_per_minute'] = df['total_exercises'] / df['duration_minutes'].replace(0, 1)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Avg Points/Exercise", f"{df['points_per_exercise'].mean():.2f}")
            st.metric("Best Points/Exercise", f"{df['points_per_exercise'].max():.2f}")
        
        with col2:
            st.metric("Avg Exercises/Minute", f"{df['exercises_per_minute'].mean():.1f}")
            st.metric("Best Exercises/Minute", f"{df['exercises_per_minute'].max():.1f}")
        
        # Efficiency trend
        fig_eff = px.line(
            df.sort_values('end_time'),
            x='end_time',
            y='points_per_exercise',
            title='Efficiency Trend (Points per Exercise)',
            labels={'end_time': 'Session Date', 'points_per_exercise': 'Points per Exercise'},
            markers=True
        )
        st.plotly_chart(fig_eff, use_container_width=True, key="performance_efficiency_trend")
    
    st.markdown("---")
    
    # Recent sessions table
    st.markdown("### 📋 Recent Sessions")
    
    # Prepare display data
    display_df = df.copy()
    display_df['date'] = display_df['end_time'].dt.strftime('%Y-%m-%d %H:%M')
    display_df = display_df[['date', 'total_jumps', 'total_squats', 'total_pushups', 'total_points', 'total_bad_moves', 'duration_minutes']]
    display_df.columns = ['Date', 'Jumps', 'Squats', 'Push-ups', 'Points', 'Bad Moves', 'Duration (min)']
    display_df = display_df.sort_values('Date', ascending=False).head(20)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Performance predictions for next session
    st.markdown("---")
    st.markdown("### 🔮 Next Session Predictions")
    
    # Get predictions for each exercise type
    exercises = ['jump', 'squat', 'pushup']
    predictions = {}
    
    for exercise in exercises:
        recent_exercise_sessions = db.get_recent_sessions(st.session_state.user_id, exercise_type=exercise, limit=10)
        if recent_exercise_sessions:
            from performance_prediction import compute_performance_prediction
            
            # Get current stats for this exercise
            if exercise == 'jump':
                current_count = df['total_jumps'].sum() if not df.empty else 0
            elif exercise == 'squat':
                current_count = df['total_squats'].sum() if not df.empty else 0
            else:  # pushup
                current_count = df['total_pushups'].sum() if not df.empty else 0
            
            current_points = df['total_points'].sum() if not df.empty else 0
            current_bad_moves = df['total_bad_moves'].sum() if not df.empty else 0
            
            pred = compute_performance_prediction(
                recent_exercise_sessions,
                exercise,
                current_count,
                current_points,
                current_bad_moves,
                None  # No active session
            )
            predictions[exercise] = pred
    
    if predictions:
        pred_cols = st.columns(3)
        exercise_names = {'jump': '🏃 Jumps', 'squat': '🦵 Squats', 'pushup': '💪 Push-ups'}
        
        for i, (exercise, pred) in enumerate(predictions.items()):
            with pred_cols[i]:
                st.markdown(f"#### {exercise_names[exercise]}")
                st.metric("Predicted Speed", f"{pred.predicted_speed:.1f} reps/min")
                st.metric("Endurance Score", f"{pred.endurance_score:.0f}/100")
                st.metric("Performance Rating", f"{pred.performance_rating:.0f}/100")
                st.markdown(f"**Trend:** {pred.trend}")
    
    st.markdown("---")
    
    # Download performance data
    st.markdown("### 📥 Export Data")
    if st.button("Download Performance Data (CSV)"):
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"performance_data_{st.session_state.user_name}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
