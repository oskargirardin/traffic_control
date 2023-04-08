from collections import defaultdict
from objects import *

class Game:
    
    def __init__(self) -> None:
        self.cars_dict = {"up": pygame.sprite.Group(), "down": pygame.sprite.Group(), "left": pygame.sprite.Group(), "right": pygame.sprite.Group()}
        self.lights_dict = {"up": True, "down": True, "left": True, "right": True}


    def move_cars(self, dt):
        for _, cars in self.cars_dict.items():
            for car in cars:
                car.move(dt)

    def apply_to_each_car(self, fun, dir = None):
        if dir:
            for car in self.cars_dict[dir]:
                fun(car)
        else:
            for direction, cars in self.cars_dict.items():
                for car in cars:
                    fun(car)
    
    def add_car(self, dir):
        self.cars_dict[dir].add([Car(direction=dir)])

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
                cars_in_front_group = pygame.sprite.Group()
                for car_in_front in cars_in_front:
                    cars_in_front_group.add([car_in_front])
                crash = pygame.sprite.spritecollideany(car, cars_in_front_group)
                if crash:
                    car.stop()
    
    def check_crash(self):
        """
        Function that checks if two cars are colliding.
        """
        checked_groups = set()
        for dir1, car_group1 in self.cars_dict.items():
            for dir2, car_group2 in self.cars_dict.items():
                if dir1 == dir2:
                    continue
                checked_groups.add((dir2, dir1))
                if (dir1, dir2) in checked_groups:
                    continue
                collisions = pygame.sprite.groupcollide(car_group1, car_group2, False, False)
                for _, collisions_in_group2 in collisions.items():
                    if collisions_in_group2:
                        return True
        return False
    
    def update_score(self, score):
        for _, car_group in self.cars_dict.items():
            for car in car_group:
                if car.is_off_screen():
                    car_group.remove(car)
                    score += 1
        return score
    

    def update_logic(self, dt, score):
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
            if cars.has():
                return True
        return False

