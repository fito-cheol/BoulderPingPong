import pygame

from camera import Camera
from physics import Physics
from renderer import Renderer
from config import FPS

class Game:
    def __init__(self, homography):
        self.camera = Camera()
        self.physics = Physics()
        self.renderer = Renderer(homography)
        self.clock = pygame.time.Clock()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False

            player_positions = self.camera.get_player_positions()
            self.physics.update(player_positions, 1 / FPS)
            self.renderer.render(self.physics.ball_pos, player_positions, self.physics.score)
            self.clock.tick(FPS)

        self.camera.release()
        self.renderer.quit()