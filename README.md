# AI Athlete Trainer - Web Application

A comprehensive web application for tracking and analyzing jump training sessions with real-time posture analysis and leaderboard features.

## Features

- 👤 **User Registration**: Name and age-based user profiles
- 📹 **Video Upload**: Upload and analyze pre-recorded videos
- 📷 **Camera Support**: Real-time jump detection using webcam
- 🏃 **Jump Detection**: Automatic jump counting with MediaPipe pose estimation
- ⚠️ **Posture Analysis**: Detects bad moves (knee valgus, forward lean, knees over toes)
- 📊 **Points System**: 10 points per jump, -2 points per bad move
- 💾 **SQLite Database**: Stores all training data, sessions, and statistics
- 🏆 **Leaderboard**: Top performers ranked by points and jumps
- 📈 **Dashboard**: Comprehensive statistics and charts
- 📱 **Responsive UI**: Built with Streamlit for easy access

## Installation

### 1. Prerequisites

- Python 3.8 or higher
- SQLite3 (included with Python)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

Run the setup script to create the SQLite database:

```bash
python setup_database.py
```

This will create `athlete_trainer.db` in the source directory.

### 4. Optional: Configure Custom Database Path

If you want to use a custom database location, create a `.streamlit/secrets.toml` file:

```toml
[sqlite]
database_path = "path/to/your/athlete_trainer.db"
```

If not specified, the database will be created automatically in the source directory.

### 5. Run the Application

```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`

## Usage

1. **Registration**: Enter your name and age when first opening the app
2. **Start Training**: 
   - Choose to upload a video file or use your camera
   - Click "Start Processing" or "Start Camera"
3. **Training Session**:
   - The app will calibrate for 30 frames
   - Start jumping! The app tracks jumps, points, and bad moves
   - View real-time warnings for posture issues
4. **View Results**:
   - Check the leaderboard to see top performers
   - View dashboard for overall statistics
   - Your session data is automatically saved

## Scoring System

- **Base Points**: 10 points per successful jump
- **Penalties**: -2 points per bad move detected
- **Bad Moves Detected**:
  - Left/Right Knee Valgus (knees caving in)
  - Excessive Forward Lean
  - Knees Over Toes

## Database Schema

- **users**: User profiles (name, age)
- **sessions**: Training sessions with totals
- **jumps**: Individual jump records with posture analysis
- **squats**: Individual squat records with posture analysis
- **pushups**: Individual push-up records with posture analysis

## Project Structure

```
.
├── app.py                 # Main Streamlit application
├── database.py            # Database connection and operations
├── jump_detector.py       # Jump detection and posture analysis
├── database_setup_sqlite.sql  # SQLite database schema
├── setup_database.py      # Database setup script
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Technologies Used

- **Streamlit**: Web application framework
- **MediaPipe**: Pose estimation and tracking
- **OpenCV**: Video processing
- **SQLite**: Database storage (file-based, no server required)
- **Plotly**: Interactive charts and visualizations
- **Pandas**: Data manipulation

## Notes

- The app processes videos in real-time, so large files may take time
- Camera functionality requires browser permissions
- For best results, ensure good lighting and clear view of the person
- The calibration phase helps adapt to different body sizes and positions

## Troubleshooting

**Database Connection Issues**:
- Run `python setup_database.py` to create the database
- Check file permissions in the directory
- Ensure the database file `athlete_trainer.db` exists
- If using custom path, verify it in `.streamlit/secrets.toml`

**Video Processing Issues**:
- Supported formats: MP4, AVI, MOV, MKV
- Ensure video contains clear view of person jumping
- Check file size and format compatibility

**Camera Not Working**:
- Grant browser permissions for camera access
- Ensure camera is not being used by another application
- Try refreshing the page

## Future Enhancements

- User authentication and login system
- Exercise variety (push-ups, squats, etc.)
- Video playback with annotations
- Export session reports
- Mobile app version
- Social features and challenges

## License

This project is open source and available for educational purposes.









