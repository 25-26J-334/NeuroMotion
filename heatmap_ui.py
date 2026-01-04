"""
UI Components for displaying contribution heatmap
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from database import Database

def heatmap_page():
    """Display the activity heatmap page"""
    
    # Back button
    if st.button("← Back to Training"):
        st.session_state.page = 'main'
        st.rerun()

    st.title("📅 Activity Calendar")
    st.markdown("---")

    db = Database()
    if not db.is_connected():
        st.error("Database connection error. Please check your setup.")
        return

    # Get daily stats for the last year
    stats = db.get_daily_exercise_stats(days=365)
    
    # Process data for heatmap
    if not stats:
        st.info("No training data available yet. Start training to see your activity status!")
        return

    # Create a complete date range for the last year
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=364) # 52 weeks * 7 days roughly
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # Create DataFrame from stats
    df_stats = pd.DataFrame(stats)
    
    # Ensure 'date' column is datetime
    if not df_stats.empty:
        df_stats['date'] = pd.to_datetime(df_stats['date']).dt.date
    
    # Create lookup dictionary for stats
    stats_dict = {}
    if not df_stats.empty:
        for _, row in df_stats.iterrows():
            total_exercises = (row.get('jumps', 0) or 0) + \
                              (row.get('squats', 0) or 0) + \
                              (row.get('pushups', 0) or 0)
            stats_dict[row['date']] = total_exercises

    # Prepare data for Plotly Heatmap
    # We need to organize data into value lists for z (intensity), x (week), y (day of week)
    
    z_data = [[0 for _ in range(53)] for _ in range(7)]
    hover_text = [['' for _ in range(53)] for _ in range(7)]
    dates_data = [['' for _ in range(53)] for _ in range(7)]
    
    # GitHub style: Mon (0) to Sun (6) on Y axis
    # X axis is weeks. We need to map dates to (week_idx, day_idx)
    
    # Align the grid so the last column is the current week
    # Working backwards from today might be easier to visualize locally, 
    # but for a standard calendar view left-to-right, we start from start_date.
    
    # Find the day of week of start_date to offset properly?
    # Actually, often heatmaps just autofit. 
    # Let's try a strict grid mapping by week number relative to start.
    
    for i, single_date in enumerate(date_range):
        date_obj = single_date.date()
        
        # Calculate grid position
        # Week number from start (0 to 52)
        days_from_start = (date_obj - start_date).days
        week_idx = days_from_start // 7
        day_idx = date_obj.weekday() # 0=Mon, 6=Sun
        
        if week_idx < 53:
            val = stats_dict.get(date_obj, 0)
            z_data[day_idx][week_idx] = val
            dates_data[day_idx][week_idx] = date_obj.strftime('%Y-%m-%d')
            hover_text[day_idx][week_idx] = f"Date: {date_obj.strftime('%b %d, %Y')}<br>Exercises: {val}"

    # Colorscale: GitHub-like green
    colors = [
        [0.0, '#ebedf0'],   # 0 items (light grey)
        [0.0001, '#9be9a8'], # 1+ items (light green)
        [0.2, '#9be9a8'],
        [0.4, '#40c463'],
        [0.6, '#30a14e'],
        [0.8, '#216e39'],
        [1.0, '#216e39']    # Max items (dark green)
    ]
    
    # Custom color scale based on max value to ensure visibility
    max_val = max([max(row) for row in z_data])
    if max_val == 0:
        max_val = 1 # Avoid division by zero in scaling if needed, though plotly handles it
    
    # Layout configuration
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=[f"Week {i}" for i in range(53)], # You might want actual dates here, but simplified for grid
        y=day_names,
        text=hover_text,
        hoverinfo='text',
        colorscale='Greens', # Built-in greens is good, or we can use custom
        showscale=True,
        xgap=2, # Gap between cells
        ygap=2,
    ))
    
    fig.update_layout(
        title="Training Consistency (Last 365 Days)",
        xaxis_title="",
        yaxis_title="",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=250,
        margin=dict(l=40, r=40, t=40, b=20),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False, # Hide week numbers
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            autorange='reversed' # Mon at top, Sun at bottom
        )
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Add some summary stats below
    total_year = sum([sum(row) for row in z_data])
    active_days = sum([sum([1 for val in row if val > 0]) for row in z_data])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Exercises (Year)", total_year)
    with col2:
        st.metric("Active Days", active_days)
    with col3:
        st.metric("Longest Streak", "Calculated separately") # Placeholder or implement logic
    
