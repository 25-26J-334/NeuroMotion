"""
Burpee detection module with posture analysis and phase tracking.
"""
import cv2
import mediapipe as mp
import numpy as np
from math import degrees
from typing import Dict

class BurpeeDetector:
    def __init__(self, calibration_frames=50, jump_height="medium"):
        """Initialize MediaPipe pose detection for burpees"""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Configuration
        self.CALIBRATION_FRAMES = calibration_frames
        self.SMOOTHING = 0.7
        self.BACK_ARCH_THRESHOLD = 20
        self.MIN_PLANK_EXTENSION = 0.5 # Minimum distance between shoulder and ankle relative to height
        
        # Height thresholds will be set during calibration
        self.jump_thresholds = {
            "low": 0.05,     # 5% of height
            "medium": 0.10,  # 10% of height
            "high": 0.15     # 15% of height
        }
        self.jump_threshold_pct = self.jump_thresholds.get(jump_height, 0.10)
        
        self.reset()
    
    def reset(self):
        """Reset detector state for new session"""
        self.burpee_count = 0
        self.calibrating = True
        self.calibration_samples = []
        self.baseline_y = None # Standing shoulder height
        self.baseline_ankle_y = None # Standing ankle height
        self.jump_threshold = None # Y value required to count a jump
        self.plank_threshold = None # Y value required to be in plank
        
        self.smoothed_shoulder_y = None
        self.smoothed_ankle_y = None
        
        self.phase = "standing" # standing -> down -> plank -> up -> jumping -> standing
        
        self.posture_warnings = []
        self.danger_detected = False
        self.current_burpee_warnings = []
        self.current_burpee_bad_moves = 0
        
        self.rep_history = []
        self.rep_start_frame = None
    
    def start_recalibration(self):
        """Start recalibration process"""
        self.calibrating = True
        self.calibration_samples = []
        self.baseline_y = None
        self.baseline_ankle_y = None
        self.jump_threshold = None
        self.plank_threshold = None
    
    def calculate_angle(self, a, b, c):
        """Calculate angle between three points"""
        a, b, c = np.array(a), np.array(b), np.array(c)
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(degrees(radians))
        return min(angle, 360 - angle)
    
    def check_back_arch(self, landmarks: Dict) -> bool:
        """Check for excessive back arching during plank"""
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
            if "EXCESSIVE BACK ARCH" not in self.current_burpee_warnings:
                self.current_burpee_warnings.append("EXCESSIVE BACK ARCH")
                self.current_burpee_bad_moves += 1
            return True
        return False
        
    def check_plank_extension(self, landmarks: Dict) -> bool:
        """Check if legs are extended far enough back in plank"""
        shoulder = [
            (landmarks['shoulder_l'][0] + landmarks['shoulder_r'][0]) / 2,
            (landmarks['shoulder_l'][1] + landmarks['shoulder_r'][1]) / 2
        ]
        ankle = [
            (landmarks['ankle_l'][0] + landmarks['ankle_r'][0]) / 2,
            (landmarks['ankle_l'][1] + landmarks['ankle_r'][1]) / 2
        ]
        
        # Calculate horizontal distance between shoulders and ankles
        extension = abs(ankle[0] - shoulder[0])
        
        if extension < self.MIN_PLANK_EXTENSION:
            self.posture_warnings.append("EXTEND LEGS FULLY")
            if "EXTEND LEGS FULLY" not in self.current_burpee_warnings:
                self.current_burpee_warnings.append("EXTEND LEGS FULLY")
                self.current_burpee_bad_moves += 1
            return True
        return False
    
    def analyze_posture(self, landmarks: Dict):
        """Analyze posture and detect bad moves depending on the phase"""
        self.posture_warnings = []
        
        if self.phase == "plank":
            back_arch = self.check_back_arch(landmarks)
            extension = self.check_plank_extension(landmarks)
            
            if back_arch:
                self.danger_detected = True
            else:
                self.danger_detected = False

    def process_frame(self, frame, frame_index=0):
        """Process a single frame and return annotated frame and status"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb_frame)
        
        status = {
            'burpee_count': self.burpee_count,
            'status_text': 'Waiting for pose...',
            'calibrating': self.calibrating,
            'danger_detected': False,
            'warnings': [],
            'points': 0,
            'bad_moves': 0
        }
        
        if result.pose_landmarks:
            lm = result.pose_landmarks.landmark
            
            # Extract key vertical positions
            shoulder_y = (lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y + lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y) / 2
            ankle_y = (lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].y + lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE].y) / 2
            
            # Smooth tracking
            if self.smoothed_shoulder_y is None:
                self.smoothed_shoulder_y = shoulder_y
                self.smoothed_ankle_y = ankle_y
            else:
                self.smoothed_shoulder_y = (self.SMOOTHING * self.smoothed_shoulder_y) + ((1 - self.SMOOTHING) * shoulder_y)
                self.smoothed_ankle_y = (self.SMOOTHING * self.smoothed_ankle_y) + ((1 - self.SMOOTHING) * ankle_y)
            
            if self.calibrating:
                # Need standing pose to calibrate
                self.calibration_samples.append((self.smoothed_shoulder_y, self.smoothed_ankle_y))
                status['status_text'] = f"Calibrating (Stand Straight)... {len(self.calibration_samples)}/{self.CALIBRATION_FRAMES}"
                
                if len(self.calibration_samples) >= self.CALIBRATION_FRAMES:
                    shoulders = [s[0] for s in self.calibration_samples]
                    ankles = [s[1] for s in self.calibration_samples]
                    
                    self.baseline_y = sum(shoulders) / len(shoulders)
                    self.baseline_ankle_y = sum(ankles) / len(ankles)
                    
                    body_height = self.baseline_ankle_y - self.baseline_y
                    
                    # Jump threshold (shoulders must go above this line) - remember Y is inverted
                    self.jump_threshold = self.baseline_y - (body_height * self.jump_threshold_pct)
                    
                    # Plank threshold (shoulders must go below this line)
                    self.plank_threshold = self.baseline_y + (body_height * 0.4)
                    
                    self.calibrating = False
                    status['status_text'] = "Ready - Start Burpees!"
            
            elif not self.calibrating:
                # State Machine Logic
                
                if self.phase == "standing":
                    # Check if going down to plank
                    if self.smoothed_shoulder_y > self.plank_threshold:
                        self.phase = "plank"
                        self.rep_start_frame = frame_index
                        self.current_burpee_warnings = []
                        self.current_burpee_bad_moves = 0
                        status['status_text'] = "Plank Phase"
                    else:
                        status['status_text'] = "Standing"
                        
                elif self.phase == "plank":
                    # Check if returning to standing
                    if self.smoothed_shoulder_y < (self.baseline_y + 0.1):
                        self.phase = "up"
                        status['status_text'] = "Coming Up"
                    else:
                        status['status_text'] = "Plank Phase"
                        
                elif self.phase == "up":
                    # Check for jump
                    if self.smoothed_shoulder_y < self.jump_threshold:
                        self.phase = "jumping"
                        status['status_text'] = "Jumping!"
                    # Or if they skipped the jump and just stood for a while, we might penalize or complete rep
                    elif self.smoothed_shoulder_y > self.plank_threshold:
                        # Went back down without jumping
                        self.phase = "plank"
                        
                elif self.phase == "jumping":
                    # When returning to standing from jump
                    if self.smoothed_shoulder_y > self.baseline_y - 0.05:
                        # Completed full rep
                        self.burpee_count += 1
                        points = 10 - (self.current_burpee_bad_moves * 2)
                        points = max(0, points)
                        
                        self.rep_history.append({
                            'rep_number': self.burpee_count,
                            'start_frame': self.rep_start_frame,
                            'end_frame': frame_index,
                            'points': points
                        })
                        
                        self.phase = "standing"
                        status['status_text'] = f"Rep Complete! ({self.burpee_count})"
                        status['points'] = points
                        status['bad_moves'] = self.current_burpee_bad_moves
                    else:
                        status['status_text'] = "Jumping!"

            # Posture analysis
            landmarks_dict = {
                'shoulder_l': [lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].x, lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y],
                'shoulder_r': [lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].x, lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y],
                'hip_l': [lm[self.mp_pose.PoseLandmark.LEFT_HIP].x, lm[self.mp_pose.PoseLandmark.LEFT_HIP].y],
                'hip_r': [lm[self.mp_pose.PoseLandmark.RIGHT_HIP].x, lm[self.mp_pose.PoseLandmark.RIGHT_HIP].y],
                'ankle_l': [lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].x, lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].y],
                'ankle_r': [lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE].x, lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE].y]
            }
            
            if not self.calibrating:
                self.analyze_posture(landmarks_dict)
                status['warnings'] = self.posture_warnings.copy()
                status['danger_detected'] = self.danger_detected

            status['burpee_count'] = self.burpee_count
            
            # Draw skeleton
            landmark_color = (0, 0, 255) if status['danger_detected'] else (0, 255, 0)
            connection_color = (0, 0, 255) if status['danger_detected'] else (255, 255, 255)
            
            landmark_drawing_spec = self.mp_draw.DrawingSpec(
                color=landmark_color, thickness=2, circle_radius=2
            )
            connection_drawing_spec = self.mp_draw.DrawingSpec(
                color=connection_color, thickness=2
            )
            
            self.mp_draw.draw_landmarks(
                frame,
                result.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=landmark_drawing_spec,
                connection_drawing_spec=connection_drawing_spec
            )
            
        # Draw calibration lines
        if not self.calibrating and self.baseline_y is not None:
            h, w = frame.shape[:2]
            
            # Baseline
            base_px = int(self.baseline_y * h)
            cv2.line(frame, (0, base_px), (w, base_px), (0, 255, 0), 2)
            
            # Jump threshold
            jump_px = int(self.jump_threshold * h)
            cv2.line(frame, (0, jump_px), (w, jump_px), (0, 255, 255), 2)
            
            # Plank threshold
            plank_px = int(self.plank_threshold * h)
            cv2.line(frame, (0, plank_px), (w, plank_px), (255, 165, 0), 2)
            
        return frame, status
