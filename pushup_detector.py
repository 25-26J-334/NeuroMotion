"""
Push-up detection module with posture analysis
Separate from jump_detector.py and squat_detector.py to keep functionality isolated
"""
import cv2
import mediapipe as mp
import numpy as np
from math import degrees, atan2
from typing import Dict, List, Tuple

class PushupDetector:
    def __init__(self, calibration_frames=100):
        """Initialize MediaPipe pose detection for push-ups"""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Configuration
        self.CALIBRATION_FRAMES = calibration_frames
        self.SMOOTHING = 0.7
        self.PUSHUP_DEPTH_THRESHOLD = 0.15  # Shoulder must go down by this much (15% of frame height)
        self.BACK_ARCH_THRESHOLD = 20  # Excessive back arching
        self.HEAD_POSITION_THRESHOLD = 0.1  # Head should be aligned with body
        self.ARM_ANGLE_THRESHOLD = 30  # Arms should be at proper angle (not too wide/narrow)
        self.HIP_SAG_THRESHOLD = 0.1  # Hips should not sag too much
        
        # State variables
        self.reset()
    
    def reset(self):
        """Reset detector state for new session"""
        self.pushup_count = 0
        self.pushing_down = False
        self.calibrating = True
        self.calibration_samples = []
        self.baseline_nose_y = None  # Up position (nose height)
        self.pushup_threshold = None  # Down position threshold
        self.smoothed_nose_y = None
        self.posture_warnings = []
        self.danger_detected = False
        self.current_pushup_warnings = []
        self.current_pushup_bad_moves = 0
        self.was_down = False  # Track if we were in down position
        self.rep_history = []
        self.rep_start_frame = None
    
    def start_recalibration(self):
        """Start recalibration process"""
        self.calibrating = True
        self.calibration_samples = []
        self.baseline_nose_y = None
        self.pushup_threshold = None
        self.smoothed_nose_y = None
    
    def calculate_angle(self, a, b, c):
        """Calculate angle between three points"""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(degrees(radians))
        angle = min(angle, 360 - angle)
        return angle
    
    def check_back_arch(self, landmarks: Dict) -> bool:
        """Check for excessive back arching (sagging back)"""
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
            self.current_pushup_warnings.append("EXCESSIVE BACK ARCH")
            return True
        return False
    
    def check_head_position(self, landmarks: Dict) -> bool:
        """Check if head is too low or too high (should be aligned with body)"""
        nose = landmarks['nose']
        shoulder = [
            (landmarks['shoulder_l'][0] + landmarks['shoulder_r'][0]) / 2,
            (landmarks['shoulder_l'][1] + landmarks['shoulder_r'][1]) / 2
        ]
        
        # Head should be roughly aligned with shoulders (not too far forward/back)
        head_offset = abs(nose[1] - shoulder[1])
        if head_offset > self.HEAD_POSITION_THRESHOLD:
            self.posture_warnings.append("POOR HEAD POSITION")
            self.current_pushup_warnings.append("POOR HEAD POSITION")
            return True
        return False
    
    def check_arm_angle(self, landmarks: Dict, side: str) -> bool:
        """Check if arms are at proper angle (not too wide or too narrow)"""
        shoulder = landmarks[f'shoulder_{side}']
        elbow = landmarks[f'elbow_{side}']
        wrist = landmarks[f'wrist_{side}']
        
        angle = self.calculate_angle(shoulder, elbow, wrist)
        # Proper push-up angle: between 90-150 degrees
        if angle < 90 or angle > 150:
            self.posture_warnings.append(f"{side.upper()} ARM ANGLE INCORRECT")
            self.current_pushup_warnings.append(f"{side.upper()} ARM ANGLE INCORRECT")
            return True
        return False
    
    def check_hip_sag(self, landmarks: Dict) -> bool:
        """Check if hips are sagging too much (body not straight)"""
        shoulder = [
            (landmarks['shoulder_l'][0] + landmarks['shoulder_r'][0]) / 2,
            (landmarks['shoulder_l'][1] + landmarks['shoulder_r'][1]) / 2
        ]
        hip = [
            (landmarks['hip_l'][0] + landmarks['hip_r'][0]) / 2,
            (landmarks['hip_l'][1] + landmarks['hip_r'][1]) / 2
        ]
        ankle = [
            (landmarks['ankle_l'][0] + landmarks['ankle_r'][0]) / 2,
            (landmarks['ankle_l'][1] + landmarks['ankle_r'][1]) / 2
        ]
        
        # Calculate if hip is sagging below the line between shoulder and ankle
        # In proper push-up, hip should be roughly aligned with shoulder-ankle line
        shoulder_ankle_line_y = shoulder[1] + (ankle[1] - shoulder[1]) * 0.5
        hip_sag = hip[1] - shoulder_ankle_line_y
        
        if hip_sag > self.HIP_SAG_THRESHOLD:
            self.posture_warnings.append("HIP SAGGING")
            self.current_pushup_warnings.append("HIP SAGGING")
            return True
        return False
    
    def analyze_posture(self, landmarks: Dict):
        """Analyze posture and detect bad moves during push-ups"""
        self.posture_warnings = []
        self.current_pushup_warnings = []
        self.current_pushup_bad_moves = 0
        
        back_arch = self.check_back_arch(landmarks)
        head_position = self.check_head_position(landmarks)
        left_arm_angle = self.check_arm_angle(landmarks, 'l')
        right_arm_angle = self.check_arm_angle(landmarks, 'r')
        hip_sag = self.check_hip_sag(landmarks)
        
        self.danger_detected = (back_arch or head_position or 
                                left_arm_angle or right_arm_angle or hip_sag)
        
        # Count bad moves (each warning type counts as 1)
        self.current_pushup_bad_moves = len(set(self.current_pushup_warnings))
    
    def process_frame(self, frame, frame_index=None) -> Tuple[np.ndarray, Dict]:
        """
        Process a single frame and return annotated frame and status
        
        Returns:
            frame: Annotated frame with pose overlay
            status: Dictionary with pushup_count, status_text, warnings, etc.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)
        
        status = {
            'person_detected': False,
            'status_text': "No Person",
            'pushup_count': self.pushup_count,
            'calibrating': self.calibrating,
            'warnings': [],
            'danger_detected': False,
            'points': 0,
            'bad_moves': 0
        }
        
        if result.pose_landmarks:
            status['person_detected'] = True
            lm = result.pose_landmarks.landmark
            
            # Calculate nose position (key for push-up detection - more reliable than shoulders)
            nose = lm[self.mp_pose.PoseLandmark.NOSE]
            nose_y = nose.y
            
            # Smooth nose position
            if self.smoothed_nose_y is None:
                self.smoothed_nose_y = nose_y
            else:
                self.smoothed_nose_y = (self.SMOOTHING * self.smoothed_nose_y + 
                                       (1 - self.SMOOTHING) * nose_y)
            
            # Calibration phase
            if self.calibrating:
                self.calibration_samples.append(self.smoothed_nose_y)
                status['status_text'] = f"Calibrating... {len(self.calibration_samples)}/{self.CALIBRATION_FRAMES}"
                
                if len(self.calibration_samples) >= self.CALIBRATION_FRAMES:
                    # Baseline is the nose position when up (at top of push-up)
                    self.baseline_nose_y = sum(self.calibration_samples) / len(self.calibration_samples)
                    # Push-up threshold: nose must go down by PUSHUP_DEPTH_THRESHOLD
                    # Add a small offset to make detection more reliable
                    self.pushup_threshold = self.baseline_nose_y + self.PUSHUP_DEPTH_THRESHOLD
                    self.calibrating = False
                    status['status_text'] = "Ready - Start Push-ups!"
            
            # Push-up detection (only after calibration)
            elif not self.calibrating:
                # Check if nose goes down (pushing down)
                if not self.pushing_down and self.smoothed_nose_y >= self.pushup_threshold:
                    self.pushing_down = True
                    self.rep_start_frame = frame_index
                    self.was_down = True
                    status['status_text'] = "Pushing Down ↓"
                    self.current_pushup_warnings = []
                    self.current_pushup_bad_moves = 0
                
                # Check if nose returns to baseline (pushing up)
                elif self.pushing_down and self.smoothed_nose_y < self.baseline_nose_y:
                    # Only count as completed push-up if we went down first
                    if self.was_down:
                        self.pushing_down = False
                        self.was_down = False
                        self.pushup_count += 1
                        
                        # Calculate points: 10 points per push-up, -2 per bad move
                        points = 10 - (self.current_pushup_bad_moves * 2)
                        points = max(0, points)  # No negative points
                        
                        # Record rep history
                        self.rep_history.append({
                            'rep_number': self.pushup_count,
                            'start_frame': self.rep_start_frame,
                            'end_frame': frame_index,
                            'points': points
                        })
                        
                        status['pushup_count'] = self.pushup_count
                        status['status_text'] = f"Pushing Up ✓ ({self.pushup_count} push-ups)"
                        status['warnings'] = self.current_pushup_warnings.copy()
                        status['danger_detected'] = self.danger_detected
                        status['points'] = points
                        status['bad_moves'] = self.current_pushup_bad_moves
                    else:
                        status['status_text'] = f"Up Position ({self.pushup_count} push-ups)"
                else:
                    if self.pushing_down:
                        status['status_text'] = f"Pushing Down ({self.pushup_count} push-ups)"
                    else:
                        status['status_text'] = f"Up Position ({self.pushup_count} push-ups)"
            
            # Get landmarks for posture analysis
            landmarks_dict = {
                'nose': [lm[self.mp_pose.PoseLandmark.NOSE].x, lm[self.mp_pose.PoseLandmark.NOSE].y],
                'shoulder_l': [lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].x, lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y],
                'shoulder_r': [lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].x, lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y],
                'elbow_l': [lm[self.mp_pose.PoseLandmark.LEFT_ELBOW].x, lm[self.mp_pose.PoseLandmark.LEFT_ELBOW].y],
                'elbow_r': [lm[self.mp_pose.PoseLandmark.RIGHT_ELBOW].x, lm[self.mp_pose.PoseLandmark.RIGHT_ELBOW].y],
                'wrist_l': [lm[self.mp_pose.PoseLandmark.LEFT_WRIST].x, lm[self.mp_pose.PoseLandmark.LEFT_WRIST].y],
                'wrist_r': [lm[self.mp_pose.PoseLandmark.RIGHT_WRIST].x, lm[self.mp_pose.PoseLandmark.RIGHT_WRIST].y],
                'hip_l': [lm[self.mp_pose.PoseLandmark.LEFT_HIP].x, lm[self.mp_pose.PoseLandmark.LEFT_HIP].y],
                'hip_r': [lm[self.mp_pose.PoseLandmark.RIGHT_HIP].x, lm[self.mp_pose.PoseLandmark.RIGHT_HIP].y],
                'ankle_l': [lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].x, lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].y],
                'ankle_r': [lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE].x, lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE].y]
            }
            
            # Analyze posture (only when pushing down)
            if self.pushing_down:
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
        if not self.calibrating and self.baseline_nose_y is not None and self.pushup_threshold is not None:
            h, w = frame.shape[:2]
            
            # Draw baseline (green) - up position
            base_px = int(self.baseline_nose_y * h)
            cv2.line(frame, (0, base_px), (w, base_px), (0, 255, 0), 2)
            
            # Draw push-up threshold line (yellow) - down position threshold
            threshold_px = int(self.pushup_threshold * h)
            cv2.line(frame, (0, threshold_px), (w, threshold_px), (0, 255, 255), 3)
            
            # Draw current nose position line (blue)
            if self.smoothed_nose_y is not None:
                nose_px = int(self.smoothed_nose_y * h)
                cv2.line(frame, (0, nose_px), (w, nose_px), (255, 0, 0), 2)
        
        return frame, status

