import pygame
import numpy as np
import cv2
from typing import Tuple, List, Union
import config
from config import SCREEN_WIDTH, SCREEN_HEIGHT, BALL_RADIUS, SCALE_FACTOR, \
    COLORS, HAND_RADIUS
import time
import random

# 상수 정의
BORDER_THICKNESS = int(10 * SCALE_FACTOR)  # 테두리 두께 (픽셀)
CENTER_LINE_THICKNESS = int(5 * SCALE_FACTOR)  # 중앙선 두께 (픽셀)
DASH_LENGTH = int(20 * SCALE_FACTOR)  # 중앙선 대시 길이 (픽셀)
GAP_LENGTH = int(10 * SCALE_FACTOR)  # 중앙선 대시 간격 (픽셀)
FONT_SIZE = int(36 * SCALE_FACTOR)  # 폰트 크기 (픽셀)
BALL_BORDER_RATIO = 0.1  # 공 테두리 비율
SCORE_Y_OFFSET = int(50 * SCALE_FACTOR)  # 점수 텍스트 Y 오프셋 (픽셀)
WARNING_Y_OFFSET = 50  # 경고 텍스트 Y 오프셋 (픽셀)
KEY_STATUS_Y_OFFSET = int(50 * SCALE_FACTOR)  # 키 상태 텍스트 Y 오프셋 (픽셀)
SHAKE_DURATION = 2.0  # 화면 흔들림 지속 시간 (초)
SHAKE_MAGNITUDE = 10  # 화면 흔들림 최대 오프셋 (픽셀)

class Renderer:
    """게임 화면을 렌더링하는 클래스"""
    def __init__(self, homography: np.ndarray, camera):
        """렌더러 초기화: 화면, 폰트, 호모그래피, 카메라 설정"""
        try:
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
            self.shake_start_time = None
            self.shake_offset = (0, 0)
        except Exception as e:
            print(f"렌더러 초기화 중 오류: {e}")
            raise

    def update_key_state(self, key: int, state: bool) -> None:
        """키 입력 상태 업데이트"""
        try:
            key_map = {
                pygame.K_w: 'w', pygame.K_s: 's', pygame.K_a: 'a', pygame.K_d: 'd',
                pygame.K_UP: 'up', pygame.K_DOWN: 'down', pygame.K_LEFT: 'left', pygame.K_RIGHT: 'right'
            }
            if key in key_map:
                self.key_states[key_map[key]] = state
        except Exception as e:
            print(f"키 상태 업데이트 중 오류: {e}")

    def toggle_camera(self) -> None:
        """카메라 화면 표시 상태 토글"""
        try:
            self.show_camera = not self.show_camera
            print(f"카메라 화면 {'표시' if self.show_camera else '숨김'}")
        except Exception as e:
            print(f"카메라 토글 중 오류: {e}")

    def transform_coordinates(self, points: Union[np.ndarray, List[float]]) -> np.ndarray:
        """좌표 변환 (호모그래피 미사용, 단순 변환)"""
        try:
            return self.simple_transform(points)
        except Exception as e:
            print(f"좌표 변환 중 오류: {e}")
            return np.array([])

    def simple_transform(self, points: Union[np.ndarray, List[float]]) -> np.ndarray:
        """단순 좌표 변환"""
        try:
            points = np.array(points, dtype=np.float32)
            if points.ndim == 1:
                points = points.reshape(1, -1)
            return points
        except Exception as e:
            print(f"단순 좌표 변환 중 오류: {e}")
            return np.array([])

    def transform_ball(self, points: Union[np.ndarray, List[float]]) -> np.ndarray:
        """공의 좌표를 화면 좌표로 변환"""
        try:
            points = np.array(points, dtype=np.float32)
            if points.ndim == 1:
                points = points.reshape(1, -1)
            scale_x = SCREEN_WIDTH
            scale_y = SCREEN_HEIGHT
            return points * np.array([scale_x, scale_y])
        except Exception as e:
            print(f"공 좌표 변환 중 오류: {e}")
            return np.array([])

    def transform_player(self, points: Union[np.ndarray, List[float]]) -> np.ndarray:
        """플레이어 좌표를 화면 좌표로 변환"""
        try:
            points = np.array(points, dtype=np.float32)
            if points.ndim == 1:
                points = points.reshape(1, -1)
            scale_x = config.WALL_WIDTH
            scale_y = config.WALL_HEIGHT
            return points * np.array([scale_x, scale_y]) + np.array([config.FOCUS_X, config.FOCUS_Y])
        except Exception as e:
            print(f"플레이어 좌표 변환 중 오류: {e}")
            return np.array([])

    def draw_borders_and_center_line(self, shake_offset: Tuple[int, int]) -> None:
        """테두리와 점선 중앙선 그리기"""
        try:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            offset_x, offset_y = shake_offset

            # 상단 및 하단 테두리
            pygame.draw.rect(overlay, COLORS['top_bottom_border'],
                            (offset_x, offset_y, SCREEN_WIDTH, BORDER_THICKNESS))
            pygame.draw.rect(overlay, COLORS['top_bottom_border'],
                            (offset_x, SCREEN_HEIGHT - BORDER_THICKNESS + offset_y,
                             SCREEN_WIDTH, BORDER_THICKNESS))
            # 좌측 및 우측 테두리
            pygame.draw.rect(overlay, COLORS['left_border'],
                            (offset_x, offset_y, BORDER_THICKNESS, SCREEN_HEIGHT))
            pygame.draw.rect(overlay, COLORS['right_border'],
                            (SCREEN_WIDTH - BORDER_THICKNESS + offset_x, offset_y,
                             BORDER_THICKNESS, SCREEN_HEIGHT))
            # 중앙 점선
            center_x = SCREEN_WIDTH // 2 + offset_x
            y = offset_y
            while y < SCREEN_HEIGHT + offset_y:
                pygame.draw.line(overlay, COLORS['center_line'],
                               (center_x, y),
                               (center_x, min(y + DASH_LENGTH, SCREEN_HEIGHT + offset_y)),
                               CENTER_LINE_THICKNESS)
                y += DASH_LENGTH + GAP_LENGTH

            self.screen.blit(overlay, (0, 0))
        except Exception as e:
            print(f"테두리 및 중앙선 그리기 중 오류: {e}")

    def render(self, ball_pos: List[float], player_positions: List[List[float]], score: Tuple[int, int],
               goal_scored: bool = False, ball_trail: List[np.ndarray] = None) -> None:
        """게임 화면 렌더링: 배경, 테두리, 공, 플레이어, 점수, 키 상태"""
        try:
            # 화면 흔들림 계산
            self.shake_offset = self.get_screen_shake(goal_scored)
            offset_x, offset_y = self.shake_offset

            # 카메라 뷰 렌더링
            self.render_camera_view(offset_x, offset_y)

            # 테두리와 중앙선 그리기
            self.draw_borders_and_center_line(self.shake_offset)

            # 공과 궤적 렌더링
            self.render_trail(ball_trail, offset_x, offset_y)
            self.render_ball(ball_pos, offset_x, offset_y)

            # 플레이어 렌더링
            self.render_player(offset_x, offset_y, player_positions)

            # 점수 렌더링
            self.render_score(offset_x, offset_y, score)

            # 키 입력 상태 렌더링
            self.render_key_input(offset_x, offset_y)

            pygame.display.flip()
        except Exception as e:
            print(f"화면 렌더링 중 오류: {e}")

    def render_key_input(self, offset_x: int, offset_y: int) -> None:
        """키 입력 상태 렌더링"""
        try:
            key_status_text = " ".join(key.upper() for key, state in self.key_states.items() if state)
            if key_status_text:
                key_text = self.font.render(f"키: {key_status_text}", True, (255, 255, 255))
                key_rect = key_text.get_rect(topleft=(10 + offset_x, SCREEN_HEIGHT - KEY_STATUS_Y_OFFSET + offset_y))
                self.screen.blit(key_text, key_rect)
        except Exception as e:
            print(f"키 상태 렌더링 중 오류: {e}")

    def render_score(self, offset_x: int, offset_y: int, score: Tuple[int, int]) -> None:
        """점수 렌더링"""
        try:
            score_text = self.font.render(f"{score[0]} : {score[1]}", True, COLORS['score'])
            text_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2 + offset_x, SCORE_Y_OFFSET + offset_y))
            self.screen.blit(score_text, text_rect)
        except Exception as e:
            print(f"점수 렌더링 중 오류: {e}")

    def render_player(self, offset_x: int, offset_y: int, player_positions: List[List[float]]) -> None:
        """플레이어(손/발) 렌더링"""
        try:
            for i, pos in enumerate(player_positions):
                screen_pos = self.transform_player(pos)
                if screen_pos.shape[0] > 0:
                    color = COLORS['hand'] if i < 2 else COLORS['foot']
                    radius = int(HAND_RADIUS)
                    x, y = int(screen_pos[0, 0] + offset_x), int(screen_pos[0, 1] + offset_y)
                    if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                        pygame.draw.circle(self.screen, color, (x, y), radius)
        except Exception as e:
            print(f"플레이어 렌더링 중 오류: {e}")

    def get_screen_shake(self, goal_scored: bool) -> Tuple[int, int]:
        """화면 흔들림 효과 계산"""
        try:
            if goal_scored and self.shake_start_time is None:
                self.shake_start_time = time.time()
            elif self.shake_start_time is not None:
                elapsed = time.time() - self.shake_start_time
                if elapsed < SHAKE_DURATION:
                    return (
                        random.randint(-SHAKE_MAGNITUDE, SHAKE_MAGNITUDE),
                        random.randint(-SHAKE_MAGNITUDE, SHAKE_MAGNITUDE)
                    )
                else:
                    self.shake_start_time = None
                    return (0, 0)
            return (0, 0)
        except Exception as e:
            print(f"화면 흔들림 계산 중 오류: {e}")
            return (0, 0)

    def render_camera_view(self, offset_x: int, offset_y: int) -> None:
        """카메라 뷰 렌더링"""
        try:
            self.screen.fill((0, 0, 0))  # 화면 초기화
            if self.show_camera:
                frame = self.camera.get_frame()
                if frame is not None:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_resized = cv2.resize(frame_rgb, (config.WALL_WIDTH, config.WALL_HEIGHT))
                    frame_surface = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
                    self.screen.blit(frame_surface, (config.FOCUS_X + offset_x, config.FOCUS_Y + offset_y))
                else:
                    print("카메라 프레임이 없습니다.")
            else:
                self.screen.fill((0, 0, 0))
        except Exception as e:
            print(f"카메라 뷰 렌더링 중 오류: {e}")

    def render_ball(self, ball_pos: List[float], offset_x: int, offset_y: int) -> None:
        """공 렌더링"""
        try:
            ball_screen = self.transform_ball(ball_pos)
            if ball_screen.shape[0] > 0:
                ball_radius_pixel = int(BALL_RADIUS)
                border_thickness = max(1, int(ball_radius_pixel * BALL_BORDER_RATIO))
                x, y = int(ball_screen[0, 0] + offset_x), int(ball_screen[0, 1] + offset_y)
                if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                    pygame.draw.circle(self.screen, COLORS['ball'], (x, y), ball_radius_pixel)
                    pygame.draw.circle(self.screen, COLORS['ball_border'], (x, y), ball_radius_pixel, border_thickness)
        except Exception as e:
            print(f"공 렌더링 중 오류: {e}")

    def render_trail(self, ball_trail: List[np.ndarray], offset_x: int, offset_y: int) -> None:
        """공 궤적 렌더링"""
        try:
            if ball_trail:
                for i, trail_pos in enumerate(ball_trail):
                    trail_screen = self.transform_ball(trail_pos)
                    if trail_screen.shape[0] > 0:
                        ball_radius_pixel = int(BALL_RADIUS)
                        alpha = int(255 * (1 - i / len(ball_trail)))  # 페이드 효과
                        trail_surface = pygame.Surface((ball_radius_pixel * 2, ball_radius_pixel * 2), pygame.SRCALPHA)
                        pygame.draw.circle(trail_surface, (*COLORS['ball'], alpha),
                                        (ball_radius_pixel, ball_radius_pixel), ball_radius_pixel)
                        x, y = int(trail_screen[0, 0] + offset_x), int(trail_screen[0, 1] + offset_y)
                        if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                            self.screen.blit(trail_surface, (x - ball_radius_pixel, y - ball_radius_pixel))
        except Exception as e:
            print(f"공 궤적 렌더링 중 오류: {e}")

    def quit(self) -> None:
        """렌더러 종료 및 Pygame 정리"""
        try:
            pygame.quit()
        except Exception as e:
            print(f"Pygame 종료 중 오류: {e}")