import cv2
import mediapipe as mp
import numpy as np
import time
import os
from config import WALL_WIDTH, WALL_HEIGHT, LANDMARKS_TO_TRACK, MAX_RECONNECT_ATTEMPTS, SCALE_FACTOR

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Error: Cannot open webcam")
        ret, frame = self.cap.read()
        if ret:
            self.camera_width = frame.shape[1]
            self.camera_height = frame.shape[0]
        else:
            self.camera_width, self.camera_height = 1280, 720
            print("Warning: Using default camera resolution (1280x720)")

        self.model_path = r"C:\Users\USER\PycharmProjects\BoulderPingPong\pose_landmarker_full.task"
        if not os.path.exists(self.model_path):
            raise RuntimeError(
                f"Error: Model file not found at {self.model_path}\n"
                "Please download the model from: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models"
            )

        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_poses=2,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.landmarker = PoseLandmarker.create_from_options(options)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = MAX_RECONNECT_ATTEMPTS

    def get_player_positions(self):
        if not self.cap.isOpened():
            print("Error: Camera disconnected, attempting to reconnect...")
            self.cap.release()
            self.cap = cv2.VideoCapture(0)
            self.reconnect_attempts += 1
            if self.reconnect_attempts > self.max_reconnect_attempts:
                print("Error: Max reconnect attempts reached.")
                return []
            if not self.cap.isOpened():
                print("Error: Reconnection failed. Retrying in 2 seconds...")
                time.sleep(2)
                return []
            self.reconnect_attempts = 0

        ret, frame = self.cap.read()
        if not ret or frame is None:
            print("Error: Failed to capture frame")
            return []

        if frame.shape[0] == 0 or frame.shape[1] == 0:
            print("Error: Invalid frame dimensions")
            return []

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        try:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        except Exception as e:
            print(f"Error creating mp.Image: {e}")
            return []

        timestamp_ms = int(time.time() * 1000)
        try:
            pose_landmarker_result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        except Exception as e:
            print(f"Error detecting landmarks: {e}")
            return []

        positions = []
        if pose_landmarker_result and pose_landmarker_result.pose_landmarks:
            print(f"Detected {len(pose_landmarker_result.pose_landmarks)} person(s)")
            for person_idx, pose_landmarks in enumerate(pose_landmarker_result.pose_landmarks):
                for idx, landmark in enumerate(pose_landmarks):
                    if idx in LANDMARKS_TO_TRACK:
                        try:
                            x = landmark.x * self.camera_width * (WALL_WIDTH / self.camera_width)
                            y = landmark.y * self.camera_height * (WALL_HEIGHT / self.camera_height)
                            positions.append([x, y])
                        except AttributeError as e:
                            print(f"Error processing landmark {idx} for person {person_idx + 1}: {e}")
        else:
            print("No landmarks detected in this frame")

        return positions

    def get_frame(self):
        if not self.cap.isOpened():
            print("Error: Camera disconnected, attempting to reconnect...")
            self.cap.release()
            self.cap = cv2.VideoCapture(0)
            self.reconnect_attempts += 1
            if self.reconnect_attempts > self.max_reconnect_attempts:
                print("Error: Max reconnect attempts reached.")
                return None
            if not self.cap.isOpened():
                print("Error: Reconnection failed. Retrying in 2 seconds...")
                time.sleep(2)
                return None
            self.reconnect_attempts = 0

        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        self.cap.release()
        self.landmarker.close()
        cv2.destroyAllWindows()