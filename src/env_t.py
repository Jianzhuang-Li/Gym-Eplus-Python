import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)
from gym_energyplus.env.eplus_env import EplusEnv
from gym_energyplus.util.constant import DATA_CONFIGURATION_PATH

conf = os.path.join(DATA_CONFIGURATION_PATH, "default_configuration.json")

def reward_func(obs):
    # oat = obs["OAT"]
    core_top_temp = obs["Core_top_temp"]
    reward_term = {"oat_reward": core_top_temp}
    return round(core_top_temp), reward_term


env = EplusEnv(conf, reward_func)
terminal = False
truncated = False
env_timestep = 0
sim_temstep = 0

for i in range(5):
    if i > 0:
        env_timestep = env.timestep
        sim_temstep = env.energyplus_simulator.timestep
        print(env_timestep, sim_temstep)
    obs, info = env.reset()
    terminal = False
    truncated = False
    while not terminal and not truncated:
        act = [obs[0], obs[1]]
        # print(act)
        obs, reward, terminal, truncated, info = env.step(act)
