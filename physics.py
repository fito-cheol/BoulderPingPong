import numpy as np
import random
from config import WALL_WIDTH, WALL_HEIGHT, BALL_RADIUS, HITBOX_RADIUS, INITIAL_BALL_SPEED_SCALE, BALL_SPEED_SCALE, ROUND_END_DELAY
import time

class Physics:
    def __init__(self):
        self.reset_ball()
        self.score = [0, 0]
        self.ignore_collisions = False
        self.target_side = None
        self.round_ended = False
        self.round_end_time = None

    def check_collision(self, ball_pos, hit_pos, ball_radius, hit_radius):
        """공과 히트박스 간 충돌 감지"""
        distance = np.linalg.norm(ball_pos - np.array(hit_pos))
        return distance < (ball_radius + hit_radius)

    def update(self, player_positions, dt):
        """물리 상태 업데이트"""
        if self.round_ended:
            if time.time() - self.round_end_time >= ROUND_END_DELAY:
                self.reset_ball()
                self.round_ended = False
                self.round_end_time = None
            return

        """ 공과 사람 충돌 처리 """
        if not self.ignore_collisions:
            for pos in player_positions:
                if self.check_collision(self.ball_pos, pos, BALL_RADIUS, HITBOX_RADIUS):
                    self.ignore_collisions = True
                    self.target_side = 'left' if self.ball_pos[0] > WALL_WIDTH / 2 else 'right'
                    self.ball_vel = np.array([
                        -BALL_SPEED_SCALE if self.target_side == 'left' else BALL_SPEED_SCALE,
                        random.uniform(-0.5 * BALL_SPEED_SCALE, 0.5 * BALL_SPEED_SCALE)
                    ])
                    break

        """ 공 위치 업데이트 """
        self.ball_pos += self.ball_vel * dt

        """ 공과 벽 충돌 처리 """
        isTouchLeft = self.ball_pos[0] < 0
        isTouchRight = self.ball_pos[0] > WALL_WIDTH
        isTouchBottom = self.ball_pos[1] < BALL_RADIUS
        isTouchTop = self.ball_pos[1] > WALL_HEIGHT - BALL_RADIUS

        if isTouchLeft:
            self.score[1] += 1
            self.round_ended = True
            self.round_end_time = time.time()
        elif isTouchRight:
            self.score[0] += 1
            self.round_ended = True
            self.round_end_time = time.time()
        elif isTouchBottom or isTouchTop:
            self.ball_vel[1] = -self.ball_vel[1]

        if self.ignore_collisions:
            if (self.target_side == 'left' and self.ball_pos[0] < WALL_WIDTH / 2) or \
               (self.target_side == 'right' and self.ball_pos[0] > WALL_WIDTH / 2):
                self.ignore_collisions = False
                self.target_side = None

    def reset_ball(self):
        """공을 중앙으로 리셋"""
        self.ball_pos = np.array([WALL_WIDTH / 2, WALL_HEIGHT / 2], dtype=float)
        self.ball_vel = np.array([
            random.choice([-1, 1]) * INITIAL_BALL_SPEED_SCALE,
            random.uniform(-0.5 * INITIAL_BALL_SPEED_SCALE, 0.5 * INITIAL_BALL_SPEED_SCALE)
        ], dtype=float)
        self.ignore_collisions = False
        self.target_side = None


    def reset_game(self):
        """게임 전체를 재시작"""
        self.score = [0, 0]
        self.reset_ball()
        self.round_ended = False
        self.round_end_time = None