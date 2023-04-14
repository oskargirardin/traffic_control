import pygame
import math
from traffic_control_game.envs.logic import *


dist_center = Setup.DIST_CENTER
center_y = Setup.CENTER_Y
center_x = Setup.CENTER_X
    

def draw_dashed_line(display, color, start_pos, end_pos, width=1, dash_length=10):
    origin = Point(start_pos)
    target = Point(end_pos)
    displacement = target - origin
    length = len(displacement)
    slope = displacement.__div__(length) 

    for index in range(0, length//dash_length, 2):
        start = origin + (slope *    index    * dash_length)
        end   = origin + (slope * (index + 1) * dash_length)
        pygame.draw.line(display, color, start.get(), end.get(), width)

def draw_background(display):
    global dist_center, center_y, center_x
    # Draw grass
    pygame.draw.rect(display, color=Setup.GREEN, rect = pygame.rect.Rect(0, 0, center_x-dist_center, center_y-dist_center))
    pygame.draw.rect(display, color=Setup.GREEN, rect = pygame.rect.Rect(center_x+dist_center, 0, center_x-dist_center, center_y-dist_center))
    pygame.draw.rect(display, color=Setup.GREEN, rect = pygame.rect.Rect(center_x+dist_center, center_y+dist_center, center_x-dist_center, center_y-dist_center))
    pygame.draw.rect(display, color=Setup.GREEN, rect = pygame.rect.Rect(0, center_y+dist_center, center_x-dist_center, center_y-dist_center))
    # Horizontal lines (horizontal road)
    pygame.draw.line(display , Setup.BLACK, (0, center_y-dist_center), (center_x-dist_center, center_y-dist_center), width = 2)
    pygame.draw.line(display , Setup.BLACK, (center_x+dist_center, center_y-dist_center), (Setup.WIDTH, center_y-dist_center), width = 2)
    pygame.draw.line(display , Setup.BLACK, (0, center_y+dist_center), (center_x-dist_center, center_y+dist_center), width = 2)
    pygame.draw.line(display , Setup.BLACK, (center_x+dist_center, center_y+dist_center), (Setup.WIDTH, center_y+dist_center), width = 2)
    # Vertical lines (vertical road)
    pygame.draw.line(display , Setup.BLACK, (center_x-dist_center, 0), (center_x-dist_center, center_y-dist_center), width = 2)
    pygame.draw.line(display , Setup.BLACK, (center_x-dist_center, center_y+dist_center), (center_x-dist_center, Setup.HEIGHT), width = 2)
    pygame.draw.line(display , Setup.BLACK, (center_x+dist_center, 0), (center_x+dist_center,  center_y-dist_center), width = 2)
    pygame.draw.line(display , Setup.BLACK, (center_x+dist_center, center_y+dist_center), (center_x+dist_center, Setup.HEIGHT), width = 2)
    # Lines on roads
    draw_dashed_line(display, Setup.WHITE, (0, Setup.HEIGHT//2), (center_x-dist_center, Setup.HEIGHT//2), width=2, dash_length=10)
    draw_dashed_line(display, Setup.WHITE, (center_x+dist_center, Setup.HEIGHT//2), (Setup.WIDTH, Setup.HEIGHT//2), width=2, dash_length=10)
    draw_dashed_line(display , Setup.WHITE, (Setup.WIDTH//2, 0), (Setup.WIDTH//2,  center_y-dist_center), width = 2, dash_length=10)
    draw_dashed_line(display , Setup.WHITE, (Setup.WIDTH//2, center_y+dist_center), (Setup.WIDTH//2, Setup.HEIGHT), width = 2, dash_length=10)
    # Stop lines
    #pygame.draw.line(display , Setup.WHITE, (center_x-dist_center, center_y-dist_center), (center_x, center_y-dist_center), width = 1)
    #pygame.draw.line(display , Setup.WHITE, (center_x-dist_center, center_y+dist_center), (center_x-dist_center, center_y), width = 1)
    #pygame.draw.line(display , Setup.WHITE, (center_x+dist_center, center_y+dist_center), (center_x, center_y+dist_center), width = 1)
    #pygame.draw.line(display , Setup.WHITE, (center_x+dist_center, center_y-dist_center), (center_x+dist_center, center_y), width = 1)


def draw_lights(display, lights_dict, yellows):
    global dist_center, center_y, center_x
    # Stop lines
    pygame.draw.line(display , Setup.GREEN if lights_dict["north"] else Setup.RED, (center_x-dist_center, center_y-dist_center), (center_x, center_y-dist_center), width = 1)
    pygame.draw.line(display , Setup.GREEN if lights_dict["west"] else Setup.RED, (center_x-dist_center, center_y+dist_center), (center_x-dist_center, center_y), width = 1)
    pygame.draw.line(display , Setup.GREEN if lights_dict["south"] else Setup.RED, (center_x+dist_center, center_y+dist_center), (center_x, center_y+dist_center), width = 1)
    pygame.draw.line(display , Setup.GREEN if lights_dict["east"] else Setup.RED, (center_x+dist_center, center_y-dist_center), (center_x+dist_center, center_y), width = 1)
    
    for dir in yellows:
        draw_yellow(display, dir)
        
def draw_yellow(display, dir):
    global dist_center, center_y, center_x
    if dir=="north":
        pygame.draw.line(display , Setup.YELLOW, (center_x-dist_center, center_y-dist_center), (center_x, center_y-dist_center), width = 1)
    elif dir=="west":
        pygame.draw.line(display , Setup.YELLOW, (center_x-dist_center, center_y+dist_center), (center_x-dist_center, center_y), width = 1)
    elif dir=="south":
        pygame.draw.line(display , Setup.YELLOW, (center_x+dist_center, center_y+dist_center), (center_x, center_y+dist_center), width = 1)
    else:  # east
        pygame.draw.line(display , Setup.YELLOW, (center_x+dist_center, center_y-dist_center), (center_x+dist_center, center_y), width = 1)
        

def draw_text(display, text, font, pos, color):
    text_surface = font.render(text, True, color)
    display.blit(text_surface, pos)

def draw_score(display, score, font, color):
    draw_text(display, f"Score: {score}", font, (50,50), color)


def draw_all(display, lights_dict, score, num_cars, yellows=[]):
    display.fill(Setup.GREY) # Fill the screen with black
    draw_background(display)
    draw_lights(display, lights_dict, yellows)
    draw_score(display, score, Setup.geneva50, Setup.BLACK)
    draw_text(display, f"Cars past: {num_cars}", Setup.geneva50, (50, 100), Setup.BLACK)
