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
    
    nudg_o, nudg_e = Setup.NUDGE, - Setup.NUDGE
    nudges = [nudg_o, nudg_e]
    
    initial_pos = {"north": (center_x-dist_center/2-np.random.choice(nudges), 0), "south": (center_x+dist_center/2-np.random.choice(nudges), height),
                   "east": (width, center_y-dist_center/2-np.random.choice(nudges)), "west": (0, center_y+dist_center/2-np.random.choice(nudges))}
    
    return movements[direction], Point(initial_pos[direction])



class Setup:
    
    # Size of screen
    WIDTH = 1100
    HEIGHT = 800

    # Env steps for every action
    N_ENV_STEPS = 150

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREY = (144,142,142)
    GREEN = (111, 209, 3)
    RED = (255, 0, 0)
    YELLOW = (255, 211, 67)

    # Width road
    ROAD_WIDTH = WIDTH//10
    DIST_CENTER = ROAD_WIDTH//2
    CENTER_Y = HEIGHT//2
    CENTER_X = WIDTH//2
    NUDGE = 8.5 #5
    # NUDGE_Y = 0 # 5
    CAR_HEIGHT = 20
    CAR_WIDTH = 12
    CAR_SPEED = 1
    MAX_CARS_NS = 2*((CENTER_Y - DIST_CENTER)//CAR_HEIGHT + 1) # Needs to be changed if stopping criterium at light changed
    MAX_CARS_WE = 2*((CENTER_X - DIST_CENTER)//CAR_HEIGHT + 1) # Needs to be changed if stopping criterium at light changed

    # Stop points
    STOP_LENGTH = 10
    STOP_ZONES = {
        "north": Rect(CENTER_X-DIST_CENTER, CENTER_Y-DIST_CENTER-STOP_LENGTH, DIST_CENTER, STOP_LENGTH),
        "south": Rect(CENTER_X, CENTER_Y+DIST_CENTER, DIST_CENTER, STOP_LENGTH),
        "east": Rect(CENTER_X+DIST_CENTER,CENTER_Y-DIST_CENTER, STOP_LENGTH, DIST_CENTER),
        "west": Rect(CENTER_X-DIST_CENTER-STOP_LENGTH, CENTER_Y, STOP_LENGTH, DIST_CENTER)
    }
    
    INTERSECT_AREA = Rect(CENTER_X-DIST_CENTER, CENTER_Y-DIST_CENTER, 2*DIST_CENTER, 2*DIST_CENTER)

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
                 direction="north"):
        super().__init__()

        self.direction = direction
        self.moving, self.pos = get_movement(direction)
        self.width = Setup.CAR_WIDTH
        self.height = Setup.CAR_HEIGHT
        self.speed = Setup.CAR_SPEED
        self.driving = True
        self.waiting_time = 0
        self.next_car = None
        self.pass_intersection = False

        self.image = pygame.image.load(os.path.join(os.getcwd(), IMAGE_DIR, np.random.choice(IMAGES)))
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.image = pygame.transform.rotate(self.image, ANGLES[self.direction])

        self.rect = self.image.get_rect()
        self.rect.center = (self.pos.x, self.pos.y)
            
    def check_next_car(self):
        if (self.next_car != False) and (not self.pass_intersection) and (Point(self.next_car.rect.center).dist(Point(self.rect.center))<= 1.18*self.height):
            self.stop()

    def move(self):
        if self.driving:
            self.pos = Point(self.rect.center) +  Point(self.moving)*self.speed
            self.rect.center = (self.pos.x, self.pos.y)
            self.reset_waiting()
            if (not self.pass_intersection) and (self.is_at_intersection()):
                self.pass_intersection = True
 
    def stop(self):
        self.driving = False

    def go(self):
        self.driving = True
        
    def reset_waiting(self):
        self.waiting_time = 0
    
    def update_waiting(self):
        if not self.driving:
            self.waiting_time += 1

    def draw(self, surface: pygame.display):
        surface.blit(self.image, self.rect)
        
    def is_at_intersection(self):
        return Setup.INTERSECT_AREA.collidepoint(self.rect.center)

    def is_at_light(self):
        return pygame.Rect.colliderect(self.rect, Setup.STOP_ZONES[self.direction])

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
        self.cars_dict_last = defaultdict()
        self.dirs = dirs
        self.number_cars = 0
        self.score = 0

    def move_cars(self):
        for _, cars in self.cars_dict.items():
            for car in cars:
                car.move()    

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
        next_car = Car(direction=dir)
        
        # same road lane
        if dir in ["north", "south"]:
            comp = next_car.pos.x
        else:
            comp = next_car.pos.y
            
        prec_car = self.cars_dict_last.get((dir, comp), False)
        next_car.next_car = prec_car
        self.cars_dict[dir].add([next_car])
        
        self.cars_dict_last[(dir, comp)] = next_car                
        self.number_cars += 1
        
    def set_light(self, dir, value):
        self.lights_dict[dir] = value

    def switch_light(self, dir):
        self.lights_dict[dir] = not self.lights_dict[dir]

    def get_lights(self):
        return self.lights_dict
    
    def max_wait_time(self):
        '''
        Maximum waiting time among cars that are waiting
        '''
        res = 0
        for _, cars in self.cars_dict.items():
            for car in cars:
                res = max(res, car.waiting_time)
        return res

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
                
    def move_at_yellow(self):
        for dir, cars in self.cars_dict.items():
            for car in cars:
                if not Setup.STOP_ZONES[dir].collidepoint(car.rect.center):
                    car.move()
                        
                
    def check_at_yellow(self, yellows):
        for dir in yellows:
            if len(self.cars_dict[dir])>0:
                for car in self.cars_dict[dir]:
                    if car.is_at_intersection():
                        return True
        return False


    def stop_behind_car(self):
        """
        Function that checks for every car if it should stop behind another car.
        """       
        for dir, cars in self.cars_dict.items():
            for car in cars:
                if car.driving:
                    car.check_next_car()
        
    def update_waiting(self):
        ''' Update waiting time (for all) '''
        for direct, light_green in self.lights_dict.items():
            if not light_green:
                self.apply_to_each_car(Car.update_waiting, dir=direct)
                         
    def check_crash(self):
        """
        Function that checks if two cars are colliding.
        """
        for dir, car_group in self.cars_dict.items():
            if len(car_group)>0:
                all_rest = pygame.sprite.Group()
                others_to_add = [v.sprites() for k, v in self.cars_dict.items() if (k!=dir) and (len(v)>0)]
                others_to_add = [v for k in others_to_add for v in k if v.is_at_intersection()]
                all_rest.add(*[others_to_add])
                collisions = pygame.sprite.groupcollide(car_group, all_rest, False, False)
                
                if len(collisions)>0:
                    return True
        return False
    

    def can_add_car(self, dir):
        """
        Function to verify whether a new car can be added or not (lane already full)
        """
        car_group = self.cars_dict[dir]
        car = Car(direction=dir)
        
        # same road lane
        if dir in ["north", "south"]:
            comp = car.pos.x
        else:
            comp = car.pos.y
            
        prec_car = self.cars_dict_last.get((dir, comp), False)       
         
        return (True if not prec_car else not car.rect.colliderect(prec_car.rect))    # pygame.sprite.spritecollide(car, car_group, dokill=False )


    def update_score(self):
        for dir, car_group in self.cars_dict.items():
            for car in car_group:
                if car.is_off_screen():
                    car_group.remove(car)
                    self.score += 1

        return self.score
    

    def update_logic(self):
        """
        Wrapper function to make all game updates
        """
        self.move_cars()
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

