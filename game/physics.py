import numpy as np
import random
import config
from config import INITIAL_BALL_SPEED_SCALE, BALL_SPEED_SCALE, ROUND_END_DELAY
import time
import pygame

MAX_SCREEN = 1

class Physics:
    def __init__(self):
        self.reset_ball()
        self.score = [0, 0]
        self.ignore_collisions = False
        self.target_side = None
        self.round_ended = False
        self.round_end_time = None
        self.ball_trail = []  # Store previous ball positions for trailing effect
        self.goal_scored = False  # Flag for goal event
        pygame.mixer.init()  # Initialize pygame mixer for sound
        self.collision_sound = None
        try:
            self.collision_sound = pygame.mixer.Sound('assets/332058__qubodup__collision.flac')
        except FileNotFoundError:
            print("Collision sound file not found at 'assets/332058__qubodup__collision.wav'. Please add it later.")

    def check_collision(self, ball_pos, hit_pos, hit_radius):
        """공과 히트박스 간 충돌 감지"""
        distance = np.linalg.norm(ball_pos - np.array(hit_pos))
        return distance < hit_radius

    def update(self, player_positions, dt):
        """물리 상태 업데이트"""
        if self.round_ended:
            if time.time() - self.round_end_time >= ROUND_END_DELAY:
                self.reset_ball()
                self.round_ended = False
                self.round_end_time = None
                self.goal_scored = False
            return

        """ 공과 사람 충돌 처리 """

        if self.ignore_collisions:
            ball_on_next_side = (self.target_side == 'left' and self.ball_pos[0] < MAX_SCREEN / 2) or \
                                (self.target_side == 'right' and self.ball_pos[0] > MAX_SCREEN / 2)

            if ball_on_next_side:
                self.ignore_collisions = False
                self.target_side = None
        else:
            self.handle_player_ball_collision(player_positions)


        """ 공 위치 업데이트 """
        self.ball_pos += self.ball_vel * dt

        """ 공 trail 업데이트 """
        self.ball_trail.append(self.ball_pos.copy())
        if len(self.ball_trail) > 10:
            self.ball_trail.pop(0)

        """ 공과 벽 충돌 처리 """
        self.handle_wall_ball_collision()

    def handle_wall_ball_collision(self):
        is_touch_left = self.ball_pos[0] < 0
        is_touch_right = self.ball_pos[0] > 1
        is_touch_bottom = self.ball_pos[1] < config.BALL_RADIUS_RATIO
        is_touch_top = self.ball_pos[1] > 1 - config.BALL_RADIUS_RATIO
        
        if is_touch_left:
            self.score[1] += 1
            self.round_ended = True
            self.round_end_time = time.time()
            self.goal_scored = True  # Trigger screen shake
        elif is_touch_right:
            self.score[0] += 1
            self.round_ended = True
            self.round_end_time = time.time()
            self.goal_scored = True  # Trigger screen shake
        elif is_touch_bottom or is_touch_top:
            self.ball_vel[1] = -self.ball_vel[1]

    def handle_player_ball_collision(self, player_positions):
        for pos in player_positions:
            if self.check_collision(self.ball_pos, pos, config.BALL_RADIUS_RATIO):
                self.ignore_collisions = True
                self.target_side = 'left' if self.ball_pos[0] > 1 / 2 else 'right'
                self.ball_vel = np.array([
                    -BALL_SPEED_SCALE if self.target_side == 'left' else BALL_SPEED_SCALE,
                    random.uniform(-0.5 * BALL_SPEED_SCALE, 0.5 * BALL_SPEED_SCALE)
                ])
                # Play collision sound
                if self.collision_sound:
                    self.collision_sound.play()
                break

    def reset_ball(self):
        """공을 중앙으로 리셋"""
        self.ball_pos = np.array([MAX_SCREEN / 2, MAX_SCREEN / 2], dtype=float)
        self.ball_vel = np.array([
            random.choice([-1, 1]) * INITIAL_BALL_SPEED_SCALE,
            random.uniform(-0.5 * INITIAL_BALL_SPEED_SCALE, 0.5 * INITIAL_BALL_SPEED_SCALE)
        ], dtype=float)
        self.ignore_collisions = False
        self.target_side = None
        self.ball_trail = []  # Clear trail on reset
        self.goal_scored = False

    def reset_game(self):
        """게임 전체를 재시작"""
        self.score = [0, 0]
        self.reset_ball()
        self.round_ended = False
        self.round_end_time = None
        self.goal_scored = False