import pygame
import numpy as np
import cv2
from config import WALL_WIDTH, WALL_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT, BALL_RADIUS, HITBOX_RADIUS, SCALE_FACTOR, \
    COLORS, FOCUS_X, FOCUS_Y

class Renderer:
    def __init__(self, homography, camera):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        self.font = pygame.font.Font(None, int(36 * SCALE_FACTOR))
        self.homography = homography
        self.use_homography = homography is not None
        self.camera = camera
        self.show_camera = False
        self.key_states = {
            'w': False,
            's': False,
            'a': False,
            'd': False,
            'up': False,
            'down': False,
            'left': False,
            'right': False
        }

    def update_key_state(self, key, state):
        """키 상태 업데이트"""
        key_map = {
            pygame.K_w: 'w',
            pygame.K_s: 's',
            pygame.K_a: 'a',
            pygame.K_d: 'd',
            pygame.K_UP: 'up',
            pygame.K_DOWN: 'down',
            pygame.K_LEFT: 'left',
            pygame.K_RIGHT: 'right'
        }
        if key in key_map:
            self.key_states[key_map[key]] = state

    def toggle_camera(self):
        """카메라 화면 표시 토글"""
        self.show_camera = not self.show_camera
        print(f"카메라 화면 {'표시' if self.show_camera else '숨김'}")

    def transform_coordinates(self, points):
        """호모그래피와 초점 오프셋을 사용해 좌표 변환"""
        if not self.use_homography:
            return self.simple_transform(points)

        try:
            points = np.array(points, dtype=np.float32)
            if points.ndim == 1:
                points = points.reshape(1, -1)

            if points.shape[1] != 2:
                if len(points.shape) == 1 and len(points) == 2:
                    points = points.reshape(1, 2)
                else:
                    return self.simple_transform(points)

            points = points - np.array([FOCUS_X, FOCUS_Y])
            points_homogeneous = np.column_stack([points, np.ones(points.shape[0])])
            transformed_homogeneous = self.homography @ points_homogeneous.T
            transformed = transformed_homogeneous[:2] / transformed_homogeneous[2]
            transformed = transformed.T
            return transformed

        except Exception as e:
            print(f"호모그래피 변환 실패: {e}, 기본 변환 사용")
            return self.simple_transform(points)

    def simple_transform(self, points):
        """기본 선형 변환 (호모그래피 없이)"""
        points = np.array(points, dtype=np.float32)
        if points.ndim == 1:
            points = points.reshape(1, -1)
        points = points - np.array([FOCUS_X, FOCUS_Y])
        scale_x = SCREEN_WIDTH / WALL_WIDTH
        scale_y = SCREEN_HEIGHT / WALL_HEIGHT
        transformed = points * np.array([scale_x, scale_y])
        return transformed

    def draw_borders_and_center_line(self):
        """테두리와 중앙선 그리기"""
        border_thickness = int(10 * SCALE_FACTOR)
        center_line_thickness = int(5 * SCALE_FACTOR)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        pygame.draw.rect(overlay, COLORS['top_bottom_border'], (0, 0, SCREEN_WIDTH, border_thickness))
        pygame.draw.rect(overlay, COLORS['top_bottom_border'],
                         (0, SCREEN_HEIGHT - border_thickness, SCREEN_WIDTH, border_thickness))
        pygame.draw.rect(overlay, COLORS['left_border'], (0, 0, border_thickness, SCREEN_HEIGHT))
        pygame.draw.rect(overlay, COLORS['right_border'],
                         (SCREEN_WIDTH - border_thickness, 0, border_thickness, SCREEN_HEIGHT))
        center_x = SCREEN_WIDTH // 2
        dash_length = int(20 * SCALE_FACTOR)
        gap_length = int(10 * SCALE_FACTOR)
        y = 0
        while y < SCREEN_HEIGHT:
            pygame.draw.line(overlay, COLORS['center_line'], (center_x, y),
                             (center_x, min(y + dash_length, SCREEN_HEIGHT)), center_line_thickness)
            y += dash_length + gap_length

        self.screen.blit(overlay, (0, 0))

    def render(self, ball_pos, player_positions, score):
        # 카메라 프레임 렌더링
        if self.show_camera:
            frame = self.camera.get_frame()
            if frame is not None:
                # OpenCV BGR을 RGB로 변환
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # 화면 크기에 맞게 리사이즈
                frame_resized = cv2.resize(frame_rgb, (SCREEN_WIDTH, SCREEN_HEIGHT))
                # NumPy 배열을 Pygame Surface로 변환
                frame_surface = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
                self.screen.blit(frame_surface, (0, 0))
            else:
                self.screen.fill((0, 0, 0))  # 카메라 프레임 없으면 검은색 배경
        else:
            self.screen.fill((0, 0, 0))

        self.draw_borders_and_center_line()

        # 공 그리기
        try:
            ball_screen = self.transform_coordinates(ball_pos)
            if ball_screen.shape[0] > 0:
                ball_radius_pixel = int(BALL_RADIUS * SCREEN_WIDTH / WALL_WIDTH)
                border_thickness = max(1, int(ball_radius_pixel * 0.1))
                x, y = int(ball_screen[0, 0]), int(ball_screen[0, 1])
                if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                    pygame.draw.circle(self.screen, COLORS['ball'], (x, y), ball_radius_pixel)
                    pygame.draw.circle(self.screen, COLORS['ball_border'], (x, y), ball_radius_pixel, border_thickness)
        except Exception as e:
            print(f"공 렌더링 오류: {e}")

        # 손/발 그리기
        try:
            for i, pos in enumerate(player_positions):
                screen_pos = self.transform_coordinates(pos)
                if screen_pos.shape[0] > 0:
                    color = COLORS['hand'] if i < 2 else COLORS['foot']
                    radius = int(HITBOX_RADIUS * SCREEN_WIDTH / WALL_WIDTH)
                    x, y = int(screen_pos[0, 0]), int(screen_pos[0, 1])
                    if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                        pygame.draw.circle(self.screen, color, (x, y), radius)
        except Exception as e:
            print(f"플레이어 렌더링 오류: {e}")

        # 점수 표시
        try:
            score_text = self.font.render(f"{score[0]} : {score[1]}", True, COLORS['score'])
            text_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, int(50 * SCALE_FACTOR)))
            self.screen.blit(score_text, text_rect)
        except Exception as e:
            print(f"점수 렌더링 오류: {e}")

        # 키 입력 상태 표시
        try:
            key_status_text = ""
            for key, state in self.key_states.items():
                if state:
                    key_status_text += key.upper() + " "
            if key_status_text:
                key_text = self.font.render(f"Keys: {key_status_text}", True, (255, 255, 255))
                key_rect = key_text.get_rect(topleft=(10, SCREEN_HEIGHT - int(50 * SCALE_FACTOR)))
                self.screen.blit(key_text, key_rect)
        except Exception as e:
            print(f"키 상태 렌더링 오류: {e}")

        # 캘리브레이션 상태 표시
        if not self.use_homography:
            try:
                warning_text = self.font.render("기본 변환 사용 중 (캘리브레이션 없음)", True, (255, 255, 0))
                warning_rect = warning_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
                self.screen.blit(warning_text, warning_rect)
            except Exception as e:
                print(f"경고 텍스트 렌더링 오류: {e}")

        pygame.display.flip()

    def quit(self):
        pygame.quit()