import sys
import os
import logging
import json
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)
sys.path.append(config['EnergyPlusPath']) 
import pyenergyplus.api

# run energy_plus api
api = pyenergyplus.api.EnergyPlusAPI()
state = api.state_manager.new_state()


class CallbackFunc:
    def  __init__(self, logger) -> None:
        self.callback_state = 0
        self.logger = logger

    def begin_zone_timestemp(self, state_argue):
        self.callback_state = self.callback_state + 1
        # cur = api.exchange.month(state)\
        zone_step_num = api.exchange.zone_time_step_number(state)
        zone_step = api.exchange.zone_time_step(state)
        year = api.exchange.year(state)
        hour = api.exchange.hour(state)
        current_time = api.exchange.current_time(state)
        self.logger.info(f"call back state: {self.callback_state}, current_time:{current_time}")

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
energyplus_dir = config['EnergyPlusPath']

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


call_func = CallbackFunc(logger)
api.runtime.callback_begin_zone_timestep_after_init_heat_balance(state, call_func.begin_zone_timestemp)

idf_to_run = energyplus_dir + "/ExampleFiles/5ZoneAirCooled.idf"

api.runtime.run_energyplus(state,
    [
        '-w', weather_dir+"/USA_CO_Golden-NREL.724666_TMY3.epw",
        '-d', 'out',
        idf_to_run
    ]
)
