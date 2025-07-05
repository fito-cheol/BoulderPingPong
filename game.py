import pygame
import time
from physics import Physics
from renderer import Renderer
from config import FPS, FULLSCREEN, SCREEN_WIDTH, SCREEN_HEIGHT, SCALE_FACTOR, WALL_WIDTH, WALL_HEIGHT, FOCUS_X, \
    FOCUS_Y, WIDTH_ADJUST_STEP, HEIGHT_ADJUST_STEP, FOCUS_ADJUST_STEP

# 상수 정의
MIN_WALL_SIZE = 0.1  # 최소 벽 크기 (미터)
FRAME_TIME = 1 / FPS  # 프레임당 시간 (초)

class Game:
    def __init__(self, camera, homography: np.ndarray):
        """게임 초기화: 카메라, 물리 엔진, 렌더러, 클럭 설정"""
        self.camera = camera
        self.physics = Physics()
        self.renderer = Renderer(homography, camera)
        self.clock = pygame.time.Clock()

    def handle_key_events(self, event: pygame.event.Event) -> None:
        """키 입력 이벤트 처리"""
        import config
        if event.type == pygame.KEYDOWN:
            self.renderer.update_key_state(event.key, True)
            if event.key == pygame.K_r:
                self.physics.reset_game()
                print("게임이 재시작되었습니다.")
            elif event.key == pygame.K_w:
                config.WALL_HEIGHT = max(MIN_WALL_SIZE, config.WALL_HEIGHT + HEIGHT_ADJUST_STEP)
                print(f"상하 영역 크기: {config.WALL_HEIGHT:.1f}m")
            elif event.key == pygame.K_s:
                config.WALL_HEIGHT = max(MIN_WALL_SIZE, config.WALL_HEIGHT - HEIGHT_ADJUST_STEP)
                print(f"상하 영역 크기: {config.WALL_HEIGHT:.1f}m")
            elif event.key == pygame.K_a:
                config.WALL_WIDTH = max(MIN_WALL_SIZE, config.WALL_WIDTH - WIDTH_ADJUST_STEP)
                print(f"좌우 영역 크기: {config.WALL_WIDTH:.1f}m")
            elif event.key == pygame.K_d:
                config.WALL_WIDTH = max(MIN_WALL_SIZE, config.WALL_WIDTH + WIDTH_ADJUST_STEP)
                print(f"좌우 영역 크기: {config.WALL_WIDTH:.1f}m")
            elif event.key == pygame.K_UP:
                config.FOCUS_Y -= FOCUS_ADJUST_STEP
                print(f"화면 중심 Y: {config.FOCUS_Y:.1f}m")
            elif event.key == pygame.K_DOWN:
                config.FOCUS_Y += FOCUS_ADJUST_STEP
                print(f"화면 중심 Y: {config.FOCUS_Y:.1f}m")
            elif event.key == pygame.K_LEFT:
                config.FOCUS_X -= FOCUS_ADJUST_STEP
                print(f"화면 중심 X: {config.FOCUS_X:.1f}m")
            elif event.key == pygame.K_RIGHT:
                config.FOCUS_X += FOCUS_ADJUST_STEP
                print(f"화면 중심 X: {config.FOCUS_X:.1f}m")
            elif event.key == pygame.K_p:
                self.renderer.toggle_camera()
        elif event.type == pygame.KEYUP:
            self.renderer.update_key_state(event.key, False)

    def run(self) -> None:
        """게임 메인 루프 실행"""
        running = True
        last_update_time = time.time()

        while running:
            # 이벤트 처리
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle_key_events(event)

            # 프레임 시간 제어
            current_time = time.time()
            dt = current_time - last_update_time
            if dt < FRAME_TIME:
                continue
            last_update_time = current_time

            # 플레이어 위치 업데이트 및 렌더링
            player_positions = self.camera.get_player_positions()
            self.physics.update(player_positions, dt)
            self.renderer.render(self.physics.ball_pos, player_positions, self.physics.score)
            self.clock.tick(FPS)

        # 게임 종료 및 리소스 정리
        self.camera.release()
        self.renderer.quit()