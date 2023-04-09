import pygame
import sys
from pygame_setup import *
from draw import *
from objects import *
from logic import *

# Initialize Pygame
pygame.init()

# Set up the window
window = pygame.display.set_mode((Setup.WIDTH, Setup.HEIGHT))
pygame.display.set_caption("Traffic Control")

score, iter, num_cars = 0, 0, 0
crash = False
dirs = ["left", "down", "right", "up"]

T = 1000
n_cars_per_round = 50

cars_fun = [Setup.cos_fun(100, T, 0, 130), Setup.cos_fun(100, T, 500, 130), Setup.cos_fun(100, T, 1000, 130), Setup.cos_fun(100, T, 1500, 130)]
iter_left = [fun(0) for fun in cars_fun]

round_done = False
# Initialize game
my_game = Game()
# Clock
clock = pygame.time.Clock()

# Game loop
running = True
while running:
    dt = clock.tick(60)
    iter = (iter+1) % T
    iter_left = [x-1 for x in iter_left]
    if not round_done:
        for dir, n_iter in enumerate(iter_left):
            if n_iter <= 0:
                my_dir = dirs[dir]
                my_game.add_car(my_dir)
                iter_left[dir] = cars_fun[dir](iter)
                num_cars += 1

    # Handle events
    for event in pygame.event.get():
        
        if event.type == pygame.QUIT: 
            # Quit Pygame
            pygame.quit()   # running = False
            sys.exit()
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                my_game.switch_light("right")
            if event.key == pygame.K_UP:
                my_game.switch_light("down")
            if event.key == pygame.K_RIGHT:
                my_game.switch_light("left")
            if event.key == pygame.K_DOWN:
                my_game.switch_light("up")

    # Update game state
    score = my_game.update_logic(dt, score)

    # Draw everything
    draw(window, my_game.lights_dict, score, num_cars)
    my_game.draw_cars(window)

    if num_cars >= n_cars_per_round:
        round_done = True

    if round_done and (not my_game.cars_on_screen()):
        running = False

    pygame.display.update()  # Update the screen

