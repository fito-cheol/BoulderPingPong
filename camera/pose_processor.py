import mediapipe as mp
import numpy as np
import cv2
import os
from typing import Dict, Any, Optional, Callable
from .config_manager import CameraConfig

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


class PoseProcessor:
    """Handles pose landmark detection using MediaPipe."""

    def __init__(self, config: CameraConfig, progress_callback: Optional[Callable] = None):
        self.config = config
        self.progress_callback = progress_callback
        self.landmarker = self._init_landmarker()

    def _init_landmarker(self) -> PoseLandmarker:
        """Initialize the MediaPipe PoseLandmarker."""
        if self.progress_callback:
            self.progress_callback("Loading AI model...")

        if not os.path.exists(self.config.model_path):
            raise RuntimeError(
                f"Model file not found at {self.config.model_path}. "
                "Please download from: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models"
            )

        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.config.model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_poses=2,
            min_pose_detection_confidence=self.config.confidence_threshold,
            min_pose_presence_confidence=self.config.confidence_threshold,
            min_tracking_confidence=self.config.confidence_threshold
        )
        print("Loading MediaPipe model...")
        landmarker = PoseLandmarker.create_from_options(options)
        print("MediaPipe model loaded successfully")
        return landmarker

    def process_frame(self, frame: np.ndarray, timestamp_ms: int) -> Any:
        """Process a frame to detect pose landmarks."""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        return self.landmarker.detect_for_video(mp_image, timestamp_ms)

    def process_pose_landmarks(self, pose_landmarks: Any) -> Dict[str, Any]:
        """Process pose landmarks into structured data."""
        player_data = {
            'landmarks': {},
            'hands': [],
            'feet': [],
            'head': {},
            'body': {}
        }
        for idx, landmark in enumerate(pose_landmarks):
            try:
                x = max(0.0, min(1.0, landmark.x))
                y = max(0.0, min(1.0, landmark.y))
                z = getattr(landmark, 'z', 0.0)
                visibility = getattr(landmark, 'visibility', 0.0)
                presence = getattr(landmark, 'presence', 0.0)

                landmark_data = {
                    'x': x, 'y': y, 'z': z,
                    'visibility': visibility,
                    'presence': presence,
                    'landmark_index': idx
                }

                if idx in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                    player_data['head'][idx] = landmark_data
                elif idx in [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]:
                    if idx == 15 and visibility > 0.1:
                        landmark_data['side'] = 'left'
                        player_data['hands'].append(landmark_data)
                    elif idx == 16 and visibility > 0.1:
                        landmark_data['side'] = 'right'
                        player_data['hands'].append(landmark_data)
                elif idx in [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]:
                    if idx == 27 and visibility > 0.05:
                        landmark_data['side'] = 'left'
                        player_data['feet'].append(landmark_data)
                    elif idx == 28 and visibility > 0.05:
                        landmark_data['side'] = 'right'
                        player_data['feet'].append(landmark_data)
                    else:
                        player_data['body'][idx] = landmark_data
                else:
                    player_data['body'][idx] = landmark_data
            except AttributeError:
                continue
        return player_data

    def close(self) -> None:
        """Close the landmarker."""
        self.landmarker.close()