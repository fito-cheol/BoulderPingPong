import pygame
import numpy as np
from config import WALL_WIDTH, WALL_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT, BALL_RADIUS, HITBOX_RADIUS, GOAL_WIDTH, GOAL_HEIGHT, GOAL_Y

class Renderer:
    def __init__(self, homography):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        self.font = pygame.font.Font(None, 36)
        self.homography = homography

    def transform_coordinates(self, points):
        """호모그래피를 사용해 좌표 변환"""
        points = np.array(points, dtype=np.float32)
        if points.ndim == 1:
            points = points.reshape(1, -1, 2)
        transformed = cv2.perspectiveTransform(points, self.homography)
        return transformed.reshape(-1, 2)

    def render(self, ball_pos, player_positions, score):
        self.screen.fill((0, 0, 0))

        # 공 그리기
        ball_screen = self.transform_coordinates(ball_pos)
        pygame.draw.circle(self.screen, (255, 255, 255),
                          (int(ball_screen[0, 0]), int(ball_screen[0, 1])),
                          int(BALL_RADIUS * SCREEN_WIDTH / WALL_WIDTH))

        # 손/발 그리기
        for pos in player_positions:
            screen_pos = self.transform_coordinates(pos)
            pygame.draw.circle(self.screen, (0, 0, 255),
                              (int(screen_pos[0, 0]), int(screen_pos[0, 1])),
                              int(HITBOX_RADIUS * SCREEN_WIDTH / WALL_WIDTH))

        # 골대 그리기
        goal_corners = np.array([
            [0, GOAL_Y], [GOAL_WIDTH, GOAL_Y],
            [GOAL_WIDTH, GOAL_Y + GOAL_HEIGHT], [0, GOAL_Y + GOAL_HEIGHT]
        ])
        goal_screen = self.transform_coordinates(goal_corners)
        pygame.draw.polygon(self.screen, (255, 0, 0), goal_screen)
        goal_corners_right = np.array([
            [WALL_WIDTH - GOAL_WIDTH, GOAL_Y], [WALL_WIDTH, GOAL_Y],
            [WALL_WIDTH, GOAL_Y + GOAL_HEIGHT], [WALL_WIDTH - GOAL_WIDTH, GOAL_Y + GOAL_HEIGHT]
        ])
        goal_screen_right = self.transform_coordinates(goal_corners_right)
        pygame.draw.polygon(self.screen, (255, 0, 0), goal_screen_right)

        # 점수 표시
        score_text = self.font.render(f"{score[0]} : {score[1]}", True, (255, 255, 255))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - 50, 20))

        pygame.display.flip()

    def quit(self):
        pygame.quit()