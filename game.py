import pygame
import time
from physics import Physics
from renderer import Renderer
from config import FPS, FULLSCREEN, SCREEN_WIDTH, SCREEN_HEIGHT, SCALE_FACTOR, WALL_WIDTH, WALL_HEIGHT, FOCUS_X, \
    FOCUS_Y, WIDTH_ADJUST_STEP, HEIGHT_ADJUST_STEP, FOCUS_ADJUST_STEP

class Game:
    def __init__(self, camera, homography):
        self.camera = camera
        self.physics = Physics()
        self.renderer = Renderer(homography)
        self.clock = pygame.time.Clock()

    def run(self):
        running = True
        last_update_time = time.time()

        import config

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.renderer.update_key_state(event.key, True)
                    if event.key == pygame.K_r:
                        self.physics.reset_game()
                        print("게임이 재시작되었습니다.")
                    elif event.key == pygame.K_w:
                        config.WALL_HEIGHT = max(0.1, config.WALL_HEIGHT + HEIGHT_ADJUST_STEP)
                        print(f"상하 영역 크기: {config.WALL_HEIGHT:.1f}m")
                    elif event.key == pygame.K_s:
                        config.WALL_HEIGHT = max(0.1, config.WALL_HEIGHT - HEIGHT_ADJUST_STEP)
                        print(f"상하 영역 크기: {config.WALL_HEIGHT:.1f}m")
                    elif event.key == pygame.K_a:
                        config.WALL_WIDTH = max(0.1, config.WALL_WIDTH - WIDTH_ADJUST_STEP)
                        print(f"좌우 영역 크기: {config.WALL_WIDTH:.1f}m")
                    elif event.key == pygame.K_d:
                        config.WALL_WIDTH = max(0.1, config.WALL_WIDTH + WIDTH_ADJUST_STEP)
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
                elif event.type == pygame.KEYUP:
                    self.renderer.update_key_state(event.key, False)

            current_time = time.time()
            dt = current_time - last_update_time
            if dt < 1 / FPS:
                continue
            last_update_time = current_time

            player_positions = self.camera.get_player_positions()
            self.physics.update(player_positions, dt)
            self.renderer.render(self.physics.ball_pos, player_positions, self.physics.score)
            self.clock.tick(FPS)

        self.camera.release()
        self.renderer.quit()