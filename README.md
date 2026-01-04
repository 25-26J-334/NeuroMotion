# Athlete Performance and Training AI-Based System

- **Project ID:** 25-26J-334  
- **Team:** Manulakshan_IT22283962 | Mathumitha_IT21379338 | Sylvester_IT22311368 | Jude Jawakker_IT22330864
- **Git repository:** https://github.com/25-26J-334/NeuroMotion.git
- **Course:** IT4010 – Research Project (2025 July)  
- **Specialization:** Information Technology (IT)  
- **Research Group:** Software Systems & Technologies (SST)  
- **Institution:** Sri Lanka Institute of Information Technology (SLIIT)

---

## 1. Overview

The **Athlete Performance and Training AI-Based System** is a video-driven, AI-powered platform designed to monitor, analyze, and enhance athlete performance without relying on intrusive wearable devices. The system uses **computer vision**, **machine learning**, and **intelligent training recommendations** to deliver real-time, sport-specific insights to athletes, coaches, and sports institutions.

### 1.1 Motivation

Traditional athlete monitoring approaches have several limitations:

- Manual observation by coaches is **subjective** and **inconsistent**.
- Wearable sensors can be **intrusive**, **uncomfortable**, and **expensive**.
- Existing AI tools often lack **sport-specific context** and **real-time, actionable insights**.
- There is limited use of **predictive analytics** and **adaptive training** in many training environments.

This project aims to address these gaps by creating a **wearable-free, video-based AI system** that can:

- Analyze form and technique in real time.
- Predict performance trends and injury risks.
- Recommend adaptive, personalized training plans.
- Serve as a foundational framework for sports analytics research in Sri Lanka.

---

## 2. Problem Statement

Current athlete performance monitoring solutions suffer from one or more of the following issues:

1. **Subjectivity and inconsistency** in coach-driven assessments.
2. **High dependency on wearables and sensors**, which can be costly and impractical in many training environments.
3. **Lack of sport-specific AI models**, resulting in generic or non-actionable insights.
4. **Limited predictive capability**, focusing mostly on descriptive statistics rather than proactive injury prevention or performance optimization.
5. **Fragmented systems**, where data acquisition, analysis, and visualization are not integrated into a cohesive workflow.

### Research Gap

There is a need for an **integrated, sport-specific, video-driven AI system** that:

- Uses **computer vision** for real-time pose and technique analysis.
- Uses **machine learning** to forecast performance and identify injury risks.
- Provides **adaptive, data-driven training recommendations**.
- Integrates all components into a **single, coherent platform** accessible via a modern web interface.

---

## 3. Project Objectives

### 3.1 Main Objective

To **design and develop an AI-powered system** that enhances athlete performance by collecting, analyzing, and interpreting multimodal training data (primarily video), enabling:

- Predictive insights  
- Injury prevention  
- Technique correction  
- Personalized training recommendations  

### 3.2 Sub Objectives

1. **Data Pipeline & Integration System**  
   - Design and implement a robust data acquisition and preprocessing pipeline for sports video and related data.

2. **Computer Vision for Form & Technique Analysis**  
   - Implement pose estimation and biomechanical analysis for real-time detection of technique errors.

3. **AI Models for Performance Prediction**  
   - Develop machine learning models to predict athlete performance trends and injury risk.

4. **Personalized Training & Visualization System**  
   - Build a user-friendly dashboard and intelligent recommender that delivers adaptive training plans and feedback.

---

## 4. System Architecture

### 4.1 High-Level Architecture Diagram

```text
                         ┌────────────────────────────────────┐
                         │        DATA SOURCES                 │
                         │-------------------------------------│
                         │ -  Live training camera feeds        │
                         │ -  Uploaded training videos          │
                         │ -  Public sports datasets            │
                         │   (SportsPose, AthletePose3D, etc.)│
                         └───────────────┬─────────────────────┘
                                         │
                                         ▼
                 ┌─────────────────────────────────────────────┐
                 │   COMPONENT 1: DATA PIPELINE & INTEGRATION  │
                 │   (Preprocessing, normalization, metadata)  │
                 └───────────────┬─────────────────────────────┘
                                 │
                                 ▼
                ┌──────────────────────────────────────────────┐
                │ COMPONENT 2: COMPUTER VISION & POSE ANALYSIS │
                │ (Pose estimation, joint angles, form errors) │
                └────────────────┬─────────────────────────────┘
                                 │
                                 ▼
          ┌─────────────────────────────────────────────────────────┐
          │   COMPONENT 3: PERFORMANCE PREDICTION MODELS           │
          │ (Trend forecasting, injury risk, anomaly detection)    │
          └─────────────────────┬──────────────────────────────────┘
                                │
                                ▼
          ┌─────────────────────────────────────────────────────────┐
          │ COMPONENT 4: DASHBOARD & TRAINING RECOMMENDER          │
          │ (Visualization, RL-based adaptive plans, chatbot, etc.)│
          └─────────────────────┬──────────────────────────────────┘
                                │
                                ▼
                    ┌────────────────────────────────┐
                    │        END USERS                │
                    │---------------------------------│
                    │ -  Athletes                      │
                    │ -  Coaches                       │
                    │ -  Sports institutions           │
                    └────────────────────────────────┘
```

---

### 4.2 Data Flow

1. **Raw video data is ingested from cameras, uploaded files, or public datasets.**
   
2. **The Data Pipeline component preprocesses videos:**
   - Standardizes formats & resolutions
   - Extracts frames
   - Aligns multi-camera angles
   - Annotates with metadata (player, context, session info)
     
3. **The Computer Vision component:**
   - Runs pose estimation (MediaPipe/OpenPose, etc.)
   - Extracts skeletal keypoints and calculates joint angles
   - Identifies deviations from optimal technique
     
4. **ML models:**
   - Use historical and current features to predict performance, fatigue, injury risk, and trends.

5. **The Dashboard & Recommender:**
   - Visualizes metrics
   - Shows real-time corrective feedback
   - Suggests personalized training plans (e.g., using RL)
   - Logs and tracks progress over time

---

## 5. Modules and Responsibilities

### 5.1 Component 1 – Data Pipeline & Integration System

**Member: Y. Manulakshan (IT22283962)**
   - Multi-source video acquisition (live feeds, uploads, datasets)
   - Video preprocessing and normalization (resolution, frame rate, noise removal)
   - Frame extraction and multi-view synchronization
   - Metadata annotation (athlete, session, context)
   - Data storage and API integration for downstream modules

### 5.2 Component 2 – Computer Vision for Form & Technique Analysis

**Member: G. Mathumitha (IT21379338)**
   - Pose estimation using MediaPipe / OpenPose
   - Keypoint extraction and joint angle computation
   - Technique error detection (e.g., incorrect posture, misaligned joints)
   - Real-time feedback generation (e.g., “Increase knee drive”, “Correct hip alignment”)
   - Integration of visual overlays and metrics for the dashboard

### 5.3 Component 3 – AI Models for Performance Prediction

**Member: L. M. Sylvester (IT22311368)**
   - Feature engineering from pose data and training logs
   - Regression models for performance forecasting
   - Classification models for injury/fatigue risk
   - Anomaly detection for unusual patterns
   - Model evaluation, tuning, and performance reporting

### 5.4 Component 4 – Personalized Training & Visualization System

**Member: G. Jude Jawakker (IT22330864)**
   - Web-based dashboard for performance visualization
   - Real-time feedback display and alerting
   - Adaptive training recommender (e.g., using Reinforcement Learning or decision trees)
   - Progress tracking and historical analytics
   - Chatbot integration for question–answer style interactions

---

## 6. Technology Stack

### 6.1 Backend Language

Python 3.8+ (as per README.md)
Web Framework
Streamlit (the app is run using streamlit run app.py)
Computer Vision / Pose Estimation
OpenCV (video capture + frame processing)
MediaPipe (pose estimation / posture tracking)
Data Processing / Analytics
NumPy (numerical operations)
Pandas (tabular manipulation, summaries)
Visualization
Plotly (interactive charts inside Streamlit)
Imaging Utilities
Pillow (image handling inside UI / processing pipeline)

6.2 Frontend
Framework
Streamlit UI (Python-based UI; no React/Next.js frontend in this repo)
Visualization
Plotly (charts/graphs rendered in the Streamlit app)
Styling
Streamlit default styling (no Tailwind/MUI setup found)

6.3 Databases and Storage
Relational DB
SQLite (local file-based DB; mentioned explicitly in README.md)
NoSQL DB
Not used (no MongoDB dependencies/config found)
File Storage
Local filesystem (videos/images/db stored locally in the project environment)

6.4 Tools & DevOps
Version Control
Git (repo contains .git/)
Containerization / CI/CD
Not present (no Dockerfile / docker-compose.yml found in this workspace)

7. Dependencies (Actual project dependencies)
7.1 Python (Backend + CV + Analytics) — from requirements.txt
streamlit (>=1.28.0)
opencv-python (>=4.8.0)
mediapipe (>=0.10.0)
numpy (>=1.24.0)
plotly (>=5.17.0)
pandas (>=2.0.0)
Pillow (>=10.0.0)

7.2 Frontend (Streamlit UI) — formatted like your example
streamlit (main UI framework)
plotly (charts/visualizations rendered in Streamlit)
Pillow (image handling/display utilities)
opencv-python (camera/video UI components)
mediapipe (pose visualization overlays in UI)
pandas (data display/tables in UI)
numpy (data prep for UI components)

8. Installation and Setup
8.1 Prerequisites
Git installed and configured
Python 3.8+ and pip
SQLite3 (included with Python; no separate DB server needed)

8.2 Backend Setup

# Clone repository
git clone https://github.com/<your-org>/<your-repo>.git
cd <your-repo>

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Initialize SQLite database
python setup_database.py

# Run the Streamlit app
streamlit run app.py

The app will open in your browser at http://localhost:8501

8.3 Frontend Setup
Not applicable
This project uses Streamlit for the UI; there is no separate frontend to build or serve.
The Streamlit app provides the complete web interface when you run streamlit run app.py.

8.4 Database Setup
SQLite is used; no external database server is required.
The database file (athlete_trainer.db) is created automatically by setup_database.py in the project directory.
Optional: Create .streamlit/secrets.toml to specify a custom database path:
[sqlite]
database_path = "path/to/your/athlete_trainer.db"

9. Repository Structure

root/
├── README.md                     # Main project documentation
├── requirements.txt              # Python/Streamlit dependencies
├── .gitignore
├── .streamlit/
│   ├── secrets.toml.example      # Optional DB path config
│   └── static/
│       └── athlete.png
│
├── app.py                        # Main Streamlit application (entry point)
├── database.py                   # Database connection and operations
├── setup_database.py             # Database initialization script
│
├── jump_detector.py             # Jump detection and posture analysis
├── squat_detector.py            # Squat detection (if implemented)
├── pushup_detector.py           # Push-up detection (if implemented)
│
├── recommendation_engine.py     # Recommendation logic
├── recommendations_ui.py        # UI components for recommendations
│
├── database_setup_sqlite.sql    # SQLite schema definition
├── database_migration_*.sql     # Migration scripts (if any)
│
├── create_sample_data.py        # Utility to populate sample data
├── create_secrets.py            # Helper for secrets setup
│
├── check_*.py                   # Various debugging/validation scripts
├── test_*.py                    # Test scripts
│
├── static/
│   ├── css/
│   │   └── athlete.png
│   └── videos/
│       └── input_jump_video.mp4
│
└── docs/ (not present in current repo)

10. Git Workflow and Collaboration (Updated)

10.1 Branching Strategy (Actual)
develop – Stable, production-ready code (your production branch)
master – Legacy/main reference branch
feature/background – Background-related features
feature/graph – Graph/chart functionality
feature/graph-color – Graph color/styling enhancements
feature/training_plans – Training plan features
feature/ui – UI improvements and components

10.2 Example Workflow (Updated for your project)

# Pull latest changes from production branch
git checkout develop
git pull origin develop

# Create a feature branch
git checkout -b feature/ui-dashboard

# Work on code, then stage and commit
git add .
git commit -m "feat(ui): redesign dashboard with new charts"

# Push branch
git push origin feature/ui-dashboard

# Open a Pull Request from this branch into 'develop'
# After review and approval, merge the PR

# Update local develop branch after merge
git checkout develop
git pull origin develop

10.3 Commit Message Convention (Recommended for your project)

feat: new feature
fix: bug fix
docs: documentation
refactor: code restructuring
test: adding tests

feat(cv): add mediapipe pose estimation for jump detection
feat(ui): redesign dashboard with interactive charts
feat(db): add squat and push-up tables to schema
fix(app): resolve camera initialization error
fix(detector): correct knee valgus detection threshold
docs(readme): update installation instructions
refactor(database): extract connection logic to separate module
test(jump): add unit tests for jump counter
feat(recommendations): implement personalized training plans

10.4 Viewing History for Evaluation

# Show graphical history of all branches
git log --oneline --graph --all --decorate

# Show commits per contributor
git shortlog -sn --all

# Show merge commits (indicates collaboration)
git log --merges --oneline

# Show branch activity
git branch -a

# Show recent commits on develop
git log --oneline -10 develop

# Show commits by specific author
git log --oneline --author="username"

# Show commits on a feature branch
git log --oneline feature/ui

11. Evaluation and Success Criteria (Updated for your project)
11.1 Functional Success
Real-time pose extraction and technique analysis using MediaPipe via webcam/video
Accurate detection of technique errors:
Knee valgus (knees caving in)
Excessive forward lean
Knees over toes
Meaningful performance tracking:
Jump counting with points system (10 points per jump, -2 per bad move)
Session summaries and leaderboard rankings
Working dashboard that visualizes:
Real-time jump counts and points
Posture warnings during exercise
Leaderboard and user statistics
Historical session data

11.2 Technical Success
Clean, modular code structure:
Separate modules: app.py, database.py, jump_detector.py, recommendation_engine.py
Clear separation of UI, data, and detection logic
Proper use of Git:
Feature branches: feature/ui, feature/graph, feature/training_plans, etc.
Production code in develop branch
Merge commits showing collaboration
Working build and run instructions:
Clear README.md with setup steps
requirements.txt with all dependencies
One-command startup: streamlit run app.py
Documented database schema:
SQLite schema in database_setup_sqlite.sql
Clear table structure for users, sessions, jumps, squats, pushups

11.3 User/Stakeholder Success
Athlete/coach feedback:
Clear real-time posture warnings during training
Understandable scoring system and leaderboard
Actionable recommendations from the recommendation engine
Demonstrable value:
Identifies posture issues not obvious to the naked eye
Tracks progress over multiple sessions
Provides competitive motivation through leaderboard
Offers personalized training recommendations

12. Data, Privacy, and Ethics (Updated for your project)
Data Sources
Public datasets: Use datasets like SportsPose, AthletePose3D, UCF101, PoseTrack, COCO Keypoints for initial development and benchmarking
Custom recordings: Obtain informed consent from participants before recording
Sample data: Your project includes input_jump_video.mp4 as reference/test footage
Privacy Measures
Anonymization: No names or IDs stored in jump/session data; consider face blurring in video processing
Secure storage: SQLite database stored locally with restricted access to the project team
Data retention: Clear policy for how long session videos and data are stored
Ethics and Disclaimers
Non-medical: Clearly state that posture analysis and recommendations are supportive insights, not medical diagnoses
Accuracy limits: Document the limitations of MediaPipe-based pose estimation
User consent: Include consent prompts when enabling camera/video recording

13. Future Work (Updated for your project)
Feature Extensions
Multi-sport support: Add specialized technique rules for squats, push-ups, and other exercises
Advanced biomechanics: Incorporate more parameters like force estimation, ground contact time, movement velocity
Enhanced recommendations: Improve the recommendation engine with machine learning-based personalization
Platform Integration
External platforms: Integrate with training apps, athlete management systems, or wearable devices
Cloud deployment: Deploy to cloud environment (AWS, Azure, GCP) for remote access and scalability
Mobile app: Develop a companion mobile application for on-the-go training
Technical Improvements
Real-time enhancements: Optimize for lower latency real-time processing
Multi-user support: Add proper authentication and multi-user profiles
Advanced analytics: Implement more sophisticated statistical analysis and trend detection

14. Contact and Contributors
Y. Manulakshan – Data Pipeline & Integration
G. Mathumitha – Computer Vision for Form & Technique
L. M. Sylvester – AI Models for Performance Prediction
G. Jude Jawakker – Personalized Training & Visualization

Prof. Samantha Rajapaksha – Sri Lanka Institute of Information Technology (SLIIT)

15. License
This project is developed as part of the SLIIT IT4010 Research Project and is primarily intended
for academic and research purposes. Licensing and reuse outside the academic context are
subject to institutional policies.


