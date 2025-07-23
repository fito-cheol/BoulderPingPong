import cv2
import time
import numpy as np
from typing import Optional, Callable
from .config_manager import CameraConfig
from .camera_utils import select_camera


class CameraManager:
    """Manages camera connection and configuration."""

    def __init__(self, config: CameraConfig, camera_index: Optional[int] = None,
                 progress_callback: Optional[Callable] = None):
        self.config = config
        self.camera_index = camera_index if camera_index is not None else select_camera()
        self.progress_callback = progress_callback
        self.camera = self._connect_camera()
        self.reconnect_attempts = 0

    def _connect_camera(self) -> cv2.VideoCapture:
        """Attempt to connect to the camera with multiple backends."""
        if self.progress_callback:
            self.progress_callback("Connecting to camera...")

        backends = [cv2.CAP_ANY, cv2.CAP_DSHOW, cv2.CAP_MSMF]
        for backend in backends:
            try:
                cap = cv2.VideoCapture(self.camera_index, backend)
                if cap.isOpened():
                    print(f"Camera {self.camera_index} connected with backend {backend}")
                    self._configure_camera(cap)
                    return cap
            except Exception as e:
                print(f"Backend {backend} failed: {e}")
                if cap:
                    cap.release()
        raise RuntimeError(f"Cannot open camera {self.camera_index} with any backend")

    def _configure_camera(self, cap: cv2.VideoCapture) -> None:
        """Configure camera settings."""
        if self.progress_callback:
            self.progress_callback("Configuring camera...")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])
        cap.set(cv2.CAP_PROP_FPS, self.config.fps)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)

        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0:
            self.camera_width = frame.shape[1]
            self.camera_height = frame.shape[0]
            print(f"Camera resolution: {self.camera_width}x{self.camera_height}")
        else:
            self.camera_width, self.camera_height = self.config.resolution
            print("Warning: Using default camera resolution (1280x720)")

    def reconnect_camera(self) -> bool:
        """Attempt to reconnect to the camera."""
        print(f"Reconnecting to camera {self.camera_index}...")
        self.camera.release()
        time.sleep(1)

        try:
            self.camera = self._connect_camera()
            self.reconnect_attempts = 0
            return True
        except RuntimeError:
            self.reconnect_attempts += 1
            print(f"Reconnection failed. Attempt {self.reconnect_attempts}/{self.config.max_reconnect_attempts}")
            return False

    def get_frame(self) -> Optional[np.ndarray]:
        """Capture a frame from the camera."""
        if not self.camera.isOpened():
            if not self.reconnect_camera():
                return None
        ret, frame = self.camera.read()
        return frame if ret and frame is not None and frame.size > 0 else None

    def release(self) -> None:
        """Release camera resources."""
        if self.camera:
            self.camera.release()
