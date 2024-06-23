import sys
sys.path.append("/home/jianzhuang/Research/Gym-Eplus-Python")
from gym_energyplus.envs.gym_energyplus import GymEnergyPlus
import os
import json
import logging
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
print(root_dir)
energyplus_dir = config['EnergyPlusPath']

# setup logger
logger = logging.getLogger()
logging.basicConfig(level = logging.INFO,format = '%(asctime)s-%(filename)s-%(lineno)d-%(levelname)s: %(message)s')
logger = logging.getLogger()

# path of idf and weather file
weather_dir = root_dir + "/weather/USA_CO_Golden-NREL.724666_TMY3.epw"
out_dir = root_dir + "/out"
print(weather_dir)
print(out_dir)
#idf_to_run = energyplus_dir + "/ExampleFiles/5ZoneAirCooled.idf"
idf_to_run = energyplus_dir + "/ExampleFiles/EMSCustomOutputVariable.idf"


sim = GymEnergyPlus(weather_dir, out_dir, idf_to_run, logger)
sim.run()

