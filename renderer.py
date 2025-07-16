import pygame
import numpy as np
import cv2
from typing import Tuple, List, Union
# 변경되는 변수는 직접 import config.WALL_WIDTH, config.WALL_HEIGHT, config.FOCUS_X, config.FOCUS_Y
import config
from config import SCREEN_WIDTH, SCREEN_HEIGHT, BALL_RADIUS, HITBOX_RADIUS, SCALE_FACTOR, \
    COLORS



# 상수 정의
BORDER_THICKNESS = int(10 * SCALE_FACTOR)  # 테두리 두께
CENTER_LINE_THICKNESS = int(5 * SCALE_FACTOR)  # 중앙선 두께
DASH_LENGTH = int(20 * SCALE_FACTOR)  # 중앙선 대시 길이
GAP_LENGTH = int(10 * SCALE_FACTOR)  # 중앙선 대시 간격
FONT_SIZE = int(36 * SCALE_FACTOR)  # 폰트 크기
BALL_BORDER_RATIO = 0.1  # 공 테두리 비율
SCORE_Y_OFFSET = int(50 * SCALE_FACTOR)  # 점수 텍스트 Y 오프셋
WARNING_Y_OFFSET = 50  # 경고 텍스트 Y 오프셋
KEY_STATUS_Y_OFFSET = int(50 * SCALE_FACTOR)  # 키 상태 텍스트 Y 오프셋

class Renderer:
    def __init__(self, homography: np.ndarray, camera):
        """렌더러 초기화: 화면, 폰트, 호모그래피 설정"""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        self.font = pygame.font.Font(None, FONT_SIZE)
        self.homography = homography
        self.use_homography = homography is not None
        self.camera = camera
        self.show_camera = False
        self.key_states = {
            'w': False, 's': False, 'a': False, 'd': False,
            'up': False, 'down': False, 'left': False, 'right': False
        }

    def update_key_state(self, key: int, state: bool) -> None:
        """키 상태를 업데이트"""
        key_map = {
            pygame.K_w: 'w', pygame.K_s: 's', pygame.K_a: 'a', pygame.K_d: 'd',
            pygame.K_UP: 'up', pygame.K_DOWN: 'down', pygame.K_LEFT: 'left', pygame.K_RIGHT: 'right'
        }
        if key in key_map:
            self.key_states[key_map[key]] = state

    def toggle_camera(self) -> None:
        """카메라 화면 표시 상태를 토글"""
        self.show_camera = not self.show_camera
        print(f"카메라 화면 {'표시' if self.show_camera else '숨김'}")

    def transform_coordinates(self, points: Union[np.ndarray, List[float]]) -> np.ndarray:
        """ 호모그래피 사용하지 않고 단순 변환 """
        return self.simple_transform(points)
        #
        # """호모그래피와 초점 오프셋을 사용해 좌표 변환"""
        # if not self.use_homography:
        #     return self.simple_transform(points)
        #
        # try:
        #     points = np.array(points, dtype=np.float32)
        #     if points.ndim == 1:
        #         points = points.reshape(1, -1)
        #     if points.shape[1] != 2:
        #         points = points.reshape(1, 2)
        #
        #     points = points - np.array([config.FOCUS_X, config.FOCUS_Y])
        #     points_homogeneous = np.column_stack([points, np.ones(points.shape[0])])
        #     transformed_homogeneous = self.homography @ points_homogeneous.T2
        #     transformed = transformed_homogeneous[:2] / transformed_homogeneous[2]
        #     return transformed.T
        #
        # except Exception as e:
        #     print(f"호모그래피 변환 실패: {e}, 기본 변환 사용")
        #     return self.simple_transform(points)

    def simple_transform(self, points: Union[np.ndarray, List[float]]) -> np.ndarray:
        """호모그래피 없이 기본 선형 변환 적용"""
        points = np.array(points, dtype=np.float32)
        if points.ndim == 1:
            points = points.reshape(1, -1)
        points = points - np.array([config.FOCUS_X, config.FOCUS_Y])
        scale_x = SCREEN_WIDTH
        scale_y = SCREEN_HEIGHT
        return points * np.array([scale_x, scale_y])

    def draw_borders_and_center_line(self) -> None:
        """테두리와 점선 중앙선 그리기"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # 상단 및 하단 테두리
        pygame.draw.rect(overlay, COLORS['top_bottom_border'], (0, 0, SCREEN_WIDTH, BORDER_THICKNESS))
        pygame.draw.rect(overlay, COLORS['top_bottom_border'],
                         (0, SCREEN_HEIGHT - BORDER_THICKNESS, SCREEN_WIDTH, BORDER_THICKNESS))
        # 좌측 및 우측 테두리
        pygame.draw.rect(overlay, COLORS['left_border'], (0, 0, BORDER_THICKNESS, SCREEN_HEIGHT))
        pygame.draw.rect(overlay, COLORS['right_border'],
                         (SCREEN_WIDTH - BORDER_THICKNESS, 0, BORDER_THICKNESS, SCREEN_HEIGHT))
        # 중앙 점선
        center_x = SCREEN_WIDTH // 2
        y = 0
        while y < SCREEN_HEIGHT:
            pygame.draw.line(overlay, COLORS['center_line'], (center_x, y),
                             (center_x, min(y + DASH_LENGTH, SCREEN_HEIGHT)), CENTER_LINE_THICKNESS)
            y += DASH_LENGTH + GAP_LENGTH

        self.screen.blit(overlay, (0, 0))

    def render(self, ball_pos: List[float], player_positions: List[List[float]], score: Tuple[int, int]) -> None:
        """게임 화면 렌더링: 배경, 테두리, 공, 플레이어, 점수, 키 상태"""
        # 카메라 프레임 렌더링
        print(config.WALL_WIDTH, config.WALL_HEIGHT)
        if self.show_camera:
            frame = self.camera.get_frame()
            if frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (config.WALL_WIDTH, config.WALL_HEIGHT))
                frame_surface = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
                self.screen.blit(frame_surface, (config.FOCUS_X, config.FOCUS_Y))
            else:
                self.screen.fill((0, 0, 0))
        else:
            self.screen.fill((0, 0, 0))

        # 테두리 중앙 그리기
        self.draw_borders_and_center_line()

        # 공 그리기
        try:
            ball_screen = self.transform_coordinates(ball_pos)
            if ball_screen.shape[0] > 0:
                ball_radius_pixel = int(BALL_RADIUS * SCREEN_WIDTH)
                border_thickness = max(1, int(ball_radius_pixel * BALL_BORDER_RATIO))
                x, y = int(ball_screen[0, 0]), int(ball_screen[0, 1])
                if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                    pygame.draw.circle(self.screen, COLORS['ball'], (x, y), ball_radius_pixel)
                    pygame.draw.circle(self.screen, COLORS['ball_border'], (x, y), ball_radius_pixel, border_thickness)
        except Exception as e:
            print(f"공 렌더링 오류: {e}")

        # 플레이어(손/발) 그리기
        try:
            for i, pos in enumerate(player_positions):
                screen_pos = self.transform_coordinates(pos)
                if screen_pos.shape[0] > 0:
                    color = COLORS['hand'] if i < 2 else COLORS['foot']
                    radius = int(HITBOX_RADIUS * SCREEN_WIDTH )
                    x, y = int(screen_pos[0, 0]), int(screen_pos[0, 1])
                    if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                        pygame.draw.circle(self.screen, color, (x, y), radius)
        except Exception as e:
            print(f"플레이어 렌더링 오류: {e}")

        # 점수 표시
        try:
            score_text = self.font.render(f"{score[0]} : {score[1]}", True, COLORS['score'])
            text_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCORE_Y_OFFSET))
            self.screen.blit(score_text, text_rect)
        except Exception as e:
            print(f"점수 렌더링 오류: {e}")

        # 키 입력 상태 표시
        try:
            key_status_text = " ".join(key.upper() for key, state in self.key_states.items() if state)
            if key_status_text:
                key_text = self.font.render(f"키: {key_status_text}", True, (255, 255, 255))
                key_rect = key_text.get_rect(topleft=(10, SCREEN_HEIGHT - KEY_STATUS_Y_OFFSET))
                self.screen.blit(key_text, key_rect)
        except Exception as e:
            print(f"키 상태 렌더링 오류: {e}")

        pygame.display.flip()

    def quit(self) -> None:
        """렌더러 종료 및 Pygame 정리"""
        pygame.quit()