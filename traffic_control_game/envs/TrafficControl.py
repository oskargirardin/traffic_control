
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
    
    dirs = ["north", "east", "south", "west"]
    dirs2 = ["NS", "WE"]
    dir_index = {"north": 0, "east": 1, "south": 2, "west": 3}
    
    action_mapper = {0: {"north": True, "east": False,  "south": True, "west": False},
                     1: {"north": False, "east": True,  "south": False, "west": True},
                     2: {"north": False, "east": False,  "south": False, "west": False},
                     3: {"north": True, "east": False,  "south": True, "west": True},
                     4: {"north": True, "east": True,  "south": False, "west": False},   # noisy
                     5: {"north": False, "east": False,  "south": True, "west": True}   # noisy
                    }
    
    def __init__(self, n_states, render_mode=None):
        
        self.n_actions = len(self.action_mapper)

        self.setup = Setup
        self.window_size = (self.setup.WIDTH, self.setup.HEIGHT) 
        self.render_mode = render_mode
        #self.dt = None   # for movement of cars, initialized later (from clock.tick())
        #self.ps = self.np_random.uniform(low=0.01, high=0.05, size=len(self.dirs)) 
        
        self.ps_ns = self.np_random.uniform(low=0.078, high=0.088, size=1)
        self.ps_ew = self.np_random.uniform(low=0.01, high=0.02, size=1)
        self.ps = np.tile(np.concatenate((self.ps_ns, self.ps_ew)), 2)
        self.game = None  # game (initialized in reset)
        
        # render
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        
        # observation space
        self.n_states = n_states
        # 4-states or 2-states version
        if self.n_states == 4:
            self.observation_space = spaces.Dict(
                {
                "north": spaces.Discrete(Setup.MAX_CARS_NS, start=0),
                "south": spaces.Discrete(Setup.MAX_CARS_NS, start=0),
                "east": spaces.Discrete(Setup.MAX_CARS_WE, start=0),
                "west": spaces.Discrete(Setup.MAX_CARS_WE, start=0),
                }
            )
        elif self.n_states == 2:
            self.observation_space = spaces.Dict(
                {
                "NS": spaces.Discrete(2*Setup.MAX_CARS_NS, start=0),
                "WE": spaces.Discrete(2*Setup.MAX_CARS_WE, start=0)
                }
            )

        # action space
        #self.action_space = spaces.MultiDiscrete([2]*len(self.dirs))
        self.action_space = spaces.Discrete(self.n_actions)
        self.previous_action = None
        
        # if human-rendering is used will be initialized
        self.window = None
        self.clock = None
        
        
        
    def _get_obs(self):
        ''' translates the environment state into an observation 
            to be updated in .step if we want additional info'''
        
        # number of waiting cars in each line
        waiting = [0]*self.n_states
        for dir, sprites in self.game.cars_dict.items():
            for car in sprites:
                # Add cars to waiting list. Modulo takes care of 2-state and 4-state scenarios.
                waiting[self.dir_index[dir]%self.n_states] += int(not car.driving)
                    
        if self.n_states == 2:
            return {dir: wait for dir, wait in zip(self.dirs2, waiting)}
        else:
            return {dir: wait for dir, wait in zip(self.dirs, waiting)}
    
    
    def _get_info(self):
        ''' auxiliary info returned '''
        return {"score": self.game.score, "max_wait_time": self.game.max_wait_time()}
    
    
    def reset(self, seed=None, options=None):
        ''' called before step and anytime done is issued
            returns tuple of initial observation and auxiliary info
            use self.np_random to fix the seed to a deterministic state
        ''' 

        super().reset(seed=seed)  
        
        self.game = Game(self.dirs)

        observation = {dir: 0 for dir in self.dirs2} if self.n_states == 2 else {dir: 0 for dir in self.dirs} # 0 waiting cars at the beginning
        self.previous_action = 2   # all red
        
        info = {"score": 0}
        self.render()

        return observation, info
    
    
    def step(self, action):
        ''' computes next state of environment by passing agent's action
            return 4-tuple (obs, reward, done, info)'''
        
        if action != self.previous_action:
            yellows = []
            for (_, prev_light),(new_direct, new_light) in zip(self.action_mapper[self.previous_action].items(), self.action_mapper[action].items()):
                if (prev_light) and (not new_light):
                    yellows.append(new_direct)

            while self.game.check_at_yellow(yellows):
                # Update game state            
                self.game.move_at_yellow()  
                self.game.stop_behind_car()
                self.game.update_score()
                
                if self.render_mode == "human":
                
                    draw_all(self.window, self.game.lights_dict, self.game.score, self.game.number_cars, yellows)
                    self.game.draw_cars(self.window)
                    # Update the screen
                    pygame.display.update()
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT: 
                                # Quit Pygame
                                self.close()  
                    
        for dir_light, value_light in self.action_mapper[action].items():
            self.game.set_light(dir_light, value_light)
                
        terminated = False
        self.previous_action = action   # need interaction with previous action to set the yellow light

        # Let the environment run for multiple frames with the same action -> light switch appear less often        
        for _ in range(self.setup.N_ENV_STEPS):
                        
            # Draw cars randomly  (respecting seed from gym.Env)
            draws = self.np_random.binomial(1, p=self.ps)
            cars_to_add = np.array(self.dirs)[np.argwhere(draws==1).ravel()]
            for dir in cars_to_add:
                self.game.add_car(dir)
                
            # Update game state
            self.game.move_cars()  
            self.game.check_lights()
            self.game.stop_behind_car()
            self.game.update_score()

            observation = self._get_obs()
            info = self._get_info()
            
            # Consistent reward (from https://www.sciencedirect.com/science/article/pii/S0950705123001909)
            reward = - np.sum(list(observation.values())) - int(0.025*self.game.max_wait_time())
            
            if self.render_mode == "human":
                self.render()

            # Conditions for termination (others to be added???)
            if self.game.check_crash():
                reward = -1000  # negative rewards for termination??
                terminated = True
                break
            
        # Positive reward if there is not any car waiting
        #if np.sum(list(observation.values()))==0:
        #    reward=25
            
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
                
                if event.type == pygame.QUIT: 
                    # Quit Pygame
                    self.close()
        
            # Update the screen
            pygame.display.update()
            
        else:  # rgb_array
            pass
        
        #self.dt = 20 # Keeping the same speed of cars so that the agent learns for a fixed speed (indep. of CPU speed)
        
    def close(self):
        ''' close any open resources that were used by the environment '''
        if self.window is not None:
            pygame.quit()
            sys.exit()
            