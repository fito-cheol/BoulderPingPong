WALL_WIDTH = 3.66
WALL_HEIGHT = 3.66
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 30
BALL_RADIUS = 0.1
HITBOX_RADIUS = 0.06
GOAL_WIDTH = 0.2
GOAL_HEIGHT = 1.0
GOAL_Y = (WALL_HEIGHT - GOAL_HEIGHT) / 2
CHESSBOARD_SIZE = (8, 8)
SQUARE_SIZE = 0.3
LANDMARKS_TO_TRACK = {15, 16, 27, 28}
MAX_RECONNECT_ATTEMPTS = 5
SCALE_FACTOR = 2.0
BALL_SPEED_SCALE = 2.0
INITIAL_BALL_SPEED_SCALE = 0.5
ROUND_END_DELAY = 1.0
FULLSCREEN=True
FOCUS_X = 0.0  # 초점의 x 오프셋 (미터 단위)
FOCUS_Y = 0.0  # 초점의 y 오프셋 (미터 단위)
WIDTH_ADJUST_STEP = 0.1  # 좌우폭 조절 단위 (미터)
HEIGHT_ADJUST_STEP = 0.1  # 상하폭 조절 단위 (미터)
FOCUS_ADJUST_STEP = 0.1  # 초점 이동 단위 (미터)
COLORS = {
    'hand': (0, 0, 255),
    'foot': (0, 220, 220),
    'ball': (255, 255, 255),
    'ball_border': (0, 0, 0),
    'score': (120, 255, 120),
    'text': (0, 255, 0),
    'landmark_default': (255, 255, 255),
    'connection': (0, 255, 255),
    'left_border': (0, 0, 255),
    'right_border': (255, 0, 0),
    'top_bottom_border': (255, 255, 255),
    'center_line': (255, 255, 255)
}