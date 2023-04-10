from collections import defaultdict
import pygame
import math
import numpy as np
import os
from pygame.rect import Rect
import pygame
import math



pygame.font.init()
IMAGE_DIR = "img"
IMAGES = os.listdir(IMAGE_DIR)
ANGLES = {"south": 0, "north": 180, "east": 90, "west": 270}




def get_movement(direction):
    dist_center = Setup.DIST_CENTER
    center_x, center_y = Setup.CENTER_X, Setup.CENTER_Y
    width, height = Setup.WIDTH, Setup.HEIGHT

    movements = {"north": (0, 1), "south": (0, -1), "east": (-1, 0), "west": (1, 0)}
    
    initial_pos = {"north": (center_x-dist_center/2-Setup.NUDGE_X, 0), "south": (center_x+dist_center/2-Setup.NUDGE_X, height),
                   "east": (width, center_y-dist_center/2-Setup.NUDGE_Y), "west": (0, center_y+dist_center/2-Setup.NUDGE_Y)}
    
    return movements[direction], Point(initial_pos[direction])



class Setup:
    
    # Size of screen
    WIDTH = 1200
    HEIGHT = 800

    # Env steps for every action
    N_ENV_STEPS = 10

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
    NUDGE_X = 5
    NUDGE_Y = 5

    # Stop points
    STOP_LENGTH = 25
    STOP_ZONES = {
        "north": Rect(CENTER_X-DIST_CENTER, CENTER_Y-DIST_CENTER-STOP_LENGTH, DIST_CENTER, STOP_LENGTH),
        "south": Rect(CENTER_X, CENTER_Y+DIST_CENTER, DIST_CENTER, STOP_LENGTH),
        "east": Rect(CENTER_X+DIST_CENTER,CENTER_Y-DIST_CENTER, STOP_LENGTH, DIST_CENTER),
        "west": Rect(CENTER_X-DIST_CENTER-STOP_LENGTH, CENTER_Y, STOP_LENGTH, DIST_CENTER)
    }

    # Font
    geneva50 = pygame.font.SysFont("geneva", 50)


    def cos_fun(A, T, phi, k):
        return lambda x: A*math.cos(2*math.pi*x/T + phi)+k
    
    

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



class Car(pygame.sprite.Sprite):

    def __init__(self,
                 direction="north",
                 width=12,
                 height=21,
                 speed=0.2):
        super().__init__()

        self.direction = direction
        self.moving, self.pos = get_movement(direction)
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



class Game:
    
    def __init__(self, dirs):
        self.cars_dict = {dir: pygame.sprite.Group() for dir in dirs} 
        self.lights_dict = {dir: True for dir in dirs} 
        self.number_cars = 0
        self.score = 0

    def move_cars(self, dt):
        for _, cars in self.cars_dict.items():
            for car in cars:
                car.move(dt)

    def apply_to_each_car(self, fun, dir = None):
        if dir:
            for car in self.cars_dict[dir]:
                fun(car)
        else:
            for _, cars in self.cars_dict.items():
                for car in cars:
                    fun(car)       
        
    def add_car(self, dir):
        if not self.can_add_car(dir):
            return
        self.cars_dict[dir].add([Car(direction=dir)])
        self.number_cars += 1
        
    def set_light(self, dir, value):
        self.lights_dict[dir] = value

    def switch_light(self, dir):
        self.lights_dict[dir] = not self.lights_dict[dir]

    def draw_cars(self, surface):
        for _, cars in self.cars_dict.items():
            for car in cars:
                car.draw(surface)


    def check_lights(self):
        """
        Function that checks if the lights are red or green and updates their movement.
        """
        for dir, green in self.lights_dict.items():
            if green: # Light is green
                self.apply_to_each_car(Car.go, dir=dir)
            if not green: # Light is red
                self.apply_to_each_car(Car.should_stop, dir=dir)

    def stop_behind_car(self):
        """
        Function that checks for every car if it should stop behind another car.
        """
        for dir, cars in self.cars_dict.items():
            for car in cars:
                cars_in_front = list(filter(lambda x: car.pos.dot(Point(car.moving)) < x.pos.dot(Point(x.moving)), self.cars_dict[dir]))
                immediate_cars = sorted(cars_in_front, key=lambda x: x.pos.dot(Point(x.moving)), reverse=False)
                if (len(immediate_cars)>0) and (Point(car.rect.center).dist(Point(immediate_cars[0].rect.center))<car.height*1.2):
                    car.stop()
                         
    def check_crash(self):
        """
        Function that checks if two cars are colliding.
        """
        for dir, car_group in self.cars_dict.items():
            if len(car_group)>0:
                all_rest = pygame.sprite.Group()
                all_rest.add(*[v.sprites() for k, v in self.cars_dict.items() if (k!=dir) and (len(v)>0)])
                collisions = pygame.sprite.groupcollide(car_group, all_rest, False, False)
                
                if len(collisions)>0:
                    return True
        return False
    

    def can_add_car(self, dir):
        car_group = self.cars_dict[dir]
        car = Car(direction=dir)
        return not pygame.sprite.spritecollide(car, car_group, dokill=False )
        


    def update_score(self):
        for _, car_group in self.cars_dict.items():
            for car in car_group:
                if car.is_off_screen():
                    car_group.remove(car)
                    self.score += 1

        return self.score
    

    def update_logic(self, dt):
        """
        Wrapper function to make all game updates
        """
        self.move_cars(dt)
        self.check_lights()
        self.stop_behind_car()
        if self.check_crash():
            score = 0
        score = self.update_score(score)
        return score 
        
    def update_interval(self, iter_count, fun):
        return int(fun(iter_count))
    
    def cars_on_screen(self):
        for _, cars in self.cars_dict.items():
            if len(cars) > 0:
                return True
        return False

