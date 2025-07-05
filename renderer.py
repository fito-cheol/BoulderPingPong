import pygame
import numpy as np
import cv2
from config import WALL_WIDTH, WALL_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT, BALL_RADIUS, HITBOX_RADIUS, SCALE_FACTOR, COLORS

class Renderer:
    def __init__(self, homography):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        self.font = pygame.font.Font(None, int(36 * SCALE_FACTOR))
        self.homography = homography

    def transform_coordinates(self, points):
        """호모그래피를 사용해 좌표 변환"""
        points = np.array(points, dtype=np.float32)
        if points.ndim == 1:
            points = points.reshape(1, -1, 2)
        transformed = cv2.perspectiveTransform(points, self.homography)
        return transformed.reshape(-1, 2)

    def draw_borders_and_center_line(self):
        """테두리와 중앙선 그리기"""
        border_thickness = int(10 * SCALE_FACTOR)
        center_line_thickness = int(5 * SCALE_FACTOR)
        alpha = 0.5
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # 상단 테두리
        pygame.draw.rect(overlay, COLORS['top_bottom_border'], (0, 0, SCREEN_WIDTH, border_thickness))
        # 하단 테두리
        pygame.draw.rect(overlay, COLORS['top_bottom_border'], (0, SCREEN_HEIGHT - border_thickness, SCREEN_WIDTH, border_thickness))
        # 왼쪽 테두리
        pygame.draw.rect(overlay, COLORS['left_border'], (0, 0, border_thickness, SCREEN_HEIGHT))
        # 오른쪽 테두리
        pygame.draw.rect(overlay, COLORS['right_border'], (SCREEN_WIDTH - border_thickness, 0, border_thickness, SCREEN_HEIGHT))
        # 중앙선 (점선)
        center_x = SCREEN_WIDTH // 2
        dash_length = int(20 * SCALE_FACTOR)
        gap_length = int(10 * SCALE_FACTOR)
        y = 0
        while y < SCREEN_HEIGHT:
            pygame.draw.line(overlay, COLORS['center_line'], (center_x, y), (center_x, min(y + dash_length, SCREEN_HEIGHT)), center_line_thickness法

System: The response was cut off due to exceeding the token limit. Below is the continuation and completion of the changes to the `renderer.py` file, along with the remaining files (`camera.py`, `config.py`, `game.py`, `main.py`) to fully reflect the functionality from `test_game.py`. I'll also ensure that the `.gitignore` and `requirements.txt` artifacts are not duplicated, as they were already provided.

### Continuation of `renderer.py`
The `renderer.py` file is updated to incorporate the border and center line drawing, score display, and color configurations from `test_game.py`. The `draw_borders_and_center_line` function is adapted to use Pygame's drawing methods with semi-transparent overlays.

<xaiArtifact artifact_id="2ec49ca7-4475-4f6b-b353-7e8fa0212042" artifact_version_id="89b3800e-7a48-40ec-ad56-f4a99e21f884" title="renderer.py" contentType="text/python">
import pygame
import numpy as np
import cv2
from config import WALL_WIDTH, WALL_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT, BALL_RADIUS, HITBOX_RADIUS, SCALE_FACTOR, COLORS

class Renderer:
    def __init__(self, homography):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        self.font = pygame.font.Font(None, int(36 * SCALE_FACTOR))
        self.homography = homography

    def transform_coordinates(self, points):
        """호모그래피를 사용해 좌표 변환"""
        points = np.array(points, dtype=np.float32)
        if points.ndim == 1:
            points = points.reshape(1, -1, 2)
        transformed = cv2.perspectiveTransform(points, self.homography)
        return transformed.reshape(-1, 2)

    def draw_borders_and_center_line(self):
        """테두리와 중앙선 그리기"""
        border_thickness = int(10 * SCALE_FACTOR)
        center_line_thickness = int(5 * SCALE_FACTOR)
        alpha = 0.5
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # 상단 테두리
        pygame.draw.rect(overlay, COLORS['top_bottom_border'], (0, 0, SCREEN_WIDTH, border_thickness))
        # 하단 테두리
        pygame.draw.rect(overlay, COLORS['top_bottom_border'], (0, SCREEN_HEIGHT - border_thickness, SCREEN_WIDTH, border_thickness))
        # 왼쪽 테두리
        pygame.draw.rect(overlay, COLORS['left_border'], (0, 0, border_thickness, SCREEN_HEIGHT))
        # 오른쪽 테두리
        pygame.draw.rect(overlay, COLORS['right_border'], (SCREEN_WIDTH - border_thickness, 0, border_thickness, SCREEN_HEIGHT))
        # 중앙선 (점선)
        center_x = SCREEN_WIDTH // 2
        dash_length = int(20 * SCALE_FACTOR)
        gap_length = int(10 * SCALE_FACTOR)
        y = 0
        while y < SCREEN_HEIGHT:
            pygame.draw.line(overlay, COLORS['center_line'], (center_x, y), (center_x, min(y + dash_length, SCREEN_HEIGHT)), center_line_thickness)
            y += dash_length + gap_length

        # 투명도 적용
        self.screen.blit(overlay, (0, 0))

    def render(self, ball_pos, player_positions, score):
        self.screen.fill((0, 0, 0))
        self.draw_borders_and_center_line()

        # 공 그리기
        ball_screen = self.transform_coordinates(ball_pos)
        ball_radius_pixel = int(BALL_RADIUS * SCREEN_WIDTH / WALL_WIDTH)
        border_thickness = max(1, int(ball_radius_pixel * 0.1))
        pygame.draw.circle(self.screen, COLORS['ball'], (int(ball_screen[0, 0]), int(ball_screen[0, 1])), ball_radius_pixel)
        pygame.draw.circle(self.screen, COLORS['ball_border'], (int(ball_screen[0, 0]), int(ball_screen[0, 1])), ball_radius_pixel, border_thickness)

        # 손/발 그리기
        for pos in player_positions:
            screen_pos = self.transform_coordinates(pos)
            color = COLORS['hand'] if pos in player_positions[:2] else COLORS['foot']  # Assuming first two positions are hands
            pygame.draw.circle(self.screen, color, (int(screen_pos[0, 0]), int(screen_pos[0, 1])), int(HITBOX_RADIUS * SCREEN_WIDTH / WALL_WIDTH))

        # 점수 표시
        score_text = self.font.render(f"{score[0]} : {score[1]}", True, COLORS['score'])
        text_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, int(50 * SCALE_FACTOR)))
        self.screen.blit(score_text, text_rect)

        pygame.display.flip()

    def quit(self):
        pygame.quit()