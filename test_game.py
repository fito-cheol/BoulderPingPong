import cv2
import mediapipe as mp
import numpy as np
import time
import os
import random
import pyautogui
from dataclasses import dataclass
from physics import Physics
from config import WALL_WIDTH, WALL_HEIGHT, BALL_RADIUS, HITBOX_RADIUS, FPS

# Constants
SHOW_CAMERA_FEED = False
FULLSCREEN = True  # 전체 화면 모드 플래그
LANDMARKS_TO_TRACK = {15, 16, 27, 28}  # Hand/foot landmarks
MAX_RECONNECT_ATTEMPTS = 5
SCALE_FACTOR = 2.0  # 화면 확대 비율
BALL_SPEED_SCALE = 2.0  # 공 속도 증가 배율 (충돌 후)
INITIAL_BALL_SPEED_SCALE = 0.5  # 초기 공 속도 배율
ROUND_END_DELAY = 1.0  # 1-second delay after round ends
좌우반전 = False
디버깅 = False
# Color configuration (BGR format)
COLORS = {
    'hand': (0, 0, 255),  # Red for hands (landmarks 15, 16)
    'foot': (0, 220, 220),  # Yellow for feet (landmarks 27, 28)
    'ball': (255, 255, 255),  # White for ball fill
    'ball_border': (0, 0, 0),  # Black for ball border
    'score' : (120, 255, 120 ), # 점수 표기 색
    'text': (0, 255, 0),  # Green for text labels
    'landmark_default': (255, 255, 255),  # White for default landmarks
    'connection': (0, 255, 255),  # Cyan for pose connections
    'left_border': (0, 0, 255),  # Red for left border
    'right_border': (255, 0, 0),  # Blue for right border
    'top_bottom_border': (255, 255, 255),  # White for top/bottom borders
    'center_line': (255, 255, 255)  # White for center line
}

@dataclass
class CameraConfig:
    width: int
    height: int
    cap: cv2.VideoCapture
    screen_width: int = None  # 화면 해상도 추가
    screen_height: int = None

def initialize_camera() -> CameraConfig:
    """Initialize camera and return configuration with screen resolution."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")

    ret, frame = cap.read()
    if not ret:
        cap.release()
        raise RuntimeError("Failed to capture frame")

    # 화면 해상도 가져오기
    if FULLSCREEN:
        screen_width, screen_height = pyautogui.size()
    else:
        screen_width, screen_height = frame.shape[1], frame.shape[0]

    return CameraConfig(frame.shape[1], frame.shape[0], cap, screen_width, screen_height)

def setup_pose_landmarker(model_path: str) -> mp.tasks.vision.PoseLandmarker:
    """Setup and return PoseLandmarker."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}. Download from: "
                                "https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models")

    options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_poses=2,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    return mp.tasks.vision.PoseLandmarker.create_from_options(options)

def transform_coordinates(points, config: CameraConfig):
    """Convert world coordinates (meters) to pixel coordinates with scaling."""
    points = np.array(points, dtype=np.float32)
    if points.ndim == 1:
        points = points.reshape(1, -1, 2)
    scale = np.array([config.screen_width / WALL_WIDTH, config.screen_height / WALL_HEIGHT])
    transformed = points * scale
    return transformed.reshape(-1, 2)

def draw_landmark_info(frame: np.ndarray, person_idx: int, landmark_idx: int,
                       x_m: float, y_m: float, pos_y: int) -> None:
    """Draw landmark information on frame."""
    label = f"P{person_idx} L{landmark_idx}: ({x_m:.2f}m, {y_m:.2f}m)"
    cv2.putText(frame, label, (10, pos_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5 * SCALE_FACTOR, COLORS['text'], 1, cv2.LINE_AA)

def draw_landmark(frame: np.ndarray, landmark, idx: int, config: CameraConfig) -> None:
    """Draw individual landmark on frame."""
    try:
        x_pixel = int(landmark.x * config.width * (config.screen_width / config.width))
        y_pixel = int(landmark.y * config.height * (config.screen_height / config.height))
        color = COLORS['hand'] if idx in {15, 16} else COLORS['foot']
        cv2.circle(frame, (x_pixel, y_pixel), int(10 * SCALE_FACTOR), color, -1)
    except AttributeError as e:
        print(f"Invalid landmark {idx}: {e}")

def draw_ball(frame: np.ndarray, ball_pos: np.ndarray, config: CameraConfig) -> None:
    """Draw ball with border on frame."""
    ball_screen = transform_coordinates(ball_pos, config)
    ball_radius_pixel = int(BALL_RADIUS * config.screen_width / WALL_WIDTH)
    border_thickness = max(1, int(ball_radius_pixel * 0.1))
    cv2.circle(frame, (int(ball_screen[0, 0]), int(ball_screen[0, 1])), ball_radius_pixel, COLORS['ball'], -1)
    cv2.circle(frame, (int(ball_screen[0, 0]), int(ball_screen[0, 1])), ball_radius_pixel, COLORS['ball_border'], border_thickness)

def draw_score(frame: np.ndarray, score: list, config: CameraConfig) -> None:
    """Draw score in the center of the screen."""
    label = f"{score[0]} : {score[1]}"
    text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1 * SCALE_FACTOR, 2)[0]
    text_x = int((config.screen_width - text_size[0]) // 2)
    text_y = int(50 * SCALE_FACTOR)
    cv2.putText(frame, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1 * SCALE_FACTOR, COLORS['score'], 2, cv2.LINE_AA)

def draw_borders_and_center_line(frame: np.ndarray, config: CameraConfig) -> None:
    """Draw semi-transparent rectangular borders and a center line."""
    border_thickness = int(10 * SCALE_FACTOR)
    center_line_thickness = int(5 * SCALE_FACTOR)
    alpha = 0.5  # Transparency for borders and center line
    overlay = frame.copy()

    # Top border (cyan)
    cv2.rectangle(overlay, (0, 0), (config.screen_width, border_thickness), COLORS['top_bottom_border'], -1)
    # Bottom border (cyan)
    cv2.rectangle(overlay, (0, config.screen_height - border_thickness),
                  (config.screen_width, config.screen_height), COLORS['top_bottom_border'], -1)
    # Left border (red)
    cv2.rectangle(overlay, (0, 0), (border_thickness, config.screen_height), COLORS['left_border'], -1)
    # Right border (blue)
    cv2.rectangle(overlay, (config.screen_width - border_thickness, 0),
                  (config.screen_width, config.screen_height), COLORS['right_border'], -1)
    # Center line (white, dashed)
    center_x = config.screen_width // 2
    dash_length = int(20 * SCALE_FACTOR)
    gap_length = int(10 * SCALE_FACTOR)
    y = 0
    while y < config.screen_height:
        cv2.line(overlay, (center_x, y), (center_x, min(y + dash_length, config.screen_height)),
                 COLORS['center_line'], center_line_thickness)
        y += dash_length + gap_length

    # Blend overlay with original frame for transparency
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

def process_landmarks(frame: np.ndarray, landmarks: list, config: CameraConfig, physics: Physics) -> tuple[np.ndarray, int, list]:
    """Process landmarks, draw on frame, and collect positions for physics."""
    player_positions = []
    text_y = int(30 * SCALE_FACTOR)
    for person_idx, pose_landmarks in enumerate(landmarks):
        person_positions = []
        try:
            custom_style = mp.solutions.drawing_styles.get_default_pose_landmarks_style()
            for idx in custom_style:
                custom_style[idx].color = COLORS['landmark_default']
                custom_style[idx].connection_color = COLORS['connection']

            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                pose_landmarks,
                mp.solutions.pose.POSE_CONNECTIONS,
                landmark_drawing_spec=custom_style
            )
        except Exception as e:
            print(f"Error drawing landmarks for person {person_idx + 1}: {e}")
            for idx, landmark in enumerate(pose_landmarks):
                if idx in LANDMARKS_TO_TRACK:
                    draw_landmark(frame, landmark, idx, config)

        for idx, landmark in enumerate(pose_landmarks):
            if idx in LANDMARKS_TO_TRACK:
                try:
                    x_m = landmark.x * config.width * (WALL_WIDTH / config.width)
                    y_m = landmark.y * config.height * (WALL_HEIGHT / config.height)
                    person_positions.append([x_m, y_m])
                    draw_landmark(frame, landmark, idx, config)
                    if 디버깅:
                        draw_landmark_info(frame, person_idx + 1, idx, x_m, y_m, text_y)
                    text_y += int(30 * SCALE_FACTOR)
                except AttributeError as e:
                    print(f"Error processing landmark {idx} for person {person_idx + 1}: {e}")
        if person_positions:
            player_positions.extend(person_positions)

    if not physics.round_ended:  # Only draw ball if round hasn't ended
        draw_ball(frame, physics.ball_pos, config)
    draw_score(frame, physics.score, config)
    return frame, text_y, player_positions

def draw_landmark(frame: np.ndarray, landmark, idx: int, config: CameraConfig) -> None:
    """Draw individual landmark on frame."""
    try:
        x_pixel = int(landmark.x * config.width * (config.screen_width / config.width))
        y_pixel = int(landmark.y * config.height * (config.screen_height / config.height))
        color = COLORS['hand'] if idx in {15, 16} else COLORS['foot']
        cv2.circle(frame, (x_pixel, y_pixel), int(10 * SCALE_FACTOR), color, -1)
    except AttributeError as e:
        print(f"Invalid landmark {idx}: {e}")

def draw_landmarks(frame: np.ndarray, landmarks: list, config: CameraConfig) -> tuple[np.ndarray, int, list]:
    """Draw landmarks and collect positions for physics."""
    player_positions = []
    text_y = int(30 * SCALE_FACTOR)
    for person_idx, pose_landmarks in enumerate(landmarks):
        person_positions = []
        try:
            custom_style = mp.solutions.drawing_styles.get_default_pose_landmarks_style()
            for idx in custom_style:
                custom_style[idx].color = COLORS['landmark_default']
                custom_style[idx].connection_color = COLORS['connection']

            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                pose_landmarks,
                mp.solutions.pose.POSE_CONNECTIONS,
                landmark_drawing_spec=custom_style
            )
        except Exception as e:
            print(f"Error drawing landmarks for person {person_idx + 1}: {e}")

        for idx, landmark in enumerate(pose_landmarks):
            if idx in LANDMARKS_TO_TRACK:
                try:
                    x_m = landmark.x * config.width * (WALL_WIDTH / config.width)
                    y_m = landmark.y * config.height * (WALL_HEIGHT / config.height)
                    person_positions.append([x_m, y_m])
                    draw_landmark(frame, landmark, idx, config)
                    if 디버깅:
                        draw_landmark_info(frame, person_idx + 1, idx, x_m, y_m, text_y)
                    text_y += int(30 * SCALE_FACTOR)
                except AttributeError as e:
                    print(f"Error processing landmark {idx} for person {person_idx + 1}: {e}")
        if person_positions:
            player_positions.extend(person_positions)

    return frame, text_y, player_positions

def process_landmarks(frame: np.ndarray, landmarks: list, config: CameraConfig, physics: Physics) -> tuple[np.ndarray, int, list]:
    """Process landmarks, draw ball and score."""
    frame, text_y, player_positions = draw_landmarks(frame, landmarks, config)
    if not physics.round_ended:
        draw_ball(frame, physics.ball_pos, config)
    draw_score(frame, physics.score, config)
    return frame, text_y, player_positions


class CustomPhysics(Physics):
    def __init__(self):
        super().__init__()
        self.ball_vel *= INITIAL_BALL_SPEED_SCALE  # Set initial ball speed to 0.5x
        self.ignore_collisions = False  # Flag to prevent collisions during transit
        self.target_side = None  # 'left' or 'right'
        self.round_ended = False  # Flag to indicate round has ended
        self.round_end_time = None  # Time when round ended

    def update(self, player_positions, dt):
        """Update physics with custom collision and boundary logic."""
        if self.round_ended:
            # Check if 1-second delay has passed
            if time.time() - self.round_end_time >= ROUND_END_DELAY:
                self.reset_ball()
                self.round_ended = False
                self.round_end_time = None
            return

        if not self.ignore_collisions:
            for pos in player_positions:
                if self.check_collision(self.ball_pos, pos, BALL_RADIUS, HITBOX_RADIUS):
                    self.ignore_collisions = True
                    # Move ball to opposite side with full speed
                    self.target_side = 'left' if self.ball_pos[0] > WALL_WIDTH / 2 else 'right'
                    self.ball_vel = np.array([
                        -BALL_SPEED_SCALE if self.target_side == 'left' else BALL_SPEED_SCALE,
                        random.uniform(-0.5 * BALL_SPEED_SCALE, 0.5 * BALL_SPEED_SCALE)
                    ])

        # Update ball position
        self.ball_pos += self.ball_vel * dt

        # Check boundaries
        if self.ball_pos[0] < 0:
            self.score[1] += 1  # Right player scores
            self.round_ended = True
            self.round_end_time = time.time()
        elif self.ball_pos[0] > WALL_WIDTH:
            self.score[0] += 1  # Left player scores
            self.round_ended = True
            self.round_end_time = time.time()
        elif self.ball_pos[1] < BALL_RADIUS or self.ball_pos[1] > WALL_HEIGHT - BALL_RADIUS:
            self.ball_vel[1] = -self.ball_vel[1]

        # Re-enable collisions when ball crosses center
        if self.ignore_collisions:
            if (self.target_side == 'left' and self.ball_pos[0] < WALL_WIDTH / 2) or \
               (self.target_side == 'right' and self.ball_pos[0] > WALL_WIDTH / 2):
                self.ignore_collisions = False
                self.target_side = None

    def reset_ball(self):
        """Reset ball to center with initial speed."""
        self.ball_pos = np.array([WALL_WIDTH / 2, WALL_HEIGHT / 2])
        self.ball_vel = np.array([
            random.choice([-1, 1]) * INITIAL_BALL_SPEED_SCALE,
            random.uniform(-0.5 * INITIAL_BALL_SPEED_SCALE, 0.5 * INITIAL_BALL_SPEED_SCALE)
        ])
        self.ignore_collisions = False
        self.target_side = None


def main(MAX_RECONNECT_ATTEMPTS=10):
    model_path = r"C:\Users\USER\PycharmProjects\BoulderPingPong\pose_landmarker_full.task"
    try:
        config = initialize_camera()
        landmarker = setup_pose_landmarker(model_path)
        physics = CustomPhysics()
    except Exception as e:
        print(f"Initialization error: {e}")
        return

    window_name = "Hand/Foot and Ball Tracking"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    if FULLSCREEN:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    else:
        cv2.resizeWindow(window_name, int(config.width * SCALE_FACTOR), int(config.height * SCALE_FACTOR))

    try:
        with landmarker:
            reconnect_attempts = 0
            last_update_time = time.time()
            while True:
                current_time = time.time()
                dt = current_time - last_update_time
                if dt < 1 / FPS:
                    continue
                last_update_time = current_time

                if not config.cap.isOpened():
                    if reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                        raise RuntimeError("Max reconnect attempts reached")
                    config.cap.release()
                    config = initialize_camera()
                    reconnect_attempts += 1
                    time.sleep(2)
                    continue

                # 프레임 준비
                ret, frame = config.cap.read()
                if not ret or frame is None:
                    print("Failed to capture frame")
                    reconnect_attempts += 1
                    continue

                # 프레임 리사이즈 및 패딩 추가
                if FULLSCREEN:
                    frame_height, frame_width = frame.shape[:2]
                    screen_ratio = config.screen_width / config.screen_height
                    frame_ratio = frame_width / frame_height

                    if frame_ratio > screen_ratio:
                        new_width = config.screen_width
                        new_height = int(config.screen_width / frame_ratio)
                    else:
                        new_height = config.screen_height
                        new_width = int(config.screen_height * frame_ratio)

                    frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

                    if new_width < config.screen_width or new_height < config.screen_height:
                        top = (config.screen_height - new_height) // 2
                        bottom = config.screen_height - new_height - top
                        left = (config.screen_width - new_width) // 2
                        right = config.screen_width - new_width - left
                        frame = cv2.copyMakeBorder(frame, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(0, 0, 0))
                else:
                    frame = cv2.resize(frame, (int(config.width * SCALE_FACTOR), int(config.height * SCALE_FACTOR)), interpolation=cv2.INTER_LINEAR)

                # 카메라 프레임 또는 검정색 배경 선택
                if SHOW_CAMERA_FEED:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                else:
                    frame_bgr = np.zeros((config.screen_height, config.screen_width, 3), dtype=np.uint8)

                # 랜드마크 감지
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 항상 카메라 입력 사용
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
                result = landmarker.detect_for_video(mp_image, int(time.time() * 1000))

                # 테두리와 중앙선 그리기
                draw_borders_and_center_line(frame_bgr, config)

                # 랜드마크 처리
                if result.pose_landmarks:
                    print(f"Detected {len(result.pose_landmarks)} person(s)")
                    frame_bgr, _, player_positions = process_landmarks(frame_bgr, result.pose_landmarks, config, physics)
                else:
                    print("No landmarks detected")
                    player_positions = []
                    if not physics.round_ended:
                        draw_ball(frame_bgr, physics.ball_pos, config)
                    draw_score(frame_bgr, physics.score, config)

                # 물리 업데이트
                physics.update(player_positions, 1 / FPS)

                if 좌우반전:
                    frame_flipped = cv2.flip(frame_bgr, 1)
                    cv2.imshow(window_name, frame_flipped)
                else:
                    cv2.imshow(window_name, frame_bgr)

                if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
                    break

    except Exception as e:
        print(f"Runtime error: {e}")
    finally:
        config.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()