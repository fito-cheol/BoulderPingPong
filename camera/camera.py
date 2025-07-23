import cv2
import time
import numpy as np
from typing import List, Dict, Optional, Callable, Any
from config_manager import CameraConfig
from camera_manager import CameraManager
from pose_processor import PoseProcessor


class Camera:
    """Integrates camera capture and pose detection."""
    def __init__(self, config: CameraConfig = CameraConfig(), camera_index: Optional[int] = None,
                 progress_callback: Optional[Callable] = None):
        """Initialize camera and pose landmarker.

        Args:
            config: Configuration for camera and pose detection.
            camera_index: Camera index, auto-select if None.
            progress_callback: Optional callback for progress updates.
        """
        self.config = config
        self.camera_manager = CameraManager(config, camera_index, progress_callback)
        self.pose_processor = PoseProcessor(config, progress_callback)
        self.progress_callback = progress_callback
        if self.progress_callback:
            self.progress_callback("Initialization complete")

    def _capture_and_process_frame(self) -> tuple[Optional[np.ndarray], Optional[Any]]:
        """Capture and process a frame for pose detection."""
        if not self.camera_manager.camera.isOpened():
            if not self.camera_manager.reconnect_camera():
                if self.camera_manager.reconnect_attempts > self.config.max_reconnect_attempts:
                    print("Error: Max reconnect attempts reached.")
                    return None, None
                return None, None

        frame = self.camera_manager.get_frame()
        if frame is None:
            print("Error: Failed to capture frame")
            return None, None

        if frame.shape[0] == 0 or frame.shape[1] == 0:
            print("Error: Invalid frame dimensions")
            return None, None

        # Apply search margin if specified
        if self.config.search_margin_x > 0 or self.config.search_margin_y > 0:
            height, width = frame.shape[:2]
            margin_x = int(width * self.config.search_margin_x)
            margin_y = int(height * self.config.search_margin_y)
            frame = frame[margin_y:height-margin_y, margin_x:width-margin_x]
            if frame.size == 0:
                print("Error: Invalid frame after applying margins")
                return None, None

        timestamp_ms = int(time.time() * 1000)
        result = self.pose_processor.process_frame(frame, timestamp_ms)
        return frame, result

    def get_player_positions(self) -> List[List[float]]:
        """Get normalized [x, y] coordinates of tracked landmarks.

        Returns:
            List of [x, y] coordinates for tracked landmarks.
        """
        frame, result = self._capture_and_process_frame()
        if not result or not result.pose_landmarks:
            return []

        positions = []
        for pose_landmarks in result.pose_landmarks:
            for idx, landmark in enumerate(pose_landmarks):
                if idx in self.config.landmarks_to_track:
                    positions.append([landmark.x, landmark.y])
        return positions

    def get_full_pose_data(self) -> List[Dict[str, Any]]:
        """Get full pose data for all detected persons.

        Returns:
            List of dictionaries containing pose data (head, hands, feet, body).
        """
        frame, result = self._capture_and_process_frame()
        if not result or not result.pose_landmarks:
            return []

        # Adjust coordinates for margins
        original_width = self.camera_manager.camera_width
        original_height = self.camera_manager.camera_height
        margin_x = self.config.search_margin_x * original_width
        margin_y = self.config.search_margin_y * original_height
        width = original_width - 2 * margin_x
        height = original_height - 2 * margin_y

        players_data = []
        for pose_landmarks in result.pose_landmarks:
            player_data = self.pose_processor.process_pose_landmarks(pose_landmarks)
            # Adjust coordinates if margins are applied
            if margin_x > 0 or margin_y > 0:
                for section in ['head', 'hands', 'feet', 'body']:
                    if section == 'hands' or section == 'feet':
                        for item in player_data[section]:
                            item['x'] = (item['x'] * width + margin_x) / original_width
                            item['y'] = (item['y'] * height + margin_y) / original_height
                    else:
                        for idx, data in player_data[section].items():
                            data['x'] = (data['x'] * width + margin_x) / original_width
                            data['y'] = (data['y'] * height + margin_y) / original_height
            players_data.append(player_data)
        return players_data

    def get_frame(self) -> Optional[np.ndarray]:
        """Get the raw camera frame."""
        return self.camera_manager.get_frame()

    def release(self) -> None:
        """Release all resources."""
        self.camera_manager.release()
        self.pose_processor.close()
        cv2.destroyAllWindows()
