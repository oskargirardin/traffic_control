from pygame.rect import Rect
import pygame
import math


pygame.font.init()

class Setup:
    # Size of screen
    WIDTH = 1200
    HEIGHT = 800

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREY = (144,142,142)
    GREEN = (111, 209, 3)
    RED = (255, 0, 0)

    # Width road
    ROAD_WIDTH = WIDTH//10
    DIST_CENTER = ROAD_WIDTH//2
    CENTER_Y = HEIGHT//2
    CENTER_X = WIDTH//2

    # Stop points
    STOP_LENGTH = 25
    STOP_ZONES = {
        "down": Rect(CENTER_X-DIST_CENTER, CENTER_Y-DIST_CENTER-STOP_LENGTH, DIST_CENTER, STOP_LENGTH),
        "up": Rect(CENTER_X, CENTER_Y+DIST_CENTER, DIST_CENTER, STOP_LENGTH),
        "left": Rect(CENTER_X+DIST_CENTER,CENTER_Y-DIST_CENTER, STOP_LENGTH, DIST_CENTER),
        "right": Rect(CENTER_X-DIST_CENTER-STOP_LENGTH, CENTER_Y, STOP_LENGTH, DIST_CENTER)
    }

    # Font
    geneva50 = pygame.font.SysFont("geneva", 50)


    def cos_fun(A, T, phi, k):
        return lambda x: A*math.cos(2*math.pi*x/T + phi)+k