import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)
from gym_energyplus.envs.gym_energyplus import GymEnergyPlus
import os
import json
import logging
conf_path = 'D:\\lijianzhuang\\Reaserch\\new-research\\Gym-EnergyPlus\\DRL-EnergyPlus\\gym_eplus\config.json'
with open(conf_path, 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
print(root_dir)
plat_form = sys.platform
energyplus_dir = config[f'EnergyPlusPath_v24_{plat_form}']

# setup logger
logger = logging.getLogger()
logging.basicConfig(level = logging.INFO,format = '%(asctime)s-%(filename)s-%(lineno)d-%(levelname)s: %(message)s')
logger = logging.getLogger()

# path of idf and weather file
# weather_dir = root_dir + "\\weather\\USA_CO_Golden-NREL.724666_TMY3.epw"
weather_dir = root_dir + "\\weather\\USA_NY_New.York-John.F.Kennedy.Intl.AP.744860_TMY3.epw"
out_dir = root_dir + "\\out"
print(weather_dir)
print(out_dir)
#idf_to_run = energyplus_dir + "/ExampleFiles/5ZoneAirCooled.idf"
# idf_to_run = energyplus_dir + "\\ExampleFiles\\EMSCustomOutputVariable.idf"
# idf_to_run = root_dir + "\model\ASHRAE901_ApartmentHighRise_STD2022_NewYork.idf"
idf_to_run = "D:\\lijianzhuang\\Reaserch\\new-research\\idf_model\\ASHRAE901_OfficeLarge_STD2022_NewYork.idf"

sim = GymEnergyPlus(weather_dir, out_dir, idf_to_run, logger)
sim.run()
