from gym.envs.registration import register

register(
    id='traffic_control_v0',
    entry_point='TrafficControlContent.envs:TrafficControl'
)
