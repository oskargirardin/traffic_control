import gymnasium as gym
import numpy as np
import os, sys
import time
import sys
import traffic_control_game
import pygame


# Initialization of environment, passing variables to verify experiments

 # number of autonomous Pygame steps between each of the player's actions
env_steps = 150 
# maximum cap on waiting time (used as a terminal condition)
max_waiting_time = 25  
# probability of generation for each lane 
# (we set the same frequency for the two axis east-west and north-south, with the former doubling the latter by construction)
ps_ns = np.random.uniform(low=0.025, high=0.035, size=1)
ps_ew = np.random.uniform(low=0.06, high=0.065, size=1)
ps = np.tile(np.concatenate((ps_ns, ps_ew)), 2)

# passing init dictionary to environment
env_info = {"ps": ps, "max_wait_time": max_waiting_time, "env_steps": env_steps, "n_states": 2}        
        
# environment instantiation
env = gym.make("traffic_control-v0", env_info=env_info, render_mode="human") 
obs, info = env.reset()

# Anonymous function loop
actions_loop =  [0]*2 + [1]

i = 0

while True:
    # Select next action
    action = actions_loop[i%len(actions_loop)]   

    # Appy action and return new observation of the environment
    obs, reward, done, _, info = env.step(action)

    # Visualization
    print(obs, "*** reward:", reward, "*** action:", action, "*** info: ", info)

    # Render the game
    env.render()
    i+=1

    if done:
        break

env.close()

