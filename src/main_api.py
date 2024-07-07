import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)
from gym_energyplus.simulators.gym_energyplus import GymEnergyPlus
from gym_energyplus.util.constant import DATA_CONFIGURATION_PATH, DATA_BUILDINGS_PATH, DATA_WEATHER_PATH
from gym_energyplus.generator.generator import Generator
from gym_energyplus.util.logger import Logger, LOG_LEVEL_MODEL_JSON
import time
from queue import Queue
# setup logger

logger = Logger().getLogger("main_api", LOG_LEVEL_MODEL_JSON)

out_dir ='D:\\lijianzhuang\\Reaserch\\new-research\\Gym-EnergyPlus\\DRL-EnergyPlus\\gym_eplus\\out'
weather = os.path.join(DATA_WEATHER_PATH,'USA_NY_New.York-John.F.Kennedy.Intl.AP.744860_TMY3.epw')
idf_file = os.path.join(DATA_BUILDINGS_PATH,'ASHRAE901_OfficeLarge_STD2022_NewYork.idf')
conf = os.path.join(DATA_CONFIGURATION_PATH,"default_configuration.json")

logger.info(weather)
logger.info(idf_file)
logger.info(conf)
gen = Generator()
gen.load_by_data(conf)
gen.weather_file = weather 
gen.idf_file = idf_file 
gen.out = out_dir
obs_queue = Queue(maxsize=1)
info_queue = Queue(maxsize=1)
act_queue = Queue(maxsize=1)
sim = GymEnergyPlus(logger, gen, obs_queue, info_queue, act_queue)
for i in range(2):
    sim.reset()
    sim.run()
    #sim.data_ task.submit()
    while not sim.simulation_complete:
        time.sleep(5)
