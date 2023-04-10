
import gymnasium as gym
from gymnasium import spaces

import pygame
import numpy as np
import os
import time
import sys

from traffic_control_game.envs.draw import *
from traffic_control_game.envs.logic import *
    

class TrafficControlEnv(gym.Env):
    
    metadata = {"render_modes": ["human"], "render_fps": 60}
    dirs = ["east", "north", "west", "south"]
    
    
    def __init__(self, n_actions, render_mode=None):
        
        self.n_actions = n_actions

        self.setup = Setup
        self.window_size = (self.setup.WIDTH, self.setup.HEIGHT) 
        self.render_mode = render_mode
        self.dt = None   # for movement of cars, initialized later (from clock.tick())
        self.max_car_in_line = 99   #   max amount of car queuing??
        self.ps = self.np_random.uniform(low=0.01, high=0.05, size=len(self.dirs))  # probabilities of car generation for each line??
        self.game = None  # game (initialized in reset)
        # render
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        
        # observation space
        self.observation_space = spaces.Dict({
                                            dir_: spaces.Discrete(self.max_car_in_line, start=0)
                                            for dir_ in self.dirs
                                              })
        
        # action space
        #self.action_space = spaces.MultiDiscrete([2]*len(self.dirs))
        self.action_space = spaces.Discrete(self.n_actions)
        
        # if human-rendering is used will be initialized
        self.window = None
        self.clock = None
        
        
        
    def _get_obs(self):
        ''' translates the environment state into an observation 
            to be updated in .step if we want additional info'''
        
        # number of waiting cars in each line
        waiting = [0]*len(self.dirs)
        for idx, (dir, sprites) in enumerate(self.game.cars_dict.items()):
            for car in sprites:
                waiting[idx] += int(not car.driving)
        return {dir: wait for dir, wait in zip(self.dirs, waiting)}
    
    
    def _get_info(self):
        ''' auxiliary info returned '''
        return {"score": self.game.score}
    
    
    def reset(self, seed=None, options=None):
        ''' called before step and anytime done is issued
            returns tuple of initial observation and auxiliary info
            use self.np_random to fix the seed to a deterministic state
        ''' 

        super().reset(seed=seed)  
        
        self.game = Game(self.dirs)

        observation = {dir: 0 for dir in self.dirs}  # 0 waiting cars at the beginning
        info = {"score": 0}

        self.render()

        return observation, info
    
    
    def step(self, action):
        ''' computes next state of environment by passing agent's action
            return 4-tuple (obs, reward, done, info)'''
        
        #for dir_light, value_light in zip(self.dirs, action):
        #    self.game.set_light(dir_light, bool(value_light))
        if action == 0:
            self.game.set_light("south", True)
            self.game.set_light("north", True)
            self.game.set_light("east", False)
            self.game.set_light("west", False)
        elif action == 1:
            self.game.set_light("east", False)
            self.game.set_light("west", False)
            self.game.set_light("south", True)
            self.game.set_light("north", True)
        elif action == 2:
            self.game.set_light("east", False)
            self.game.set_light("west", False)
            self.game.set_light("south", False)
            self.game.set_light("north", False)
        elif action == 3:
            self.game.set_light("east", True)
            self.game.set_light("west", True)
            self.game.set_light("south", True)
            self.game.set_light("north", True)
        
        terminated = False

        # Let the environment run for multiple frames with the same action -> light switch appear less often
        for _ in range(self.setup.N_ENV_STEPS):
            # Draw cars randomly  (respecting seed from gym.Env)
            draws = self.np_random.binomial(1, p=self.ps)
            cars_to_add = np.array(self.dirs)[np.argwhere(draws==1).ravel()]
            for dir in cars_to_add:
                self.game.add_car(dir)
                
            # Update game state
            self.game.move_cars(self.dt)  
            self.game.check_lights()
            self.game.stop_behind_car()
            self.game.update_score()

            observation = self._get_obs()
            info = self._get_info()
            
            # Consistent reward (from https://www.sciencedirect.com/science/article/pii/S0950705123001909)
            reward = - np.sum(list(observation.values()))

            if self.render_mode == "human":
                self.render()

            # Conditions for termination (others to be added???)
            if self.game.check_crash():
                reward = -10000  # negative rewards for termination??
                terminated = True
                break
        
        

        return observation, reward, terminated, False, info
    

    def render(self):
        if self.window is None and self.render_mode == "human":
            # Initialize Pygame
            pygame.init()
            pygame.font.init()
            pygame.display.init()
            # Set up the window
            self.window = pygame.display.set_mode(self.window_size)
            pygame.display.set_caption("Traffic Control")
            
            
        if self.clock is None and self.render_mode == "human":
            self.clock = pygame.time.Clock()
            
        if self.render_mode == "human":
            # Draw everything
            draw_all(self.window, self.game.lights_dict, self.game.score, self.game.number_cars)
            self.game.draw_cars(self.window)
        
            # Handle events
            for event in pygame.event.get():
                    
                # inverted here as I found it more intuitive (not gonna use them anyway)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.game.switch_light("west")
                    if event.key == pygame.K_UP:
                        self.game.switch_light("north")
                    if event.key == pygame.K_RIGHT:
                        self.game.switch_light("east")
                    if event.key == pygame.K_DOWN:
                        self.game.switch_light("south")
        
            # Update the screen
            pygame.display.update()

            # We need to ensure that human-rendering occurs at the predefined framerate.
            # The following line will automatically add a delay to keep the framerate stable.
            self.dt = self.clock.tick(self.metadata["render_fps"])
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                        # Quit Pygame
                        self.close()
            
        else:  # rgb_array
            pass
        
        self.dt = 20 # Keeping the same speed of cars so that the agent learns for a fixed speed (indep. of CPU speed)
        
    def close(self):
        ''' close any open resources that were used by the environment '''
        if self.window is not None:
            pygame.quit()
            sys.exit()
            