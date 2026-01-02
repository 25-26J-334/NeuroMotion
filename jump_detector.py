"""
Jump detection module with posture analysis
Extracted from the original jump.py for use in Streamlit
"""
import cv2
import mediapipe as mp
import numpy as np
from math import degrees, atan2
from typing import Dict, List, Tuple

class JumpDetector:
    def __init__(self, calibration_frames=100, jump_height="medium"):
        """Initialize MediaPipe pose detection"""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Configuration
        self.CALIBRATION_FRAMES = calibration_frames
        self.jump_height = jump_height  # "low", "medium", or "high"
        self.JUMP_THRESHOLD_OFFSET = 0.01  # Base offset (1% above baseline) - smaller value = threshold closer to baseline
        self.CALIBRATION_OFFSET_ADJUSTMENT = 0.0  # Testing offset: positive = threshold closer to baseline (yellow line lower), negative = threshold higher (easier to trigger)
        self.SMOOTHING = 0.7
        self.KNEE_VALGUS_THRESHOLD = 15
        self.FORWARD_LEAN_THRESHOLD = 30
        self.KNEE_OVER_TOE_THRESHOLD = 0.1
        
        # State variables
        self.reset()
    
    def reset(self):
        """Reset detector state for new session"""
        self.jump_count = 0
        self.jumping = False
        self.calibrating = True
        self.calibration_samples = []
        self.baseline_y = None  # Yellow line position (varies by jump_height)
        self.jump_threshold = None
        self.smoothed_hip_y = None
        self.smoothed_trigger_y = None  # Trigger point: low=ankles, medium=knees, high=knees
        self.smoothed_yellow_line_y = None  # Yellow line position: low=(ankles+knees)/2, medium=(knees+hips)/2, high=(shoulders+hips)/2
        self.posture_warnings = []
        self.danger_detected = False
        self.current_jump_warnings = []
        self.current_jump_bad_moves = 0
        # Ensure jump_height is preserved (don't reset it - it's a configuration, not state)
        if not hasattr(self, 'jump_height') or self.jump_height is None:
            self.jump_height = "medium"  # Default fallback
    
    def start_recalibration(self):
        """Start recalibration process - resets calibration state"""
        self.calibrating = True
        self.calibration_samples = []
        self.baseline_y = None
        self.jump_threshold = None
        self.smoothed_trigger_y = None
        self.smoothed_yellow_line_y = None
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
            self.current_jump_warnings.append(f"{side.upper()} KNEE VALGUS")
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
            self.current_jump_warnings.append("EXCESSIVE FORWARD LEAN")
            return True
        return False
    
    def check_knees_over_toes(self, landmarks: Dict, side: str) -> bool:
        """Check if knees go too far over toes"""
        knee = landmarks[f'knee_{side}']
        ankle = landmarks[f'ankle_{side}']
        toe = [ankle[0], ankle[1] - 0.05]
        
        if (knee[0] - toe[0]) > self.KNEE_OVER_TOE_THRESHOLD:
            self.posture_warnings.append(f"{side.upper()} KNEE OVER TOES")
            self.current_jump_warnings.append(f"{side.upper()} KNEE OVER TOES")
            return True
        return False
    
    def analyze_posture(self, landmarks: Dict):
        """Analyze posture and detect bad moves"""
        self.posture_warnings = []
        self.current_jump_warnings = []
        self.current_jump_bad_moves = 0
        
        left_valgus = self.check_knee_valgus(landmarks, 'l')
        right_valgus = self.check_knee_valgus(landmarks, 'r')
        forward_lean = self.check_forward_lean(landmarks)
        left_knee_over = self.check_knees_over_toes(landmarks, 'l')
        right_knee_over = self.check_knees_over_toes(landmarks, 'r')
        
        self.danger_detected = (left_valgus or right_valgus or forward_lean or 
                                left_knee_over or right_knee_over)
        
        # Count bad moves (each warning type counts as 1)
        self.current_jump_bad_moves = len(set(self.current_jump_warnings))
    
    def process_frame(self, frame) -> Tuple[np.ndarray, Dict]:
        """
        Process a single frame and return annotated frame and status
        
        Returns:
            frame: Annotated frame with pose overlay
            status: Dictionary with jump_count, status_text, warnings, etc.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)
        
        status = {
            'person_detected': False,
            'status_text': "No Person",
            'jump_count': self.jump_count,
            'calibrating': self.calibrating,
            'warnings': [],
            'danger_detected': False,
            'points': 0,
            'bad_moves': 0
        }
        
        if result.pose_landmarks:
            status['person_detected'] = True
            lm = result.pose_landmarks.landmark
            
            # Calculate hip position (for display)
            left_hip = lm[self.mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = lm[self.mp_pose.PoseLandmark.RIGHT_HIP]
            hip_y = (left_hip.y + right_hip.y) / 2.0
            
            # Calculate knee positions
            left_knee = lm[self.mp_pose.PoseLandmark.LEFT_KNEE]
            right_knee = lm[self.mp_pose.PoseLandmark.RIGHT_KNEE]
            
            # Calculate ankle positions (for low jump height)
            left_ankle = lm[self.mp_pose.PoseLandmark.LEFT_ANKLE]
            right_ankle = lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE]
            
            # Calculate shoulder positions (for high jump height)
            left_shoulder = lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            
            # Calculate trigger point (what we track) and yellow line position based on jump_height
            # IMPORTANT: Validate jump_height to prevent using wrong trigger points
            if self.jump_height is None:
                self.jump_height = "medium"  # Default fallback
            
            if self.jump_height == "low":
                # Low: Trigger = ankles (27,28), Yellow line = center of (ankles + knees)
                # Trigger point: ankles
                left_trigger = left_ankle.y
                right_trigger = right_ankle.y
                trigger_y = (left_trigger + right_trigger) / 2.0
                
                # Yellow line: center of (ankles + knees)
                left_yellow = (left_ankle.y + left_knee.y) / 2.0
                right_yellow = (right_ankle.y + right_knee.y) / 2.0
                yellow_line_y = (left_yellow + right_yellow) / 2.0
                
            elif self.jump_height == "medium":
                # Medium: Trigger = leg_elbow/knees (25,26), Yellow line = center of (knees + hips)
                # CRITICAL: For medium, we MUST use KNEES (25,26), NOT ankles (27,28)!
                # Trigger point: knees ONLY - absolutely NO ankles!
                left_trigger = left_knee.y  # Using LEFT_KNEE (25), NOT LEFT_ANKLE (27)
                right_trigger = right_knee.y  # Using RIGHT_KNEE (26), NOT RIGHT_ANKLE (28)
                trigger_y = (left_trigger + right_trigger) / 2.0
                
                # Yellow line: center of (knees + hips)
                left_yellow = (left_knee.y + left_hip.y) / 2.0
                right_yellow = (right_knee.y + right_hip.y) / 2.0
                yellow_line_y = (left_yellow + right_yellow) / 2.0
                
            elif self.jump_height == "high":
                # High: Trigger = knees (25,26), Yellow line = center of (shoulders + hips)
                # Trigger point: knees
                left_trigger = left_knee.y
                right_trigger = right_knee.y
                trigger_y = (left_trigger + right_trigger) / 2.0
                
                # Yellow line: center of (shoulders + hips)
                left_yellow = (left_shoulder.y + left_hip.y) / 2.0
                right_yellow = (right_shoulder.y + right_hip.y) / 2.0
                yellow_line_y = (left_yellow + right_yellow) / 2.0
            else:
                # Fallback to medium if unknown value
                # Default to medium: Trigger = knees (25,26), Yellow line = center of (knees + hips)
                self.jump_height = "medium"  # Fix invalid value
                left_trigger = left_knee.y
                right_trigger = right_knee.y
                trigger_y = (left_trigger + right_trigger) / 2.0
                left_yellow = (left_knee.y + left_hip.y) / 2.0
                right_yellow = (right_knee.y + right_hip.y) / 2.0
                yellow_line_y = (left_yellow + right_yellow) / 2.0
            
            # Smooth trigger point (what we track for jump detection)
            if self.smoothed_trigger_y is None:
                self.smoothed_trigger_y = trigger_y
            else:
                self.smoothed_trigger_y = (self.SMOOTHING * self.smoothed_trigger_y + 
                                          (1 - self.SMOOTHING) * trigger_y)
            
            # Smooth yellow line position (for display)
            if self.smoothed_yellow_line_y is None:
                self.smoothed_yellow_line_y = yellow_line_y
            else:
                self.smoothed_yellow_line_y = (self.SMOOTHING * self.smoothed_yellow_line_y + 
                                               (1 - self.SMOOTHING) * yellow_line_y)
            
            # Also smooth hip position for display
            if self.smoothed_hip_y is None:
                self.smoothed_hip_y = hip_y
            else:
                self.smoothed_hip_y = (self.SMOOTHING * self.smoothed_hip_y + 
                                      (1 - self.SMOOTHING) * hip_y)
            
            # Calibration phase - calibrate yellow line position
            if self.calibrating:
                self.calibration_samples.append(self.smoothed_yellow_line_y)
                status['status_text'] = f"Calibrating... {len(self.calibration_samples)}/{self.CALIBRATION_FRAMES}"
                
                if len(self.calibration_samples) >= self.CALIBRATION_FRAMES:
                    # Baseline is the yellow line position when standing
                    self.baseline_y = sum(self.calibration_samples) / len(self.calibration_samples)
                    # Yellow line threshold (baseline with optional adjustment)
                    self.jump_threshold = self.baseline_y + self.CALIBRATION_OFFSET_ADJUSTMENT
                    self.calibrating = False
                    status['status_text'] = "Ready - Start Jumping!"
            
            # Jump detection (only after calibration) - using trigger point
            elif not self.calibrating:
                # Check if trigger point goes above yellow line (jumping)
                # When trigger point goes above yellow line = jump detected
                if not self.jumping and self.smoothed_trigger_y < self.jump_threshold:
                    self.jumping = True
                    status['status_text'] = "Jumping ↑"
                    self.current_jump_warnings = []
                    self.current_jump_bad_moves = 0
                
                # Check if trigger point returns to or below yellow line (landed)
                elif self.jumping and self.smoothed_trigger_y >= self.jump_threshold:
                    self.jumping = False
                    self.jump_count += 1
                    
                    # Calculate points: 10 points per jump, -2 per bad move
                    points = 10 - (self.current_jump_bad_moves * 2)
                    points = max(0, points)  # No negative points
                    
                    status['jump_count'] = self.jump_count
                    status['status_text'] = f"Landed ✓ ({self.jump_count} jumps)"
                    status['warnings'] = self.current_jump_warnings.copy()
                    status['danger_detected'] = self.danger_detected
                    status['points'] = points
                    status['bad_moves'] = self.current_jump_bad_moves
                else:
                    status['status_text'] = f"Standing ({self.jump_count} jumps)"
            
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
            
            # Analyze posture (only when jumping)
            if self.jumping:
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
        
        # Draw calibration lines (only after calibration is complete) - draw outside pose detection
        # so lines remain visible even if person temporarily moves out of frame
        if not self.calibrating and self.baseline_y is not None and self.jump_threshold is not None:
            h, w = frame.shape[:2]
            
            # Draw baseline (green) - standing position (draw first so it's behind)
            base_px = int(self.baseline_y * h)
            cv2.line(frame, (0, base_px), (w, base_px), (0, 255, 0), 2)
            
            # Draw jump threshold line (yellow) - EXACTLY at the trigger point based on jump_height
            # This line is at the baseline (center point when standing)
            # When center point goes above this yellow line, jump is detected
            threshold_px = int(self.jump_threshold * h)
            cv2.line(frame, (0, threshold_px), (w, threshold_px), (0, 255, 255), 3)
            
            # Draw trigger point line (blue) - current trigger point (varies by jump_height)
            if self.smoothed_trigger_y is not None:
                trigger_px = int(self.smoothed_trigger_y * h)
                cv2.line(frame, (0, trigger_px), (w, trigger_px), (255, 0, 0), 2)
            
            # Draw hip position line (cyan) - current hip position (for reference)
            if self.smoothed_hip_y is not None:
                hip_px = int(self.smoothed_hip_y * h)
                cv2.line(frame, (0, hip_px), (w, hip_px), (255, 255, 0), 1)
        
        return frame, status
