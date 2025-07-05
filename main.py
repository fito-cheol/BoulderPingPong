import pygame
from camera import Camera
from calibration import calibrate_projector
from game import Game
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FULLSCREEN

def main():
    pygame.init()
    camera = Camera()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN if FULLSCREEN else 0)
    homography = calibrate_projector(camera, screen)
    game = Game(homography)
    game.run()

if __name__ == "__main__":
    main()