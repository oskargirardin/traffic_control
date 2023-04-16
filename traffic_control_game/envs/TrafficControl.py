
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
    """ Implementation of Gym environment for Traffic Control,
        with one intersection, four roads and two traffic lanes of cars per road
    """
    
    # macro variable of the environment
    metadata = {"render_modes": ["human"], "render_fps": 60}
    
    # car directions (different formulations, we used the second)
    dirs = ["north", "east", "south", "west"]
    dirs2 = ["NS", "WE"]
    dir_index = {"north": 0, "east": 1, "south": 2, "west": 3}
    
    # mapper of actions to Traffic Lights Phases, for each direction the boolean indicates whether 
    # the light is green or red. The first 2 actions are optimal (optimal policy is to alternate)
    # 3rd is feasible but not optimal (all lights green), 4th 5th and 6th cause collission
    # and the agent should learn not to select them
    action_mapper = {0: {"north": True, "east": False,  "south": True, "west": False},
                     1: {"north": False, "east": True,  "south": False, "west": True},
                     2: {"north": False, "east": False,  "south": False, "west": False},
                     3: {"north": True, "east": True,  "south": True, "west": True},
                     4: {"north": True, "east": True,  "south": False, "west": False},   # noisy
                     5: {"north": False, "east": False,  "south": True, "west": True}   # noisy
                    }
    
    def __init__(self, env_info, render_mode=None):
        """ Initialization, most of arguments are only stated, will be initialized in reset
            It defines action and observation space
            
            Args:
            env_info (dict): dictionary for initialization with 
                            "ps": probability of generation for the direction
                            "max_wait_time": upper bound on waiting time (condition for termination)
                            "env_steps": autonomous loops of the environment between each of agent's action
        """
        
        # number of actions
        self.n_actions = len(self.action_mapper)

        # setup encapsulating all macro variables
        self.setup = Setup
        # pygame screen
        self.window_size = (self.setup.WIDTH, self.setup.HEIGHT) 
        self.render_mode = render_mode
        
        # game 
        self.game = None  
        # default probability of generation (uniform)
        self.ps = env_info.get("ps", np.array([1/self.n_actions]*self.n_actions))
        # max waiting time (condition for termination)
        self.max_wait_time = env_info.get("max_wait_time", 1500)
        # autonomous loops of Pygame environment for each agent's action
        self.env_steps = env_info.get("env_steps", 50) 
        
        # render
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        
        # observation space
        self.n_states = env_info.get("n_states", 2) 
        
        # 4-states or 2-states version (eventually we used 2 states)
        if self.n_states == 4:
            self.observation_space = spaces.Dict(
                {
                "north": spaces.Discrete(Setup.MAX_CARS_NS, start=0),
                "south": spaces.Discrete(Setup.MAX_CARS_NS, start=0),
                "east": spaces.Discrete(Setup.MAX_CARS_WE, start=0),
                "west": spaces.Discrete(Setup.MAX_CARS_WE, start=0),
                "wt": spaces.Discrete(self.max_wait_time),
                "pa": spaces.Discrete(self.n_actions)
                }
            )
            
        # NS and WE are number of waiting cars on the two axis (considered together)
        # WT is maximum waiting time, PA is previous active phase (previous action)
        elif self.n_states == 2:
            self.observation_space = spaces.Dict(
                {
                "NS": spaces.Discrete(2*Setup.MAX_CARS_NS, start=0),
                "WE": spaces.Discrete(2*Setup.MAX_CARS_WE, start=0),
                "WT": spaces.Discrete(self.max_wait_time),
                "PA": spaces.Discrete(self.n_actions)
                }
            )

        # action space
        self.action_space = spaces.Discrete(self.n_actions)
        self.previous_action = None
        
        # if human-rendering is used will be initialized
        self.window = None
        self.clock = None      
        
    def _get_obs(self):
        ''' Translates the environment state into an observation
        
            Returns:
            dict: dictionary containing 
                - negative sum of waiting cars for each direction
                - max waiting time (used as component of reward)
                - previous action (active phase)
        '''
        
        # number of waiting cars in each line
        waiting = [0]*self.n_states
        for dir, sprites in self.game.cars_dict.items():
            for car in sprites:
                # add cars to waiting list. modulo takes care of 2-state and 4-state scenarios.
                waiting[self.dir_index[dir]%self.n_states] += int(not car.driving)
        
        # maximum waiting time recovered from the active game
        # previous action is stored in the environment  
        if self.n_states == 2:
            return {**{dir: wait for dir, wait in zip(self.dirs2, waiting)}, 
                    **{"WT": self.game.max_wait_time(), "PA": self.previous_action} }
        else:
            return {**{dir: wait for dir, wait in zip(self.dirs, waiting)},
                    **{"wt": self.game.max_wait_time(), "pa": self.previous_action}}
    
    
    def _get_info(self):
        ''' Function returning info dictionary (environment information not used in decision process)
        
        Returns:
            dict: dictionary containing score (number of cars that exited the screen)
        '''
        return ({"score": self.game.score})    
    
    def reset(self, seed=None, options=None):
        ''' Called before step and anytime done is issued, returns tuple of initial observation and auxiliary info
            self.np_random has been used to fix the seed to a deterministic state
            
            Returns:
            dict: dictionary describing the next state (information available to the agent),
            dict: info dictionary (containing score)
        ''' 
        
        # enviroment seed
        super().reset(seed=seed)  
        
        self.game = Game(self.dirs)
        
        # initial action is the red phase (all lights are turned off)
        self.previous_action = 2   

        # 0 waiting cars at the beginning
        dir_wait = {dir: 0 for dir in self.dirs2} if self.n_states == 2 else {dir: 0 for dir in self.dirs} 
        observation = {**dir_wait, **{"WT": 0, "PA": self.previous_action}} if self.n_states == 2 else {**dir_wait, **{"wt": 0, "pa": self.previous_action}}
        
        info = {"score": 0}
        
        # starting pygame screen
        self.render()

        return observation, info
    
    
    def step(self, action):
        ''' Computes next state of environment by passing agent's action
        
            Returns:
                dict: dictionary describing next state
                float: reward, function of state information (consistent reward)
                bool: terminated, indicating whether episode is finished or not
                dict: info dictionary
        '''
        
        # to implement yellow lights, we track the lights that were green, turning red with new action
        if action != self.previous_action:
            yellows = []
            for (_, prev_light),(new_direct, new_light) in zip(self.action_mapper[self.previous_action].items(), self.action_mapper[action].items()):
                if (prev_light) and (not new_light):
                    yellows.append(new_direct)
            
            # pygame loop until all cars in the considered lanes have passed the intersection
            while self.game.check_at_yellow(yellows): 
                self.game.move_at_yellow()   # move cars
                self.game.stop_behind_car() # check to stop before next cars
                self.game.update_score()  # updating cars that exited the sc    
                
                # visualize these changes if rendering is active
                if self.render_mode == "human":
                    # draw background, visual score, lights and cars
                    draw_all(self.window, self.game.lights_dict, self.game.score, self.game.number_cars, yellows)
                    self.game.draw_cars(self.window)
                    # update the screen
                    pygame.display.update()
                    # check for quitting
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT: 
                                # quit Pygame
                                self.close()  
           
        # switch to next phase, setting all appropriate lights         
        for dir_light, value_light in self.action_mapper[action].items():
            self.game.set_light(dir_light, value_light)
                
        terminated = False
        self.previous_action = action   # need interaction with previous action to set the yellow light
        self.game.update_waiting()  # update maximum waiting time (considered as number of user actions in which car does not move)

        # environment runs autonomously for multiple frames between actions        
        for _ in range(self.env_steps):
                        
            # generate cars according to given probabilities of appearence and draw them (respecting seed from gym.Env)
            draws = self.np_random.binomial(1, p=self.ps)
            cars_to_add = np.array(self.dirs)[np.argwhere(draws==1).ravel()]
            for dir in cars_to_add:
                self.game.add_car(dir)
                
            # update game state
            self.game.move_cars()  
            self.game.check_lights()
            self.game.stop_behind_car()
            self.game.update_score()

            # get next state and info
            observation = self._get_obs()
            info = self._get_info()
            
            # consistent reward (from https://www.sciencedirect.com/science/article/pii/S0950705123001909)
            reward = - np.sum(list(observation.values())[:2]) - int(8*list(observation.values())[2])
            
            # render pygame if expected
            if self.render_mode == "human":
                self.render()

            # Conditions for termination: 1. crash, 2. maximum waiting time surpassed
            if self.game.check_crash() or self.game.max_wait_time()>self.max_wait_time:
                reward = -5000  
                terminated = True
                break
                    
        return observation, reward, terminated, False, info
    

    def render(self):
        """ Function to handle Pygame
        """
        # initialize pygame if screen does not exist yet (first call in reset)
        if self.window is None and self.render_mode == "human":
            pygame.init()
            pygame.font.init()
            pygame.display.init()
            # set up the window
            self.window = pygame.display.set_mode(self.window_size)
            pygame.display.set_caption("Traffic Control")
            
        # initialize clock to control FPS of the screen
        if self.clock is None and self.render_mode == "human":
            self.clock = pygame.time.Clock()
            
        if self.render_mode == "human":
            # draw everything
            draw_all(self.window, self.game.lights_dict, self.game.score, self.game.number_cars)
            self.game.draw_cars(self.window)
        
            # handle events
            for event in pygame.event.get():
                    
                # used only during experiments (user control of lights switch)
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
                    # quit Pygame
                    self.close()
        
            # Update the screen
            pygame.display.update()
        
         # rgb_array
        else: 
            pass  # not implemented
        
    def close(self):
        ''' close any open resources that were used by the environment
        '''
        if self.window is not None:
            pygame.quit()
            sys.exit()
            