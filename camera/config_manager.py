import os
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class CameraConfig:
    """Camera and pose landmarker configuration."""
    model_path: str = os.getenv("POSE_MODEL_PATH", "camera/pose_landmarker_heavy.task")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", 0.5))
    resolution: Tuple[int, int] = (1280, 720)
    fps: int = 30
    max_reconnect_attempts: int = 3
    search_margin_x: float = 0.1
    search_margin_y: float = 0.1
    landmarks_to_track: Optional[List[int]] = None

    def __post_init__(self):
        self.landmarks_to_track = self.landmarks_to_track or [
            0, 11, 12, 15, 16, 23, 24, 27, 28
        ]