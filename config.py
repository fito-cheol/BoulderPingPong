import math

FPS = 60

MAGNIFY_WALL_RATIO = 1.5
MAGNIFY_FOCUS_RATIO = (MAGNIFY_WALL_RATIO - 1) * 0.5

FULLSCREEN = True

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 1024

WALL_WIDTH = 1280
WALL_HEIGHT = 1024
FOCUS_X = 0
FOCUS_Y = 0

WIDTH_ADJUST_STEP = math.floor(SCREEN_WIDTH * 0.05)  # 좌우폭 조절 단위
HEIGHT_ADJUST_STEP = math.floor(SCREEN_HEIGHT * 0.05)  # 상하폭 조절 단위
FOCUS_ADJUST_STEP = math.floor(SCREEN_HEIGHT * 0.05)  # 초점 이동 단위

BALL_RADIUS_RATIO = 1 / 20
BALL_RADIUS = math.floor(BALL_RADIUS_RATIO * SCREEN_HEIGHT)
HITBOX_RADIUS = BALL_RADIUS
HAND_RADIUS_RATIO = 1 / 20
HAND_RADIUS = math.floor(HAND_RADIUS_RATIO * SCREEN_HEIGHT)

BALL_SPEED_SCALE = 0.35
INITIAL_BALL_SPEED_SCALE = 0.2
ROUND_END_DELAY = 2.5

GOAL_WIDTH = 0.2
GOAL_HEIGHT = 1.0
GOAL_Y = (WALL_HEIGHT - GOAL_HEIGHT) / 2

CHESSBOARD_SIZE = (8, 8)
SQUARE_SIZE = 0.3

MAX_RECONNECT_ATTEMPTS = 5
SCALE_FACTOR = 2.0

COLORS = {
    'hand': (0, 0, 255),
    'foot': (0, 220, 220),
    'ball': (255, 255, 255),
    'ball_border': (0, 0, 0),
    'score': (200, 255, 170),
    'text': (0, 255, 0),
    'landmark_default': (255, 255, 255),
    'connection': (0, 255, 255),
    'left_border': (0, 0, 255),
    'right_border': (255, 0, 0),
    'top_bottom_border': (255, 255, 255),
    'center_line': (255, 255, 255)
}