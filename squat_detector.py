"""
Squat detection module with posture analysis
Separate from jump_detector.py to keep functionality isolated
"""
import cv2
import mediapipe as mp
import numpy as np
from math import degrees, atan2
from typing import Dict, List, Tuple

class SquatDetector:
    def __init__(self, calibration_frames=100):
        """Initialize MediaPipe pose detection for squats"""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Configuration
        self.CALIBRATION_FRAMES = calibration_frames
        self.SMOOTHING = 0.7
        self.SQUAT_DEPTH_THRESHOLD = 0.15  # Hip must go down by this much (15% of frame height)
        self.KNEE_VALGUS_THRESHOLD = 15
        self.FORWARD_LEAN_THRESHOLD = 30
        self.KNEE_OVER_TOE_THRESHOLD = 0.1
        self.BACK_ARCH_THRESHOLD = 20  # Excessive back arching
        
        # State variables
        self.reset()
    
    def reset(self):
        """Reset detector state for new session"""
        self.squat_count = 0
        self.squatting = False
        self.calibrating = True
        self.calibration_samples = []
        self.baseline_hip_y = None  # Standing hip position
        self.squat_threshold = None  # Depth threshold for squat
        self.smoothed_hip_y = None
        self.posture_warnings = []
        self.danger_detected = False
        self.current_squat_warnings = []
        self.current_squat_bad_moves = 0
        self.was_down = False  # Track if we were in down position
    
    def start_recalibration(self):
        """Start recalibration process"""
        self.calibrating = True
        self.calibration_samples = []
        self.baseline_hip_y = None
        self.squat_threshold = None
        self.smoothed_hip_y = None
    
    def calculate_angle(self, a, b, c):
        """Calculate angle between three points"""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(degrees(radians))
        angle = min(angle, 360 - angle)
        return angle
    
    def check_knee_valgus(self, landmarks: Dict, side: str) -> bool:
        """Check for knee valgus (knees caving in)"""
        hip = landmarks[f'hip_{side}']
        knee = landmarks[f'knee_{side}']
        ankle = landmarks[f'ankle_{side}']
        
        angle = self.calculate_angle(hip, knee, ankle)
        valgus_angle = abs(angle - 180)
        
        if valgus_angle > self.KNEE_VALGUS_THRESHOLD:
            self.posture_warnings.append(f"{side.upper()} KNEE VALGUS")
            self.current_squat_warnings.append(f"{side.upper()} KNEE VALGUS")
            return True
        return False
    
    def check_forward_lean(self, landmarks: Dict) -> bool:
        """Check for excessive forward lean"""
        shoulder = [
            (landmarks['shoulder_l'][0] + landmarks['shoulder_r'][0]) / 2,
            (landmarks['shoulder_l'][1] + landmarks['shoulder_r'][1]) / 2
        ]
        hip = [
            (landmarks['hip_l'][0] + landmarks['hip_r'][0]) / 2,
            (landmarks['hip_l'][1] + landmarks['hip_r'][1]) / 2
        ]
        hip_above = [hip[0], hip[1] - 0.1]
        
        angle = self.calculate_angle(shoulder, hip, hip_above)
        if angle < (180 - self.FORWARD_LEAN_THRESHOLD):
            self.posture_warnings.append("EXCESSIVE FORWARD LEAN")
            self.current_squat_warnings.append("EXCESSIVE FORWARD LEAN")
            return True
        return False
    
    def check_knees_over_toes(self, landmarks: Dict, side: str) -> bool:
        """Check if knees go too far over toes"""
        knee = landmarks[f'knee_{side}']
        ankle = landmarks[f'ankle_{side}']
        toe = [ankle[0], ankle[1] - 0.05]
        
        if (knee[0] - toe[0]) > self.KNEE_OVER_TOE_THRESHOLD:
            self.posture_warnings.append(f"{side.upper()} KNEE OVER TOES")
            self.current_squat_warnings.append(f"{side.upper()} KNEE OVER TOES")
            return True
        return False
    
    def check_back_arch(self, landmarks: Dict) -> bool:
        """Check for excessive back arching (hyperextension)"""
        shoulder = [
            (landmarks['shoulder_l'][0] + landmarks['shoulder_r'][0]) / 2,
            (landmarks['shoulder_l'][1] + landmarks['shoulder_r'][1]) / 2
        ]
        hip = [
            (landmarks['hip_l'][0] + landmarks['hip_r'][0]) / 2,
            (landmarks['hip_l'][1] + landmarks['hip_r'][1]) / 2
        ]
        hip_below = [hip[0], hip[1] + 0.1]
        
        angle = self.calculate_angle(shoulder, hip, hip_below)
        if angle < (180 - self.BACK_ARCH_THRESHOLD):
            self.posture_warnings.append("EXCESSIVE BACK ARCH")
            self.current_squat_warnings.append("EXCESSIVE BACK ARCH")
            return True
        return False
    
    def analyze_posture(self, landmarks: Dict):
        """Analyze posture and detect bad moves during squats"""
        self.posture_warnings = []
        self.current_squat_warnings = []
        self.current_squat_bad_moves = 0
        
        left_valgus = self.check_knee_valgus(landmarks, 'l')
        right_valgus = self.check_knee_valgus(landmarks, 'r')
        forward_lean = self.check_forward_lean(landmarks)
        left_knee_over = self.check_knees_over_toes(landmarks, 'l')
        right_knee_over = self.check_knees_over_toes(landmarks, 'r')
        back_arch = self.check_back_arch(landmarks)
        
        self.danger_detected = (left_valgus or right_valgus or forward_lean or 
                                left_knee_over or right_knee_over or back_arch)
        
        # Count bad moves (each warning type counts as 1)
        self.current_squat_bad_moves = len(set(self.current_squat_warnings))
    
    def process_frame(self, frame) -> Tuple[np.ndarray, Dict]:
        """
        Process a single frame and return annotated frame and status
        
        Returns:
            frame: Annotated frame with pose overlay
            status: Dictionary with squat_count, status_text, warnings, etc.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)
        
        status = {
            'person_detected': False,
            'status_text': "No Person",
            'squat_count': self.squat_count,
            'calibrating': self.calibrating,
            'warnings': [],
            'danger_detected': False,
            'points': 0,
            'bad_moves': 0
        }
        
        if result.pose_landmarks:
            status['person_detected'] = True
            lm = result.pose_landmarks.landmark
            
            # Calculate hip position (key for squat detection)
            left_hip = lm[self.mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = lm[self.mp_pose.PoseLandmark.RIGHT_HIP]
            hip_y = (left_hip.y + right_hip.y) / 2.0
            
            # Smooth hip position
            if self.smoothed_hip_y is None:
                self.smoothed_hip_y = hip_y
            else:
                self.smoothed_hip_y = (self.SMOOTHING * self.smoothed_hip_y + 
                                      (1 - self.SMOOTHING) * hip_y)
            
            # Calibration phase
            if self.calibrating:
                self.calibration_samples.append(self.smoothed_hip_y)
                status['status_text'] = f"Calibrating... {len(self.calibration_samples)}/{self.CALIBRATION_FRAMES}"
                
                if len(self.calibration_samples) >= self.CALIBRATION_FRAMES:
                    # Baseline is the hip position when standing
                    self.baseline_hip_y = sum(self.calibration_samples) / len(self.calibration_samples)
                    # Squat threshold: hip must go down by SQUAT_DEPTH_THRESHOLD
                    self.squat_threshold = self.baseline_hip_y + self.SQUAT_DEPTH_THRESHOLD
                    self.calibrating = False
                    status['status_text'] = "Ready - Start Squatting!"
            
            # Squat detection (only after calibration)
            elif not self.calibrating:
                # Check if hip goes down (squatting down)
                if not self.squatting and self.smoothed_hip_y >= self.squat_threshold:
                    self.squatting = True
                    self.was_down = True
                    status['status_text'] = "Squatting Down ↓"
                    self.current_squat_warnings = []
                    self.current_squat_bad_moves = 0
                
                # Check if hip returns to baseline (standing up)
                elif self.squatting and self.smoothed_hip_y < self.baseline_hip_y:
                    # Only count as completed squat if we went down first
                    if self.was_down:
                        self.squatting = False
                        self.was_down = False
                        self.squat_count += 1
                        
                        # Calculate points: 10 points per squat, -2 per bad move
                        points = 10 - (self.current_squat_bad_moves * 2)
                        points = max(0, points)  # No negative points
                        
                        status['squat_count'] = self.squat_count
                        status['status_text'] = f"Standing Up ✓ ({self.squat_count} squats)"
                        status['warnings'] = self.current_squat_warnings.copy()
                        status['danger_detected'] = self.danger_detected
                        status['points'] = points
                        status['bad_moves'] = self.current_squat_bad_moves
                    else:
                        status['status_text'] = f"Standing ({self.squat_count} squats)"
                else:
                    if self.squatting:
                        status['status_text'] = f"Squatting Down ({self.squat_count} squats)"
                    else:
                        status['status_text'] = f"Standing ({self.squat_count} squats)"
            
            # Get landmarks for posture analysis
            landmarks_dict = {
                'nose': [lm[self.mp_pose.PoseLandmark.NOSE].x, lm[self.mp_pose.PoseLandmark.NOSE].y],
                'shoulder_l': [lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].x, lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y],
                'shoulder_r': [lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].x, lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y],
                'hip_l': [lm[self.mp_pose.PoseLandmark.LEFT_HIP].x, lm[self.mp_pose.PoseLandmark.LEFT_HIP].y],
                'hip_r': [lm[self.mp_pose.PoseLandmark.RIGHT_HIP].x, lm[self.mp_pose.PoseLandmark.RIGHT_HIP].y],
                'knee_l': [lm[self.mp_pose.PoseLandmark.LEFT_KNEE].x, lm[self.mp_pose.PoseLandmark.LEFT_KNEE].y],
                'knee_r': [lm[self.mp_pose.PoseLandmark.RIGHT_KNEE].x, lm[self.mp_pose.PoseLandmark.RIGHT_KNEE].y],
                'ankle_l': [lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].x, lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].y],
                'ankle_r': [lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE].x, lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE].y],
                'heel_l': [lm[self.mp_pose.PoseLandmark.LEFT_HEEL].x, lm[self.mp_pose.PoseLandmark.LEFT_HEEL].y],
                'heel_r': [lm[self.mp_pose.PoseLandmark.RIGHT_HEEL].x, lm[self.mp_pose.PoseLandmark.RIGHT_HEEL].y]
            }
            
            # Analyze posture (only when squatting)
            if self.squatting:
                self.analyze_posture(landmarks_dict)
                status['warnings'] = self.posture_warnings.copy()
                status['danger_detected'] = self.danger_detected
            
            # Draw skeleton with color coding
            landmark_color = (0, 0, 255) if status['danger_detected'] else (0, 255, 0)
            connection_color = (0, 0, 255) if status['danger_detected'] else (255, 255, 255)
            
            landmark_drawing_spec = self.mp_draw.DrawingSpec(
                color=landmark_color,
                thickness=2,
                circle_radius=2
            )
            connection_drawing_spec = self.mp_draw.DrawingSpec(
                color=connection_color,
                thickness=2
            )
            
            self.mp_draw.draw_landmarks(
                frame,
                result.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=landmark_drawing_spec,
                connection_drawing_spec=connection_drawing_spec
            )
        
        # Draw calibration lines (only after calibration is complete)
        if not self.calibrating and self.baseline_hip_y is not None and self.squat_threshold is not None:
            h, w = frame.shape[:2]
            
            # Draw baseline (green) - standing position
            base_px = int(self.baseline_hip_y * h)
            cv2.line(frame, (0, base_px), (w, base_px), (0, 255, 0), 2)
            
            # Draw squat threshold line (yellow) - depth threshold + 10 pixels above
            # The threshold already includes the 10 pixel offset, so draw it directly
            threshold_px = int(self.squat_threshold * h)
            cv2.line(frame, (0, threshold_px), (w, threshold_px), (0, 255, 255), 3)
            
            # Draw current hip position line (blue)
            if self.smoothed_hip_y is not None:
                hip_px = int(self.smoothed_hip_y * h)
                cv2.line(frame, (0, hip_px), (w, hip_px), (255, 0, 0), 2)
        
        return frame, status

