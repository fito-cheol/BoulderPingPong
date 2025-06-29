import pygame
from camera import Camera
from calibration import calibrate_projector
from game import Game

def main():
    camera = Camera()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    homography = calibrate_projector(camera, screen)
    game = Game(homography)
    game.run()

if __name__ == "__main__":
    main()