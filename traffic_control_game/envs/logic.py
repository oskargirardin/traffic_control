from collections import defaultdict
import pygame
import math
import numpy as np
import os
from pygame.rect import Rect
import pygame
import math



# Initialization of pygame
pygame.font.init()

# Macro variables
IMAGE_DIR = "img"
IMAGES = os.listdir(IMAGE_DIR)
ANGLES = {"south": 0, "north": 180, "east": 90, "west": 270}


def get_movement(direction):
    """ Function called at the instantiation of each car. 
        It sets the basis vector determining the direction (for the movement on the screen at each iteration)
        As well as the initial position (which determines the traffic lane, drawn randomly)

    Args:
        direction (str): direction in which we want to generate the next car

    Returns:
        tuple: basis vector for direction
        Point: 2-d coordinates determining the center of the rect for a car
    """
    dist_center = Setup.DIST_CENTER
    center_x, center_y = Setup.CENTER_X, Setup.CENTER_Y
    width, height = Setup.WIDTH, Setup.HEIGHT

    movements = {"north": (0, 1), "south": (0, -1), "east": (-1, 0), "west": (1, 0)}
    
    # random choice between two possible distances (for the two traffic lanes)
    nudg_o, nudg_e = Setup.NUDGE, - Setup.NUDGE
    nudges = [nudg_o, nudg_e]
    
    # initial positions (later moved using the basis vector of movement)
    initial_pos = {"north": (center_x-dist_center/2-np.random.choice(nudges), 0), "south": (center_x+dist_center/2-np.random.choice(nudges), height),
                   "east": (width, center_y-dist_center/2-np.random.choice(nudges)), "west": (0, center_y+dist_center/2-np.random.choice(nudges))}
    
    return movements[direction], Point(initial_pos[direction])



class Setup:
    """ Class that stores all macro-level variables on which the logic is based
        to allow for encapsulation and easy control
    """
    
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
    # Center of each side
    CENTER_Y = HEIGHT//2
    CENTER_X = WIDTH//2
    # Displacement that characterized the two traffic lanes
    NUDGE = 8.5 
    # Dimensions of each car
    CAR_HEIGHT = 20
    CAR_WIDTH = 12
    CAR_SPEED = 1
    # Maximum number of cars waiting, defining the boundaries of the observation space
    MAX_CARS_NS = 2*((CENTER_Y - DIST_CENTER)//CAR_HEIGHT + 1) 
    MAX_CARS_WE = 2*((CENTER_X - DIST_CENTER)//CAR_HEIGHT + 1) 

    # Stop areas placed in front of each traffic light (a Pygame surface)
    STOP_LENGTH = 10
    STOP_ZONES = {
        "north": Rect(CENTER_X-DIST_CENTER, CENTER_Y-DIST_CENTER-STOP_LENGTH, DIST_CENTER, STOP_LENGTH),
        "south": Rect(CENTER_X, CENTER_Y+DIST_CENTER, DIST_CENTER, STOP_LENGTH),
        "east": Rect(CENTER_X+DIST_CENTER,CENTER_Y-DIST_CENTER, STOP_LENGTH, DIST_CENTER),
        "west": Rect(CENTER_X-DIST_CENTER-STOP_LENGTH, CENTER_Y, STOP_LENGTH, DIST_CENTER)
    }
    # Pygame surface defining the intersection area (to check for collision, during yellow lights for instance)
    INTERSECT_AREA = Rect(CENTER_X-DIST_CENTER, CENTER_Y-DIST_CENTER, 2*DIST_CENTER, 2*DIST_CENTER)

    # Pygame font
    geneva50 = pygame.font.SysFont("geneva", 50)

    def cos_fun(A, T, phi, k):
        """ Function used at the beginning for car generation (thought of defining different arrival rates)
            Not used eventually
        """
        return lambda x: A*math.cos(2*math.pi*x/T + phi)+k
    
    

class Point:
    """ Class defining the concept of Point, used for collision as well as car movements
        It implements some common point operation such as translation and dot product, useful throughout the game
    """

    def __init__(self, point_t=(0, 0)):
        """ Setting of x and y coordinate
        """
        self.x = float(point_t[0])
        self.y = float(point_t[1])

    def __add__(self, other):
        """ Addition operation
        """
        return Point((self.x + other.x, self.y + other.y))

    def __sub__(self, other):
        """ Difference operator
        """
        return Point((self.x - other.x, self.y - other.y))

    def __mul__(self, scalar):
        """ Multiplication operator
        """
        return Point((self.x*scalar, self.y*scalar))

    def __div__(self, scalar):
        """ Division operator
        """
        return Point((self.x/scalar, self.y/scalar))

    def __len__(self):
        """ Eucledian norm of vector
        """
        return int(math.sqrt(self.x**2 + self.y**2))

    def dot(self, other):
        """ Dot product between vectors
        """
        return np.array(self.get()).dot(np.array(other.get()))
    
    def dist(self, other):
        """ Eucledian distance between points
        """
        return int(math.sqrt((self.x-other.x)**2 + (self.y-other.y)**2))
        
    def get(self):
        """ Get method to access coordinates
        """
        return (self.x, self.y)



class Car(pygame.sprite.Sprite):
    """ Class for Car, at the basis of traffic control, handled by a Game instantiation
    """

    def __init__(self, direction="north"):
        # init of superclass Sprite
        super().__init__()

        self.direction = direction
        # get basis vector for direction and initial position
        self.moving, self.pos = get_movement(direction)
        # store useful measures from the Setup class
        self.width = Setup.CAR_WIDTH
        self.height = Setup.CAR_HEIGHT
        self.speed = Setup.CAR_SPEED
        # boolean stating whether car moving or not (red light)
        self.driving = True
        self.waiting_time = 0
        # reference to the next car are stored for efficiency issues (avoid double loops for checking)
        self.next_car = None
        # once passed the intersection, this attribute is changed to avoid additional checks for stopping
        # (for efficiency issues)
        self.pass_intersection = False
        # pick a random image from the repertory, scale and rotate it depending on the direction
        self.image = pygame.image.load(os.path.join(os.getcwd(), IMAGE_DIR, np.random.choice(IMAGES)))
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.image = pygame.transform.rotate(self.image, ANGLES[self.direction])
        # set the center of the image (pygame surface) at the initial coordinates
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos.x, self.pos.y)
            
    def check_next_car(self):
        """ Check for the necessity of stopping (hitting the next car in the traffic lane)
            If the car is not the first in the lane and it has not yet passed the intersection,
            a check is performed regarding the distance from the next car (keeping a buffer for esthetics)
        """
        if (self.next_car != False) and (not self.pass_intersection) and (Point(self.next_car.rect.center).dist(Point(self.rect.center))<= 1.18*self.height):
            self.stop()

    def move(self):
        """ Main function applied to each car on the screen to displace it (if it is moving)
        """
        if self.driving:
            self.pos = Point(self.rect.center) +  Point(self.moving)*self.speed
            self.rect.center = (self.pos.x, self.pos.y)
            # every time the car moves, waiting time is reset to 0
            self.reset_waiting()
            # if not yet passed the intersection, we check (once) if this has happened after the movement
            if (not self.pass_intersection) and (self.is_at_intersection()):
                self.pass_intersection = True
 
    def stop(self):
        """ Method setting driving to False if car is steady
        """
        self.driving = False

    def go(self):
        """ Method setting driving to False if a red/yellow light is present
        """
        self.driving = True
        
    def reset_waiting(self):
        """ Method called inside self.move() to reset the waiting time to 0 every time
            the car moves
        """
        self.waiting_time = 0
    
    def update_waiting(self):
        """ Method to autoincrement waiting time (once for each of agent's action, if car keeps
            remaining steady)
        """
        if not self.driving:
            self.waiting_time += 1

    def draw(self, surface: pygame.display):
        """ Blit the car on the Pygame screen

        Args:
            surface (pygame.display): active Pygame screen
        """
        surface.blit(self.image, self.rect)
        
    def is_at_intersection(self):
        """ Method used to check if the intersection area defined in Setup
            collides with the car's surface

        Returns:
            bool: whether the car is at the intersection or not
        """
        return Setup.INTERSECT_AREA.collidepoint(self.rect.center)

    def is_at_light(self):
        """ Method used to check if the car is one of the first in a traffic lane before
            the intersection, that is its surface is colliding with the stopping area (one for 
            each direction)

        Returns:
            bool: whether the car is at the stopping area
        """
        return pygame.Rect.colliderect(self.rect, Setup.STOP_ZONES[self.direction])

    def should_stop(self):
        """ Wrapping function that incorporates the logic that if car is colliding with the stopping area
            (and the light is either red or yellow) then it should stop (self.driving set to False), otherwise
            it's free to go
        """
        if self.is_at_light():
            self.stop()
        else:
            self.go()

    def is_off_screen(self):
        """ Method called during the game at each iteration to check if some of the cars have managed to cross the
            intersection (they are not out of the active screen). If they are, they are removed from the Pygame groups
            and the score is updated

        Returns:
            bool: whether the car is still on the active screen or not
        """
        screen_rect = pygame.Rect(-self.width, -self.height, Setup.WIDTH+2*self.width, Setup.HEIGHT+2*self.height)
        return not pygame.Rect.colliderect(self.rect, screen_rect)
    

class Game:
    """ Game class to track and take care of all the dynamics
    """
    
    def __init__(self, dirs):
        """ Initialization

        Args:
            dirs (list of str): list of possible directions, passed by the environment (we changed the def on  the way)
        """
        # dictionary storing the car groups, one for each direction
        self.cars_dict = {dir: pygame.sprite.Group() for dir in dirs} 
        # dictionary with a bool for each traffic light to determine the color
        self.lights_dict = {dir: True for dir in dirs} 
        # dictionary used to store the last car in each lane (to assign to each car its .next car in an optimized manner)
        self.cars_dict_last = defaultdict()
        self.dirs = dirs
        self.number_cars = 0
        self.score = 0

    def move_cars(self):
        """ Move all cars (if they are driving)
        """
        for _, cars in self.cars_dict.items():
            for car in cars:
                car.move()    

    def apply_to_each_car(self, fun, dir = None):
        """ Function used to apply a method to every car on the screen in an encapsulated manner

        Args:
            fun (callable): method to trigger for each car
            dir (str, optional): if present, the function is applied only to the subgroup of cars in the specified direction.
                                 Defaults to None.
        """
        if dir:
            for car in self.cars_dict[dir]:
                fun(car)
        else:
            for _, cars in self.cars_dict.items():
                for car in cars:
                    fun(car)       
        
    def add_car(self, dir):
        """ Method used to add a new car in a specified direction
            If first checkes if an additional car can be added (lanes not full), then it sets
            the car that was previously the last in the lane as the next car for the new one,
            and finally stores the new car as the last in a lane

        Args:
            dir (str): direction for which we want a new car
        """
        # check if new car would not overlap with any of the existing ones (lane is full)
        if not self.can_add_car(dir):
            return
        next_car = Car(direction=dir)
        
        # same road lane
        if dir in ["north", "south"]:
            comp = next_car.pos.x
        else:
            comp = next_car.pos.y
            
        # get car that was previously the last one in the given lane
        prec_car = self.cars_dict_last.get((dir, comp), False)
        # sets it as the next car of the new car
        next_car.next_car = prec_car
        # stores the new car as the last one in the lane
        self.cars_dict[dir].add([next_car])
        
        self.cars_dict_last[(dir, comp)] = next_car                
        self.number_cars += 1
        
    def set_light(self, dir, value):
        """ Access method to set the traffic light of the specified direction
            to a specified value

        Args:
            dir (str): direction, to identify the corresponding light
            value (bool): whether to light it up (green) or not (red)
        """
        self.lights_dict[dir] = value

    def switch_light(self, dir):
        """ Method similar to the one above, used to switch the color of the traffic light
            (dependent on the existing value attached to it)

        Args:
            dir (str): specified direction to identify the corresponding traffic light
        """
        self.lights_dict[dir] = not self.lights_dict[dir]

    def get_lights(self):
        """ Get method to access the dictionary of light values (storing all the colors active at the moment)

        Returns:
            dict: dictionary storing the values of each traffic light
        """
        return self.lights_dict
    
    def max_wait_time(self):
        """ Method to access the maximum waiting time among the waiting cars
            as those not moving have a waiting time equal to 0

        Returns:
            int: maximum waiting time across all the cars on the screen
        """
        res = 0
        for _, cars in self.cars_dict.items():
            for car in cars:
                res = max(res, car.waiting_time)
        return res

    def draw_cars(self, surface):
        """ Wrapper function used to draw all the cars on screen

        Args:
            surface (pygame surface): active screen
        """
        for _, cars in self.cars_dict.items():
            for car in cars:
                car.draw(surface)

    def check_lights(self):
        """ Function that checks if the lights are red or green and updates movement of each car
        """
        for dir, green in self.lights_dict.items():
            if green: # Light is green
                self.apply_to_each_car(Car.go, dir=dir)
            if not green: # Light is red
                self.apply_to_each_car(Car.should_stop, dir=dir)
                
    def move_at_yellow(self):
        """ Method used to move the cars that are still driving and not colliding with the corresponding
            stopping area (dependent on the car's direction), that is used to clear the intersection at any
            change of lights ("yellow" light)
        """
        for dir, cars in self.cars_dict.items():
            for car in cars:
                if not Setup.STOP_ZONES[dir].collidepoint(car.rect.center):
                    car.move()
                        
                
    def check_at_yellow(self, yellows):
        """ Method used to check in any of the specified directions (yellows, that is those switching from
            green to red) there are cars still at the intersection, in order to wait for them to pass

        Args:
            yellows (list of str): list of directions that switched from green to red (called within the environment)

        Returns:
            bool: boolean describing whether there is at least one car still at the intersection, to be waited for
        """
        for dir in yellows:
            if len(self.cars_dict[dir])>0:
                for car in self.cars_dict[dir]:
                    if car.is_at_intersection():
                        return True
        return False


    def stop_behind_car(self):
        """ Function that checks for every car on the screen whether it should stop behind another car.
        """       
        for dir, cars in self.cars_dict.items():
            for car in cars:
                if car.driving:
                    car.check_next_car()
        
    def update_waiting(self):
        """ Update waiting time (for all cars not driving, that is those that are waiting)
            Called once for all the cars present on screen, once for each action taken by the agent
        """
        for direct, light_green in self.lights_dict.items():
            if not light_green:
                self.apply_to_each_car(Car.update_waiting, dir=direct)
                         
    def check_crash(self):
        """ Function that checks if two cars belonging to different directions are colliding.
            The same condition with respect to a given traffic lane is in fact implemented by
            .check_next_car()

        Returns:
            bool: whether a collision has happened on the screen or not
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
        """ Function to verify whether a new car can be added or not (lane already full)

        Args:
            dir (str): specified direction of the new car we want to add (randomly sampled according to the given
                       probabilities)

        Returns:
            bool: whether the new car is colliding with any of the already existing cars on the lane or not
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
        """ Wrapper function that calls .is_off_screen() to check if any of the existing cars has left the screen
            In case this happened, the car is removed from the Sprite groups which contains all instances
            For any of the cars that left the screen, the score is auto-incremented
    

        Returns:
            int: updated score to be included in the information dictionary of the environment
        """
        for dir, car_group in self.cars_dict.items():
            for car in car_group:
                if car.is_off_screen():
                    car_group.remove(car)
                    self.score += 1

        return self.score
    

    def update_logic(self):
        """ Wrapper function to make all game updates, eventually not used since difference in the procedure
            between red and yellow lights

        Returns:
            int: updated score
        """
        self.move_cars()
        self.check_lights()
        self.stop_behind_car()
        if self.check_crash():
            score = 0
        score = self.update_score(score)
        return score 
        
    def update_interval(self, iter_count, fun):
        """ Not used eventually """
        return int(fun(iter_count))
    
    def cars_on_screen(self):
        """ Get function to return whether any car is present on the screen or not

        Returns:
            bool: specifying this condition
        """
        for _, cars in self.cars_dict.items():
            if len(cars) > 0:
                return True
        return False

