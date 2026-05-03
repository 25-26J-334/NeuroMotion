"""
Step-up detection module with posture analysis and phase tracking.
"""
import cv2
import mediapipe as mp
import numpy as np
from math import degrees
from typing import Dict, List, Optional

class StepupDetector:
    def __init__(self, calibration_frames=50):
        """Initialize MediaPipe pose detection for step-ups"""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Configuration
        self.CALIBRATION_FRAMES = calibration_frames
        self.SMOOTHING = 0.7
        self.HIP_RISE_THRESHOLD = 0.15 # 15% of height
        
        self.reset()
    
    def reset(self):
        """Reset detector state for new session"""
        self.stepup_count = 0
        self.calibrating = True
        self.calibration_samples = []
        self.baseline_hip_y = None # Standing hip height
        self.baseline_knee_y = None # Standing knee height
        self.up_threshold = None # Hip Y value required to count as "on top"
        
        self.smoothed_hip_y = None
        self.smoothed_knee_y = None
        
        self.phase = "standing" # standing -> stepping_up -> on_top -> stepping_down -> standing
        
        self.posture_warnings = []
        self.danger_detected = False
        self.current_rep_warnings = []
        self.current_rep_bad_moves = 0
        
        self.rep_history = []
        self.rep_start_frame = None
    
    def start_recalibration(self):
        """Start recalibration process"""
        self.calibrating = True
        self.calibration_samples = []
        self.baseline_hip_y = None
        self.baseline_knee_y = None
        self.up_threshold = None
    
    def calculate_angle(self, a, b, c):
        """Calculate angle between three points"""
        a, b, c = np.array(a), np.array(b), np.array(c)
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(degrees(radians))
        return min(angle, 360 - angle)
    
    def analyze_posture(self, landmarks: Dict):
        """Analyze posture and detect bad moves"""
        self.posture_warnings = []
        self.danger_detected = False
        
        # Check for knee alignment on top
        if self.phase == "on_top":
            hip_l = landmarks['hip_l']
            knee_l = landmarks['knee_l']
            ankle_l = landmarks['ankle_l']
            hip_r = landmarks['hip_r']
            knee_r = landmarks['knee_r']
            ankle_r = landmarks['ankle_r']
            
            angle_l = self.calculate_angle(hip_l, knee_l, ankle_l)
            angle_r = self.calculate_angle(hip_r, knee_r, ankle_r)
            
            # If knees aren't straight enough on top
            if angle_l < 160 or angle_r < 160:
                self.posture_warnings.append("STRAIGHTEN KNEES ON TOP")
                if "STRAIGHTEN KNEES ON TOP" not in self.current_rep_warnings:
                    self.current_rep_warnings.append("STRAIGHTEN KNEES ON TOP")
                    self.current_rep_bad_moves += 1

    def process_frame(self, frame, frame_index=0):
        """Process a single frame and return annotated frame and status"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb_frame)
        
        status = {
            'stepup_count': self.stepup_count,
            'status_text': 'Waiting for pose...',
            'calibrating': self.calibrating,
            'danger_detected': False,
            'warnings': [],
            'points': 0,
            'bad_moves': 0
        }
        
        if result.pose_landmarks:
            lm = result.pose_landmarks.landmark
            
            # Extract key vertical positions (average of both sides)
            hip_y = (lm[self.mp_pose.PoseLandmark.LEFT_HIP].y + lm[self.mp_pose.PoseLandmark.RIGHT_HIP].y) / 2
            knee_y = (lm[self.mp_pose.PoseLandmark.LEFT_KNEE].y + lm[self.mp_pose.PoseLandmark.RIGHT_KNEE].y) / 2
            shoulder_y = (lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y + lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y) / 2
            ankle_y = (lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].y + lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE].y) / 2
            
            # Smooth tracking
            if self.smoothed_hip_y is None:
                self.smoothed_hip_y = hip_y
                self.smoothed_knee_y = knee_y
            else:
                self.smoothed_hip_y = (self.SMOOTHING * self.smoothed_hip_y) + ((1 - self.SMOOTHING) * hip_y)
                self.smoothed_knee_y = (self.SMOOTHING * self.smoothed_knee_y) + ((1 - self.SMOOTHING) * knee_y)
            
            if self.calibrating:
                self.calibration_samples.append((self.smoothed_hip_y, self.smoothed_knee_y, shoulder_y, ankle_y))
                status['status_text'] = f"Calibrating... {len(self.calibration_samples)}/{self.CALIBRATION_FRAMES}"
                
                if len(self.calibration_samples) >= self.CALIBRATION_FRAMES:
                    hips = [s[0] for s in self.calibration_samples]
                    knees = [s[1] for s in self.calibration_samples]
                    shoulders = [s[2] for s in self.calibration_samples]
                    ankles = [s[3] for s in self.calibration_samples]
                    
                    self.baseline_hip_y = sum(hips) / len(hips)
                    self.baseline_knee_y = sum(knees) / len(knees)
                    avg_shoulder = sum(shoulders) / len(shoulders)
                    avg_ankle = sum(ankles) / len(ankles)
                    
                    body_height = avg_ankle - avg_shoulder
                    
                    # Up threshold (hips must go above this line)
                    self.up_threshold = self.baseline_hip_y - (body_height * self.HIP_RISE_THRESHOLD)
                    
                    self.calibrating = False
                    status['status_text'] = "Ready - Start Step-ups!"
            
            elif not self.calibrating:
                # State Machine Logic
                if self.phase == "standing":
                    if self.smoothed_hip_y < (self.baseline_hip_y - 0.05):
                        self.phase = "stepping_up"
                        self.rep_start_frame = frame_index
                        self.current_rep_warnings = []
                        self.current_rep_bad_moves = 0
                        status['status_text'] = "Stepping Up..."
                    else:
                        status['status_text'] = "Standing"
                        
                elif self.phase == "stepping_up":
                    if self.smoothed_hip_y < self.up_threshold:
                        self.phase = "on_top"
                        status['status_text'] = "On Top!"
                    elif self.smoothed_hip_y > (self.baseline_hip_y - 0.02):
                        self.phase = "standing"
                        
                elif self.phase == "on_top":
                    if self.smoothed_hip_y > (self.up_threshold + 0.05):
                        self.phase = "stepping_down"
                        status['status_text'] = "Stepping Down..."
                        
                elif self.phase == "stepping_down":
                    if self.smoothed_hip_y > (self.baseline_hip_y - 0.05):
                        # Completed rep
                        self.stepup_count += 1
                        points = 10 - (self.current_rep_bad_moves * 2)
                        points = max(0, points)
                        
                        self.rep_history.append({
                            'rep_number': self.stepup_count,
                            'start_frame': self.rep_start_frame,
                            'end_frame': frame_index,
                            'points': points,
                            'bad_moves': self.current_rep_bad_moves,
                            'warnings': self.current_rep_warnings.copy()
                        })
                        
                        self.phase = "standing"
                        status['status_text'] = f"Rep Complete! ({self.stepup_count})"
                        status['points'] = points
                        status['bad_moves'] = self.current_rep_bad_moves

            # Posture analysis
            landmarks_dict = {
                'shoulder_l': [lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].x, lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y],
                'shoulder_r': [lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].x, lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y],
                'hip_l': [lm[self.mp_pose.PoseLandmark.LEFT_HIP].x, lm[self.mp_pose.PoseLandmark.LEFT_HIP].y],
                'hip_r': [lm[self.mp_pose.PoseLandmark.RIGHT_HIP].x, lm[self.mp_pose.PoseLandmark.RIGHT_HIP].y],
                'knee_l': [lm[self.mp_pose.PoseLandmark.LEFT_KNEE].x, lm[self.mp_pose.PoseLandmark.LEFT_KNEE].y],
                'knee_r': [lm[self.mp_pose.PoseLandmark.RIGHT_KNEE].x, lm[self.mp_pose.PoseLandmark.RIGHT_KNEE].y],
                'ankle_l': [lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].x, lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].y],
                'ankle_r': [lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE].x, lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE].y]
            }
            
            if not self.calibrating:
                self.analyze_posture(landmarks_dict)
                status['warnings'] = self.posture_warnings.copy()
                status['danger_detected'] = self.danger_detected

            status['stepup_count'] = self.stepup_count
            
            # Draw skeleton
            landmark_color = (0, 0, 255) if status['danger_detected'] else (0, 255, 0)
            connection_color = (0, 0, 255) if status['danger_detected'] else (255, 255, 255)
            
            self.mp_draw.draw_landmarks(
                frame,
                result.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_draw.DrawingSpec(color=landmark_color, thickness=2, circle_radius=2),
                self.mp_draw.DrawingSpec(color=connection_color, thickness=2)
            )
            
        return frame, status
