import asyncio
import pygame
import time
import numpy as np
from game.physics import Physics
from game.renderer import Renderer
from config import FPS, WIDTH_ADJUST_STEP, HEIGHT_ADJUST_STEP, FOCUS_ADJUST_STEP

# 상수 정의
MIN_WALL_SIZE = 0.1  # 최소 벽 크기 (미터)
FRAME_TIME = 1 / FPS  # 프레임당 시간 (초)
DEBOUNCE_TIME = 0.1  # 키 입력 디바운스 시간 (초)

# 키 바인딩 정의
KEY_BINDINGS = {
    'reset': pygame.K_r,          # 게임 재시작 키
    'wall_height_up': pygame.K_w,  # 벽 높이 증가 키
    'wall_height_down': pygame.K_s,  # 벽 높이 감소 키
    'wall_width_left': pygame.K_a,  # 벽 너비 감소 키
    'wall_width_right': pygame.K_d,  # 벽 너비 증가 키
    'focus_up': pygame.K_UP,      # 화면 중심 Y축 위로 이동 키
    'focus_down': pygame.K_DOWN,   # 화면 중심 Y축 아래로 이동 키
    'focus_left': pygame.K_LEFT,   # 화면 중심 X축 왼쪽으로 이동 키
    'focus_right': pygame.K_RIGHT,  # 화면 중심 X축 오른쪽으로 이동 키
    'toggle_camera': pygame.K_p,   # 카메라 전환 키
    'quit': pygame.K_ESCAPE       # 게임 종료 키
}

class InputHandler:
    """키보드 입력 이벤트를 처리하는 클래스"""
    def __init__(self, game):
        """입력 핸들러 초기화"""
        self.game = game  # 게임 객체 참조
        self.last_key_time = 0  # 마지막 키 입력 시간
        self.is_processing = False  # 입력 처리 중 여부

    def handle_key_event(self, event: pygame.event.Event) -> bool:
        """키 이벤트를 디바운싱 처리와 함께 처리. 종료 시 True 반환"""
        current_time = time.time()
        if self.is_processing or (current_time - self.last_key_time < DEBOUNCE_TIME):
            return False  # 처리 중이거나 디바운스 시간 내 입력 무시

        self.is_processing = True
        self.last_key_time = current_time
        import config

        if event.type == pygame.KEYDOWN:
            self.game.renderer.update_key_state(event.key, True)
            try:
                if event.key == KEY_BINDINGS['reset']:
                    self.game.physics.reset_game()
                    print("게임이 재시작되었습니다.")
                elif event.key == KEY_BINDINGS['wall_height_up']:
                    config.WALL_HEIGHT = max(MIN_WALL_SIZE, config.WALL_HEIGHT + HEIGHT_ADJUST_STEP)
                    print(f"벽 높이: {config.WALL_HEIGHT:.1f}m")
                elif event.key == KEY_BINDINGS['wall_height_down']:
                    config.WALL_HEIGHT = max(MIN_WALL_SIZE, config.WALL_HEIGHT - HEIGHT_ADJUST_STEP)
                    print(f"벽 높이: {config.WALL_HEIGHT:.1f}m")
                elif event.key == KEY_BINDINGS['wall_width_left']:
                    config.WALL_WIDTH = max(MIN_WALL_SIZE, config.WALL_WIDTH - WIDTH_ADJUST_STEP)
                    print(f"벽 너비: {config.WALL_WIDTH:.1f}m")
                elif event.key == KEY_BINDINGS['wall_width_right']:
                    config.WALL_WIDTH = max(MIN_WALL_SIZE, config.WALL_WIDTH + WIDTH_ADJUST_STEP)
                    print(f"벽 너비: {config.WALL_WIDTH:.1f}m")
                elif event.key == KEY_BINDINGS['focus_up']:
                    config.FOCUS_Y -= FOCUS_ADJUST_STEP
                    print(f"화면 중심 Y: {config.FOCUS_Y:.1f}m")
                elif event.key == KEY_BINDINGS['focus_down']:
                    config.FOCUS_Y += FOCUS_ADJUST_STEP
                    print(f"화면 중심 Y: {config.FOCUS_Y:.1f}m")
                elif event.key == KEY_BINDINGS['focus_left']:
                    config.FOCUS_X -= FOCUS_ADJUST_STEP
                    print(f"화면 중심 X: {config.FOCUS_X:.1f}m")
                elif event.key == KEY_BINDINGS['focus_right']:
                    config.FOCUS_X += FOCUS_ADJUST_STEP
                    print(f"화면 중심 X: {config.FOCUS_X:.1f}m")
                elif event.key == KEY_BINDINGS['toggle_camera']:
                    self.game.renderer.toggle_camera()
                    print("카메라 모드가 전환되었습니다.")
                elif event.key == KEY_BINDINGS['quit']:
                    return True
            except Exception as e:
                print(f"키 이벤트 처리 중 오류: {e}")
        elif event.type == pygame.KEYUP:
            self.game.renderer.update_key_state(event.key, False)

        self.is_processing = False
        return False

class Game:
    """게임의 주요 로직을 관리하는 클래스"""
    def __init__(self, camera, homography: np.ndarray):
        """게임 구성 요소 초기화"""
        try:
            self.camera = camera  # 카메라 객체
            self.physics = Physics()  # 물리 엔진
            self.renderer = Renderer(homography, camera)  # 렌더러
            self.clock = pygame.time.Clock()  # 프레임 제어용 클럭
            self.input_handler = InputHandler(self)  # 입력 핸들러
        except Exception as e:
            print(f"게임 초기화 중 오류: {e}")
            raise

    def setup(self):
        """Pygame 초기 설정"""
        pygame.init()

    async def update_loop(self):
        """게임 상태 업데이트 및 렌더링"""
        try:
            player_positions = self.camera.get_player_positions()  # 플레이어 위치 가져오기
            self.physics.update(player_positions, FRAME_TIME)  # 물리 엔진 업데이트
            self.renderer.render(
                self.physics.ball_pos,  # 공 위치
                player_positions,       # 플레이어 위치
                self.physics.score,     # 점수
                self.physics.goal_scored,  # 골 여부
                self.physics.ball_trail  # 공 궤적
            )
        except Exception as e:
            print(f"업데이트 루프 중 오류: {e}")

    async def main(self):
        """Pyodide 호환을 위한 메인 게임 루프"""
        self.setup()
        last_update_time = time.time()

        while True:
            try:
                # 이벤트 처리
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or self.input_handler.handle_key_event(event):
                        self.cleanup()
                        return

                # 프레임 시간 제어
                current_time = time.time()
                dt = current_time - last_update_time
                if dt < FRAME_TIME:
                    await asyncio.sleep(FRAME_TIME - dt)
                    continue
                last_update_time = current_time

                # 게임 상태 업데이트 및 렌더링
                await self.update_loop()
                self.clock.tick(FPS)

            except Exception as e:
                print(f"메인 루프 중 오류: {e}")
                await asyncio.sleep(FRAME_TIME)

    def cleanup(self):
        """리소스 정리"""
        try:
            self.camera.release()  # 카메라 리소스 해제
            self.renderer.quit()   # 렌더러 종료
            pygame.quit()          # Pygame 종료
        except Exception as e:
            print(f"리소스 정리 중 오류: {e}")
