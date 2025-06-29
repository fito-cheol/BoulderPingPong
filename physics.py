import numpy as np
import random
from config import WALL_WIDTH, WALL_HEIGHT, BALL_RADIUS, HITBOX_RADIUS, GOAL_WIDTH, GOAL_HEIGHT, GOAL_Y

class Physics:
    def __init__(self):
        self.ball_pos = np.array([WALL_WIDTH / 2, WALL_HEIGHT / 2], dtype=float)
        self.ball_vel = np.array([random.choice([-1, 1]) * 1.0, random.uniform(-0.5, 0.5)], dtype=float)
        self.score = [0, 0]

    def check_collision(self, ball_pos, hit_pos, ball_radius, hit_radius):
        """공과 히트박스 간 충돌 감지"""
        distance = np.linalg.norm(ball_pos - np.array(hit_pos))
        return distance < (ball_radius + hit_radius)

    def reflect_velocity(self, ball_vel, hit_pos, ball_pos):
        """공 반사 계산"""
        normal = ball_pos - np.array(hit_pos)
        normal = normal / (np.linalg.norm(normal) + 1e-6)
        dot = np.dot(ball_vel, normal)
        return ball_vel - 2 * dot * normal

    def update(self, player_positions, dt):
        """물리 상태 업데이트"""
        # 손/발 충돌
        for pos in player_positions:
            if self.check_collision(self.ball_pos, pos, BALL_RADIUS, HITBOX_RADIUS):
                self.ball_vel = self.reflect_velocity(self.ball_vel, pos, self.ball_pos)

        # 벽 경계 충돌
        if self.ball_pos[0] < BALL_RADIUS or self.ball_pos[0] > WALL_WIDTH - BALL_RADIUS:
            self.ball_vel[0] = -self.ball_vel[0]
        if self.ball_pos[1] < BALL_RADIUS or self.ball_pos[1] > WALL_HEIGHT - BALL_RADIUS:
            self.ball_vel[1] = -self.ball_vel[1]

        # 골대 충돌
        if self.ball_pos[0] < GOAL_WIDTH and GOAL_Y < self.ball_pos[1] < GOAL_Y + GOAL_HEIGHT:
            self.score[1] += 1
            self.ball_pos = np.array([WALL_WIDTH / 2, WALL_HEIGHT / 2])
            self.ball_vel = np.array([random.choice([-1, 1]) * 1.0, random.uniform(-0.5, 0.5)])
        elif self.ball_pos[0] > WALL_WIDTH - GOAL_WIDTH and GOAL_Y < self.ball_pos[1] < GOAL_Y + GOAL_HEIGHT:
            self.score[0] += 1
            self.ball_pos = np.array([WALL_WIDTH / 2, WALL_HEIGHT / 2])
            self.ball_vel = np.array([random.choice([-1, 1]) * 1.0, random.uniform(-0.5, 0.5)])

        self.ball_pos += self.ball_vel * dt