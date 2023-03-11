import pygame
from pygame_setup import *
import math
import numpy as np

class Point:
    # constructed using a normal tupple
    def __init__(self, point_t = (0,0)):
        self.x = float(point_t[0])
        self.y = float(point_t[1])
    # define all useful operators
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
    # get back values in original tuple format
    def get(self):
        return (self.x, self.y)


def get_movement(direction, nudgex, nudgey):
    dist_center = Setup.ROAD_WIDTH//2
    center_y = Setup.HEIGHT//2
    center_x = Setup.WIDTH//2
    movements = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}
    initial_pos = {"down": (center_x-dist_center/2-nudgex, 0), "up": (center_x+dist_center/2-nudgex, Setup.HEIGHT), "left": (Setup.WIDTH, center_y-dist_center/2-nudgey), "right": (0, center_y+dist_center/2-nudgey)}
    return movements[direction], Point(initial_pos[direction])

class Car(pygame.sprite.Sprite):

    def __init__(self, 
                 direction = "down",
                 width = 10,
                 height = 10,
                 speed = 0.1):
        super().__init__()
        self.direction = direction
        self.moving, self.pos = get_movement(direction, width/2, height/2)
        self.width = width
        self.height = height
        self.speed = speed
        self.driving = True
        self.rect = pygame.rect.Rect(self.pos.x, self.pos.y, self.width, self.height)

    def get_rect(self):
        self.rect = pygame.rect.Rect(self.pos.x, self.pos.y, self.width, self.height)
        return self.rect

    def move(self, dt):
        if self.driving:
            self.pos += Point(self.moving)*self.speed*dt

    def stop(self):
        self.driving = False

    def go(self):
        self.driving = True

    def draw(self, surface):
        rect = self.get_rect()
        pygame.draw.rect(surface, Setup.BLACK, rect=rect, border_radius=min(self.height, self.width) // 2)
    
    def is_at_light(self):
        return pygame.Rect.colliderect(self.get_rect(), Setup.STOP_ZONES[self.direction])

    def should_stop(self):
        if self.is_at_light():
            self.stop()
        else:
            self.go()
    
    def is_off_screen(self):
        screen_rect = pygame.Rect(-self.width, -self.height, Setup.WIDTH+2*self.width, Setup.HEIGHT+2*self.height)
        return not pygame.Rect.colliderect(self.get_rect(), screen_rect)
