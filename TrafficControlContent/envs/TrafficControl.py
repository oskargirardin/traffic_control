import gymnasium as gym
import numpy as np
import os
import time
import sys

class TrafficControlEnv(gym.Env):
    def __init__(self, 
               height = 40,
               width = 40):
        self._screen_size = (width,height)
        self._game = None
        self._render = None

    def render(self, mode = "human"):
        characters = {
            1: " ",
            0: "@"
        }
        r = np.zeros((self._screen_size[0],self._screen_size[1]), dtype='int32')
        self._render = r
        
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                r_str += characters[r[i,j]]
            r_str += '\n'
        
        return r_str

    def reset(self):
        pass
    
    def close(self):
        pass