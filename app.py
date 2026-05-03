"""
AI Athlete Trainer - Streamlit Web Application
Main application file with user interface, video processing, and dashboard
"""
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from database import Database
from jump_detector import JumpDetector
from squat_detector import SquatDetector
from pushup_detector import PushupDetector
from recommendation_engine import RecommendationEngine
from recommendations_ui import recommendations_page, add_recommendations_to_sidebar
from heatmap_ui import heatmap_page
from muscle_heatmap_ui import heatmap_page_v2 as muscle_heatmap_page
from report_generator import ReportGenerator
from exercise_validator import ExerciseValidator
import groq

# Fatigue Detection Helper Functions
def calculate_fatigue_score(pred):
    """Calculate fatigue score based on performance trends and patterns"""
    if pred.history_points < 3:
        return 0.0
    
    fatigue_score = 0.0
    
    # Factor 1: Trend analysis (declining trend increases fatigue)
    if hasattr(pred, 'trend') and hasattr(pred, 'trend_strength'):
        if pred.trend == 'declining':
            fatigue_score += 30 * pred.trend_strength
        elif pred.trend == 'stable':
            fatigue_score += 10 * pred.trend_strength
    
    # Factor 2: Performance variance based on prediction confidence
    if hasattr(pred, 'r2_speed') and hasattr(pred, 'r2_endurance'):
        # Lower R² values indicate more variance/less consistency
        avg_r2 = (pred.r2_speed + pred.r2_endurance) / 2
        variance_factor = max(0, (1 - avg_r2) * 25)
        fatigue_score += variance_factor
    
    # Factor 3: Error rates (higher errors may indicate fatigue)
    if hasattr(pred, 'rmse_speed') and hasattr(pred, 'rmse_endurance'):
        # Normalize error rates (assuming typical ranges)
        error_factor = min((pred.rmse_speed + pred.rmse_endurance) / 20, 20)
        fatigue_score += error_factor
    
    # Factor 4: Performance drop based on trend strength and direction
    if hasattr(pred, 'trend_strength') and hasattr(pred, 'trend'):
        if pred.trend == 'declining':
            drop_factor = pred.trend_strength * 30
            fatigue_score += drop_factor
    
    return min(fatigue_score, 100.0)

def get_fatigue_level(fatigue_score):
    """Get fatigue level based on score"""
    if fatigue_score >= 70:
        return "High"
    elif fatigue_score >= 40:
        return "Moderate"
    elif fatigue_score >= 20:
        return "Low"
    else:
        return "Minimal"

def get_fatigue_color(fatigue_level):
    """Get color for fatigue level"""
    colors = {
        "Minimal": "#00FF00",    # Green
        "Low": "#FFFF00",        # Yellow  
        "Moderate": "#FFA500",    # Orange
        "High": "#FF0000"         # Red
    }
    return colors.get(fatigue_level, "#FFFFFF")
from performance_prediction import compute_performance_prediction
import os
import streamlit.components.v1 as components

def trigger_voice_alert(text):
    """Trigger a browser-based voice alert using Web Speech API"""
    if not st.session_state.get('voice_alerts_enabled', False):
        return
        
    # Rate limiting: 4 seconds between alerts
    current_time = time.time()
    last_alert_time = st.session_state.get('last_voice_alert_time', 0)
    
    if current_time - last_alert_time > 4:
        st.session_state.last_voice_alert_time = current_time
        # Use components.html to inject JavaScript for SpeechSynthesis
        js_code = f"""
            <script>
            if ('speechSynthesis' in window) {{
                const utterance = new SpeechSynthesisUtterance("{text}");
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                window.speechSynthesis.speak(utterance);
            }}
            </script>
        """
        # Render a tiny hidden component
        components.html(js_code, height=0, width=0)

def load_css():
    """Load custom CSS styles"""
    try:
        css_path = os.path.join(os.path.dirname(__file__), "static", "css", "style.css")
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        print(f"Error loading CSS: {e}")

# Page configuration
st.set_page_config(
    page_title="AI Athlete Trainer",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'user_age' not in st.session_state:
    st.session_state.user_age = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'session_start_time' not in st.session_state:
    st.session_state.session_start_time = None
if 'detector' not in st.session_state:
    st.session_state.detector = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'exercise_type' not in st.session_state:
    st.session_state.exercise_type = 'jump'  # 'jump' or 'squat'
if 'page' not in st.session_state:
    st.session_state.page = 'login' # Start with login page
if 'session_stats' not in st.session_state:
    st.session_state.session_stats = {
        'total_jumps': 0,
        'total_squats': 0,
        'total_pushups': 0,
        'total_points': 0,
        'total_bad_moves': 0,
        'jumps_data': [],
        'squats_data': [],
        'pushups_data': []
    }
if 'squat_detector' not in st.session_state:
    st.session_state.squat_detector = None
if 'pushup_detector' not in st.session_state:
    st.session_state.pushup_detector = None
if 'voice_alerts_enabled' not in st.session_state:
    st.session_state.voice_alerts_enabled = False
if 'last_voice_alert_time' not in st.session_state:
    st.session_state.last_voice_alert_time = 0
if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'performance_prediction' not in st.session_state:
    st.session_state.performance_prediction = None
if 'performance_prediction_exercise' not in st.session_state:
    st.session_state.performance_prediction_exercise = None
for ex in ['jump', 'squat', 'pushup']:
    if f'{ex}_best_rep_gif' not in st.session_state:
        st.session_state[f'{ex}_best_rep_gif'] = None
    if f'{ex}_worst_rep_gif' not in st.session_state:
        st.session_state[f'{ex}_worst_rep_gif'] = None
if 'report_clicked' not in st.session_state:
    st.session_state.report_clicked = False
if 'workout_clicked' not in st.session_state:
    st.session_state.workout_clicked = False
if 'diet_clicked' not in st.session_state:
    st.session_state.diet_clicked = False

def update_performance_prediction(db, exercise_type: str, current_count: int):
    if not st.session_state.user_id:
        return
    if st.session_state.session_start_time is None:
        st.session_state.session_start_time = datetime.now()

    try:
        recent_sessions = db.get_recent_sessions(st.session_state.user_id, exercise_type=exercise_type, limit=20)
    except Exception:
        recent_sessions = []

    prediction = compute_performance_prediction(
        recent_sessions=recent_sessions,
        exercise_type=exercise_type,
        current_count=int(current_count or 0),
        current_points=int(st.session_state.session_stats.get('total_points', 0) or 0),
        current_bad_moves=int(st.session_state.session_stats.get('total_bad_moves', 0) or 0),
        current_session_start=st.session_state.session_start_time,
    )
    st.session_state.performance_prediction = prediction
    st.session_state.performance_prediction_exercise = exercise_type

def render_performance_prediction_panel(exercise_type: str):
    st.markdown("### 🔮 Performance Prediction")
    pred = st.session_state.get('performance_prediction')
    pred_ex = st.session_state.get('performance_prediction_exercise')
    if not pred or pred_ex != exercise_type:
        st.caption("Start training to see predictions based on your session history.")
        return

    # Main prediction metrics
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Pred Speed (reps/min)", f"{pred.predicted_speed_rpm:.1f}")
    with metric_col2:
        st.metric("Endurance Score", f"{pred.predicted_endurance_score:.0f}/100")
    with metric_col3:
        st.metric("Performance Rating", f"{pred.predicted_rating:.0f}/100")

    # Trend analysis with confidence
    trend_col1, trend_col2, trend_col3 = st.columns(3)
    with trend_col1:
        st.markdown(f"**Trend:** {pred.trend.upper()}")
    with trend_col2:
        st.markdown(f"**Trend Strength:** {pred.trend_strength:.3f}")
    with trend_col3:
        st.markdown(f"**Data Points:** {pred.history_points}")
    
    # Confidence interval
    if pred.history_points >= 2:
        st.markdown(f"**95% Confidence Interval:** {pred.confidence_interval['lower']:.1f} - {pred.confidence_interval['upper']:.1f}")
    
    st.markdown("---")
    
    # Fatigue Detection Section
    if pred.history_points >= 3:
        st.markdown("#### 😴 Fatigue Detection")
        
        # Calculate fatigue metrics
        fatigue_score = calculate_fatigue_score(pred)
        fatigue_level = get_fatigue_level(fatigue_score)
        fatigue_color = get_fatigue_color(fatigue_level)
        
        # Display fatigue status
        fatigue_col1, fatigue_col2, fatigue_col3 = st.columns(3)
        with fatigue_col1:
            st.markdown(f"**Fatigue Level:**")
            st.markdown(f"<span style='color: {fatigue_color}; font-size: 1.2em; font-weight: bold;'>{fatigue_level}</span>", 
                       unsafe_allow_html=True)
        
        with fatigue_col2:
            st.markdown(f"**Fatigue Score:**")
            st.markdown(f"<span style='color: {fatigue_color}; font-size: 1.2em; font-weight: bold;'>{fatigue_score:.1f}/100</span>", 
                       unsafe_allow_html=True)
        
        with fatigue_col3:
            st.markdown(f"**Recommendation:**")
            if fatigue_score >= 70:
                st.markdown("🛑 **Take a Break**", unsafe_allow_html=True)
            elif fatigue_score >= 40:
                st.markdown("⚠️ **Slow Down**", unsafe_allow_html=True)
            else:
                st.markdown("✅ **Keep Going**", unsafe_allow_html=True)
        
        # Fatigue trend analysis
        if hasattr(pred, 'trend') and pred.trend == 'declining' and pred.trend_strength > 0.3:
            st.markdown(f"📉 **Performance Decline:** {pred.trend_strength:.1%} declining trend detected")
        
        # Personalized recommendations
        if fatigue_score >= 70:
            st.warning("🧘 **Recommended:** Take a 5-10 minute break. Hydrate and stretch before continuing.")
            st.info("💡 **Tip:** Fatigue can increase injury risk and reduce form quality.")
        elif fatigue_score >= 40:
            st.info("💡 **Suggestion:** Consider reducing intensity or taking shorter breaks between sets.")
        
        st.markdown("---")
    
    st.markdown("---")
    
    # Performance History Chart
    if pred.performance_history:
        st.markdown("#### 📈 Performance Trend Over Time")
        
        # Prepare data for plotting
        history_df = pd.DataFrame(pred.performance_history)
        
        # Create trend chart
        fig = go.Figure()
        
        # Add speed trend
        fig.add_trace(go.Scatter(
            x=history_df['session_number'],
            y=history_df['speed_rpm'],
            mode='lines+markers',
            name='Speed (reps/min)',
            line=dict(color='#00A8E8', width=3),
            marker=dict(size=8)
        ))
        
        # Add endurance trend
        fig.add_trace(go.Scatter(
            x=history_df['session_number'],
            y=history_df['endurance_score'],
            mode='lines+markers',
            name='Endurance Score',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=8)
        ))
        
        # Add rating trend
        fig.add_trace(go.Scatter(
            x=history_df['session_number'],
            y=history_df['rating'],
            mode='lines+markers',
            name='Performance Rating',
            line=dict(color='#4ECDC4', width=3),
            marker=dict(size=8)
        ))
        
        # Add predicted values as dashed lines
        if pred.history_points >= 1:
            next_session = pred.history_points + 1
            
            # Add predicted values
            fig.add_trace(go.Scatter(
                x=[next_session],
                y=[pred.predicted_speed_rpm],
                mode='markers',
                name='Pred Speed',
                marker=dict(color='#00A8E8', size=12, symbol='diamond')
            ))
            
            fig.add_trace(go.Scatter(
                x=[next_session],
                y=[pred.predicted_endurance_score],
                mode='markers',
                name='Pred Endurance',
                marker=dict(color='#FF6B6B', size=12, symbol='diamond')
            ))
            
            fig.add_trace(go.Scatter(
                x=[next_session],
                y=[pred.predicted_rating],
                mode='markers',
                name='Pred Rating',
                marker=dict(color='#4ECDC4', size=12, symbol='diamond')
            ))
        
        fig.update_layout(
            title="Performance Trends & Predictions",
            xaxis_title="Session Number",
            yaxis_title="Score / Value",
            height=400,
            showlegend=True,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"performance_trend_chart_{exercise_type}_{st.session_state.get('session_id', 'default')}_{hash(str(time.time()))}")
        
        st.markdown("---")
    
    # Training Load Forecast
    st.markdown("#### 🔮 Future Performance Under Different Training Loads")
    try:
        df = pd.DataFrame(pred.forecast)
        df = df.rename(columns={
            'training_load': 'Training Load',
            'pred_speed_rpm': 'Speed (reps/min)',
            'pred_endurance_score': 'Endurance',
            'pred_rating': 'Rating'
        })
        
        # Add load descriptions
        df['Load Description'] = df['Training Load'].apply(
            lambda x: 'Light (80%)' if x == 0.8 else ('Normal (100%)' if x == 1.0 else 'Heavy (120%)')
        )
        
        # Reorder columns
        df = df[['Load Description', 'Training Load', 'Speed (reps/min)', 'Endurance', 'Rating']]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Create forecast chart
        fig_forecast = go.Figure()
        
        loads = df['Training Load'].values
        speeds = df['Speed (reps/min)'].values
        endurance = df['Endurance'].values
        ratings = df['Rating'].values
        
        fig_forecast.add_trace(go.Scatter(
            x=loads,
            y=speeds,
            mode='lines+markers',
            name='Speed',
            line=dict(color='#00A8E8', width=3),
            marker=dict(size=10)
        ))
        
        fig_forecast.add_trace(go.Scatter(
            x=loads,
            y=endurance,
            mode='lines+markers',
            name='Endurance',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=10)
        ))
        
        fig_forecast.add_trace(go.Scatter(
            x=loads,
            y=ratings,
            mode='lines+markers',
            name='Rating',
            line=dict(color='#4ECDC4', width=3),
            marker=dict(size=10)
        ))
        
        fig_forecast.update_layout(
            title="Performance Forecast by Training Load",
            xaxis_title="Training Load (Relative to Current)",
            yaxis_title="Predicted Performance",
            height=350,
            showlegend=True,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig_forecast, use_container_width=True, key=f"performance_forecast_chart_{exercise_type}_{st.session_state.get('session_id', 'default')}_{hash(str(time.time()))}")
        
    except Exception as e:
        st.error(f"Error displaying forecast: {str(e)}")
        pass

def extract_gif(video_path, start_frame, end_frame, output_path, resize_factor=0.5):
    """Extract a segment of video and save as GIF"""
    import os
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False
    
    # Validation
    if start_frame is None or end_frame is None:
        cap.release()
        return False
    
    # Add a small buffer before and after (approx 0.5s)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    buffer = int(fps * 0.5)
    start_frame = max(0, start_frame - buffer)
    end_frame = end_frame + buffer
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    frames = []
    current_frame = start_frame
    while current_frame <= end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Resize to make GIF smaller
        w = int(frame.shape[1] * resize_factor)
        h = int(frame.shape[0] * resize_factor)
        frame = cv2.resize(frame, (w, h))
        
        # Convert to RGB for PIL
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(Image.fromarray(frame_rgb))
        current_frame += 1
    
    cap.release()
    
    if frames:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        frames[0].save(
            output_path, 
            save_all=True, 
            append_images=frames[1:], 
            duration=int(1000/fps), 
            loop=0
        )
        return True
    return False

def extract_highlights_gifs(video_path, rep_history, exercise_type):
    """Identify best and worst reps and extract them as GIFs"""
    if not rep_history or len(rep_history) < 2:
        return
    
    # Sort by points to find best and worst
    sorted_reps = sorted(rep_history, key=lambda x: x['points'], reverse=True)
    
    best_rep = sorted_reps[0]
    worst_rep = sorted_reps[-1]
    
    # Don't show if they are the same rep (e.g. only 1 rep done, but we checked length >= 2)
    if best_rep['rep_number'] == worst_rep['rep_number']:
        return

    import tempfile
    temp_dir = os.path.join(tempfile.gettempdir(), "athlete_highlights")
    
    best_gif_path = os.path.join(temp_dir, f"best_{exercise_type}.gif")
    worst_gif_path = os.path.join(temp_dir, f"worst_{exercise_type}.gif")
    
    if extract_gif(video_path, best_rep['start_frame'], best_rep['end_frame'], best_gif_path):
        st.session_state[f"{exercise_type}_best_rep_gif"] = best_gif_path
        
    if extract_gif(video_path, worst_rep['start_frame'], worst_rep['end_frame'], worst_gif_path):
        st.session_state[f"{exercise_type}_worst_rep_gif"] = worst_gif_path

def initialize_database():
    """Initialize database connection"""
    if 'db' not in st.session_state:
        st.session_state.db = Database()
    
    # Check if database is connected
    if not st.session_state.db.is_connected():
        return None
    return st.session_state.db

def login_page(db):
    """User login page"""
    load_css()
    apply_premium_styling()
    
    st.title("🏃 AI Athlete Trainer")
    st.markdown("### Welcome Back! Please login to continue")
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.form("user_login"):
        username_or_email = st.text_input("Username or Email", placeholder="Enter your username or email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if username_or_email and password:
                user = db.authenticate_user(username_or_email, password)
                if user:
                    st.session_state.user_id = user['user_id']
                    st.session_state.user_name = user['name']
                    st.session_state.user_age = user['age']
                    st.session_state.page = 'main'
                    st.success(f"Welcome back, {user['name']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid username/email or password.")
            else:
                st.warning("Please enter both username/email and password.")
    
    if st.button("New user? Create an account", use_container_width=True):
        st.session_state.page = 'register'
        st.rerun()

def apply_premium_styling():
    """Apply premium background styling with base64 encoded image if available"""
    import base64
    from pathlib import Path
    
    current_dir = Path(__file__).parent
    image_path = current_dir / "static" / "css" / "athlete.png"
    
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode()
        
        st.markdown(f"""
        <style>
        .stApp {{
            background-color: #00050D;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(0, 168, 232, 0.1) 0%, transparent 20%),
                radial-gradient(circle at 90% 80%, rgba(0, 168, 232, 0.05) 0%, transparent 20%),
                url("data:image/png;base64,{encoded_image}");
            background-size: cover, cover, cover;
            background-position: center 30%;
            background-repeat: no-repeat;
            background-attachment: fixed;
            min-height: 100vh;
        }}
        .main .block-container {{
            max-width: 600px !important;
            padding: 40px !important;
            background-color: rgba(0, 18, 41, 0.6) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border: 1px solid rgba(0, 168, 232, 0.1) !important;
            border-radius: 15px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
            margin: auto !important;
            margin-top: 50px !important;
        }}
        div[data-testid="stForm"] {{
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
        }}
        .stTextInput > label, .stNumberInput > label {{
            color: #00A8E8 !important;
            font-weight: 500 !important;
        }}
        /* Make input fields narrower and left-aligned */
        div[data-testid="stForm"] .stTextInput, 
        div[data-testid="stForm"] .stNumberInput,
        div[data-testid="stForm"] .stDateInput {{
            max-width: 400px !important;
            margin-left: 0 !important;
            margin-right: auto !important;
        }}
        /* Target BOTH regular buttons and form submit buttons */
        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] button {{
            background: linear-gradient(90deg, #001229 0%, #002b4d 100%) !important;
            border: 1px solid rgba(0, 168, 232, 0.3) !important;
            color: #00A8E8 !important;
            transition: all 0.3s ease !important;
            max-width: 400px !important;
            display: block !important;
            margin-left: 0 !important;
            margin-right: auto !important;
            margin-top: 20px !important;
            margin-bottom: 20px !important;
            width: 100% !important;
        }}
        div[data-testid="stButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {{
            border-color: #00A8E8 !important;
            box-shadow: 0 0 10px rgba(0, 168, 232, 0.2) !important;
            color: white !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        st.markdown("""
        <style>
        .stApp {
            background-color: #00050D;
            background-image: 
                radial-gradient(circle at 50% 50%, rgba(0, 168, 232, 0.15) 0%, transparent 50%);
            min-height: 100vh;
        }
        .main .block-container {
            background-color: rgba(0, 18, 41, 0.7);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 168, 232, 0.1);
            border-radius: 15px;
            padding: 30px;
            max-width: 600px;
            margin: auto;
            margin-top: 50px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        </style>
        """, unsafe_allow_html=True)

def registration_page(db):
    """User registration page"""
    load_css()
    apply_premium_styling()
    
    st.title("🏃 AI Athlete Trainer")
    st.markdown("### Create your account to start training")
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.form("user_registration_form"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username*", placeholder="Choose a username")
            email = st.text_input("Email*", placeholder="Enter your email")
        with col2:
            password = st.text_input("Password*", type="password", placeholder="Choose a password")
            confirm_password = st.text_input("Confirm Password*", type="password", placeholder="Confirm your password")
            
        name = st.text_input("Full Name", placeholder="Enter your full name")
        age = st.number_input("Age", min_value=10, max_value=120, value=20)
        
        submit = st.form_submit_button("Register & Start Training", use_container_width=True)
        
        if submit:
            if not (username and email and password):
                st.warning("Please fill in all required fields (*)")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                user_id = db.register_user(username, email, password, name or username, age)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.user_name = name or username
                    st.session_state.user_age = age
                    st.session_state.page = 'main'
                    st.success(f"Welcome, {name or username}! Your account has been created.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Registration failed. Username or email might already be taken.")
    
    if st.button("Already have an account? Login", use_container_width=True):
        st.session_state.page = 'login'
        st.rerun()

def user_registration():
    """Route between login and registration"""
    db = initialize_database()
    if db is None:
        st.error("⚠️ Database Connection Failed")
        st.markdown("""
        **Please set up the database:**
        
        **Quick Setup:**
        - Run: `python setup_database.py` from the source directory
        - This will create the SQLite database file automatically
        """)
        if st.button("🔄 Retry Connection"):
            if 'db' in st.session_state:
                del st.session_state.db
            st.rerun()
        return

    if st.session_state.get('page') == 'register':
        registration_page(db)
    else:
        login_page(db)

def render_sidebar(db):
    """Render a persistent sidebar available across all pages"""
    with st.sidebar:
        st.title(f"👤 {st.session_state.user_name}")
        st.caption(f"Age: {st.session_state.user_age}")
        
        st.markdown("---")
        
        # Exercise Type Dropdown (Styled as a button)
        with st.expander("🏃 Exercise Type", expanded=False):
            if st.button("🏃 Jump Session", use_container_width=True, type="primary" if st.session_state.exercise_type == 'jump' and st.session_state.page == 'main' else "secondary"):
                st.session_state.page = 'main'
                st.session_state.exercise_type = 'jump'
                st.session_state.session_id = None
                st.session_state.detector = None
                st.rerun()
            
            if st.button("🦵 Squat Session", use_container_width=True, type="primary" if st.session_state.exercise_type == 'squat' and st.session_state.page == 'main' else "secondary"):
                st.session_state.page = 'main'
                st.session_state.exercise_type = 'squat'
                st.session_state.session_id = None
                st.session_state.detector = None
                st.rerun()
            
            if st.button("💪 Push-up Session", use_container_width=True, type="primary" if st.session_state.exercise_type == 'pushup' and st.session_state.page == 'main' else "secondary"):
                st.session_state.page = 'main'
                st.session_state.exercise_type = 'pushup'
                st.session_state.session_id = None
                st.session_state.detector = None
                st.rerun()

            if st.button("⚔️ 1v1 Multiplayer", use_container_width=True, type="primary" if st.session_state.exercise_type == 'multiplayer' and st.session_state.page == 'main' else "secondary"):
                st.session_state.page = 'main'
                st.session_state.exercise_type = 'multiplayer'
                st.session_state.session_id = None
                st.session_state.detector = None
                st.rerun()

            st.markdown("---")
            if st.button("🦴 3D Muscle Map", use_container_width=True, type="primary" if st.session_state.page == 'muscle_map' else "secondary"):
                st.session_state.page = 'muscle_map'
                st.rerun()
        
        if st.button("📊 Dashboard", use_container_width=True, type="primary" if st.session_state.page == 'dashboard' else "secondary"):
            st.session_state.page = 'dashboard'
            st.rerun()

        if st.button("🎯 Training Plans", use_container_width=True, type="primary" if st.session_state.page == 'recommendations' else "secondary"):
            st.session_state.page = 'recommendations'
            st.rerun()

        if st.button("🤖 AI TrainBot", use_container_width=True, type="primary" if st.session_state.page == 'trainbot' else "secondary"):
            st.session_state.page = 'trainbot'
            st.rerun()
            

        if st.button("🏆 Leaderboard", use_container_width=True, type="primary" if st.session_state.page == 'leaderboard' else "secondary"):
            st.session_state.page = 'leaderboard'
            st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True):
            if st.session_state.session_id:
                db.end_session(st.session_state.session_id, st.session_state.session_stats['total_jumps'], 
                             st.session_state.session_stats['total_points'], st.session_state.session_stats['total_bad_moves'],
                             st.session_state.session_stats.get('total_squats', 0), st.session_state.session_stats.get('total_pushups', 0))
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def main_app():
    """Main application interface"""
    db = initialize_database()
    if db is None:
        st.error("Database connection lost. Please refresh the page.")
        if st.button("🔄 Refresh"):
            if 'db' in st.session_state:
                del st.session_state.db
            st.rerun()
        return
    
    # Main content area - route based on exercise type
    if st.session_state.exercise_type == 'multiplayer':
        main_app_multiplayer(db)
    elif st.session_state.exercise_type == 'squat':
        main_app_squat(db)
    elif st.session_state.exercise_type == 'pushup':
        main_app_pushup(db)
    else:
        main_app_jump(db)

def process_multiplayer_camera(db, exercise_type='jump', duration_seconds=60, p1_name="Player 1", p2_name="Player 2"):
    """Split-screen 1v1 multiplayer mode. Left half = P1, Right half = P2."""
    # Initialize two independent detectors
    if exercise_type == 'jump':
        det_p1 = JumpDetector(calibration_frames=50, jump_height="medium")
        det_p2 = JumpDetector(calibration_frames=50, jump_height="medium")
    elif exercise_type == 'squat':
        det_p1 = SquatDetector(calibration_frames=50)
        det_p2 = SquatDetector(calibration_frames=50)
    else:  # pushup
        det_p1 = PushupDetector(calibration_frames=50)
        det_p2 = PushupDetector(calibration_frames=50)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("❌ Could not open camera. Check it's not in use.")
        return

    st.info(
        f"📹 **Split-Screen 1v1 Battle!** "
        f"**{p1_name}** stand on the **LEFT** half, **{p2_name}** stand on the **RIGHT** half. "
        f"Stand still for calibration, then compete!"
    )

    frame_placeholder = st.empty()
    stop_col, timer_col = st.columns([1, 3])
    stop_placeholder = stop_col.empty()
    timer_placeholder = timer_col.empty()
    score_placeholder = st.empty()

    score_p1 = 0
    score_p2 = 0
    frame_count = 0
    start_time = None      # Only starts after calibration
    calibrated = False
    game_over = False

    try:
        while True:
            # ---------- stop button ----------
            if stop_placeholder.button("⏹️ Stop", key=f"mp_stop_{frame_count}"):
                game_over = True
                break

            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            frame_count += 1
            h, w = frame.shape[:2]
            mid = w // 2

            # Split frame
            left_frame  = frame[:, :mid].copy()
            right_frame = frame[:, mid:].copy()

            # Process each half
            left_annotated,  status_p1 = det_p1.process_frame(left_frame,  frame_index=frame_count)
            right_annotated, status_p2 = det_p2.process_frame(right_frame, frame_index=frame_count)

            # Determine if both sides calibrated
            p1_calib = status_p1.get('calibrating', False)
            p2_calib = status_p2.get('calibrating', False)

            if not calibrated and not p1_calib and not p2_calib:
                calibrated = True
                start_time = time.time()

            # Start timer after calibration
            elapsed = 0
            remaining = duration_seconds
            if calibrated and start_time is not None:
                elapsed = time.time() - start_time
                remaining = max(0, duration_seconds - elapsed)
                if remaining <= 0 and not game_over:
                    game_over = True

            # Update scores using the right key per exercise
            if exercise_type == 'jump':
                score_p1 = status_p1.get('jump_count', score_p1)
                score_p2 = status_p2.get('jump_count', score_p2)
            elif exercise_type == 'squat':
                score_p1 = status_p1.get('squat_count', score_p1)
                score_p2 = status_p2.get('squat_count', score_p2)
            else:
                score_p1 = status_p1.get('pushup_count', score_p1)
                score_p2 = status_p2.get('pushup_count', score_p2)

            # ---- Draw divider line on each half ----
            # Left side label
            label_bg_color = (0, 80, 160)
            cv2.rectangle(left_annotated,  (0, 0), (mid, 50), label_bg_color, -1)
            cv2.putText(left_annotated, f"{p1_name}: {score_p1}", (10, 36),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 220, 50), 2)

            cv2.rectangle(right_annotated, (0, 0), (mid, 50), label_bg_color, -1)
            cv2.putText(right_annotated, f"{p2_name}: {score_p2}", (10, 36),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (100, 255, 100), 2)

            # Stitch halves back
            combined = np.hstack((left_annotated, right_annotated))

            # Draw center divider
            cv2.line(combined, (mid, 0), (mid, h), (255, 255, 255), 3)

            # Draw timer
            if not calibrated:
                timer_text = "⏳ Calibrating..."
                cv2.putText(combined, timer_text, (mid - 130, h - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            else:
                timer_text = f"⏱ {int(remaining)}s"
                color = (0, 255, 0) if remaining > 10 else (0, 0, 255)
                cv2.putText(combined, timer_text, (mid - 60, h - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

            if game_over:
                # Overlay winner banner
                if score_p1 > score_p2:
                    winner_text = f"🏆 {p1_name} WINS!"
                    banner_color = (0, 80, 160)
                elif score_p2 > score_p1:
                    winner_text = f"🏆 {p2_name} WINS!"
                    banner_color = (0, 120, 0)
                else:
                    winner_text = "🤝 IT'S A TIE!"
                    banner_color = (80, 0, 120)

                overlay = combined.copy()
                cv2.rectangle(overlay, (w//2 - 240, h//2 - 60), (w//2 + 240, h//2 + 60), banner_color, -1)
                cv2.addWeighted(overlay, 0.85, combined, 0.15, 0, combined)
                cv2.putText(combined, winner_text, (w//2 - 220, h//2 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

            # Display combined frame
            combined_rgb = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(combined_rgb, channels="RGB", use_container_width=True)

            # Score ribbon below
            with score_placeholder.container():
                s1, s2 = st.columns(2)
                with s1:
                    st.markdown(
                        f"<div style='text-align:center; background:rgba(0,80,160,0.25); border-radius:8px; padding:10px;'>"
                        f"<h2 style='margin:0; color:#FFDC32;'>👤 {p1_name}</h2>"
                        f"<h1 style='margin:0; color:white;'>{score_p1}</h1>"
                        f"<span style='color:#a0aec0;'>reps</span></div>",
                        unsafe_allow_html=True
                    )
                with s2:
                    st.markdown(
                        f"<div style='text-align:center; background:rgba(0,120,0,0.25); border-radius:8px; padding:10px;'>"
                        f"<h2 style='margin:0; color:#64FF64;'>👤 {p2_name}</h2>"
                        f"<h1 style='margin:0; color:white;'>{score_p2}</h1>"
                        f"<span style='color:#a0aec0;'>reps</span></div>",
                        unsafe_allow_html=True
                    )

            # Timer
            if calibrated:
                timer_placeholder.progress(
                    max(0.0, remaining / duration_seconds),
                    text=f"⏱ {int(remaining)}s remaining"
                )
            else:
                timer_placeholder.info("Stand still — calibrating both players...")

            if game_over:
                time.sleep(4)
                break

            time.sleep(0.01)

    except Exception as e:
        st.error(f"Error in multiplayer mode: {e}")
    finally:
        cap.release()

        # Show final result
        if score_p1 > score_p2:
            st.success(f"🏆 **{p1_name} WINS** with {score_p1} reps vs {score_p2} reps!")
        elif score_p2 > score_p1:
            st.success(f"🏆 **{p2_name} WINS** with {score_p2} reps vs {score_p1} reps!")
        else:
            st.info(f"🤝 **IT'S A TIE!** Both players scored {score_p1} reps!")

def main_app_multiplayer(db):
    """1v1 Multiplayer launcher page"""
    st.title("⚔️ 1v1 Multiplayer Battle")
    st.markdown(
        "Challenge a friend! **Stand on opposite sides** of the camera and compete "
        "to see who can do the most perfect reps in the time limit. 🥊"
    )

    st.markdown("---")
    st.markdown("#### ⚙️ Battle Settings")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        p1_name = st.text_input("Player 1 Name", value="Player 1", key="mp_p1_name")
    with col2:
        p2_name = st.text_input("Player 2 Name", value="Player 2", key="mp_p2_name")
    with col3:
        exercise_choice = st.selectbox(
            "Exercise",
            options=["🏃 Jump", "🦵 Squat", "💪 Push-up"],
            key="mp_exercise"
        )
    with col4:
        duration = st.selectbox(
            "Duration",
            options=["30 seconds", "60 seconds", "90 seconds"],
            index=1,
            key="mp_duration"
        )

    exercise_type_map = {"🏃 Jump": "jump", "🦵 Squat": "squat", "💪 Push-up": "pushup"}
    duration_map = {"30 seconds": 30, "60 seconds": 60, "90 seconds": 90}

    ex_type = exercise_type_map[exercise_choice]
    dur_sec = duration_map[duration]

    st.markdown("---")
    st.markdown(
        f"""
        **Instructions:**
        1. Both players should stand **facing the camera**.
        2. **{p1_name}** → stand on the **LEFT** side of the camera view.
        3. **{p2_name}** → stand on the **RIGHT** side of the camera view.
        4. Stand still and wait for **Calibration** to complete.
        5. Start performing **{exercise_choice}** reps. The player with the most reps in **{duration}** wins!
        """
    )

    if st.button("🚀 Start Battle!", use_container_width=True, type="primary"):
        process_multiplayer_camera(db, ex_type, dur_sec, p1_name, p2_name)

def show_db_update_notification(exercise_type, count, success=True):
    """Show database update notification"""
    if success:
        st.session_state[f'last_db_update_{exercise_type}'] = f"✅ {exercise_type.capitalize()} #{count} saved to database!"
        st.session_state[f'last_db_update_time_{exercise_type}'] = datetime.now().strftime("%H:%M:%S")
    else:
        st.session_state[f'last_db_update_{exercise_type}'] = f"❌ Database update failed!"
        st.session_state[f'last_db_update_time_{exercise_type}'] = datetime.now().strftime("%H:%M:%S")

def render_highlights_panel(exercise_type):
    """Render the AI Highlights panel with GIFs for a specific exercise"""
    best_key = f"{exercise_type}_best_rep_gif"
    worst_key = f"{exercise_type}_worst_rep_gif"
    
    if st.session_state.get(best_key) or st.session_state.get(worst_key):
        st.markdown("---")
        st.markdown("## 🎬 AI Highlights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            best_path = st.session_state.get(best_key)
            if best_path and os.path.exists(best_path):
                st.markdown("### 🌟 Best Rep")
                st.image(best_path, use_container_width=True)
                st.info("Perfect form detected! Keep this as your benchmark.")
            else:
                st.info("No Best Rep highlight available yet.")
                
        with col2:
            worst_path = st.session_state.get(worst_key)
            if worst_path and os.path.exists(worst_path):
                st.markdown("### ⚠️ Area for Improvement")
                st.image(worst_path, use_container_width=True)
                st.warning("Review this rep to identify technical flaws.")
            else:
                st.info("No Worst Rep highlight available yet.")

def process_video_file(uploaded_file, db, calibration_frames=100, jump_height="medium"):
    """Process uploaded video file"""
    # Initialize detector
    if st.session_state.detector is None:
        st.session_state.detector = JumpDetector(calibration_frames=calibration_frames, jump_height=jump_height)
    else:
        # Reset detector for new video with new calibration frames
        st.session_state.detector.reset()
        st.session_state.detector.CALIBRATION_FRAMES = calibration_frames
        st.session_state.detector.jump_height = jump_height
    
    # Create session if not exists
    if st.session_state.session_id is None:
        session_id = db.create_session(st.session_state.user_id)
        if session_id:
            st.session_state.session_id = session_id
            st.session_state.session_start_time = datetime.now()
        else:
            st.error("Failed to create session")
            return
    
    # Process video directly from uploaded file bytes using tempfile (auto-deletes)
    import tempfile
    import os
    
    temp_path = None
    try:
        # Create temporary file that auto-deletes when closed
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_file.write(uploaded_file.read())
            temp_path = temp_file.name
            
        # Validate video content
        validator = ExerciseValidator()
        is_valid, msg = validator.validate_video(temp_path, 'jump')
        if not is_valid:
            st.error(f"❌ Validation Failed: {msg}")
            os.unlink(temp_path)
            return
        
        # Process video
        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            st.error("Failed to open video file. Please check the file format.")
            os.unlink(temp_path)
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            st.error("Could not determine video frame count. Please check the video file.")
            cap.release()
            os.unlink(temp_path)
            return
        
        # Create side-by-side layout: 60% video, 40% posture predictor
        video_col, posture_col = st.columns([0.6, 0.4])
        
        frame_placeholder = video_col.empty()
        progress_bar = st.progress(0)
        stop_button_placeholder = st.empty()
        posture_placeholder = posture_col.empty()
        ribbon_placeholder = st.empty()
        
        frame_count = 0
        should_stop = False
        
        st.info(f"📹 Processing video: {total_frames} frames at {fps:.1f} FPS")
        
        # Process all frames
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Check for stop button
            if stop_button_placeholder.button("⏹️ Stop Processing", key=f"stop_{frame_count}"):
                should_stop = True
                break
            
            frame_count += 1
            
            # Process frame
            annotated_frame, status = st.session_state.detector.process_frame(frame, frame_index=frame_count)
            
            # Update session stats
            if status['jump_count'] > st.session_state.session_stats['total_jumps']:
                # New jump detected
                jump_data = {
                    'jump_number': status['jump_count'],
                    'points': status['points'],
                    'bad_moves': status['bad_moves'],
                    'warnings': ', '.join(status['warnings']) if status['warnings'] else 'None',
                    'has_danger': status['danger_detected']
                }
                
                # Record to database
                db.record_jump(
                    st.session_state.session_id,
                    jump_data['jump_number'],
                    jump_data['points'],
                    jump_data['bad_moves'],
                    jump_data['warnings'],
                    jump_data['has_danger']
                )
                
                # Update stats
                st.session_state.session_stats['total_jumps'] = status['jump_count']
                st.session_state.session_stats['total_points'] += jump_data['points']
                st.session_state.session_stats['total_bad_moves'] += jump_data['bad_moves']
                st.session_state.session_stats['jumps_data'].append(jump_data)
                
                update_performance_prediction(db, 'jump', st.session_state.session_stats['total_jumps'])
                
                # Update session totals in database in real-time
                db.update_session_totals(
                    st.session_state.session_id,
                    st.session_state.session_stats['total_jumps'],
                    st.session_state.session_stats['total_points'],
                    st.session_state.session_stats['total_bad_moves'],
                    0,  # total_squats for jump session
                    0   # total_pushups for jump session
                )
                # Small delay to ensure database commit completes
                time.sleep(0.01)
            
            # Draw UI overlay (simplified - no warnings on video)
            h, w = annotated_frame.shape[:2]
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (0, 0), (300, 100), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, annotated_frame, 0.3, 0, annotated_frame)
            
            cv2.putText(annotated_frame, f"Jumps: {status['jump_count']}", (15, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (232, 168, 0), 2)
            cv2.putText(annotated_frame, f"Status: {status['status_text']}", (15, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Convert to RGB for display
            annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(annotated_frame_rgb, channels="RGB")
            
            # Posture Predictor Box (40% width) - Static layout with fixed placeholders
            with posture_placeholder.container():
                st.markdown("### 🎯 Posture Predictor")
                
                # Fixed info section
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.markdown(f"**Frame:** {frame_count}/{total_frames}")
                with info_col2:
                    st.markdown(f"**Status:** {status['status_text']}")
                
                st.markdown("#### ⚠️ Warnings")
                if status['warnings']:
                    for warning in status['warnings']:
                        st.write(f"🔴 {warning}")
                else:
                    st.write("✅ No warnings")
                st.markdown("---")
            
            # Full-width Status Ribbon under video and posture box
            with ribbon_placeholder.container():
                st.markdown("### 📊 Live Performance Ribbon")
                ribbon_col1, ribbon_col2, ribbon_col3 = st.columns(3)
                
                with ribbon_col1:
                    st.markdown("#### ❌ Bad Moves")
                    st.markdown(f"## {status['bad_moves']}")
                
                with ribbon_col2:
                    st.markdown("#### 🚨 Danger")
                    if status['danger_detected']:
                        st.error("DANGER!")
                        if status['warnings']:
                            msg = f"Postural warning: {', '.join(status['warnings'])}"
                            trigger_voice_alert(msg)
                        else:
                            trigger_voice_alert("Danger detected. Check your posture.")
                    else:
                        st.success("Safe")
                
                with ribbon_col3:
                    st.markdown("#### 🥇 Stats")
                    stat_col1, stat_col2 = st.columns(2)
                    with stat_col1:
                        st.metric("Count", st.session_state.session_stats['total_jumps'])
                    with stat_col2:
                        st.metric("Points", st.session_state.session_stats['total_points'])
                
                st.markdown("---")
                
                # Database Update Status
                if f'last_db_update_jump' in st.session_state:
                    update_msg = st.session_state[f'last_db_update_jump']
                    update_time = st.session_state.get(f'last_db_update_time_jump', '')
                    st.markdown(f"#### 💾 Database Status:")
                    if '✅' in update_msg:
                        st.success(f"{update_msg} ({update_time})")
                    else:
                        st.error(f"{update_msg} ({update_time})")
                    st.markdown("---")
                
                # Fixed jump statistics - always present
                st.markdown("#### 📊 Jump Stats:")
                stats_col1, stats_col2 = st.columns(2)
                with stats_col1:
                    st.metric("Total Jumps", st.session_state.session_stats['total_jumps'])
                with stats_col2:
                    st.metric("Points", st.session_state.session_stats['total_points'])
                
                st.markdown("---")
            
            # Progress
            progress = frame_count / total_frames
            progress_bar.progress(progress)
        
        cap.release()
        
        # End session
        if st.session_state.session_id:
            db.end_session(
                st.session_state.session_id,
                st.session_state.session_stats['total_jumps'],
                st.session_state.session_stats['total_points'],
                st.session_state.session_stats['total_bad_moves'],
                0,  # total_squats for jump session
                0   # total_pushups for jump session
            )
            st.session_state.session_start_time = None
        
        if should_stop:
            st.warning("⏹️ Processing stopped by user")
        else:
            st.success(f"✅ Processing complete! Processed {frame_count} frames. Total jumps: {st.session_state.session_stats['total_jumps']}")
            
            # Extract highlights
            if not should_stop and hasattr(st.session_state.detector, 'rep_history'):
                with st.spinner("🎬 Extracting AI Highlights (Best & Worst Reps)..."):
                    extract_highlights_gifs(temp_path, st.session_state.detector.rep_history, 'jump')
        
        # Display performance analysis after processing is complete
        st.markdown("---")
        # Update prediction with final session data
        update_performance_prediction(db, 'jump', st.session_state.session_stats['total_jumps'])
        render_performance_prediction_panel('jump')
        
        # Wait a bit so user can see the success message and prediction panel before rerun
        # but rerun is necessary to update the top-level metrics
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error processing video: {str(e)}")
    finally:
        # Clean up temp file immediately
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

def process_live_camera(db, calibration_frames=100, jump_height="medium"):
    """Process live camera feed using OpenCV VideoCapture - continuous processing like video
    Uses the same configuration as video processing: knee/elbow trigger points, yellow line at center
    """
    # Initialize detector (same configuration as video processing)
    if st.session_state.detector is None:
        st.session_state.detector = JumpDetector(calibration_frames=calibration_frames, jump_height=jump_height)
    else:
        # Reset detector for new session (same as video processing)
        st.session_state.detector.reset()
        st.session_state.detector.CALIBRATION_FRAMES = calibration_frames
        st.session_state.detector.jump_height = jump_height
    
    # Create session if not exists
    if st.session_state.session_id is None:
        session_id = db.create_session(st.session_state.user_id)
        if session_id:
            st.session_state.session_id = session_id
            st.session_state.session_start_time = datetime.now()
        else:
            st.error("Failed to create session")
            return
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("❌ Could not open camera. Please check if camera is available and not being used by another application.")
        return
    
    # Create side-by-side layout: 60% video, 40% posture predictor
    video_col, posture_col = st.columns([0.6, 0.4])
    
    frame_placeholder = video_col.empty()
    stop_button_placeholder = st.empty()
    posture_placeholder = posture_col.empty()
    ribbon_placeholder = st.empty()
    
    st.info("📹 Live camera processing started! Position yourself in front of the camera. Click 'Start Processing' to begin live jump detection!")
    
    try:
        frame_count = 0
        should_stop = False
        
        # Continuous processing loop (same as video processing)
        while True:
            # Check for stop button
            if stop_button_placeholder.button("⏹️ Stop Processing", key=f"stop_camera_{frame_count}"):
                should_stop = True
                break
            
            ret, frame = cap.read()
            if not ret:
                st.warning("⚠️ Failed to read from camera. Check camera connection.")
                break
            
            frame_count += 1
            
            # Process frame
            annotated_frame, status = st.session_state.detector.process_frame(frame)
            
            # Update session stats
            if status['jump_count'] > st.session_state.session_stats['total_jumps']:
                # New jump detected
                jump_data = {
                    'jump_number': status['jump_count'],
                    'points': status['points'],
                    'bad_moves': status['bad_moves'],
                    'warnings': ', '.join(status['warnings']) if status['warnings'] else 'None',
                    'has_danger': status['danger_detected']
                }
                
                # Record to database
                db.record_jump(
                    st.session_state.session_id,
                    jump_data['jump_number'],
                    jump_data['points'],
                    jump_data['bad_moves'],
                    jump_data['warnings'],
                    jump_data['has_danger']
                )
                
                # Update stats
                st.session_state.session_stats['total_jumps'] = status['jump_count']
                st.session_state.session_stats['total_points'] += jump_data['points']
                st.session_state.session_stats['total_bad_moves'] += jump_data['bad_moves']
                st.session_state.session_stats['jumps_data'].append(jump_data)
                
                update_performance_prediction(db, 'jump', st.session_state.session_stats['total_jumps'])
                
                # Update session totals in database in real-time
                db.update_session_totals(
                    st.session_state.session_id,
                    st.session_state.session_stats['total_jumps'],
                    st.session_state.session_stats['total_points'],
                    st.session_state.session_stats['total_bad_moves'],
                    0,  # total_squats for jump session
                    0   # total_pushups for jump session
                )
                # Small delay to ensure database commit completes
                time.sleep(0.01)
            
            # Draw UI overlay (simplified - no warnings on video)
            h, w = annotated_frame.shape[:2]
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (0, 0), (300, 100), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, annotated_frame, 0.3, 0, annotated_frame)
            
            cv2.putText(annotated_frame, f"Jumps: {status['jump_count']}", (15, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (232, 168, 0), 2)
            cv2.putText(annotated_frame, f"Status: {status['status_text']}", (15, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Convert to RGB for display
            annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(annotated_frame_rgb, channels="RGB")
            
            # Posture Predictor Box (40% width) - Static layout with fixed placeholders
            with posture_placeholder.container():
                st.markdown("### 🎯 Posture Predictor")
                
                # Fixed info section
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.markdown(f"**Frame:** {frame_count}")
                with info_col2:
                    st.markdown(f"**Status:** {status['status_text']}")
                
                st.markdown("#### ⚠️ Warnings")
                if status['warnings']:
                    for warning in status['warnings']:
                        st.write(f"🔴 {warning}")
                else:
                    st.write("✅ No warnings")
                st.markdown("---")
            
            # Full-width Status Ribbon under video and posture box
            with ribbon_placeholder.container():
                st.markdown("### 📊 Live Performance Ribbon")
                ribbon_col1, ribbon_col2, ribbon_col3 = st.columns(3)
                
                with ribbon_col1:
                    st.markdown("#### ❌ Bad Moves")
                    st.markdown(f"## {status['bad_moves']}")
                
                with ribbon_col2:
                    st.markdown("#### 🚨 Danger")
                    if status['danger_detected']:
                        st.error("DANGER!")
                        if status['warnings']:
                            msg = f"Postural warning: {', '.join(status['warnings'])}"
                            trigger_voice_alert(msg)
                        else:
                            trigger_voice_alert("Danger detected. Check your posture.")
                    else:
                        st.success("Safe")
                
                with ribbon_col3:
                    st.markdown("#### 🥇 Stats")
                    stat_col1, stat_col2 = st.columns(2)
                    with stat_col1:
                        st.metric("Count", status['jump_count'])
                    with stat_col2:
                        st.metric("Points", status.get('points', 0))
                
                st.markdown("---")
            
            # Small delay for processing (adjust for performance)
            time.sleep(0.033)  # ~30 FPS
    
    except Exception as e:
        st.error(f"Error processing camera: {str(e)}")
    finally:
        cap.release()
        
        # End session
        if st.session_state.session_id:
            db.end_session(
                st.session_state.session_id,
                st.session_state.session_stats['total_jumps'],
                st.session_state.session_stats['total_points'],
                st.session_state.session_stats['total_bad_moves'],
                0,  # total_squats for jump session
                0   # total_pushups for jump session
            )
            st.session_state.session_start_time = None
        
        if should_stop:
            st.warning("⏹️ Processing stopped by user")
        else:
            st.success(f"✅ Processing complete! Processed {frame_count} frames. Total jumps: {st.session_state.session_stats['total_jumps']}")
        
        # Display performance analysis after processing is complete
        st.markdown("---")
        # Update prediction with final session data
        update_performance_prediction(db, 'jump', st.session_state.session_stats['total_jumps'])
        render_performance_prediction_panel('jump')
        
        st.rerun()

def main_app_jump(db):
    """Main jump training interface"""
    st.title("🏃 Jump Training Session")
    
    # Voice Alerts Toggle
    st.session_state.voice_alerts_enabled = st.toggle("🎙️ Enable Voice Alerts", value=st.session_state.voice_alerts_enabled, key="voice_toggle_jump")
    
    # Session stats display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Jumps", st.session_state.session_stats['total_jumps'])
    with col2:
        st.metric("Total Points", st.session_state.session_stats['total_points'])
    with col3:
        st.metric("Bad Moves", st.session_state.session_stats['total_bad_moves'])
    with col4:
        avg_points = (st.session_state.session_stats['total_points'] / 
                     max(st.session_state.session_stats['total_jumps'], 1))
        st.metric("Avg Points/Jump", f"{avg_points:.1f}")


    # Video input selection
    input_method = st.radio(
        "Select Input Method:",
        ["📹 Upload Video", "📷 Use Camera"],
        horizontal=True
    )
    
    if input_method == "📹 Upload Video":
        uploaded_file = st.file_uploader(
            "Upload a video file",
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="Upload a video file to analyze jumps"
        )
        
        if uploaded_file is not None:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                start_button = st.button("▶️ Start Processing", use_container_width=True)
            with col2:
                jump_height = st.selectbox(
                    "Jump Height",
                    options=["Low (small jump)", "Medium (normal jump)", "High (big jump)"],
                    index=1,  # Default to Medium
                    help="Select jump height level for calibration"
                )
            with col3:
                calibration_frames = st.number_input(
                    "Calibration Frames",
                    min_value=10,
                    max_value=300,
                    value=100,
                    step=10,
                    help="Number of frames to use for calibration (default: 100)"
                )
            
            if start_button:
                # Map dropdown selection to internal value
                jump_height_value = "low" if "Low" in jump_height else ("high" if "High" in jump_height else "medium")
                process_video_file(uploaded_file, db, calibration_frames, jump_height_value)
        
        if st.session_state.session_stats['total_jumps'] > 0:
            render_highlights_panel('jump')
            
            # Form Guide Expander
            with st.expander("📖 Form Guide: Correct Form"):
                guide_col1, guide_col2 = st.columns(2)
                with guide_col1:
                    st.markdown("#### ✅ Correct Form")
                    st.video("https://youtu.be/j260zYfRz8Q")
                    st.markdown("- Land softly on balls of feet\n- Keep chest up\n- Core engaged")
                # with guide_col2:
                #     st.markdown("#### ❌ Incorrect Form (Common Mistakes)")
                #     st.video("https://youtube.com/shorts/FJDZrSZQLiY?si=KjidK9GEGZWdX5FI")
                #     st.markdown("- Landing heavy on heels\n- Knees caving in\n- Poor posture")
            
            st.markdown("---")
            render_performance_prediction_panel('jump')
    
    else:  # Camera
        st.info("💡 Position yourself in front of the camera. Click 'Start Processing' to begin live jump detection!")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            start_button = st.button("▶️ Start Processing", use_container_width=True, type="primary")
        with col2:
            jump_height = st.selectbox(
                "Jump Height",
                options=["Low (small jump)", "Medium (normal jump)", "High (big jump)"],
                index=1,  # Default to Medium
                help="Select jump height level for calibration",
                key="camera_jump_height"
            )
        with col3:
            calibration_frames = st.number_input(
                "Calibration Frames",
                min_value=10,
                max_value=300,
                value=100,
                step=10,
                help="Number of frames to use for calibration (default: 100)",
                key="camera_calibration_frames"
            )
        
        if start_button:
            # Map dropdown selection to internal value
            jump_height_value = "low" if "Low" in jump_height else ("high" if "High" in jump_height else "medium")
            process_live_camera(db, calibration_frames, jump_height_value)

def main_app_squat(db):
    """Main squat training interface"""
    st.title("🦵 Squat Training Session")
    
    # Voice Alerts Toggle
    st.session_state.voice_alerts_enabled = st.toggle("🎙️ Enable Voice Alerts", value=st.session_state.voice_alerts_enabled, key="voice_toggle_squat")
    
    # Session stats display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Squats", st.session_state.session_stats['total_squats'])
    with col2:
        st.metric("Total Points", st.session_state.session_stats['total_points'])
    with col3:
        st.metric("Bad Moves", st.session_state.session_stats['total_bad_moves'])
    with col4:
        avg_points = (st.session_state.session_stats['total_points'] / 
                     max(st.session_state.session_stats['total_squats'], 1))
        st.metric("Avg Points/Squat", f"{avg_points:.1f}")


    # Video input selection
    input_method = st.radio(
        "Select Input Method:",
        ["📹 Upload Video", "📷 Use Camera"],
        horizontal=True
    )
    
    if input_method == "📹 Upload Video":
        uploaded_file = st.file_uploader(
            "Upload a video file",
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="Upload a video file to analyze squats"
        )
        
        if uploaded_file is not None:
            col1, col2 = st.columns([2, 1])
            with col1:
                start_button = st.button("▶️ Start Processing", use_container_width=True)
            with col2:
                calibration_frames = st.number_input(
                    "Calibration Frames",
                    min_value=10,
                    max_value=300,
                    value=100,
                    step=10,
                    help="Number of frames to use for calibration (default: 100)"
                )
            
            if start_button:
                process_squat_video_file(uploaded_file, db, calibration_frames)
        
        if st.session_state.session_stats['total_squats'] > 0:
            render_highlights_panel('squat')
            
            # Form Guide Expander
            with st.expander("📖 Form Guide: Correct Form"):
                guide_col1, guide_col2 = st.columns(2)
                with guide_col1:
                    st.markdown("#### ✅ Correct Form")
                    st.video("https://www.youtube.com/watch?v=xqvCmoLULNY")
                    st.markdown("- Feet shoulder-width apart\n- Chest up, back straight\n- Knees track over toes")
                # with guide_col2:
                #     st.markdown("#### ❌ Incorrect Form (Common Mistakes)")
                #     st.video("https://www.youtube.com/watch?v=T6id8FuUcao")
                #     st.markdown("- Knees caving in (Valgus)\n- Heels lifting off the ground\n- Rounding the lower back (Butt Wink)")
            
            st.markdown("---")
            render_performance_prediction_panel('squat')
    
    else:  # Camera
        st.info("💡 Position yourself in front of the camera. Click 'Start Processing' to begin live squat detection!")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            start_button = st.button("▶️ Start Processing", use_container_width=True, type="primary")
        with col2:
            calibration_frames = st.number_input(
            "Calibration Frames",
            min_value=10,
            max_value=300,
            value=100,
            step=10,
            help="Number of frames to use for calibration (default: 100)",
            key="squat_camera_calibration_frames"
        )
        
        if start_button:
            process_squat_live_camera(db, calibration_frames)

def process_squat_video_file(uploaded_file, db, calibration_frames=100):
    """Process uploaded video file for squats"""
    # Initialize detector
    if st.session_state.squat_detector is None:
        st.session_state.squat_detector = SquatDetector(calibration_frames=calibration_frames)
    else:
        # Reset detector for new video
        st.session_state.squat_detector.reset()
        st.session_state.squat_detector.CALIBRATION_FRAMES = calibration_frames
    
    # Create session if not exists
    if st.session_state.session_id is None:
        session_id = db.create_session(st.session_state.user_id)
        if session_id:
            st.session_state.session_id = session_id
            st.session_state.session_start_time = datetime.now()
        else:
            st.error("Failed to create session")
            return
    
    # Process video directly from uploaded file bytes using tempfile
    import tempfile
    import os
    
    temp_path = None
    try:
        # Create temporary file that auto-deletes when closed
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_file.write(uploaded_file.read())
            temp_path = temp_file.name
            
        # Validate video content
        validator = ExerciseValidator()
        is_valid, msg = validator.validate_video(temp_path, 'squat')
        if not is_valid:
            st.error(f"❌ Validation Failed: {msg}")
            os.unlink(temp_path)
            return
        
        # Process video
        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            st.error("Failed to open video file. Please check the file format.")
            os.unlink(temp_path)
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            st.error("Could not determine video frame count. Please check the video file.")
            cap.release()
            os.unlink(temp_path)
            return
        
        # Create side-by-side layout: 60% video, 40% posture predictor
        video_col, posture_col = st.columns([0.6, 0.4])
        
        frame_placeholder = video_col.empty()
        progress_bar = st.progress(0)
        stop_button_placeholder = st.empty()
        posture_placeholder = posture_col.empty()
        ribbon_placeholder_squat_video = st.empty()
        
        frame_count = 0
        should_stop = False
        
        st.info(f"📹 Processing video: {total_frames} frames at {fps:.1f} FPS")
        
        # Process all frames
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Check for stop button
            if stop_button_placeholder.button("⏹️ Stop Processing", key=f"squat_stop_{frame_count}"):
                should_stop = True
                break
            
            frame_count += 1
            
            # Process frame
            annotated_frame, status = st.session_state.squat_detector.process_frame(frame, frame_index=frame_count)
            
            # Update session stats
            if status['squat_count'] > st.session_state.session_stats['total_squats']:
                # New squat detected
                squat_data = {
                    'squat_number': status['squat_count'],
                    'points': status['points'],
                    'bad_moves': status['bad_moves'],
                    'warnings': ', '.join(status['warnings']) if status['warnings'] else 'None',
                    'has_danger': status['danger_detected']
                }
                
                # Record to database
                db.record_squat(
                    st.session_state.session_id,
                    squat_data['squat_number'],
                    squat_data['points'],
                    squat_data['bad_moves'],
                    squat_data['warnings'],
                    squat_data['has_danger']
                )
                
                # Update stats
                st.session_state.session_stats['total_squats'] = status['squat_count']
                st.session_state.session_stats['total_points'] += squat_data['points']
                st.session_state.session_stats['total_bad_moves'] += squat_data['bad_moves']
                st.session_state.session_stats['squats_data'].append(squat_data)
                
                update_performance_prediction(db, 'squat', st.session_state.session_stats['total_squats'])
                
                # Update session totals in database in real-time
                db.update_session_totals(
                    st.session_state.session_id,
                    0,  # total_jumps for squat session
                    st.session_state.session_stats['total_points'],
                    st.session_state.session_stats['total_bad_moves'],
                    st.session_state.session_stats.get('total_squats', 0),
                    0   # total_pushups for squat session
                )
                # Small delay to ensure database commit completes
                time.sleep(0.01)
            
            # Draw UI overlay
            h, w = annotated_frame.shape[:2]
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (0, 0), (300, 100), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, annotated_frame, 0.3, 0, annotated_frame)
            
            cv2.putText(annotated_frame, f"Squats: {status['squat_count']}", (15, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"Status: {status['status_text']}", (15, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Convert to RGB for display
            annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(annotated_frame_rgb, channels="RGB")
            
            # Posture Predictor Box
            with posture_placeholder.container():
                st.markdown("### 🎯 Posture Predictor")
                
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.markdown(f"**Frame:** {frame_count}/{total_frames}")
                with info_col2:
                    st.markdown(f"**Status:** {status['status_text']}")
                
                st.markdown("#### ⚠️ Warnings")
                if status['warnings']:
                    for warning in status['warnings']:
                        st.write(f"🔴 {warning}")
                else:
                    st.write("✅ No warnings")
                st.markdown("---")
            
            # Full-width Status Ribbon under video and posture box
            with ribbon_placeholder_squat_video.container():
                st.markdown("### 📊 Live Performance Ribbon")
                ribbon_col1, ribbon_col2, ribbon_col3 = st.columns(3)
                
                with ribbon_col1:
                    st.markdown("#### ❌ Bad Moves")
                    st.markdown(f"## {status['bad_moves']}")
                
                with ribbon_col2:
                    st.markdown("#### 🚨 Danger")
                    if status['danger_detected']:
                        st.error("DANGER!")
                        if status['warnings']:
                            msg = f"Postural warning: {', '.join(status['warnings'])}"
                            trigger_voice_alert(msg)
                        else:
                            trigger_voice_alert("Danger detected. Check your posture.")
                    else:
                        st.success("Safe")
                
                with ribbon_col3:
                    st.markdown("#### 🥇 Stats")
                    stat_col1, stat_col2 = st.columns(2)
                    with stat_col1:
                        st.metric("Count", st.session_state.session_stats['total_squats'])
                    with stat_col2:
                        st.metric("Points", st.session_state.session_stats['total_points'])
                
                st.markdown("---")
            
            # Progress
            progress = frame_count / total_frames
            progress_bar.progress(progress)
        
        cap.release()
        
        # End session
        if st.session_state.session_id:
            db.end_session(
                st.session_state.session_id,
                0,  # total_jumps for squat session
                st.session_state.session_stats['total_points'],
                st.session_state.session_stats['total_bad_moves'],
                st.session_state.session_stats.get('total_squats', 0),
                0  # total_pushups for squat session
            )
            st.session_state.session_start_time = None
        
        if should_stop:
            st.warning("⏹️ Processing stopped by user")
        else:
            st.success(f"✅ Processing complete! Processed {frame_count} frames. Total squats: {st.session_state.session_stats['total_squats']}")
            
            # Extract highlights
            if not should_stop and hasattr(st.session_state.squat_detector, 'rep_history'):
                with st.spinner("🎬 Extracting AI Highlights (Best & Worst Reps)..."):
                    extract_highlights_gifs(temp_path, st.session_state.squat_detector.rep_history, 'squat')
        
        # Display performance analysis after processing is complete
        st.markdown("---")
        # Update prediction with final session data
        update_performance_prediction(db, 'squat', st.session_state.session_stats['total_squats'])
        render_performance_prediction_panel('squat')
        
        # Wait a bit before rerun to see final results
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error processing video: {str(e)}")
    finally:
        # Clean up temp file immediately
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

def process_squat_live_camera(db, calibration_frames=100):
    """Process live camera feed for squats"""
    # Initialize detector
    if st.session_state.squat_detector is None:
        st.session_state.squat_detector = SquatDetector(calibration_frames=calibration_frames)
    else:
        # Reset detector for new session
        st.session_state.squat_detector.reset()
        st.session_state.squat_detector.CALIBRATION_FRAMES = calibration_frames
    
    # Create session if not exists
    if st.session_state.session_id is None:
        session_id = db.create_session(st.session_state.user_id)
        if session_id:
            st.session_state.session_id = session_id
            st.session_state.session_start_time = datetime.now()
        else:
            st.error("Failed to create session")
            return
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("❌ Could not open camera. Please check if camera is available and not being used by another application.")
        return
    
    # Create side-by-side layout: 60% video, 40% posture predictor
    video_col, posture_col = st.columns([0.6, 0.4])
    
    frame_placeholder = video_col.empty()
    stop_button_placeholder = st.empty()
    posture_placeholder = posture_col.empty()
    ribbon_placeholder_squat_camera = st.empty()
    
    st.info("📹 Live camera processing started! Position yourself and start squatting.")
    
    try:
        frame_count = 0
        should_stop = False
        
        # Continuous processing loop
        while True:
            # Check for stop button
            if stop_button_placeholder.button("⏹️ Stop Processing", key=f"squat_stop_camera_{frame_count}"):
                should_stop = True
                break
            
            ret, frame = cap.read()
            if not ret:
                st.warning("⚠️ Failed to read from camera. Check camera connection.")
                break
            
            frame_count += 1
            
            # Process frame
            annotated_frame, status = st.session_state.squat_detector.process_frame(frame)
            
            # Update session stats
            if status['squat_count'] > st.session_state.session_stats['total_squats']:
                # New squat detected
                squat_data = {
                    'squat_number': status['squat_count'],
                    'points': status['points'],
                    'bad_moves': status['bad_moves'],
                    'warnings': ', '.join(status['warnings']) if status['warnings'] else 'None',
                    'has_danger': status['danger_detected']
                }
                
                # Record to database
                db.record_squat(
                    st.session_state.session_id,
                    squat_data['squat_number'],
                    squat_data['points'],
                    squat_data['bad_moves'],
                    squat_data['warnings'],
                    squat_data['has_danger']
                )
                
                # Update stats
                st.session_state.session_stats['total_squats'] = status['squat_count']
                st.session_state.session_stats['total_points'] += squat_data['points']
                st.session_state.session_stats['total_bad_moves'] += squat_data['bad_moves']
                st.session_state.session_stats['squats_data'].append(squat_data)
                
                update_performance_prediction(db, 'squat', st.session_state.session_stats['total_squats'])
                
                # Update session totals in database in real-time
                db.update_session_totals(
                    st.session_state.session_id,
                    0,  # total_jumps for squat session
                    st.session_state.session_stats['total_points'],
                    st.session_state.session_stats['total_bad_moves'],
                    st.session_state.session_stats.get('total_squats', 0),
                    0   # total_pushups for squat session
                )
                # Small delay to ensure database commit completes
                time.sleep(0.01)
            
            # Draw UI overlay
            h, w = annotated_frame.shape[:2]
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (0, 0), (300, 100), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, annotated_frame, 0.3, 0, annotated_frame)
            
            cv2.putText(annotated_frame, f"Squats: {status['squat_count']}", (15, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"Status: {status['status_text']}", (15, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Convert to RGB for display
            annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(annotated_frame_rgb, channels="RGB")
            
            # Posture Predictor Box
            with posture_placeholder.container():
                st.markdown("### 🎯 Posture Predictor")
                
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.markdown(f"**Frame:** {frame_count}")
                with info_col2:
                    st.markdown(f"**Status:** {status['status_text']}")
                
                st.markdown("#### ⚠️ Warnings")
                if status['warnings']:
                    for warning in status['warnings']:
                        st.write(f"🔴 {warning}")
                else:
                    st.write("✅ No warnings")
                st.markdown("---")
            
            # Full-width Status Ribbon under video and posture box
            with ribbon_placeholder_squat_camera.container():
                st.markdown("### 📊 Live Performance Ribbon")
                ribbon_col1, ribbon_col2, ribbon_col3 = st.columns(3)
                
                with ribbon_col1:
                    st.markdown("#### ❌ Bad Moves")
                    st.markdown(f"## {status['bad_moves']}")
                
                with ribbon_col2:
                    st.markdown("#### 🚨 Danger")
                    if status['danger_detected']:
                        st.error("DANGER!")
                        if status['warnings']:
                            msg = f"Postural warning: {', '.join(status['warnings'])}"
                            trigger_voice_alert(msg)
                        else:
                            trigger_voice_alert("Danger detected. Check your posture.")
                    else:
                        st.success("Safe")
                
                with ribbon_col3:
                    st.markdown("#### 🥇 Stats")
                    stat_col1, stat_col2 = st.columns(2)
                    with stat_col1:
                        st.metric("Count", status['squat_count'])
                    with stat_col2:
                        st.metric("Points", status.get('points', 0))
                
                st.markdown("---")
            
            # Small delay for processing
            time.sleep(0.033)  # ~30 FPS
    
    except Exception as e:
        st.error(f"Error processing camera: {str(e)}")
    finally:
        cap.release()
        
        # End session
        if st.session_state.session_id:
            db.end_session(
                st.session_state.session_id,
                0,  # total_jumps for squat session
                st.session_state.session_stats['total_points'],
                st.session_state.session_stats['total_bad_moves'],
                st.session_state.session_stats.get('total_squats', 0),
                0  # total_pushups for squat session
            )
            st.session_state.session_start_time = None
        
        if should_stop:
            st.warning("⏹️ Processing stopped by user")
        else:
            st.success(f"✅ Processing complete! Processed {frame_count} frames. Total squats: {st.session_state.session_stats['total_squats']}")
        
        # Display performance analysis after processing is complete
        st.markdown("---")
        # Update prediction with final session data
        update_performance_prediction(db, 'squat', st.session_state.session_stats['total_squats'])
        render_performance_prediction_panel('squat')
        
        st.rerun()

def main_app_pushup(db):
    """Main push-up training interface"""
    st.title("💪 Push-up Training Session")
    
    # Voice Alerts Toggle
    st.session_state.voice_alerts_enabled = st.toggle("🎙️ Enable Voice Alerts", value=st.session_state.voice_alerts_enabled, key="voice_toggle_pushup")
    
    # Session stats display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Push-ups", st.session_state.session_stats['total_pushups'])
    with col2:
        st.metric("Total Points", st.session_state.session_stats['total_points'])
    with col3:
        st.metric("Bad Moves", st.session_state.session_stats['total_bad_moves'])
    with col4:
        avg_points = (st.session_state.session_stats['total_points'] / 
                     max(st.session_state.session_stats['total_pushups'], 1))
        st.metric("Avg Points/Push-up", f"{avg_points:.1f}")


    # Video input selection
    input_method = st.radio(
        "Select Input Method:",
        ["📹 Upload Video", "📷 Use Camera"],
        horizontal=True
    )
    
    if input_method == "📹 Upload Video":
        uploaded_file = st.file_uploader(
            "Upload a video file",
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="Upload a video file to analyze push-ups"
        )
        
        if uploaded_file is not None:
            col1, col2 = st.columns([2, 1])
            with col1:
                start_button = st.button("▶️ Start Processing", use_container_width=True)
            with col2:
                calibration_frames = st.number_input(
                    "Calibration Frames",
                    min_value=10,
                    max_value=300,
                    value=100,
                    step=10,
                    help="Number of frames to use for calibration (default: 100)"
                )
            
            if start_button:
                process_pushup_video_file(uploaded_file, db, calibration_frames)
        
        if st.session_state.session_stats['total_pushups'] > 0:
            render_highlights_panel('pushup')
            
            # Form Guide Expander
            with st.expander("📖 Form Guide: Correct Form"):
                guide_col1, guide_col2 = st.columns(2)
                with guide_col1:
                    st.markdown("#### ✅ Correct Form")
                    st.video("https://www.youtube.com/watch?v=pKZ-lkKKMws")
                    st.markdown("- Body in a straight line\n- Hands slightly wider than shoulders\n- Elbows tucked 45 degrees")
                # with guide_col2:
                #     st.markdown("#### ❌ Incorrect Form (Common Mistakes)")
                #     st.video("https://www.youtube.com/watch?v=4Bc1tPaYkOo")
                #     st.markdown("- Flared elbows (T-shape)\n- Sagging hips/arched back\n- Partial range of motion")
            
            st.markdown("---")
            render_performance_prediction_panel('pushup')
    
    else:  # Camera
        st.info("💡 Position yourself in front of the camera in push-up position. Click 'Start Processing' to begin live push-up detection!")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            start_button = st.button("▶️ Start Processing", use_container_width=True, type="primary")
        with col2:
            calibration_frames = st.number_input(
                "Calibration Frames",
                min_value=10,
                max_value=300,
                value=100,
                step=10,
                help="Number of frames to use for calibration (default: 100)",
                key="pushup_camera_calibration_frames"
            )
        
        if start_button:
            process_pushup_live_camera(db, calibration_frames)

def process_pushup_video_file(uploaded_file, db, calibration_frames=100):
    """Process uploaded video file for push-ups"""
    # Initialize detector
    if st.session_state.pushup_detector is None:
        st.session_state.pushup_detector = PushupDetector(calibration_frames=calibration_frames)
    else:
        # Reset detector for new video
        st.session_state.pushup_detector.reset()
        st.session_state.pushup_detector.CALIBRATION_FRAMES = calibration_frames
    
    # Create session if not exists
    if st.session_state.session_id is None:
        session_id = db.create_session(st.session_state.user_id)
        if session_id:
            st.session_state.session_id = session_id
            st.session_state.session_start_time = datetime.now()
        else:
            st.error("Failed to create session")
            return
    
    # Process video directly from uploaded file bytes using tempfile
    import tempfile
    import os
    
    temp_path = None
    try:
        # Create temporary file that auto-deletes when closed
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_file.write(uploaded_file.read())
            temp_path = temp_file.name
            
        # Validate video content
        validator = ExerciseValidator()
        is_valid, msg = validator.validate_video(temp_path, 'pushup')
        if not is_valid:
            st.error(f"❌ Validation Failed: {msg}")
            os.unlink(temp_path)
            return
        
        # Process video
        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            st.error("Failed to open video file. Please check the file format.")
            os.unlink(temp_path)
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            st.error("Could not determine video frame count. Please check the video file.")
            cap.release()
            os.unlink(temp_path)
            return
        
        # Create side-by-side layout: 60% video, 40% posture predictor
        video_col, posture_col = st.columns([0.6, 0.4])
        
        frame_placeholder = video_col.empty()
        progress_bar = st.progress(0)
        stop_button_placeholder = st.empty()
        posture_placeholder = posture_col.empty()
        ribbon_placeholder = st.empty()
        
        frame_count = 0
        should_stop = False
        
        st.info(f"📹 Processing video: {total_frames} frames at {fps:.1f} FPS")
        
        # Process all frames
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Check for stop button
            if stop_button_placeholder.button("⏹️ Stop Processing", key=f"pushup_stop_{frame_count}"):
                should_stop = True
                break
            
            frame_count += 1
            
            # Process frame
            annotated_frame, status = st.session_state.pushup_detector.process_frame(frame, frame_index=frame_count)
            
            # Update session stats
            if status['pushup_count'] > st.session_state.session_stats['total_pushups']:
                # New push-up detected
                pushup_data = {
                    'pushup_number': status['pushup_count'],
                    'points': status['points'],
                    'bad_moves': status['bad_moves'],
                    'warnings': ', '.join(status['warnings']) if status['warnings'] else 'None',
                    'has_danger': status['danger_detected']
                }
                
                # Record to database
                try:
                    db.record_pushup(
                        st.session_state.session_id,
                        pushup_data['pushup_number'],
                        pushup_data['points'],
                        pushup_data['bad_moves'],
                        pushup_data['warnings'],
                        pushup_data['has_danger']
                    )
                    
                    # Update stats
                    st.session_state.session_stats['total_pushups'] = status['pushup_count']
                    st.session_state.session_stats['total_points'] += pushup_data['points']
                    st.session_state.session_stats['total_bad_moves'] += pushup_data['bad_moves']
                    st.session_state.session_stats['pushups_data'].append(pushup_data)
                    
                    update_performance_prediction(db, 'pushup', st.session_state.session_stats['total_pushups'])
                    
                    # Update session totals in database in real-time
                    db.update_session_totals(
                        st.session_state.session_id,
                        0,  # total_jumps for push-up session
                        st.session_state.session_stats['total_points'],
                        st.session_state.session_stats['total_bad_moves'],
                        0,  # total_squats for push-up session
                        st.session_state.session_stats.get('total_pushups', 0)
                    )
                    # Show success notification
                    show_db_update_notification('pushup', status['pushup_count'], success=True)
                    # Small delay to ensure database commit completes
                    time.sleep(0.01)
                except Exception as e:
                    show_db_update_notification('pushup', status['pushup_count'], success=False)
                    st.error(f"Database error: {str(e)}")
            
            # Draw UI overlay
            h, w = annotated_frame.shape[:2]
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (0, 0), (300, 100), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, annotated_frame, 0.3, 0, annotated_frame)
            
            cv2.putText(annotated_frame, f"Push-ups: {status['pushup_count']}", (15, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"Status: {status['status_text']}", (15, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Convert to RGB for display
            annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(annotated_frame_rgb, channels="RGB")
            
            # Posture Predictor Box
            with posture_placeholder.container():
                st.markdown("### 🎯 Posture Predictor")
                
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.markdown(f"**Frame:** {frame_count}/{total_frames}")
                with info_col2:
                    st.markdown(f"**Status:** {status['status_text']}")
                
                st.markdown("#### ⚠️ Warnings")
                if status['warnings']:
                    for warning in status['warnings']:
                        st.write(f"🔴 {warning}")
                else:
                    st.write("✅ No warnings")
                st.markdown("---")
            
            # Full-width Status Ribbon under video and posture box
            with ribbon_placeholder.container():
                st.markdown("### 📊 Live Performance Ribbon")
                ribbon_col1, ribbon_col2, ribbon_col3 = st.columns(3)
                
                with ribbon_col1:
                    st.markdown("#### ❌ Bad Moves")
                    st.markdown(f"## {status['bad_moves']}")
                
                with ribbon_col2:
                    st.markdown("#### 🚨 Danger")
                    if status['danger_detected']:
                        st.error("DANGER!")
                        if status['warnings']:
                            msg = f"Postural warning: {', '.join(status['warnings'])}"
                            trigger_voice_alert(msg)
                        else:
                            trigger_voice_alert("Danger detected. Check your posture.")
                    else:
                        st.success("Safe")
                
                with ribbon_col3:
                    st.markdown("#### 🥇 Stats")
                    stat_col1, stat_col2 = st.columns(2)
                    with stat_col1:
                        st.metric("Count", st.session_state.session_stats['total_pushups'])
                    with stat_col2:
                        st.metric("Points", st.session_state.session_stats['total_points'])
                
                st.markdown("---")
            
            # Progress
            progress = frame_count / total_frames
            progress_bar.progress(progress)
        
        cap.release()
        
        # End session
        if st.session_state.session_id:
            db.end_session(
                st.session_state.session_id,
                0,  # total_jumps for push-up session
                st.session_state.session_stats['total_points'],
                st.session_state.session_stats['total_bad_moves'],
                0,  # total_squats for push-up session
                st.session_state.session_stats.get('total_pushups', 0)
            )
            st.session_state.session_start_time = None
        
        if should_stop:
            st.warning("⏹️ Processing stopped by user")
        else:
            st.success(f"✅ Processing complete! Processed {frame_count} frames. Total push-ups: {st.session_state.session_stats['total_pushups']}")
            
            # Extract highlights
            if not should_stop and hasattr(st.session_state.pushup_detector, 'rep_history'):
                with st.spinner("🎬 Extracting AI Highlights (Best & Worst Reps)..."):
                    extract_highlights_gifs(temp_path, st.session_state.pushup_detector.rep_history, 'pushup')
        
        # Display performance analysis after processing is complete
        st.markdown("---")
        # Update prediction with final session data
        update_performance_prediction(db, 'pushup', st.session_state.session_stats['total_pushups'])
        render_performance_prediction_panel('pushup')
        
        # Wait a bit before rerun to see final results
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error processing video: {str(e)}")
    finally:
        # Clean up temp file immediately
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

def process_pushup_live_camera(db, calibration_frames=100):
    """Process live camera feed for push-ups"""
    # Initialize detector
    if st.session_state.pushup_detector is None:
        st.session_state.pushup_detector = PushupDetector(calibration_frames=calibration_frames)
    else:
        # Reset detector for new session
        st.session_state.pushup_detector.reset()
        st.session_state.pushup_detector.CALIBRATION_FRAMES = calibration_frames
    
    # Create session if not exists
    if st.session_state.session_id is None:
        session_id = db.create_session(st.session_state.user_id)
        if session_id:
            st.session_state.session_id = session_id
            st.session_state.session_start_time = datetime.now()
        else:
            st.error("Failed to create session")
            return
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("❌ Could not open camera. Please check if camera is available and not being used by another application.")
        return
    
    # Create side-by-side layout: 60% video, 40% posture predictor
    video_col, posture_col = st.columns([0.6, 0.4])
    
    frame_placeholder = video_col.empty()
    stop_button_placeholder = st.empty()
    posture_placeholder = posture_col.empty()
    ribbon_placeholder = st.empty()
    
    st.info("📹 Live camera processing started! Position yourself in push-up position and start doing push-ups.")
    
    try:
        frame_count = 0
        should_stop = False
        
        # Continuous processing loop
        while True:
            # Check for stop button
            if stop_button_placeholder.button("⏹️ Stop Processing", key=f"pushup_stop_camera_{frame_count}"):
                should_stop = True
                break
            
            ret, frame = cap.read()
            if not ret:
                st.warning("⚠️ Failed to read from camera. Check camera connection.")
                break
            
            frame_count += 1
            
            # Process frame
            annotated_frame, status = st.session_state.pushup_detector.process_frame(frame)
            
            # Update session stats
            if status['pushup_count'] > st.session_state.session_stats['total_pushups']:
                # New push-up detected
                pushup_data = {
                    'pushup_number': status['pushup_count'],
                    'points': status['points'],
                    'bad_moves': status['bad_moves'],
                    'warnings': ', '.join(status['warnings']) if status['warnings'] else 'None',
                    'has_danger': status['danger_detected']
                }
                
                # Record to database
                try:
                    db.record_pushup(
                        st.session_state.session_id,
                        pushup_data['pushup_number'],
                        pushup_data['points'],
                        pushup_data['bad_moves'],
                        pushup_data['warnings'],
                        pushup_data['has_danger']
                    )
                    
                    # Update stats
                    st.session_state.session_stats['total_pushups'] = status['pushup_count']
                    st.session_state.session_stats['total_points'] += pushup_data['points']
                    st.session_state.session_stats['total_bad_moves'] += pushup_data['bad_moves']
                    st.session_state.session_stats['pushups_data'].append(pushup_data)
                    
                    update_performance_prediction(db, 'pushup', st.session_state.session_stats['total_pushups'])
                    
                    # Update session totals in database in real-time
                    db.update_session_totals(
                        st.session_state.session_id,
                        0,  # total_jumps for push-up session
                        st.session_state.session_stats['total_points'],
                        st.session_state.session_stats['total_bad_moves'],
                        0,  # total_squats for push-up session
                        st.session_state.session_stats.get('total_pushups', 0)
                    )
                    # Show success notification
                    show_db_update_notification('pushup', status['pushup_count'], success=True)
                    # Small delay to ensure database commit completes
                    time.sleep(0.01)
                except Exception as e:
                    show_db_update_notification('pushup', status['pushup_count'], success=False)
                    st.error(f"Database error: {str(e)}")
            
            # Draw UI overlay
            h, w = annotated_frame.shape[:2]
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (0, 0), (300, 100), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, annotated_frame, 0.3, 0, annotated_frame)
            
            cv2.putText(annotated_frame, f"Push-ups: {status['pushup_count']}", (15, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"Status: {status['status_text']}", (15, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Convert to RGB for display
            annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(annotated_frame_rgb, channels="RGB")
            
            # Posture Predictor Box
            with posture_placeholder.container():
                st.markdown("### 🎯 Posture Predictor")
                
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.markdown(f"**Frame:** {frame_count}")
                with info_col2:
                    st.markdown(f"**Status:** {status['status_text']}")
                
                st.markdown("#### ⚠️ Warnings")
                if status['warnings']:
                    for warning in status['warnings']:
                        st.write(f"🔴 {warning}")
                else:
                    st.write("✅ No warnings")
                st.markdown("---")
            
            # Full-width Status Ribbon under video and posture box
            with ribbon_placeholder.container():
                st.markdown("### 📊 Live Performance Ribbon")
                ribbon_col1, ribbon_col2, ribbon_col3 = st.columns(3)
                
                with ribbon_col1:
                    st.markdown("#### ❌ Bad Moves")
                    st.markdown(f"## {status['bad_moves']}")
                
                with ribbon_col2:
                    st.markdown("#### 🚨 Danger")
                    if status['danger_detected']:
                        st.error("DANGER!")
                        if status['warnings']:
                            msg = f"Postural warning: {', '.join(status['warnings'])}"
                            trigger_voice_alert(msg)
                        else:
                            trigger_voice_alert("Danger detected. Check your posture.")
                    else:
                        st.success("Safe")
                
                with ribbon_col3:
                    st.markdown("#### 🥇 Stats")
                    stat_col1, stat_col2 = st.columns(2)
                    with stat_col1:
                        st.metric("Count", status['pushup_count'])
                    with stat_col2:
                        st.metric("Points", status.get('points', 0))
                
                st.markdown("---")
            
            # Small delay for processing
            time.sleep(0.033)  # ~30 FPS
    
    except Exception as e:
        st.error(f"Error processing camera: {str(e)}")
    finally:
        cap.release()
        
        # End session
        if st.session_state.session_id:
            db.end_session(
                st.session_state.session_id,
                0,  # total_jumps for push-up session
                st.session_state.session_stats['total_points'],
                st.session_state.session_stats['total_bad_moves'],
                0,  # total_squats for push-up session
                st.session_state.session_stats.get('total_pushups', 0)
            )
            st.session_state.session_start_time = None
        
        if should_stop:
            st.warning("⏹️ Processing stopped by user")
        else:
            st.success(f"✅ Processing complete! Processed {frame_count} frames. Total push-ups: {st.session_state.session_stats['total_pushups']}")
        
        # Display performance analysis after processing is complete
        st.markdown("---")
        # Update prediction with final session data
        update_performance_prediction(db, 'pushup', st.session_state.session_stats['total_pushups'])
        render_performance_prediction_panel('pushup')
        
        st.rerun()

def leaderboard_page():
    """Display leaderboard with separate sections for each exercise"""
    st.title("🏆 Leaderboards")
    
    db = initialize_database()
    if db is None:
        st.error("Database connection failed. Please check your setup.")
        return
    
    # Create tabs for different leaderboards
    tab1, tab2, tab3, tab4 = st.tabs(["🏃 Jumps", "🦵 Squats", "💪 Push-ups", "📊 Overall"])
    
    # Jump Leaderboard
    with tab1:
        st.subheader("🏃 Jump Leaderboard")
        leaderboard = db.get_leaderboard(limit=20, exercise_type='jump')
        
        if leaderboard:
            df = pd.DataFrame(leaderboard)
            df['total_points'] = df['total_points'].fillna(0).astype(int)
            df['total_count'] = df['total_count'].fillna(0).astype(int)
            df['total_bad_moves'] = df['total_bad_moves'].fillna(0).astype(int)
            df['Rank'] = range(1, len(df) + 1)
            
            df_display = df[['Rank', 'name', 'age', 'total_count', 'total_points', 
                           'total_bad_moves', 'total_sessions', 'last_session']]
            df_display.columns = ['Rank', 'Name', 'Age', 'Total Jumps', 'Total Points', 
                                 'Bad Moves', 'Sessions', 'Last Session']
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(df.head(10), x='name', y='total_points', 
                            title="Top 10 by Points", labels={'name': 'Name', 'total_points': 'Points'},
                            color_discrete_sequence=['#FF2E2E'])
                st.plotly_chart(fig, use_container_width=True, key="jump_leaderboard_points")
            with col2:
                fig = px.bar(df.head(10), x='name', y='total_count',
                            title="Top 10 by Jumps", labels={'name': 'Name', 'total_count': 'Jumps'},
                            color_discrete_sequence=['#00A8E8'])
                st.plotly_chart(fig, use_container_width=True, key="jump_leaderboard_jumps")
        else:
            st.info("No jump data available yet. Start training to see rankings!")
    
    # Squat Leaderboard
    with tab2:
        st.subheader("🦵 Squat Leaderboard")
        leaderboard = db.get_leaderboard(limit=20, exercise_type='squat')
        
        if leaderboard:
            df = pd.DataFrame(leaderboard)
            df['total_points'] = df['total_points'].fillna(0).astype(int)
            df['total_count'] = df['total_count'].fillna(0).astype(int)
            df['total_bad_moves'] = df['total_bad_moves'].fillna(0).astype(int)
            df['Rank'] = range(1, len(df) + 1)
            
            df_display = df[['Rank', 'name', 'age', 'total_count', 'total_points', 
                           'total_bad_moves', 'total_sessions', 'last_session']]
            df_display.columns = ['Rank', 'Name', 'Age', 'Total Squats', 'Total Points', 
                                 'Bad Moves', 'Sessions', 'Last Session']
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(df.head(10), x='name', y='total_points', 
                            title="Top 10 by Points", labels={'name': 'Name', 'total_points': 'Points'},
                            color_discrete_sequence=['#FF2E2E'])
                st.plotly_chart(fig, use_container_width=True, key="squat_leaderboard_points")
            with col2:
                fig = px.bar(df.head(10), x='name', y='total_count',
                            title="Top 10 by Squats", labels={'name': 'Name', 'total_count': 'Squats'},
                            color_discrete_sequence=['#F28500'])
                st.plotly_chart(fig, use_container_width=True, key="squat_leaderboard_squats")
        else:
            st.info("No squat data available yet. Start training to see rankings!")
    
    # Push-up Leaderboard
    with tab3:
        st.subheader("💪 Push-up Leaderboard")
        leaderboard = db.get_leaderboard(limit=20, exercise_type='pushup')
        
        if leaderboard:
            df = pd.DataFrame(leaderboard)
            df['total_points'] = df['total_points'].fillna(0).astype(int)
            df['total_count'] = df['total_count'].fillna(0).astype(int)
            df['total_bad_moves'] = df['total_bad_moves'].fillna(0).astype(int)
            df['Rank'] = range(1, len(df) + 1)
            
            df_display = df[['Rank', 'name', 'age', 'total_count', 'total_points', 
                           'total_bad_moves', 'total_sessions', 'last_session']]
            df_display.columns = ['Rank', 'Name', 'Age', 'Total Push-ups', 'Total Points', 
                                 'Bad Moves', 'Sessions', 'Last Session']
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(df.head(10), x='name', y='total_points', 
                            title="Top 10 by Points", labels={'name': 'Name', 'total_points': 'Points'},
                            color_discrete_sequence=['#FF2E2E'])
                st.plotly_chart(fig, use_container_width=True, key="pushup_leaderboard_points")
            with col2:
                fig = px.bar(df.head(10), x='name', y='total_count',
                            title="Top 10 by Push-ups", labels={'name': 'Name', 'total_count': 'Push-ups'},
                            color_discrete_sequence=['#66FF00'])
                st.plotly_chart(fig, use_container_width=True, key="pushup_leaderboard_pushups")
        else:
            st.info("No push-up data available yet. Start training to see rankings!")
    
    # Overall Leaderboard
    with tab4:
        st.subheader("📊 Overall Leaderboard")
        leaderboard = db.get_leaderboard(limit=20, exercise_type='all')
        
        if leaderboard:
            df = pd.DataFrame(leaderboard)
            df['total_points'] = df['total_points'].fillna(0).astype(int)
            df['total_count'] = df['total_count'].fillna(0).astype(int)
            df['total_bad_moves'] = df['total_bad_moves'].fillna(0).astype(int)
            df['Rank'] = range(1, len(df) + 1)
            
            df_display = df[['Rank', 'name', 'age', 'total_count', 'total_points', 
                           'total_bad_moves', 'total_sessions', 'last_session']]
            df_display.columns = ['Rank', 'Name', 'Age', 'Total Exercises', 'Total Points', 
                                 'Bad Moves', 'Sessions', 'Last Session']
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(df.head(10), x='name', y='total_points', 
                            title="Top 10 by Points", labels={'name': 'Name', 'total_points': 'Points'},
                            color_discrete_sequence=['#FF2E2E'])
                st.plotly_chart(fig, use_container_width=True, key="overall_leaderboard_points")
            with col2:
                fig = px.bar(df.head(10), x='name', y='total_count',
                            title="Top 10 by Total Exercises", labels={'name': 'Name', 'total_count': 'Exercises'},
                            color_discrete_sequence=['#D162A4'])
                st.plotly_chart(fig, use_container_width=True, key="overall_leaderboard_total")
        else:
            st.info("No data available yet. Start training to see rankings!")

def dashboard_page():
    """Display comprehensive dashboard with statistics and charts"""
    st.title("📊 Personalized Fitness Dashboard")
    
    db = initialize_database()
    if db is None:
        st.error("Database connection failed. Please check your setup.")
        return
    
    stats = db.get_overall_stats()
    hourly_stats = db.get_hourly_exercise_stats(hours=24)
    exercise_dist = db.get_exercise_distribution()
    
    # Overall metrics - Row 1
    # Custom CSS for cards
    st.markdown("""
    <style>
    .dashboard-card {
        background-color: #001229;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    .metric-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #aaaaaa;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

    # Overall metrics - Card View
    st.markdown("### 📈 Overall Statistics")
    
    st.markdown(f"""
    <div class="dashboard-card">
        <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px;">
            <div class="metric-container">
                <div class="metric-label">Total Participants</div>
                <div class="metric-value">{stats.get('total_participants', 0)}</div>
            </div>
            <div class="metric-container">
                <div class="metric-label">Total Sessions</div>
                <div class="metric-value">{stats.get('total_sessions', 0)}</div>
            </div>
            <div class="metric-container">
                <div class="metric-label">Total Exercises</div>
                <div class="metric-value">{stats.get('total_exercises', 0)}</div>
            </div>
            <div class="metric-container">
                <div class="metric-label">Total Points</div>
                <div class="metric-value">{stats.get('total_points', 0)}</div>
            </div>
            <div class="metric-container">
                <div class="metric-label">Bad Moves</div>
                <div class="metric-value">{stats.get('total_bad_moves', 0)}</div>
            </div>
            <div class="metric-container">
                <div class="metric-label">Avg/Session</div>
                <div class="metric-value">{stats.get('avg_exercises_per_session', 0):.1f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Exercise-specific metrics - Card View
    st.markdown("### 🏋️ Exercise Breakdown")
    
    st.markdown(f"""
    <div class="dashboard-card">
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
            <div class="metric-container">
                <div class="metric-label">🏃 Total Jumps</div>
                <div class="metric-value" style="color: #00A8E8;">{stats.get('total_jumps', 0)}</div>
            </div>
            <div class="metric-container">
                <div class="metric-label">🦵 Total Squats</div>
                <div class="metric-value" style="color: #F28500;">{stats.get('total_squats', 0)}</div>
            </div>
            <div class="metric-container">
                <div class="metric-label">💪 Total Push-ups</div>
                <div class="metric-value" style="color: #66FF00;">{stats.get('total_pushups', 0)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts Section
    st.markdown("### 📊 Visualizations")
    
    # Pie Chart - Exercise Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Exercise Distribution")
        if exercise_dist['jumps'] + exercise_dist['squats'] + exercise_dist['pushups'] > 0:
            df_pie = pd.DataFrame({
                'exercise': ['Jumps', 'Squats', 'Push-ups'],
                'value': [exercise_dist['jumps'], exercise_dist['squats'], exercise_dist['pushups']]
            })
            fig_pie = px.pie(
                df_pie,
                values='value',
                names='exercise',
                color='exercise',
                title="Exercise Type Distribution",
                color_discrete_map={
                    'Jumps': '#00A8E8',
                    'Squats': '#F28500',
                    'Push-ups': '#66FF00'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True, key="dashboard_pie_chart")
        else:
            st.info("No exercise data available yet")
    
    with col2:
        st.markdown("#### Top Performers by Exercise")
        top_jumps = db.get_top_performers_by_exercise('jump', 5)
        top_squats = db.get_top_performers_by_exercise('squat', 5)
        top_pushups = db.get_top_performers_by_exercise('pushup', 5)
        
        if top_jumps or top_squats or top_pushups:
            fig_bar = go.Figure()
            
            if top_jumps:
                df_jumps = pd.DataFrame(top_jumps)
                fig_bar.add_trace(go.Bar(
                    name='Jumps',
                    x=df_jumps['name'],
                    y=df_jumps['count'],
                    marker_color='#00A8E8'
                ))
            
            if top_squats:
                df_squats = pd.DataFrame(top_squats)
                fig_bar.add_trace(go.Bar(
                    name='Squats',
                    x=df_squats['name'],
                    y=df_squats['count'],
                    marker_color='#F28500'
                ))
            
            if top_pushups:
                df_pushups = pd.DataFrame(top_pushups)
                fig_bar.add_trace(go.Bar(
                    name='Push-ups',
                    x=df_pushups['name'],
                    y=df_pushups['count'],
                    marker_color='#66FF00'
                ))
            
            fig_bar.update_layout(
                title="Top 5 Performers by Exercise Type",
                xaxis_title="User",
                yaxis_title="Count",
                barmode='group'
            )
            st.plotly_chart(fig_bar, use_container_width=True, key="dashboard_bar_chart")
        else:
            st.info("No performer data available yet")
    
    # Time-based Statistics Charts
    if hourly_stats:
        st.markdown("#### 🕒 Time Trends (Last 24 Hours)")
        df_time = pd.DataFrame(hourly_stats)
        df_time['hour'] = pd.to_datetime(df_time['hour'])
        df_time = df_time.sort_values('hour')
        for _col in ['jumps', 'squats', 'pushups', 'points', 'participants', 'sessions']:
            if _col in df_time.columns:
                df_time[_col] = pd.to_numeric(df_time[_col], errors='coerce').fillna(0)
        hour_end = pd.Timestamp.now().floor('H')
        hour_start = hour_end - pd.Timedelta(hours=23)
        all_hours = pd.date_range(start=hour_start, end=hour_end, freq='H')
        df_time = (
            df_time
            .set_index('hour')
            .reindex(all_hours)
            .rename_axis('hour')
            .reset_index()
        )
        for _col in ['jumps', 'squats', 'pushups', 'points', 'participants', 'sessions']:
            if _col in df_time.columns:
                df_time[_col] = df_time[_col].fillna(0)
        
        # Line Chart - Exercises Over Time
        col1, col2 = st.columns(2)
        
        with col1:
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=df_time['hour'],
                y=df_time['jumps'],
                mode='lines+markers',
                name='Jumps',
                line=dict(color='#00A8E8', width=2)
            ))
            fig_line.add_trace(go.Scatter(
                x=df_time['hour'],
                y=df_time['squats'],
                mode='lines+markers',
                name='Squats',
                line=dict(color='#F28500', width=2)
            ))
            fig_line.add_trace(go.Scatter(
                x=df_time['hour'],
                y=df_time['pushups'],
                mode='lines+markers',
                name='Push-ups',
                line=dict(color='#66FF00', width=2)
            ))
            fig_line.update_layout(
                title="Exercise Count Over Time (Hourly)",
                xaxis_title="Time",
                yaxis_title="Count",
                hovermode='x unified'
            )
            st.plotly_chart(fig_line, use_container_width=True, key="dashboard_line_chart")
        
        with col2:
            fig_points = px.line(
                df_time, 
                x='hour', 
                y='points',
                title="Points Over Time (Hourly)",
                markers=True
            )
            fig_points.update_traces(line_color='#FF2E2E', line_width=2)
            st.plotly_chart(fig_points, use_container_width=True, key="dashboard_points_chart")
        
        # Bar Charts - Sessions and Participants
        col3, col4 = st.columns(2)
        
        with col3:
            fig_sessions = px.bar(
                df_time,
                x='hour',
                y='sessions',
                title="Sessions Over Time (Hourly)",
                labels={'sessions': 'Number of Sessions', 'hour': 'Time'}
            )
            fig_sessions.update_traces(marker_color='#D162A4')
            st.plotly_chart(fig_sessions, use_container_width=True, key="dashboard_sessions_chart")
        
        with col4:
            fig_participants = px.line(
                df_time,
                x='hour',
                y='participants',
                title="Active Participants Over Time (Hourly)",
                markers=True
            )
            fig_participants.update_traces(line_color='#E2E200', line_width=2)
            st.plotly_chart(fig_participants, use_container_width=True, key="dashboard_participants_chart")
    else:
        st.info("No time-based statistics available yet. Start training to see trends!")
    
    # User stats if logged in
    if st.session_state.user_id:
        st.markdown("---")
        st.markdown("### 👤 Your Personal Statistics")
        user_stats = db.get_user_stats(st.session_state.user_id)
        
        if user_stats:
            sessions = user_stats.get('total_sessions') or 0
            jumps = user_stats.get('total_jumps') or 0
            points = user_stats.get('total_points') or 0
            avg_points = user_stats.get('avg_points_per_session') or 0
            avg_points = float(avg_points) if avg_points is not None else 0.0

            st.markdown(f"""
            <div class="dashboard-card">
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
                    <div class="metric-container">
                        <div class="metric-label">Your Sessions</div>
                        <div class="metric-value" style="color: #00A8E8;">{sessions}</div>
                    </div>
                    <div class="metric-container">
                        <div class="metric-label">Your Total Jumps</div>
                        <div class="metric-value" style="color: #00A8E8;">{jumps}</div>
                    </div>
                    <div class="metric-container">
                        <div class="metric-label">Your Total Points</div>
                        <div class="metric-value" style="color: #FF2E2E;">{points}</div>
                    </div>
                    <div class="metric-container">
                        <div class="metric-label">Avg Points/Session</div>
                        <div class="metric-value">{avg_points:.1f}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Complete a training session to see your statistics!")
    
    # ── Activity Calendar (inline) ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📅 Activity Calendar")
    st.caption("Your training consistency over the last 365 days (GitHub-style)")

    try:
        from datetime import timedelta as _td
        import plotly.graph_objects as _go
        _daily = db.get_daily_exercise_stats(days=365)

        if not _daily:
            st.info("No training data yet. Complete a session to start filling this calendar!")
        else:
            _end   = datetime.now().date()
            _start = _end - _td(days=364)
            _dates = pd.date_range(start=_start, end=_end)

            _df = pd.DataFrame(_daily)
            _df['date'] = pd.to_datetime(_df['date']).dt.date
            _dict = {}
            for _, r in _df.iterrows():
                _dict[r['date']] = int((r.get('jumps') or 0) +
                                       (r.get('squats') or 0) +
                                       (r.get('pushups') or 0))

            _z    = [[0]*53 for _ in range(7)]
            _htxt = [['']*53 for _ in range(7)]
            for d in _dates:
                _d = d.date()
                _wi = (_d - _start).days // 7
                _di = _d.weekday()
                if _wi < 53:
                    _v = _dict.get(_d, 0)
                    _z[_di][_wi] = _v
                    _htxt[_di][_wi] = f"{_d.strftime('%b %d, %Y')}<br>Exercises: {_v}"

            _fig = _go.Figure(_go.Heatmap(
                z=_z,
                x=[f"W{i}" for i in range(53)],
                y=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
                text=_htxt, hoverinfo='text',
                colorscale='Greens', showscale=False,
                xgap=2, ygap=2
            ))
            _fig.update_layout(
                height=200, margin=dict(l=40, r=20, t=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, autorange='reversed')
            )
            st.plotly_chart(_fig, use_container_width=True,
                            config={'displayModeBar': False},
                            key="dashboard_activity_calendar")

            _total  = sum(sum(r) for r in _z)
            _active = sum(1 for r in _z for v in r if v > 0)
            c1, c2 = st.columns(2)
            c1.metric("Total Exercises (Year)", _total)
            c2.metric("Active Days", _active)
    except Exception as _e:
        st.warning(f"Could not load Activity Calendar: {_e}")


def get_trainbot_response(user_message):
    """Generate TrainBot response based on LLM or fallback rule-based system"""
    # Check for Groq API Key in multiple locations
    api_key = None
    found_in_section = "Not found"

    try:
        # Direct check first
        api_key = st.secrets.get('GROQ_API_KEY')
        if api_key:
            found_in_section = "Direct"
        else:
            # Check in groq section
            if 'groq' in st.secrets:
                api_key = st.secrets.groq.get('api_key')
                if api_key:
                    found_in_section = "Groq section"

            # Fallback: check every section
            if not api_key:
                for section in st.secrets:
                    try:
                        section_data = st.secrets[section]
                        if hasattr(section_data, 'get'):
                            api_key = section_data.get('GROQ_API_KEY')
                            if api_key:
                                found_in_section = f"Section '{section}'"
                                break
                            # Also check for 'api_key' in case it's named differently
                            api_key = section_data.get('api_key')
                            if api_key:
                                found_in_section = f"Section '{section}' (api_key)"
                                break
                    except:
                        continue
    except:
        pass
    
    groq_client = None
    if api_key:
        try:
            groq_client = groq.Groq(api_key=api_key)
        except Exception as e:
            print(f"Error initializing Groq client: {e}")

    if groq_client:
        try:
            # Prepare COMPREHENSIVE system and DATABASE analysis about user
            db = Database() # Use Database class to get fresh connection
            comprehensive_context = ""
            if st.session_state.user_id:
                try:
                    # Get ALL user data from entire system
                    stats = db.get_user_stats(st.session_state.user_id)
                    
                    # Get recent sessions for ALL exercise types
                    recent_sessions = db.get_recent_sessions(st.session_state.user_id, limit=20)
                    
                    # Get current performance prediction if available
                    pred = st.session_state.get('performance_prediction')
                    pred_ex = st.session_state.get('performance_prediction_exercise')
                    
                    # === ENTIRE DATABASE ANALYSIS ===
                    try:
                        # Get comprehensive database statistics
                        all_users_stats = db.get_all_users_stats() if hasattr(db, 'get_all_users_stats') else None
                        all_sessions = db.get_all_sessions() if hasattr(db, 'get_all_sessions') else None
                        leaderboard_data = db.get_leaderboard(limit=100) if hasattr(db, 'get_leaderboard') else []
                        
                        database_insights = []
                        
                        if all_users_stats:
                            total_users = len(all_users_stats)
                            total_sessions_db = sum(user.get('total_sessions', 0) for user in all_users_stats)
                            total_points_db = sum(user.get('total_points', 0) for user in all_users_stats)
                            total_jumps_db = sum(user.get('total_jumps', 0) for user in all_users_stats)
                            total_squats_db = sum(user.get('total_squats', 0) for user in all_users_stats)
                            total_pushups_db = sum(user.get('total_pushups', 0) for user in all_users_stats)
                            
                            database_insights.append(f"DATABASE OVERVIEW: {total_users} total athletes, {total_sessions_db} total sessions, {total_points_db} total points scored")
                            database_insights.append(f"EXERCISE TOTALS: {total_jumps_db} jumps, {total_squats_db} squats, {total_pushups_db} push-ups across all users")
                            
                            if total_users > 0:
                                avg_sessions_per_user = total_sessions_db / total_users
                                avg_points_per_user = total_points_db / total_users
                                database_insights.append(f"USER AVERAGES: {avg_sessions_per_user:.1f} sessions/user, {avg_points_per_user:.1f} points/user")
                        
                        if all_sessions:
                            # Analyze exercise popularity
                            jump_sessions_db = [s for s in all_sessions if s.get('exercise_type') == 'jump']
                            squat_sessions_db = [s for s in all_sessions if s.get('exercise_type') == 'squat'] 
                            pushup_sessions_db = [s for s in all_sessions if s.get('exercise_type') == 'pushup']
                            
                            database_insights.append(f"EXERCISE POPULARITY: {len(jump_sessions_db)} jump sessions, {len(squat_sessions_db)} squat sessions, {len(pushup_sessions_db)} push-up sessions")
                            
                            # Find best performances in database
                            if all_sessions:
                                best_jump_session = max([s for s in jump_sessions_db if s.get('points')], key=lambda x: x.get('points', 0))
                                best_squat_session = max([s for s in squat_sessions_db if s.get('points')], key=lambda x: x.get('points', 0))
                                best_pushup_session = max([s for s in pushup_sessions_db if s.get('points')], key=lambda x: x.get('points', 0))
                                
                                if best_jump_session and best_jump_session.get('points'):
                                    database_insights.append(f"BEST JUMP: {best_jump_session.get('points')} points")
                                if best_squat_session and best_squat_session.get('points'):
                                    database_insights.append(f"BEST SQUAT: {best_squat_session.get('points')} points")
                                if best_pushup_session and best_pushup_session.get('points'):
                                    database_insights.append(f"BEST PUSH-UP: {best_pushup_session.get('points')} points")
                        
                        if leaderboard_data:
                            # Leaderboard analysis
                            if len(leaderboard_data) > 0:
                                top_performer = leaderboard_data[0]
                                total_points_in_leaderboard = sum(user.get('total_points', 0) for user in leaderboard_data)
                                avg_leaderboard_points = total_points_in_leaderboard / len(leaderboard_data)
                                
                                database_insights.append(f"LEADERBOARD: Top score {top_performer.get('total_points', 0)}, Average {avg_leaderboard_points:.1f} points")
                                
                                # Performance distribution analysis
                                high_performers = [u for u in leaderboard_data if u.get('total_points', 0) > avg_leaderboard_points]
                                database_insights.append(f"PERFORMANCE DIST: {len(high_performers)} users above average ({len(high_performers)/len(leaderboard_data)*100:.1f}%)")
                        
                        # Add database insights to context
                        if database_insights:
                            database_context = "DATABASE ANALYSIS: " + " | ".join(database_insights) + ". "
                        else:
                            database_context = "DATABASE ANALYSIS: Limited data available. "
                    except Exception as db_error:
                        print(f"Database analysis error: {db_error}")
                        database_context = "DATABASE ANALYSIS: Temporarily unavailable. "
                    
                    # Build COMPREHENSIVE context from ALL system modules
                    context_parts = []
                    
                    # === BASIC USER PROFILE ===
                    if stats:
                        context_parts.append(f"USER PROFILE: {stats['total_sessions']} total sessions, {stats.get('total_jumps', 0)} jumps, {stats.get('total_squats', 0)} squats, {stats.get('total_pushups', 0)} push-ups, {stats['total_points']} total points, {stats.get('total_bad_moves', 0)} bad moves detected")
                    
                    # Add database context first for broader perspective
                    if database_context:
                        context_parts.append(database_context)
                    
                    # === EXERCISE-SPECIFIC ANALYSIS ===
                    if recent_sessions:
                        # Analyze by exercise type
                        jump_sessions = [s for s in recent_sessions if s.get('exercise_type') == 'jump']
                        squat_sessions = [s for s in recent_sessions if s.get('exercise_type') == 'squat']
                        pushup_sessions = [s for s in recent_sessions if s.get('exercise_type') == 'pushup']
                        
                        context_parts.append(f"EXERCISE BREAKDOWN: {len(jump_sessions)} jump sessions, {len(squat_sessions)} squat sessions, {len(pushup_sessions)} push-up sessions")
                        
                        # Performance by exercise type
                        for ex_type, sessions, ex_name in [
                            (jump_sessions, 'jump'), 
                            (squat_sessions, 'squat'), 
                            (pushup_sessions, 'pushup')
                        ]:
                            if sessions:
                                ex_points = [s.get('points', 0) for s in sessions]
                                ex_errors = [s.get('bad_moves', 0) for s in sessions]
                                ex_reps = [s.get('reps', 0) for s in sessions if s.get('reps')]
                                
                                if ex_points:
                                    avg_points = sum(ex_points) / len(ex_points)
                                    best_session = max(ex_points)
                                    context_parts.append(f"{ex_name.upper()}: Avg {avg_points:.1f} pts, Best {best_session} pts, {sum(ex_reps)} total reps")
                                
                                if ex_errors:
                                    avg_errors = sum(ex_errors) / len(ex_errors)
                                    error_rate = (avg_errors / max(sum(ex_points), 1)) * 100
                                    context_parts.append(f"{ex_name.upper()} Errors: {avg_errors:.1f} avg, {error_rate:.1f}% error rate")
                    
                    # === DASHBOARD METRICS ===
                    if stats:
                        # Performance metrics from dashboard
                        avg_points_per_session = stats['total_points'] / max(stats['total_sessions'], 1)
                        overall_error_rate = (stats.get('total_bad_moves', 0) / max(stats['total_points'], 1)) * 100
                        context_parts.append(f"DASHBOARD INSIGHTS: {avg_points_per_session:.1f} avg pts/session, {overall_error_rate:.1f}% overall error rate")
                        
                        # Performance rating
                        if stats['total_points'] > 0:
                            performance_grade = "Excellent" if avg_points_per_session > 80 else "Good" if avg_points_per_session > 60 else "Needs Improvement"
                            context_parts.append(f"Performance Grade: {performance_grade}")
                    
                    # === TRAINING PLANS ANALYSIS ===
                    try:
                        # Check if user has training recommendations
                        from recommendations_ui import get_user_recommendations
                        recommendations = get_user_recommendations(st.session_state.user_id, db)
                        if recommendations:
                            context_parts.append(f"TRAINING PLANS: {len(recommendations)} active recommendations available")
                            # Analyze recommendation types
                            rec_types = [r.get('type', 'general') for r in recommendations]
                            if rec_types:
                                context_parts.append(f"Plan Focus: {', '.join(set(rec_types))}")
                        else:
                            context_parts.append("TRAINING PLANS: No personalized plans generated yet")
                    except Exception as rec_error:
                        print(f"Training plans analysis error: {rec_error}")
                        context_parts.append("TRAINING PLANS: Analysis temporarily unavailable")
                    
                    # === ACTIVITY CALENDAR INSIGHTS ===
                    try:
                        # Get activity pattern data
                        if recent_sessions:
                            # Analyze training frequency and patterns
                            from datetime import datetime, timedelta
                            session_dates = [s.get('session_date') for s in recent_sessions if s.get('session_date')]
                            if session_dates:
                                # Calculate training frequency
                                unique_days = len(set(session_dates))
                                total_days = (datetime.now() - min(session_dates)).days + 1
                                frequency = unique_days / total_days * 7  # sessions per week
                                context_parts.append(f"ACTIVITY CALENDAR: {frequency:.1f} training days/week, {unique_days} active days")
                                
                                # Identify training patterns
                                if len(session_dates) >= 3:
                                    recent_streak = 0
                                    for i in range(len(session_dates) - 1):
                                        if (session_dates[i] - session_dates[i+1]).days == 1:
                                            recent_streak += 1
                                        else:
                                            break
                                    if recent_streak > 0:
                                        context_parts.append(f"Current Streak: {recent_streak} consecutive days")
                    except Exception as cal_error:
                        print(f"Calendar analysis error: {cal_error}")
                        context_parts.append("ACTIVITY CALENDAR: Pattern analysis temporarily unavailable")
                    
                    # === LEADERBOARD POSITION ===
                    try:
                        # Get leaderboard data
                        all_users = db.get_leaderboard(limit=50) if hasattr(db, 'get_leaderboard') else []
                        if all_users:
                            user_rank = next((i+1 for i, user in enumerate(all_users) if user.get('user_id') == st.session_state.user_id), None)
                            total_users = len(all_users)
                            
                            if user_rank:
                                percentile = (total_users - user_rank) / total_users * 100
                                context_parts.append(f"LEADERBOARD: Rank #{user_rank}/{total_users} (Top {percentile:.0f}%)")
                            else:
                                context_parts.append("LEADERBOARD: Not ranked yet")
                            
                            # Top performer comparison
                            if len(all_users) > 0:
                                top_user = all_users[0]
                                user_points = stats.get('total_points', 0)
                                top_points = top_user.get('total_points', 0)
                                gap = top_points - user_points
                                context_parts.append(f"Gap to Leader: {gap} points")
                        else:
                            context_parts.append("LEADERBOARD: Data temporarily unavailable")
                    except Exception as lb_error:
                        print(f"Leaderboard analysis error: {lb_error}")
                        context_parts.append("LEADERBOARD: Ranking temporarily unavailable")
                    
                    # === PERFORMANCE PREDICTIONS ===
                    if pred and pred_ex:
                        fatigue_score = calculate_fatigue_score(pred) if hasattr(pred, 'history_points') else 0
                        fatigue_level = get_fatigue_level(fatigue_score)
                        
                        context_parts.append(f"PREDICTION ({pred_ex}): Speed {pred.predicted_speed_rpm:.1f} reps/min, Endurance {pred.predicted_endurance_score:.0f}/100, Rating {pred.predicted_rating:.0f}/100")
                        context_parts.append(f"FATIGUE ANALYSIS: Level {fatigue_level} ({fatigue_score:.1f}/100), Trend: {pred.trend}")
                        
                        if hasattr(pred, 'confidence_interval'):
                            context_parts.append(f"Expected Range: {pred.confidence_interval['lower']:.1f} - {pred.confidence_interval['upper']:.1f}")
                        
                        # Training load recommendations
                        if hasattr(pred, 'forecast') and pred.forecast:
                            best_load = max(pred.forecast, key=lambda x: x.get('pred_rating', 0))
                            context_parts.append(f"Optimal Training Load: {best_load.get('training_load', 1.0)*100:.0f}% intensity")
                    
                    # === CURRENT SESSION STATUS ===
                    if st.session_state.get('session_stats'):
                        session_stats = st.session_state.session_stats
                        context_parts.append(f"CURRENT SESSION: {session_stats.get('total_jumps', 0)} jumps, {session_stats.get('total_squats', 0)} squats, {session_stats.get('total_pushups', 0)} push-ups, {session_stats.get('total_points', 0)} points")
                    
                    # === SYSTEM-WIDE INSIGHTS ===
                    context_parts.append("SYSTEM SCOPE: Analyzing entire database, all user sessions, performance trends, leaderboard data, training plans, activity patterns, predictions, and real-time session data")
                    
                    comprehensive_context = " COMPREHENSIVE DATABASE & SYSTEM ANALYSIS: " + " | ".join(context_parts) + ". "
                    
                except Exception as e:
                    print(f"Error gathering comprehensive context: {e}")
                    # Fallback to basic user info if comprehensive analysis fails
                    try:
                        basic_stats = db.get_user_stats(st.session_state.user_id)
                        if basic_stats:
                            comprehensive_context = f" BASIC USER DATA: {basic_stats['total_sessions']} sessions, {basic_stats.get('total_jumps', 0)} jumps, {basic_stats.get('total_squats', 0)} squats, {basic_stats.get('total_pushups', 0)} push-ups, {basic_stats['total_points']} total points. "
                        else:
                            comprehensive_context = " Limited user data available. "
                    except:
                        comprehensive_context = " User data temporarily unavailable. "
            
            # Try primary model first, then fallback if needed
            models_to_try = ["llama3-8b-8192", "llama-3.1-8b-instant", "llama3-70b-8192"]
            
            for model_name in models_to_try:
                try:
                    completion = groq_client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": f"You are TrainBot, an ELITE AI PERFORMANCE ANALYST with access to the COMPLETE athletic training system. You analyze data from ALL modules: jump sessions, squat sessions, push-up sessions, performance dashboard, training plans, activity calendar, leaderboard, fatigue detection, and performance predictions. Provide comprehensive, data-driven insights that connect patterns across all system components. Give specific, actionable advice based on their complete athletic profile. Analyze strengths, weaknesses, trends, and provide holistic recommendations.{comprehensive_context}"},
                            {"role": "user", "content": user_message}
                        ],
                        temperature=0.7,
                        max_tokens=1024,
                    )
                    response = completion.choices[0].message.content
                    # Store success info for UI feedback
                    st.session_state.last_llm_response = True
                    st.session_state.last_llm_source = f"LLaMA 3 ({model_name})"
                    return response
                except Exception as model_error:
                    print(f"Model {model_name} failed: {model_error}")
                    if model_name == models_to_try[-1]:  # Last model tried
                        raise model_error
                    continue
        except Exception as e:
            print(f"Groq API error: {e}")
            # Store detailed error info for UI feedback
            st.session_state.last_llm_response = False
            error_str = str(e)
            
            # Parse common error types
            if "400" in error_str:
                if "api_key" in error_str.lower() or "unauthorized" in error_str.lower():
                    st.session_state.last_llm_error = "Invalid API key - check your Groq API key"
                elif "model" in error_str.lower():
                    st.session_state.last_llm_error = "Model not available - check Groq model availability"
                else:
                    st.session_state.last_llm_error = f"Bad Request (400): {error_str[:100]}"
            elif "401" in error_str:
                st.session_state.last_llm_error = "Authentication failed - check your API key"
            elif "429" in error_str:
                st.session_state.last_llm_error = "Rate limit exceeded - try again later"
            elif "500" in error_str:
                st.session_state.last_llm_error = "Groq server error - try again later"
            else:
                st.session_state.last_llm_error = f"API Error: {error_str[:100]}"
            
            # Fallback to rule-based if API fails
    else:
        # Store no API key info for UI feedback
        st.session_state.last_llm_response = False
        st.session_state.last_llm_error = "API key not configured"
    
    # Rule-based fallback (original implementation)
    message_lower = user_message.lower().strip()
    
    # Greetings and introductions
    greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
    if any(word in message_lower for word in greetings):
        return "Hello! I'm TrainBot, your AI fitness assistant! 👋 How can I help you today?"
    
    # Name/identity questions
    name_patterns = ['who are you', 'what is your name', 'what\'s your name', 'tell me about yourself', 
                     'introduce yourself', 'what are you', 'who am i talking to']
    if any(pattern in message_lower for pattern in name_patterns):
        return "I'm TrainBot! 🤖 Your friendly AI fitness assistant. I'm here to help you with your training, answer questions about exercises, and guide you on your fitness journey. What would you like to know?"
    
    # Help questions
    help_patterns = ['help', 'what can you do', 'what do you do', 'how can you help', 'capabilities', 'features']
    if any(pattern in message_lower for pattern in help_patterns):
        return "I can help you with:\n\n🏃 **Exercise Information**: Ask me about jumps, squats, push-ups, and proper form\n📊 **Training Tips**: Get advice on improving your workouts\n💪 **Motivation**: I'm here to encourage you!\n❓ **Questions**: Ask me anything about fitness and training\n\nWhat would you like to know?"
    
    # Exercise-related questions
    if 'jump' in message_lower:
        if any(word in message_lower for word in ['how', 'what', 'explain', 'tell']):
            return "Jumps are great cardio exercises! 🏃 Here are some tips:\n\n✅ Keep your knees aligned with your toes\n✅ Land softly with bent knees\n✅ Maintain good posture throughout\n✅ Start with lower jumps and gradually increase height\n\nWant to know more about jump training?"
        return "Jumps are excellent for cardiovascular fitness! Want tips on proper jump technique?"
    
    if 'squat' in message_lower:
        if any(word in message_lower for word in ['how', 'what', 'explain', 'tell']):
            return "Squats are fantastic for leg strength! 🦵 Here's how to do them properly:\n\n✅ Keep your feet shoulder-width apart\n✅ Keep your back straight\n✅ Lower down until your thighs are parallel to the ground\n✅ Push through your heels when coming up\n✅ Don't let your knees go past your toes\n\nNeed more squat tips?"
        return "Squats build leg muscles and core strength! Want to know more about proper squat form?"
    
    if 'push' in message_lower or 'pushup' in message_lower or 'push-up' in message_lower:
        if any(word in message_lower for word in ['how', 'what', 'explain', 'tell']):
            return "Push-ups are great for upper body strength! 💪 Here's the proper form:\n\n✅ Keep your body in a straight line (plank position)\n✅ Lower your body until your chest nearly touches the floor\n✅ Push back up to starting position\n✅ Keep your core engaged\n✅ Breathe out as you push up, breathe in as you lower\n\nReady to improve your push-ups?"
        return "Push-ups strengthen your chest, arms, and core! Want tips on proper form?"
    
    # Training/motivation
    if any(word in message_lower for word in ['motivate', 'motivation', 'encourage', 'inspire']):
        return "You're doing amazing! 💪 Every workout counts, and consistency is key. Remember:\n\n🌟 Progress takes time - be patient with yourself\n🌟 Small improvements lead to big results\n🌟 You're stronger than you think!\n\nKeep going! What exercise would you like to focus on today?"
    
    if any(word in message_lower for word in ['tips', 'advice', 'suggestions', 'recommend']):
        return "Here are some general training tips: 🎯\n\n✅ Warm up before exercising\n✅ Maintain proper form over speed\n✅ Listen to your body and rest when needed\n✅ Stay hydrated\n✅ Set realistic goals\n✅ Track your progress\n\nWhich exercise would you like specific tips for?"
    
    # Goodbye
    if any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'farewell', 'thanks', 'thank you']):
        return "You're welcome! 😊 Keep up the great work with your training! Feel free to come back anytime if you need help or motivation. Stay strong! 💪"
    
    # Questions about the app
    if any(word in message_lower for word in ['app', 'application', 'system', 'platform']):
        return "This is the AI Athlete Trainer app! 🏃 It uses computer vision (MediaPipe) to:\n\n📹 Track your exercises in real-time\n📊 Count your reps and analyze your form\n⚠️ Detect posture issues and bad moves\n🏆 Track your progress and compete on leaderboards\n\nHave you tried the jump, squat, or push-up sessions yet?"
    
    # Default response
    default_responses = [
        "That's interesting! I'm TrainBot, your fitness assistant. Could you tell me more about what you'd like to know? I can help with exercises, training tips, or answer questions about the app! 💪",
        "I'm here to help with your fitness journey! Ask me about exercises, training tips, or how to use the app. What would you like to know? 🤖",
        "Great question! I'm TrainBot, and I can help you with exercise information, training advice, or questions about workouts. What specific topic interests you? 🏋️"
    ]
    import random
    return random.choice(default_responses)

def trainbot_page():
    """TrainBot chat interface"""
    # Custom CSS for Premium Chat UI
    st.markdown("""
    <style>
    .trainbot-header {
        background: linear-gradient(135deg, #001229 0%, #002D5C 100%);
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 25px;
        border: 1px solid rgba(0, 168, 232, 0.2);
        text-align: center;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 15px;
    }
    .status-active { background: rgba(0, 255, 127, 0.15); color: #00FF7F; border: 1px solid rgba(0, 255, 127, 0.3); }
    .status-inactive { background: rgba(255, 165, 0, 0.15); color: #FFA500; border: 1px solid rgba(255, 165, 0, 0.3); }
    
    [data-testid="stChatMessage"] { background-color: transparent !important; border: none !important; }
    [data-testid="stChatMessageContent"] { padding: 15px 20px !important; border-radius: 18px !important; }
    [data-testid="stChatMessage"]:nth-child(even) [data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, #00A8E8 0%, #007EA7 100%) !important;
        color: white !important;
        border-bottom-right-radius: 4px !important;
    }
    [data-testid="stChatMessage"]:nth-child(odd) [data-testid="stChatMessageContent"] {
        background-color: #001229 !important;
        color: #E0F4FF !important;
        border: 1px solid rgba(0, 168, 232, 0.2) !important;
        border-bottom-left-radius: 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Check for Groq API Key using the same improved logic
    api_key_detected = None
    found_in_section = "Not found"

    try:
        # Direct check first
        api_key_detected = st.secrets.get('GROQ_API_KEY')
        if api_key_detected:
            found_in_section = "Direct"
        else:
            # Check in groq section
            if 'groq' in st.secrets:
                api_key_detected = st.secrets.groq.get('api_key')
                if api_key_detected:
                    found_in_section = "Groq section"

            # Fallback: check every section
            if not api_key_detected:
                for section in st.secrets:
                    try:
                        section_data = st.secrets[section]
                        if hasattr(section_data, 'get'):
                            api_key_detected = section_data.get('GROQ_API_KEY')
                            if api_key_detected:
                                found_in_section = f"Section '{section}'"
                                break
                            api_key_detected = section_data.get('api_key')
                        if api_key_detected:
                            found_in_section = f"Section '{section}' (api_key)"
                            break
                    except:
                        continue
    except:
        pass

    # Initialize chat history with welcome message
    if len(st.session_state.chat_history) == 0:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "Hello! I'm TrainBot, your elite performance coach. 👋 I've analyzed your recent sessions—how can I help you level up today?"
        })
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # System Analysis Section
    with st.expander("📊 System Performance Analysis", expanded=False):
        if st.button("🔍 Analyze My Performance", use_container_width=True, type="primary"):
            with st.spinner("🧠 Analyzing your performance data..."):
                try:
                    db = Database()
                    analysis_prompt = "Provide a comprehensive analysis of my athletic performance based on all my data. Include strengths, areas for improvement, fatigue patterns, and specific recommendations."
                    
                    # This will trigger the enhanced context gathering
                    analysis_response = get_trainbot_response(analysis_prompt)
                    
                    st.session_state.chat_history.append({
                        "role": "user", 
                        "content": "🔍 Analyze my complete performance profile"
                    })
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": analysis_response
                    })
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
        
        # Quick stats preview
        try:
            db = Database()
            if st.session_state.user_id:
                stats = db.get_user_stats(st.session_state.user_id)
                if stats:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Sessions", stats['total_sessions'])
                    with col2:
                        st.metric("Total Points", stats['total_points'])
                    with col3:
                        error_rate = (stats.get('total_bad_moves', 0) / max(stats['total_points'], 1)) * 100
                        st.metric("Error Rate", f"{error_rate:.1f}%")
                    with col4:
                        avg_points = stats['total_points'] / max(stats['total_sessions'], 1)
                        st.metric("Avg Points/Session", f"{avg_points:.1f}")
        except:
            st.info("Complete some training sessions to see performance analysis")
    
    # AI Quick Actions Toolbar with Card-Style Buttons
    st.markdown("---")
    st.markdown("##### ⚡ AI Quick Actions")
    
    # Custom CSS for card-style buttons
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] > div {
        gap: 20px !important;
    }
    .card-button {
        background: linear-gradient(135deg, #00A8E8 0%, #0077B6 100%);
        border: none;
        border-radius: 20px;
        padding: 25px 30px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        min-height: 80px;
        width: 100%;
        cursor: pointer;
        color: white;
        font-size: 1.2rem;
        font-weight: 600;
        text-align: left;
    }
    .card-button:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    .card-button.purple {
        background: linear-gradient(135deg, #E6D5FF 0%, #C8B6FF 100%);
        color: #2D1B4E;
    }
    .card-button.red {
        background: linear-gradient(135deg, #FFE5E5 0%, #FFB3B3 100%);
        border: 1px solid #FF9999;
        color: #8B0000;
    }
    .card-button-content {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .card-button-icon {
        font-size: 2.5rem;
        opacity: 0.8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Use columns for layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📑 **Training Report** 📊", key="report_btn", use_container_width=True, help="Generate comprehensive training report"):
            st.session_state.report_clicked = True
            st.rerun()
    
    with col2:
        if st.button("🗓️ **Workout Plan** 💪", key="workout_btn", use_container_width=True, help="Get personalized workout plan"):
            st.session_state.workout_clicked = True
            st.rerun()
    
    with col3:
        if st.button("🥗 **Diet Plan** 🍎", key="diet_btn", use_container_width=True, help="Create nutrition plan"):
            st.session_state.diet_clicked = True
            st.rerun()
    
    # Handle Training Report
    if st.session_state.report_clicked:
        st.session_state.report_clicked = False
        db = Database()
        report_gen = ReportGenerator()
        
        # Check for API key properly
        api_key = None
        try:
            api_key = st.secrets.get('GROQ_API_KEY')
            if not api_key and 'groq' in st.secrets:
                api_key = st.secrets.groq.get('api_key')
        except:
            pass
        
        if api_key:
            with st.spinner("🔍 Generating comprehensive training report..."):
                try:
                    # Get comprehensive user data for report
                    stats = db.get_user_stats(st.session_state.user_id)
                    recent_sessions = db.get_recent_sessions(st.session_state.user_id, limit=10)
                    
                    # Get additional data for comprehensive report
                    all_sessions = db.get_recent_sessions(st.session_state.user_id, limit=50)
                    leaderboard_data = db.get_leaderboard(limit=100) if hasattr(db, 'get_leaderboard') else []
                    
                    # Analyze exercise-specific performance
                    jump_sessions = [s for s in all_sessions if s.get('exercise_type') == 'jump']
                    squat_sessions = [s for s in all_sessions if s.get('exercise_type') == 'squat']
                    pushup_sessions = [s for s in all_sessions if s.get('exercise_type') == 'pushup']
                    
                    # Calculate performance metrics
                    performance_grade = "Good"
                    if stats and stats['total_sessions'] > 0:
                        avg_points = stats['total_points'] / stats['total_sessions']
                        if avg_points > 80:
                            performance_grade = "Excellent"
                        elif avg_points > 60:
                            performance_grade = "Good"
                        else:
                            performance_grade = "Needs Improvement"
                    
                    # Get leaderboard position
                    user_rank = "Not ranked"
                    if leaderboard_data:
                        rank = next((i+1 for i, user in enumerate(leaderboard_data) if user.get('user_id') == st.session_state.user_id), None)
                        if rank:
                            user_rank = f"#{rank}/{len(leaderboard_data)}"
                    
                    # Generate comprehensive report prompt
                    report_prompt = f"""
                    Generate a comprehensive training report for this athlete with the following data:
                    
                    ATHLETE PROFILE:
                    - Name: {st.session_state.user_name}
                    - Total Sessions: {stats['total_sessions'] if stats else 0}
                    - Total Points: {stats['total_points'] if stats else 0}
                    - Performance Grade: {performance_grade}
                    - Leaderboard Position: {user_rank}
                    
                    EXERCISE BREAKDOWN:
                    - Jump Sessions: {len(jump_sessions)} sessions
                    - Squat Sessions: {len(squat_sessions)} sessions  
                    - Push-up Sessions: {len(pushup_sessions)} sessions
                    
                    RECENT PERFORMANCE (Last 5 Sessions):
                    {recent_sessions[:5] if recent_sessions else "No recent sessions"}
                    
                    Please provide a detailed training report including:
                    1. Executive Summary of overall performance
                    2. Strengths and areas of excellence
                    3. Areas needing improvement
                    4. Exercise-specific analysis and recommendations
                    5. Performance trends and progress
                    6. Specific training recommendations for next 4 weeks
                    7. Goal setting and targets
                    
                    Format as a professional training report with clear sections and actionable insights.
                    """
                    
                    report_content = get_trainbot_response(report_prompt)
                    
                    # Display report preview in chat
                    st.subheader("📊 Your Training Report")
                    st.markdown(report_content)
                    
                    # Create and offer PDF download
                    try:
                        filepath, filename = report_gen.create_pdf_report(st.session_state.user_name, report_content, "Comprehensive Training Report")
                        with open(filepath, "rb") as f:
                            st.download_button(
                                "📥 Download Training Report PDF", 
                                data=f, 
                                file_name=filename, 
                                mime="application/pdf", 
                                key="dl_report",
                                use_container_width=True
                            )
                        st.success("✅ Training Report generated successfully! Click the download button to save your PDF.")
                    except Exception as pdf_error:
                        st.warning("⚠️ PDF generation failed, but you can copy the report above")
                        print(f"PDF generation error: {pdf_error}")
                    
                except Exception as e:
                    st.error(f"❌ Report generation failed: {e}")
                    print(f"Report generation error: {e}")
        else: 
            st.error("⚠️ Groq API Key missing. Please configure GROQ_API_KEY in secrets.toml")
    
    # Handle Workout Plan
    if st.session_state.workout_clicked:
        st.session_state.workout_clicked = False
        db = initialize_database()
        report_gen = ReportGenerator()
        has_groq = api_key_detected
        
        if has_groq:
            with st.spinner("🎯 Designing your personalized plan..."):
                try:
                    stats = db.get_user_stats(st.session_state.user_id)
                    prompt = f"Create a 7-day workout plan for an athlete with these stats: {stats}. Include specific exercises, sets, reps, and rest periods. Format as a professional workout plan with daily breakdown."
                    plan_content = get_trainbot_response(prompt)
                    
                    # Display workout plan preview in chat
                    st.subheader("💪 Your Workout Plan")
                    st.markdown(plan_content)
                    
                    # Create and offer PDF download
                    try:
                        filepath, filename = report_gen.create_pdf_report(st.session_state.user_name, plan_content, "Workout Plan")
                        with open(filepath, "rb") as f:
                            st.download_button(
                                "📥 Download Workout Plan PDF", 
                                data=f, 
                                file_name=filename, 
                                mime="application/pdf", 
                                key="dl_workout",
                                use_container_width=True
                            )
                        st.success("✅ Workout Plan generated successfully! Click the download button to save your PDF.")
                    except Exception as pdf_error:
                        st.warning("⚠️ PDF generation failed, but you can copy the workout plan above")
                        print(f"PDF generation error: {pdf_error}")
                        
                except Exception as e:
                    st.error(f"❌ Workout plan generation failed: {e}")
                    print(f"Workout plan generation error: {e}")
        else: 
            st.error("⚠️ Groq API Key missing. Please configure GROQ_API_KEY in secrets.toml")
    
    # Handle Diet Plan
    if st.session_state.diet_clicked:
        st.session_state.diet_clicked = False
        db = initialize_database()
        report_gen = ReportGenerator()
        has_groq = api_key_detected
        
        if has_groq:
            with st.spinner("🥗 Creating your personalized diet plan..."):
                try:
                    stats = db.get_user_stats(st.session_state.user_id)
                    prompt = f"Create a 7-day diet plan for an athlete with these stats: {stats}. Include breakfast, lunch, dinner, and snacks. Focus on nutrition for athletic performance."
                    plan_content = get_trainbot_response(prompt)
                    
                    # Display diet plan preview in chat
                    st.subheader("🥗 Your Diet Plan")
                    st.markdown(plan_content)
                    
                    # Create and offer PDF download
                    try:
                        filepath, filename = report_gen.create_pdf_report(st.session_state.user_name, plan_content, "Diet Plan")
                        with open(filepath, "rb") as f:
                            st.download_button(
                                "📥 Download Diet Plan PDF", 
                                data=f, 
                                file_name=filename, 
                                mime="application/pdf", 
                                key="dl_diet",
                                use_container_width=True
                            )
                        st.success("✅ Diet Plan generated successfully! Click the download button to save your PDF.")
                    except Exception as pdf_error:
                        st.warning("⚠️ PDF generation failed, but you can copy the diet plan above")
                        print(f"PDF generation error: {pdf_error}")
                        
                except Exception as e:
                    st.error(f"❌ Diet plan generation failed: {e}")
                    print(f"Diet plan generation error: {e}")
        else: 
            st.error("⚠️ Groq API Key missing. Please configure GROQ_API_KEY in secrets.toml")

    # Chat input
    # New Chat Button
    col1, col2 = st.columns([1, 10])
    with col1:
        if st.button("➕", key="new_chat_btn", help="Start new chat", use_container_width=True):
            st.session_state.chat_history = [{
                "role": "assistant",
                "content": "Hello! I'm TrainBot, your elite performance coach. 👋 I've analyzed your recent sessions—how can I help you level up today?"
            }]
            st.rerun()
    with col2:
        if prompt := st.chat_input("Message TrainBot Coach..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            response = get_trainbot_response(prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()

# Main app logic
if st.session_state.user_id is None:
    user_registration()
else:
    # Global setup
    load_css()
    db = initialize_database()
    
    # Sidebar
    render_sidebar(db)
    
    # Determine current page
    if 'page' not in st.session_state:
        st.session_state.page = 'main'
    
    if st.session_state.page == 'leaderboard':
        leaderboard_page()
    elif st.session_state.page == 'dashboard':
        dashboard_page()
    elif st.session_state.page == 'heatmap':
        heatmap_page()
    elif st.session_state.page == 'muscle_map':
        muscle_heatmap_page()
    elif st.session_state.page == 'trainbot':
        trainbot_page()
    elif st.session_state.page == 'recommendations':
        recommendations_page()
    else:
        main_app()

