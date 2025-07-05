import pygame
from camera import Camera
from physics import Physics
from renderer import Renderer
from config import FPS, FULLSCREEN, SCREEN_WIDTH, SCREEN_HEIGHT, SCALE_FACTOR
import time

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

            current_time = time.time()
            dt = current_time - last_update_time
            if dt < 1 / FPS:
                continue
            last_update_time = current_time

            player_positions = self.camera.get_player_positions()
            self.physics.update(player_positions, dt)
            if not self.physics.round_ended:
                self.renderer.render(self.physics.ball_pos, player_positions, self.physics.score)
            else:
                self.renderer.render(self.physics.ball_pos, player_positions, self.physics.score)
            self.clock.tick(FPS)

        self.camera.release()
        self.renderer.quit()