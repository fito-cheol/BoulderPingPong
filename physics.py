import numpy as np
import random
from config import WALL_WIDTH, WALL_HEIGHT, BALL_RADIUS, HITBOX_RADIUS, INITIAL_BALL_SPEED_SCALE, BALL_SPEED_SCALE, ROUND_END_DELAY

class Physics:
    def __init__(self):
        self.ball_pos = np.array([WALL_WIDTH / 2, WALL_HEIGHT / 2], dtype=float)
        self.ball_vel = np.array([random.choice([-1, 1]) * INITIAL_BALL_SPEED_SCALE, random.uniform(-0.5 * INITIAL_BALL_SPEED_SCALE, 0.5 * INITIAL_BALL_SPEED_SCALE)], dtype=float)
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

        if not self.ignore_collisions:
            for pos in player_positions:
                if self.check_collision(self.ball_pos, pos, BALL_RADIUS, HITBOX_RADIUS):
                    self.ignore_collisions = True
                    self.target_side = 'left' if self.ball_pos[0] > WALL_WIDTH / 2 else 'right'
                    self.ball_vel = np.array([
                        -BALL_SPEED_SCALE if self.target_side == 'left' else BALL_SPEED_SCALE,
                        random.uniform(-0.5 * BALL_SPEED_SCALE, 0.5 * BALL_SPEED_SCALE)
                    ])

        self.ball_pos += self.ball_vel * dt

        if self.ball_pos[0] < 0:
            self.score[1] += 1
            self.round_ended = True
            self.round_end_time = time.time()
        elif self.ball_pos[0] > WALL_WIDTH:
            self.score[0] += 1
            self.round_ended = True
            self.round_end_time = time.time()
        elif self.ball_pos[1] < BALL_RADIUS or self.ball_pos[1] > WALL_HEIGHT - BALL_RADIUS:
            self.ball_vel[1] = -self.ball_vel[1]

        if self.ignore_collisions:
            if (self.target_side == 'left' and self.ball_pos[0] < WALL_WIDTH / 2) or \
               (self.target_side == 'right' and self.ball_pos[0] > WALL_WIDTH / 2):
                self.ignore_collisions = False
                self.target_side = None

    def reset_ball(self):
        """공을 중앙으로 리셋"""
        self.ball_pos = np.array([WALL_WIDTH / 2, WALL_HEIGHT / 2])
        self.ball_vel = np.array([
            random.choice([-1, 1]) * INITIAL_BALL_SPEED_SCALE,
            random.uniform(-0.5 * INITIAL_BALL_SPEED_SCALE, 0.5 * INITIAL_BALL_SPEED_SCALE)
        ])
        self.ignore_collisions = False
        self.target_side = None