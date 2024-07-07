import os

current_dir = os.path.dirname(__file__)
pkg_dir = os.path.dirname(current_dir)

# data
DATA_BUILDINGS_PATH = os.path.join(pkg_dir, "data\\buildings")
assert(os.path.exists(DATA_BUILDINGS_PATH))
DATA_WEATHER_PATH = os.path.join(pkg_dir, "data\\weather")
assert(os.path.exists(DATA_WEATHER_PATH))
DATA_CONFIGURATION_PATH = os.path.join(pkg_dir,"data\\configuration")

# logger
LOG_FORMAT = "%(asctime)s-%(filename)s-%(lineno)d-%(levelname)s: %(message)s"

# logger level
LOG_LEVEL_MODEL_JSON = 'INFO'
LOG_LEVEL_GYM_ENV = 'INFO'
LOG_REWARD_LEVEL = 'DEBUG'

# year
YEAR = '2017'

# ENERGYPLUS_DIR 
ENERGYPLUS_DIR = os.getenv("ENERGYPLUS_DIR")

if __name__ == "__main__":
    print(current_dir)
    print(ENERGYPLUS_DIR)
    print(DATA_BUILDINGS_PATH)