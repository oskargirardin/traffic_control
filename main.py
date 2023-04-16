import gymnasium as gym
import numpy as np
import os, sys
import time
import sys
import traffic_control_game
import pygame


env_steps = 150
max_waiting_time = 25
ps_ns = np.random.uniform(low=0.025, high=0.035, size=1)
ps_ew = np.random.uniform(low=0.06, high=0.065, size=1)
ps = np.tile(np.concatenate((ps_ns, ps_ew)), 2)

env_info = {"ps": ps, "max_wait_time": max_waiting_time, "env_steps": env_steps, "n_states": 2}        
        
env = gym.make("traffic_control-v0", env_info=env_info, render_mode="human") 
obs, info = env.reset()


actions_loop =  [1]*10 

i = 0


print(env.observation_space)
while True:
    # Select next action
    action = actions_loop[i%len(actions_loop)]               #env.action_space.sample()    # for an agent, action = agent.policy(observation)

    # Appy action and return new observation of the environment
    obs, reward, done, _, info = env.step(action)

    print(obs, "*** reward:", reward, "*** action:", action, "*** info: ", info)

    # Render the game
    #os.system("clear")
    #time.sleep(0.1)
    env.render()
    i+=1

    if done:
        break

env.close()

