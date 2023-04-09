import gymnasium as gym
import numpy as np
import os, sys
import time
import sys
import traffic_control_game
    
if __name__ == "__main__":
    # initiate environment
    #print(gym.envs.registry.keys())
    env = gym.make("traffic_control-v0", render_mode="human") 
    obs, info = env.reset()

    # iterate
    while True:

        # Select next action
        action = env.action_space.sample()    # for an agent, action = agent.policy(observation)

        # Appy action and return new observation of the environment
        obs, reward, done, _, info = env.step(action)

        # Render the game
        os.system("clear")
        env.render()

        if done:
            break

    env.close()
