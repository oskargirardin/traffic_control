import pygame
from pygame_setup import *
import math
import numpy as np
import os

IMAGE_DIR = "img"
IMAGES = os.listdir(IMAGE_DIR)
ANGLES = {"up": 0, "down": 180, "left": 90, "right": 270}


class Point:

    def __init__(self, point_t=(0, 0)):
        self.x = float(point_t[0])
        self.y = float(point_t[1])

    def __add__(self, other):
        return Point((self.x + other.x, self.y + other.y))

    def __sub__(self, other):
        return Point((self.x - other.x, self.y - other.y))

    def __mul__(self, scalar):
        return Point((self.x*scalar, self.y*scalar))

    def __div__(self, scalar):
        return Point((self.x/scalar, self.y/scalar))

    def __len__(self):
        return int(math.sqrt(self.x**2 + self.y**2))

    def dot(self, other):
        return np.array(self.get()).dot(np.array(other.get()))
    
    def dist(self, other):
        ''' other is another point '''
        return int(math.sqrt((self.x-other.x)**2 + (self.y-other.y)**2))
        
    def get(self):
        return (self.x, self.y)


def get_movement(direction, nudgex, nudgey):
    dist_center = Setup.DIST_CENTER
    center_x, center_y = Setup.CENTER_X, Setup.CENTER_Y
    width, height = Setup.WIDTH, Setup.HEIGHT

    movements = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}
    
    initial_pos = {"down": (center_x-dist_center/2-nudgex, 0), "up": (center_x+dist_center/2-nudgex, height),
                   "left": (width, center_y-dist_center/2-nudgey), "right": (0, center_y+dist_center/2-nudgey)}
    
    return movements[direction], Point(initial_pos[direction])


class Car(pygame.sprite.Sprite):

    def __init__(self,
                 direction="down",
                 width=25,
                 height=42,
                 speed=0.1):
        super().__init__()

        self.direction = direction
        self.moving, self.pos = get_movement(direction, 5, 5)
        self.width = width
        self.height = height
        self.speed = speed
        self.driving = True

        self.image = pygame.image.load(os.path.join(os.getcwd(), IMAGE_DIR, np.random.choice(IMAGES)))
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.image = pygame.transform.rotate(self.image, ANGLES[self.direction])

        self.rect = self.image.get_rect()
        self.rect.center = (self.pos.x, self.pos.y)

    def move(self, dt):
        if self.driving:
            self.pos = Point(self.rect.center) +  Point(self.moving)*self.speed*dt
            self.rect.center = (self.pos.x, self.pos.y)

    def stop(self):
        self.driving = False

    def go(self):
        self.driving = True

    def draw(self, surface: pygame.display):
        surface.blit(self.image, self.rect)
        #pygame.draw.rect(surface, Setup.BLACK, rect=rect, border_radius=min(self.height, self.width) // 2)

    def is_at_light(self):
        return (pygame.Rect.colliderect(self.rect, Setup.STOP_ZONES[self.direction])) and (Setup.STOP_ZONES[self.direction].collidepoint(self.rect.center))

    def should_stop(self):
        if self.is_at_light():
            self.stop()
        else:
            self.go()

    def is_off_screen(self):
        screen_rect = pygame.Rect(-self.width, -self.height, Setup.WIDTH+2*self.width, Setup.HEIGHT+2*self.height)
        return not pygame.Rect.colliderect(self.rect, screen_rect)
