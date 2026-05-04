import cv2
import mediapipe as mp
import mediapipe_compat  # noqa: F401 — patches mp.solutions for mediapipe >= 0.10
import numpy as np

class ExerciseValidator:
    def __init__(self):
        """Initialize MediaPipe Pose for exercise validation"""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5)

    def validate_video(self, video_path, expected_exercise):
        """
        Validates if the video matches the expected exercise.
        Samples up to 30 frames from the video to classify the dominant movement.
        
        Args:
            video_path (str): Path to the temporary video file
            expected_exercise (str): One of 'jump', 'squat', 'pushup', 'burpee'
            
        Returns:
            bool: True if the video matches the expected exercise, False otherwise
            str: Message describing the result or error
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False, "Could not open video file."
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return False, "Invalid or empty video file."
            
        # Sample up to 30 frames evenly distributed across the video
        num_samples = min(30, total_frames)
        step = max(1, total_frames // num_samples)
        
        is_horizontal_frames = 0
        max_knee_bend = 0
        min_ankle_y = 1.0
        max_ankle_y = 0.0
        
        valid_frames = 0
        
        for i in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                break
                
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.pose.process(rgb)
            
            if result.pose_landmarks:
                valid_frames += 1
                lm = result.pose_landmarks.landmark
                
                # Extract key landmarks
                shoulder_y = (lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y + lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y) / 2
                ankle_y = (lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].y + lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE].y) / 2
                shoulder_x = (lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER].x + lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].x) / 2
                ankle_x = (lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].x + lm[self.mp_pose.PoseLandmark.RIGHT_ANKLE].x) / 2
                
                # Check if body is generally horizontal (for push-up detection)
                height_diff = abs(ankle_y - shoulder_y)
                width_diff = abs(ankle_x - shoulder_x)
                if height_diff < 0.4 and width_diff > height_diff:
                    is_horizontal_frames += 1
                    
                # Track knee bend (for squat detection)
                hip = [lm[self.mp_pose.PoseLandmark.LEFT_HIP].x, lm[self.mp_pose.PoseLandmark.LEFT_HIP].y]
                knee = [lm[self.mp_pose.PoseLandmark.LEFT_KNEE].x, lm[self.mp_pose.PoseLandmark.LEFT_KNEE].y]
                ankle = [lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].x, lm[self.mp_pose.PoseLandmark.LEFT_ANKLE].y]
                
                knee_angle = self._calculate_angle(hip, knee, ankle)
                bend = 180 - knee_angle
                if bend > max_knee_bend:
                    max_knee_bend = bend
                    
                # Track vertical ankle movement (for jump detection)
                if ankle_y < min_ankle_y: min_ankle_y = ankle_y
                if ankle_y > max_ankle_y: max_ankle_y = ankle_y
                
        cap.release()
        
        if valid_frames == 0:
            return False, "Could not detect a person clearly in the video."
            
        detected_exercise = "unknown"
        
        # Heuristic classification
        is_horizontal = is_horizontal_frames / valid_frames > 0.1
        ankle_movement = max_ankle_y - min_ankle_y
        is_jumping = ankle_movement > 0.1
        is_squatting = max_knee_bend > 40
        
        if is_horizontal and is_jumping:
            detected_exercise = "burpee"
        elif is_horizontal_frames / valid_frames > 0.3:
            detected_exercise = "pushup"
        else:
            if is_jumping:  # Significant vertical movement
                detected_exercise = "jump"
            elif is_squatting:  # Deep knee bend without vertical jump
                detected_exercise = "squat"
            else:
                # Default to jump if standing but no deep bend detected, 
                # or possibly could be an invalid movement. Let's assume jump for minor bounds.
                detected_exercise = "jump"
                
        if detected_exercise == expected_exercise:
            return True, "Validation passed"
        elif expected_exercise == "stepup" and (detected_exercise in ["jump", "squat"]):
            # Step-ups often look like partial jumps or squats to the simple heuristic
            return True, "Validation passed (Step-up detected via vertical movement)"
        else:
            # Provide user-friendly exercise names
            names = {'jump': 'Jump', 'squat': 'Squat', 'pushup': 'Push-up', 'burpee': 'Burpee', 'stepup': 'Step-up'}
            det_name = names.get(detected_exercise, detected_exercise)
            exp_name = names.get(expected_exercise, expected_exercise)
            return False, f"Expected a {exp_name} video, but detected {det_name} movements."

    def _calculate_angle(self, a, b, c):
        """Calculate angle between three points"""
        a, b, c = np.array(a), np.array(b), np.array(c)
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(np.degrees(radians))
        return min(angle, 360 - angle)
