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
from performance_prediction import compute_performance_prediction

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
    st.session_state.page = 'main'
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
if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'performance_prediction' not in st.session_state:
    st.session_state.performance_prediction = None
if 'performance_prediction_exercise' not in st.session_state:
    st.session_state.performance_prediction_exercise = None

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

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Pred Speed (reps/min)", f"{pred.predicted_speed_rpm:.1f}")
    with metric_col2:
        st.metric("Endurance Score", f"{pred.predicted_endurance_score:.0f}/100")
    with metric_col3:
        st.metric("Performance Rating", f"{pred.predicted_rating:.0f}/100")

    st.markdown(f"**Trend:** {pred.trend} (based on last {pred.history_points} sessions)")

    try:
        df = pd.DataFrame(pred.forecast)
        df = df.rename(columns={
            'training_load': 'Training Load',
            'pred_speed_rpm': 'Speed (reps/min)',
            'pred_endurance_score': 'Endurance',
            'pred_rating': 'Rating'
        })
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception:
        pass

def initialize_database():
    """Initialize database connection"""
    if 'db' not in st.session_state:
        st.session_state.db = Database()
    
    # Check if database is connected
    if not st.session_state.db.is_connected():
        return None
    return st.session_state.db

def user_registration():
    """User registration form"""
    # Read and encode the image as base64
    import base64
    from pathlib import Path
    
    # Get the current directory and construct the path to the image
    current_dir = Path(__file__).parent
    image_path = current_dir / "static" / "css" / "athlete.png"
    
    # Read and encode the image
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode()
        
        # Add CSS for background image using base64
        st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url("data:image/png;base64,{encoded_image}");
            background-size: cover;
            background-position: center 30%;
            background-repeat: no-repeat;
            background-attachment: fixed;
            min-height: 100vh;
        }}
        /* Target main content area */
        .main .block-container {{
            max-width: 100px !important;
            padding: 15px !important;
            background-color: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 15px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
            position: absolute !important;
            left: 20px !important;
            top: 20px !important;
        }}
        /* Target form specifically */
        div[data-testid="stForm"] {{
            max-width: 700px !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    except Exception as e:
        # Fallback if image loading fails
        st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .main .block-container {
            background-color: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            max-width: 600px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        </style>
        """, unsafe_allow_html=True)
    
    st.title("🏃 AI Athlete Trainer")
    st.markdown("### Welcome! Please enter your details to start training")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Check database connection first
    db = initialize_database()
    if db is None:
        st.error("⚠️ Database Connection Failed")
        st.markdown("""
        **Please set up the database:**
        
        **Quick Setup:**
        - Run: `python setup_database.py` from the source directory
        - This will create the SQLite database file automatically
        
        **Optional: Custom Database Path**
        - Create `.streamlit/secrets.toml` file if you want a custom location:
          ```toml
          [sqlite]
          database_path = "path/to/your/athlete_trainer.db"
          ```
        - If not specified, the database will be created in the source directory as `athlete_trainer.db`
        """)
        
        if st.button("🔄 Retry Connection"):
            if 'db' in st.session_state:
                del st.session_state.db
            st.rerun()
        return
    
    with st.form("user_registration"):
        name = st.text_input("Name", placeholder="Enter your name")
        age = st.number_input("Age", min_value=1, max_value=120, value=18)
        submit = st.form_submit_button("Start Training", use_container_width=True)
        
        if submit:
            if name and age:
                # Check if user already exists
                existing_user = db.get_user_by_name_age(name, age)
                
                if existing_user:
                    # Login existing user
                    st.session_state.user_id = existing_user['user_id']
                    st.session_state.user_name = existing_user['name']
                    st.session_state.user_age = existing_user['age']
                    st.success(f"Welcome back, {name}! Let's continue training!")
                else:
                    # Create new user
                    user_id = db.create_user(name, age)
                    
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.user_name = name
                        st.session_state.user_age = age
                        st.success(f"Welcome, {name}! Let's start training!")
                    else:
                        st.error("Failed to create user. Please check database connection.")
                        return
                
                st.rerun()
            else:
                st.warning("Please fill in all fields")

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
    
    # Sidebar
    with st.sidebar:
        st.title(f"👤 {st.session_state.user_name}")
        st.caption(f"Age: {st.session_state.user_age}")
        
        st.markdown("### Exercise Type")
        if st.button("🏃 Jump Session", use_container_width=True, type="primary" if st.session_state.exercise_type == 'jump' else "secondary"):
            st.session_state.exercise_type = 'jump'
            st.session_state.session_id = None
            st.session_state.session_start_time = None
            st.session_state.detector = None
            st.session_state.squat_detector = None
            st.session_state.pushup_detector = None
            st.session_state.performance_prediction = None
            st.session_state.performance_prediction_exercise = None
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
            st.rerun()
        
        if st.button("🦵 Squat Session", use_container_width=True, type="primary" if st.session_state.exercise_type == 'squat' else "secondary"):
            st.session_state.exercise_type = 'squat'
            st.session_state.session_id = None
            st.session_state.session_start_time = None
            st.session_state.detector = None
            st.session_state.squat_detector = None
            st.session_state.pushup_detector = None
            st.session_state.performance_prediction = None
            st.session_state.performance_prediction_exercise = None
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
            st.rerun()
        
        if st.button("💪 Push-up Session", use_container_width=True, type="primary" if st.session_state.exercise_type == 'pushup' else "secondary"):
            st.session_state.exercise_type = 'pushup'
            st.session_state.session_id = None
            st.session_state.session_start_time = None
            st.session_state.detector = None
            st.session_state.squat_detector = None
            st.session_state.pushup_detector = None
            st.session_state.performance_prediction = None
            st.session_state.performance_prediction_exercise = None
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
            st.rerun()
        
        st.markdown("---")
        
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()
        
        if st.button("🏆 Leaderboard", use_container_width=True):
            st.session_state.page = 'leaderboard'
            st.rerun()
        
        if st.button("🎯 TrainPlans", use_container_width=True):
            st.session_state.page = 'recommendations'
            st.rerun()
        
        if st.button("🤖 TrainBot", use_container_width=True):
            st.session_state.page = 'trainbot'
            st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True):
            # End current session if active
            if st.session_state.session_id:
                db.end_session(
                    st.session_state.session_id,
                    st.session_state.session_stats['total_jumps'],
                    st.session_state.session_stats['total_points'],
                    st.session_state.session_stats['total_bad_moves'],
                    st.session_state.session_stats.get('total_squats', 0),
                    st.session_state.session_stats.get('total_pushups', 0)
                )
            
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content area - route based on exercise type
    if st.session_state.exercise_type == 'squat':
        main_app_squat(db)
    elif st.session_state.exercise_type == 'pushup':
        main_app_pushup(db)
    else:
        main_app_jump(db)

def show_db_update_notification(exercise_type, count, success=True):
    """Show database update notification"""
    if success:
        st.session_state[f'last_db_update_{exercise_type}'] = f"✅ {exercise_type.capitalize()} #{count} saved to database!"
        st.session_state[f'last_db_update_time_{exercise_type}'] = datetime.now().strftime("%H:%M:%S")
    else:
        st.session_state[f'last_db_update_{exercise_type}'] = f"❌ Database update failed!"
        st.session_state[f'last_db_update_time_{exercise_type}'] = datetime.now().strftime("%H:%M:%S")

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
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
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
                
                st.markdown("---")
                
                # Fixed warnings section - always present, updates in place
                st.markdown("#### ⚠️ Current Warnings:")
                warnings_text = ""
                if status['warnings']:
                    for warning in status['warnings']:
                        warnings_text += f"🔴 {warning}\n\n"
                else:
                    warnings_text = "✅ No warnings"
                st.markdown(warnings_text)
                
                st.markdown("---")
                
                # Fixed bad moves section - always present
                st.markdown("#### ❌ Bad Moves:")
                st.markdown(f"**{status['bad_moves']}**")
                
                st.markdown("---")
                
                # Fixed danger section - always present
                st.markdown("#### 🚨 Danger Status:")
                if status['danger_detected']:
                    st.error("**DANGER DETECTED!**")
                else:
                    st.success("**No Danger**")
                
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
                    st.metric("Total Jumps", status['jump_count'])
                with stats_col2:
                    points = status.get('points', 0)
                    st.metric("Points", points)
                
                st.markdown("---")
                render_performance_prediction_panel('jump')
            
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
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
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
                
                st.markdown("---")
                
                # Fixed warnings section - always present, updates in place
                st.markdown("#### ⚠️ Current Warnings:")
                warnings_text = ""
                if status['warnings']:
                    for warning in status['warnings']:
                        warnings_text += f"🔴 {warning}\n\n"
                else:
                    warnings_text = "✅ No warnings"
                st.markdown(warnings_text)
                
                st.markdown("---")
                
                # Fixed bad moves section - always present
                st.markdown("#### ❌ Bad Moves:")
                st.markdown(f"**{status['bad_moves']}**")
                
                st.markdown("---")
                
                # Fixed danger section - always present
                st.markdown("#### 🚨 Danger Status:")
                if status['danger_detected']:
                    st.error("**DANGER DETECTED!**")
                else:
                    st.success("**No Danger**")
                
                st.markdown("---")
                
                # Fixed jump statistics - always present
                st.markdown("#### 📊 Jump Stats:")
                stats_col1, stats_col2 = st.columns(2)
                with stats_col1:
                    st.metric("Total Jumps", status['jump_count'])
                with stats_col2:
                    points = status.get('points', 0)
                    st.metric("Points", points)
                
                st.markdown("---")
                render_performance_prediction_panel('jump')
            
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
        
        st.rerun()

def main_app_jump(db):
    """Main jump training interface"""
    st.title("🏃 Jump Training Session")
    
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
                    st.markdown(f"**Frame:** {frame_count}/{total_frames}")
                with info_col2:
                    st.markdown(f"**Status:** {status['status_text']}")
                
                st.markdown("---")
                
                st.markdown("#### ⚠️ Current Warnings:")
                warnings_text = ""
                if status['warnings']:
                    for warning in status['warnings']:
                        warnings_text += f"🔴 {warning}\n\n"
                else:
                    warnings_text = "✅ No warnings"
                st.markdown(warnings_text)
                
                st.markdown("---")
                
                st.markdown("#### ❌ Bad Moves:")
                st.markdown(f"**{status['bad_moves']}**")
                
                st.markdown("---")
                
                st.markdown("#### 🚨 Danger Status:")
                if status['danger_detected']:
                    st.error("**DANGER DETECTED!**")
                else:
                    st.success("**No Danger**")
                
                st.markdown("---")
                
                # Database Update Status
                if f'last_db_update_squat' in st.session_state:
                    update_msg = st.session_state[f'last_db_update_squat']
                    update_time = st.session_state.get(f'last_db_update_time_squat', '')
                    st.markdown(f"#### 💾 Database Status:")
                    if '✅' in update_msg:
                        st.success(f"{update_msg} ({update_time})")
                    else:
                        st.error(f"{update_msg} ({update_time})")
                    st.markdown("---")
                
                st.markdown("#### 📊 Squat Stats:")
                stats_col1, stats_col2 = st.columns(2)
                with stats_col1:
                    st.metric("Total Squats", status['squat_count'])
                with stats_col2:
                    points = status.get('points', 0)
                    st.metric("Points", points)
                
                st.markdown("---")
                render_performance_prediction_panel('squat')
            
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
                
                st.markdown("---")
                
                st.markdown("#### ⚠️ Current Warnings:")
                warnings_text = ""
                if status['warnings']:
                    for warning in status['warnings']:
                        warnings_text += f"🔴 {warning}\n\n"
                else:
                    warnings_text = "✅ No warnings"
                st.markdown(warnings_text)
                
                st.markdown("---")
                
                st.markdown("#### ❌ Bad Moves:")
                st.markdown(f"**{status['bad_moves']}**")
                
                st.markdown("---")
                
                st.markdown("#### 🚨 Danger Status:")
                if status['danger_detected']:
                    st.error("**DANGER DETECTED!**")
                else:
                    st.success("**No Danger**")
                
                st.markdown("---")
                
                # Database Update Status
                if f'last_db_update_squat' in st.session_state:
                    update_msg = st.session_state[f'last_db_update_squat']
                    update_time = st.session_state.get(f'last_db_update_time_squat', '')
                    st.markdown(f"#### 💾 Database Status:")
                    if '✅' in update_msg:
                        st.success(f"{update_msg} ({update_time})")
                    else:
                        st.error(f"{update_msg} ({update_time})")
                    st.markdown("---")
                
                st.markdown("#### 📊 Squat Stats:")
                stats_col1, stats_col2 = st.columns(2)
                with stats_col1:
                    st.metric("Total Squats", status['squat_count'])
                with stats_col2:
                    points = status.get('points', 0)
                    st.metric("Points", points)
                
                st.markdown("---")
                render_performance_prediction_panel('squat')
            
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
        
        st.rerun()

def main_app_pushup(db):
    """Main push-up training interface"""
    st.title("💪 Push-up Training Session")
    
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
                    st.markdown(f"**Frame:** {frame_count}/{total_frames}")
                with info_col2:
                    st.markdown(f"**Status:** {status['status_text']}")
                
                st.markdown("---")
                
                st.markdown("#### ⚠️ Current Warnings:")
                warnings_text = ""
                if status['warnings']:
                    for warning in status['warnings']:
                        warnings_text += f"🔴 {warning}\n\n"
                else:
                    warnings_text = "✅ No warnings"
                st.markdown(warnings_text)
                
                st.markdown("---")
                
                st.markdown("#### ❌ Bad Moves:")
                st.markdown(f"**{status['bad_moves']}**")
                
                st.markdown("---")
                
                st.markdown("#### 🚨 Danger Status:")
                if status['danger_detected']:
                    st.error("**DANGER DETECTED!**")
                else:
                    st.success("**No Danger**")
                
                st.markdown("---")
                
                # Database Update Status
                if f'last_db_update_pushup' in st.session_state:
                    update_msg = st.session_state[f'last_db_update_pushup']
                    update_time = st.session_state.get(f'last_db_update_time_pushup', '')
                    st.markdown(f"#### 💾 Database Status:")
                    if '✅' in update_msg:
                        st.success(f"{update_msg} ({update_time})")
                    else:
                        st.error(f"{update_msg} ({update_time})")
                    st.markdown("---")
                
                st.markdown("#### 📊 Push-up Stats:")
                stats_col1, stats_col2 = st.columns(2)
                with stats_col1:
                    st.metric("Total Push-ups", status['pushup_count'])
                with stats_col2:
                    points = status.get('points', 0)
                    st.metric("Points", points)
                
                st.markdown("---")
                render_performance_prediction_panel('pushup')
            
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
                
                st.markdown("---")
                
                st.markdown("#### ⚠️ Current Warnings:")
                warnings_text = ""
                if status['warnings']:
                    for warning in status['warnings']:
                        warnings_text += f"🔴 {warning}\n\n"
                else:
                    warnings_text = "✅ No warnings"
                st.markdown(warnings_text)
                
                st.markdown("---")
                
                st.markdown("#### ❌ Bad Moves:")
                st.markdown(f"**{status['bad_moves']}**")
                
                st.markdown("---")
                
                st.markdown("#### 🚨 Danger Status:")
                if status['danger_detected']:
                    st.error("**DANGER DETECTED!**")
                else:
                    st.success("**No Danger**")
                
                st.markdown("---")
                
                # Database Update Status
                if f'last_db_update_pushup' in st.session_state:
                    update_msg = st.session_state[f'last_db_update_pushup']
                    update_time = st.session_state.get(f'last_db_update_time_pushup', '')
                    st.markdown(f"#### 💾 Database Status:")
                    if '✅' in update_msg:
                        st.success(f"{update_msg} ({update_time})")
                    else:
                        st.error(f"{update_msg} ({update_time})")
                    st.markdown("---")
                
                st.markdown("#### 📊 Push-up Stats:")
                stats_col1, stats_col2 = st.columns(2)
                with stats_col1:
                    st.metric("Total Push-ups", status['pushup_count'])
                with stats_col2:
                    points = status.get('points', 0)
                    st.metric("Points", points)
                
                st.markdown("---")
                render_performance_prediction_panel('pushup')
            
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
        
        st.rerun()

def leaderboard_page():
    """Display leaderboard with separate sections for each exercise"""
    # Back button at the top
    if st.button("← Back to Training"):
        st.session_state.page = 'main'
        st.rerun()
    
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
                            title="Top 10 by Points", labels={'name': 'Name', 'total_points': 'Points'})
                st.plotly_chart(fig, use_container_width=True, key="jump_leaderboard_points")
            with col2:
                fig = px.bar(df.head(10), x='name', y='total_count',
                            title="Top 10 by Jumps", labels={'name': 'Name', 'total_count': 'Jumps'})
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
                            title="Top 10 by Points", labels={'name': 'Name', 'total_points': 'Points'})
                st.plotly_chart(fig, use_container_width=True, key="squat_leaderboard_points")
            with col2:
                fig = px.bar(df.head(10), x='name', y='total_count',
                            title="Top 10 by Squats", labels={'name': 'Name', 'total_count': 'Squats'})
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
                            title="Top 10 by Points", labels={'name': 'Name', 'total_points': 'Points'})
                st.plotly_chart(fig, use_container_width=True, key="pushup_leaderboard_points")
            with col2:
                fig = px.bar(df.head(10), x='name', y='total_count',
                            title="Top 10 by Push-ups", labels={'name': 'Name', 'total_count': 'Push-ups'})
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
                            title="Top 10 by Points", labels={'name': 'Name', 'total_points': 'Points'})
                st.plotly_chart(fig, use_container_width=True, key="overall_leaderboard_points")
            with col2:
                fig = px.bar(df.head(10), x='name', y='total_count',
                            title="Top 10 by Total Exercises", labels={'name': 'Name', 'total_count': 'Exercises'})
                st.plotly_chart(fig, use_container_width=True, key="overall_leaderboard_total")
        else:
            st.info("No data available yet. Start training to see rankings!")

def dashboard_page():
    """Display comprehensive dashboard with statistics and charts"""
    # Back button at the top
    if st.button("← Back to Training"):
        st.session_state.page = 'main'
        st.rerun()
    
    st.title("📊 Dashboard")
    
    db = initialize_database()
    if db is None:
        st.error("Database connection failed. Please check your setup.")
        return
    
    stats = db.get_overall_stats()
    hourly_stats = db.get_hourly_exercise_stats(hours=24)
    exercise_dist = db.get_exercise_distribution()
    
    # Overall metrics - Row 1
    st.markdown("### 📈 Overall Statistics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Total Participants", stats.get('total_participants', 0))
    with col2:
        st.metric("Total Sessions", stats.get('total_sessions', 0))
    with col3:
        st.metric("Total Exercises", stats.get('total_exercises', 0))
    with col4:
        st.metric("Total Points", stats.get('total_points', 0))
    with col5:
        st.metric("Bad Moves", stats.get('total_bad_moves', 0))
    with col6:
        st.metric("Avg/Session", f"{stats.get('avg_exercises_per_session', 0):.1f}")
    
    # Exercise-specific metrics - Row 2
    st.markdown("### 🏋️ Exercise Breakdown")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🏃 Total Jumps", stats.get('total_jumps', 0))
    with col2:
        st.metric("🦵 Total Squats", stats.get('total_squats', 0))
    with col3:
        st.metric("💪 Total Push-ups", stats.get('total_pushups', 0))
    
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
                    'Jumps': '#1f77b4',
                    'Squats': '#ff7f0e',
                    'Push-ups': '#2ca02c'
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
                    marker_color='#1f77b4'
                ))
            
            if top_squats:
                df_squats = pd.DataFrame(top_squats)
                fig_bar.add_trace(go.Bar(
                    name='Squats',
                    x=df_squats['name'],
                    y=df_squats['count'],
                    marker_color='#ff7f0e'
                ))
            
            if top_pushups:
                df_pushups = pd.DataFrame(top_pushups)
                fig_bar.add_trace(go.Bar(
                    name='Push-ups',
                    x=df_pushups['name'],
                    y=df_pushups['count'],
                    marker_color='#2ca02c'
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
                line=dict(color='#1f77b4', width=2)
            ))
            fig_line.add_trace(go.Scatter(
                x=df_time['hour'],
                y=df_time['squats'],
                mode='lines+markers',
                name='Squats',
                line=dict(color='#ff7f0e', width=2)
            ))
            fig_line.add_trace(go.Scatter(
                x=df_time['hour'],
                y=df_time['pushups'],
                mode='lines+markers',
                name='Push-ups',
                line=dict(color='#2ca02c', width=2)
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
            fig_points.update_traces(line_color='#d62728', line_width=2)
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
            fig_sessions.update_traces(marker_color='#9467bd')
            st.plotly_chart(fig_sessions, use_container_width=True, key="dashboard_sessions_chart")
        
        with col4:
            fig_participants = px.line(
                df_time,
                x='hour',
                y='participants',
                title="Active Participants Over Time (Hourly)",
                markers=True
            )
            fig_participants.update_traces(line_color='#8c564b', line_width=2)
            st.plotly_chart(fig_participants, use_container_width=True, key="dashboard_participants_chart")
    else:
        st.info("No time-based statistics available yet. Start training to see trends!")
    
    # User stats if logged in
    if st.session_state.user_id:
        st.markdown("---")
        st.markdown("### 👤 Your Personal Statistics")
        user_stats = db.get_user_stats(st.session_state.user_id)
        
        if user_stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                sessions = user_stats.get('total_sessions') or 0
                st.metric("Your Sessions", sessions)
            with col2:
                jumps = user_stats.get('total_jumps') or 0
                st.metric("Your Total Jumps", jumps)
            with col3:
                points = user_stats.get('total_points') or 0
                st.metric("Your Total Points", points)
            with col4:
                avg_points = user_stats.get('avg_points_per_session') or 0
                avg_points = float(avg_points) if avg_points is not None else 0.0
                st.metric("Avg Points/Session", f"{avg_points:.1f}")
        else:
            st.info("Complete a training session to see your statistics!")

def get_trainbot_response(user_message):
    """Generate TrainBot response based on user input"""
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
    # Back button at the top
    if st.button("← Back to Training"):
        st.session_state.page = 'main'
        st.rerun()
    
    st.title("🤖 TrainBot - Your AI Fitness Assistant")
    st.markdown("Chat with TrainBot to get fitness tips, exercise information, and motivation!")
    
    # Initialize chat history with welcome message
    if len(st.session_state.chat_history) == 0:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "Hello! I'm TrainBot, your AI fitness assistant! 👋 How can I help you today?"
        })
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask TrainBot anything about fitness, exercises, or training..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        response = get_trainbot_response(prompt)
        
        # Add bot response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Display bot response
        with st.chat_message("assistant"):
            st.markdown(response)
        
        # Rerun to update the chat
        st.rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# Main app logic
if st.session_state.user_id is None:
    user_registration()
else:
    # Determine current page
    if 'page' not in st.session_state:
        st.session_state.page = 'main'
    
    if st.session_state.page == 'leaderboard':
        leaderboard_page()
    elif st.session_state.page == 'dashboard':
        dashboard_page()
    elif st.session_state.page == 'trainbot':
        trainbot_page()
    elif st.session_state.page == 'recommendations':
        recommendations_page()
    else:
        main_app()

