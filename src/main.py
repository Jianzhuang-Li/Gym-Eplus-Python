import sys
import os
import logging

import pyenergyplus.api

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
# energyplus_dir = root_dir + "/3rdparty/EnergyPlusV24-1-0"
energyplus_dir = "C:/EnergyPlusV24-1-0"

# insert the repo build tree or install path into the search Path, then import the EnergyPlus APIs
sys.path.insert(0, energyplus_dir)
import pyenergyplus

# path of idf and weather file
weather_dir = root_dir + "/weather"
model_dir = root_dir + "/model"

# setup logger
logger = logging.getLogger()
logging.basicConfig(level = logging.INFO,format = '%(asctime)s-%(filename)s-%(lineno)d-%(levelname)s: %(message)s')
logger = logging.getLogger()

api_version = pyenergyplus.api.EnergyPlusAPI.api_version()
logger.info(f"PyEnergyPlus Version {api_version}")

api_path = pyenergyplus.api.api_path()
logger.info(api_path)

# run energy_plus api
api = pyenergyplus.api.EnergyPlusAPI()
state = api.state_manager.new_state()
idf_to_run = energyplus_dir + "/ExampleFiles/5ZoneAirCooled.idf"

api.runtime.run_energyplus(state,
    [
        '-w', weather_dir+"/USA_CO_Golden-NREL.724666_TMY3.epw",
        '-d', 'out',
        idf_to_run
    ]
)

