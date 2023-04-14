import gymnasium as gym
import numpy as np
import os, sys
import time
import sys
import traffic_control_game
import pygame


env = gym.make("traffic_control-v0", n_states = 2,render_mode="human") 
obs, info = env.reset()


#actions_loop = [0]*5 + [1]*5 + [0] + [1]*5 + [0] + [1]*5
#actions_loop = [2]*10+[0]
actions_loop = [0]*10

i = 0

while True:
    # Select next action
    action = actions_loop[i%len(actions_loop)]               #env.action_space.sample()    # for an agent, action = agent.policy(observation)

    # Appy action and return new observation of the environment
    obs, reward, done, _, info = env.step(action)

    print(obs, "*** reward:", reward, "*** action:", action)

    # Render the game
    #os.system("clear")
    #time.sleep(0.1)
    env.render()
    i+=1

    if done:
        break

env.close()