import pygame
import time
from physics import Physics
from renderer import Renderer
from config import FPS, FULLSCREEN, SCREEN_WIDTH, SCREEN_HEIGHT, SCALE_FACTOR, WALL_WIDTH, WALL_HEIGHT, FOCUS_X, \
    FOCUS_Y, WIDTH_ADJUST_STEP, HEIGHT_ADJUST_STEP, FOCUS_ADJUST_STEP


class Game:
    def __init__(self, camera, homography):
        self.camera = camera  # 이미 초기화된 카메라 객체를 받음
        self.physics = Physics()
        self.renderer = Renderer(homography)
        self.clock = pygame.time.Clock()

    def run(self):
        running = True
        last_update_time = time.time()

        # config 모듈의 전역 변수들을 로컬 변수로 가져와서 수정 가능하게 함
        import config

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.physics.reset_game()  # 게임 재시작
                        print("게임이 재시작되었습니다.")
                    elif event.key == pygame.K_w:
                        config.WALL_HEIGHT = max(0.1, config.WALL_HEIGHT + HEIGHT_ADJUST_STEP)
                        print(f"상하 영역 크기: {config.WALL_HEIGHT:.1f}m")
                    elif event.key == pygame.K_s:
                        config.WALL_HEIGHT = max(0.1, config.WALL_HEIGHT - HEIGHT_ADJUST_STEP)
                        print(f"상하 영역 크기: {config.WALL_HEIGHT:.1f}m")
                    elif event.key == pygame.K_d:
                        config.WALL_WIDTH = max(0.1, config.WALL_WIDTH + WIDTH_ADJUST_STEP)
                        print(f"좌우 영역 크기: {config.WALL_WIDTH:.1f}m")
                    elif event.key == pygame.K_a:
                        config.WALL_WIDTH = max(0.1, config.WALL_WIDTH - WIDTH_ADJUST_STEP)
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

            current_time = time.time()
            dt = current_time - last_update_time
            if dt < 1 / FPS:
                continue
            last_update_time = current_time

            # 카메라에서 플레이어 위치 가져오기
            player_positions = self.camera.get_player_positions()

            # 물리 엔진 업데이트
            self.physics.update(player_positions, dt)

            # 렌더링
            self.renderer.render(self.physics.ball_pos, player_positions, self.physics.score)

            # FPS 제한
            self.clock.tick(FPS)

        # 게임 종료 시 리소스 정리
        self.camera.release()
        self.renderer.quit()