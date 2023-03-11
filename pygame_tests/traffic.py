import pygame
from pygame_setup import *
from draw import *
from objects import *
from logic import *

# Initialize Pygame
pygame.init()

# Set up the window
window = pygame.display.set_mode((Setup.WIDTH, Setup.HEIGHT))
pygame.display.set_caption("Traffic Control")

score = 0
crash = False
iter = 0
T = 2000
cars_fun = [Setup.cos_fun(100, T,0, 200),Setup.cos_fun(100, T,0, 200), Setup.cos_fun(100, T,0, 200), Setup.cos_fun(100, T,0, 200)]
iter_left = [fun(0) for fun in cars_fun]
dirs = ["left", "down", "right", "up"]
# A car
my_game = Game()
# Clock
clock = pygame.time.Clock()
# Game loop
running = True
while running:
    dt = clock.tick(60)
    iter = (iter+1)%T
    iter_left = [x-1 for x in iter_left]
    for dir, n_iter in enumerate(iter_left):
        if n_iter <= 0:
            my_dir = dirs[dir]
            my_game.add_car(my_dir)
            iter_left[dir] = cars_fun[dir](iter)
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                my_game.switch_light("left")
            if event.key == pygame.K_UP:
                my_game.switch_light("up")
            if event.key == pygame.K_RIGHT:
                my_game.switch_light("right")
            if event.key == pygame.K_DOWN:
                my_game.switch_light("down")
            if event.key == pygame.K_a:
                my_game.add_car("left")
            if event.key == pygame.K_w:
                my_game.add_car("up")
            if event.key == pygame.K_s:
                my_game.add_car("down")
            if event.key == pygame.K_d:
                my_game.add_car("right")

    # Add cars


    # Update game state
    my_game.move_cars(dt)
    my_game.check_lights()
    my_game.stop_behind_car()
    if my_game.check_crash():
        score = 0
    score = my_game.update_score(score)
    # Draw everything
    window.fill(Setup.GREY) # Fill the screen with black
    # Add additional drawing code here
    draw_background(window)
    draw_lights(window, my_game.lights_dict)
    # Draw car
    my_game.draw_cars(window)
    # Draw score
    draw_score(window, score, Setup.geneva50, Setup.BLACK)
    pygame.display.update() # Update the screen
    
# Quit Pygame
pygame.quit()
