import cv2
import mediapipe as mp
import numpy as np
import time
import os
from dataclasses import dataclass

# Constants
WALL_SIZE = 3.66  # Kilter board width and height (meters)
LANDMARKS_TO_TRACK = {15, 16, 27, 28}  # Hand/foot landmarks
MAX_RECONNECT_ATTEMPTS = 5

# Color configuration (BGR format)
COLORS = {
    'hand': (0, 0, 255),  # Red for hands (landmarks 15, 16)
    'foot': (0, 220, 220),  # Yellow for feet (landmarks 27, 28)
    'text': (0, 255, 0),  # Green for text labels
    'landmark_default': (255, 255, 255),  # White for default landmarks
    'connection': (0, 255, 255)  # Cyan for pose connections
}


@dataclass
class CameraConfig:
    width: int
    height: int
    cap: cv2.VideoCapture


# MediaPipe initialization
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode
POSE_CONNECTIONS = mp_pose.POSE_CONNECTIONS


def initialize_camera() -> CameraConfig:
    """Initialize camera and return configuration."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")

    ret, frame = cap.read()
    if not ret:
        cap.release()
        raise RuntimeError("Failed to capture frame")

    return CameraConfig(frame.shape[1], frame.shape[0], cap)


def setup_pose_landmarker(model_path: str) -> PoseLandmarker:
    """Setup and return PoseLandmarker."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}. Download from: "
                                "https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models")

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.VIDEO,
        num_poses=2,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    return PoseLandmarker.create_from_options(options)


def draw_landmark_info(frame: np.ndarray, person_idx: int, landmark_idx: int,
                       x_m: float, y_m: float, pos_y: int) -> None:
    """Draw landmark information on frame."""
    label = f"P{person_idx} L{landmark_idx}: ({x_m:.2f}m, {y_m:.2f}m)"
    cv2.putText(frame, label, (10, pos_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['text'], 1, cv2.LINE_AA)


def draw_landmark(frame: np.ndarray, landmark, idx: int, config: CameraConfig) -> None:
    """Draw individual landmark on frame."""
    try:
        x_pixel = int(landmark.x * config.width)
        y_pixel = int(landmark.y * config.height)
        color = COLORS['hand'] if idx in {15, 16} else COLORS['foot']
        cv2.circle(frame, (x_pixel, y_pixel), 10, color, -1)
    except AttributeError as e:
        print(f"Invalid landmark {idx}: {e}")


def process_landmarks(frame: np.ndarray, landmarks: list, config: CameraConfig) -> tuple[np.ndarray, int]:
    """Process and draw landmarks on frame."""
    text_y = 30
    for person_idx, pose_landmarks in enumerate(landmarks):
        try:
            # Update drawing style with custom colors
            custom_style = mp_drawing_styles.get_default_pose_landmarks_style()
            for idx in custom_style:
                custom_style[idx].color = COLORS['landmark_default']
                custom_style[idx].connection_color = COLORS['connection']

            mp_drawing.draw_landmarks(
                frame,
                pose_landmarks,
                POSE_CONNECTIONS,
                landmark_drawing_spec=custom_style
            )
        except Exception as e:
            print(f"Error drawing landmarks for person {person_idx + 1}: {e}")
            # Fallback: Draw individual landmark points
            for idx, landmark in enumerate(pose_landmarks):
                if idx in LANDMARKS_TO_TRACK:
                    draw_landmark(frame, landmark, idx, config)

        for idx, landmark in enumerate(pose_landmarks):
            if idx in LANDMARKS_TO_TRACK:
                try:
                    x_m = landmark.x * config.width * (WALL_SIZE / config.width)
                    y_m = landmark.y * config.height * (WALL_SIZE / config.height)
                    draw_landmark(frame, landmark, idx, config)
                    draw_landmark_info(frame, person_idx + 1, idx, x_m, y_m, text_y)
                    text_y += 30
                except AttributeError as e:
                    print(f"Error processing landmark {idx} for person {person_idx + 1}: {e}")

    return frame, text_y


def main():
    model_path = r"pose_landmarker_heavy.task"

    try:
        config = initialize_camera()
        landmarker = setup_pose_landmarker(model_path)
    except Exception as e:
        print(f"Initialization error: {e}")
        return

    try:
        with landmarker:
            reconnect_attempts = 0
            while True:
                if not config.cap.isOpened():
                    if reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                        raise RuntimeError("Max reconnect attempts reached")
                    config.cap.release()
                    config = initialize_camera()
                    reconnect_attempts += 1
                    time.sleep(2)
                    continue

                ret, frame = config.cap.read()
                if not ret or frame is None:
                    print("Failed to capture frame")
                    reconnect_attempts += 1
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
                result = landmarker.detect_for_video(mp_image, int(time.time() * 1000))

                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                if result.pose_landmarks:
                    frame_bgr, _ = process_landmarks(frame_bgr, result.pose_landmarks, config)

                cv2.imshow("Hand/Foot Tracking", frame_bgr)
                if cv2.waitKey(1) & 0xFF == 27:
                    break

    except Exception as e:
        print(f"Runtime error: {e}")
    finally:
        config.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()