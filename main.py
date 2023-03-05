import gymnasium as gym
import numpy as np
import os
import time
import sys
import TrafficControlContent
#test
    
if __name__ == "__main__":
    # initiate environment
    #print(gym.envs.registry.keys())
    env = gym.make("traffic_control-v0")
    #obs = env.reset()

    # iterate
    while True:

        # Select next action
        #action = env.action_space.sample()  # for an agent, action = agent.policy(observation)

        # Appy action and return new observation of the environment
        #obs, reward, done, info = env.step(action)

        # Render the game
        os.system("clear")
        sys.stdout.write(env.render())
        time.sleep(0.2) # FPS

        # If player is dead break
        #if done:
        #    break

    env.close()
