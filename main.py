import gymnasium as gym
import numpy as np
import os, sys
import time
import sys
import traffic_control_game
import pygame


env = gym.make("traffic_control-v0", render_mode="human") 
obs, info = env.reset()
while True:
    # Select next action
    action = [0, 1]# env.action_space.sample()    # for an agent, action = agent.policy(observation)

    # Appy action and return new observation of the environment
    obs, reward, done, _, info = env.step(action)

    print(obs, "*** reward:", reward)

    # Render the game
    #os.system("clear")
    #time.sleep(0.1)
    env.render()

    if done:
        break

env.close()