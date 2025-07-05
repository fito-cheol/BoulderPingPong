import pygame
from camera import Camera
from physics import Physics
from renderer import Renderer
from config import FPS, FULLSCREEN, SCREEN_WIDTH, SCREEN_HEIGHT, SCALE_FACTOR, WALL_WIDTH, WALL_HEIGHT, FOCUS_X, FOCUS_Y, WIDTH_ADJUST_STEP, HEIGHT_ADJUST_STEP, FOCUS_ADJUST_STEP

class Game:
    def __init__(self, homography):
        self.camera = Camera()
        self.physics = Physics()
        self.renderer = Renderer(homography)
        self.clock = pygame.time.Clock()

    def run(self):
        running = True
        last_update_time = time.time()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.physics.reset_game()  # 게임 재시작
                    elif event.key == pygame.K_w:
                        globals()['WALL_HEIGHT'] = max(0.1, WALL_HEIGHT + HEIGHT_ADJUST_STEP)  # 상하폭 증가
                    elif event.key == pygame.K_s:
                        globals()['WALL_HEIGHT'] = max(0.1, WALL_HEIGHT - HEIGHT_ADJUST_STEP)  # 상하폭 감소
                    elif event.key == pygame.K_d:
                        globals()['WALL_WIDTH'] = max(0.1, WALL_WIDTH + WIDTH_ADJUST_STEP)  # 좌우폭 증가
                    elif event.key == pygame.K_a:
                        globals()['WALL_WIDTH'] = max(0.1, WALL_WIDTH - WIDTH_ADJUST_STEP)  # 좌우폭 감소
                    elif event.key == pygame.K_UP:
                        globals()['FOCUS_Y'] -= FOCUS_ADJUST_STEP  # 초점 위로 이동
                    elif event.key == pygame.K_DOWN:
                        globals()['FOCUS_Y'] += FOCUS_ADJUST_STEP  # 초점 아래로 이동
                    elif event.key == pygame.K_LEFT:
                        globals()['FOCUS_X'] -= FOCUS_ADJUST_STEP  # 초점 왼쪽으로 이동
                    elif event.key == pygame.K_RIGHT:
                        globals()['FOCUS_X'] += FOCUS_ADJUST_STEP  # 초점 오른쪽으로 이동

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