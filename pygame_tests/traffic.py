import pygame
from pygame_setup import *
from draw import *
from objects import *


# Initialize Pygame
pygame.init()

# Set up the window
window = pygame.display.set_mode((Setup.WIDTH, Setup.HEIGHT))
pygame.display.set_caption("Traffic Control")


#Lights:  Top   Right Bott. Left
lights = [True, True, True, True]

# A car
my_cars = []
# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                lights[3] = not lights[3]
            if event.key == pygame.K_UP:
                lights[0] = not lights[0]
            if event.key == pygame.K_RIGHT:
                lights[1] = not lights[1]
            if event.key == pygame.K_DOWN:
                lights[2] = not lights[2]
            if event.key == pygame.K_a:
                my_cars.append(Car(direction="left"))
            if event.key == pygame.K_w:
                my_cars.append(Car(direction="up"))
            if event.key == pygame.K_s:
                my_cars.append(Car(direction="down"))
            if event.key == pygame.K_d:
                my_cars.append(Car(direction="right"))
    # Update game state

    for car in my_cars:
        car.move()



    # Draw everything
    window.fill(Setup.GREY) # Fill the screen with black
    # Add additional drawing code here
    draw_background(window)
    draw_lights(window, *lights)
    # Draw car
    for car in my_cars:
        car.draw(window)
    pygame.display.update() # Update the screen
    
# Quit Pygame
pygame.quit()
