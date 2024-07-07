import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union
from ..util.constant import DATA_BUILDINGS_PATH, DATA_CONFIGURATION_PATH, DATA_WEATHER_PATH
from ..util.constant import LOG_LEVEL_MODEL_JSON, ENERGYPLUS_DIR
from ..util.logger import Logger
from eppy.modeleditor import IDF

class Generator(object):

    logger = Logger().getLogger(name="generator", level=LOG_LEVEL_MODEL_JSON)

    def __init__(self) -> None:
        self.conf_name: str = "default_configuration"
        # handle
        self.variables: Dict[str, Dict[str, str]] = {}
        self.internal_variables: Dict[str, Dict[str, str]] = {}
        self.meters: Dict[str, str] = {}
        self.actuators: Dict[str, Dict[str, str]] = {}
        # out
        self.out_path: str = None
        self.current_path: str = None
        # file
        self.weather_file: str = None
        self.idf_file: str = None
        self.idd_file: str = os.path.join(ENERGYPLUS_DIR + "Energy+.idd")

        IDF.setiddname(self.idd_file)
        self.idf = IDF(self.idf_file)

    def set_file_path(self, weather_file, idf_file, out_path):
        self.out_path = out_path
        self.weather_file = weather_file
        self.idf_file = idf_file

    def _load_file_path(self, file_dict:Dict[str, str]) -> None:
        self.out_path = file_dict["out_path"]
        self.weather_file = file_dict["weather_file"]
        self.idf_file = file_dict["idf_file"]
        print(self.out_path)

    def make_new_out_dir(self, name:str, episode:int):
        assert os.path.exists(self.out_path)
        new_out_dir_name = name + str(episode)
        new_dir = os.path.join(self.out_path, new_out_dir_name)
        assert not os.path.exists(new_dir)
        # assert not os.mkdir(new_dir)
        self.current_path = new_dir

    def load_by_data(self, conf_path):
        """
        load conf by file.
        """
        if not os.path.exists(conf_path):
            self.logger.warning(f"no file named {conf_path}.")
            return
        with open(conf_path, "r", encoding="utf-8") as conf_data:
            conf_data_str = conf_data.read()
            conf_data_json = json.loads(conf_data_str)
            self._load_variable_handle(conf_data_json["variables"])
            self._load_actuator_handle(conf_data_json["actuators"])
            self._load_meter_handle(conf_data_json["meters"])
            self._load_iternal_variables_handle(conf_data_json["internal_variables"])
            self._load_file_path(conf_data_json["path"])

    def save_to_file(self, save_path:str):
        """
        save config to file.
        """
        if not os.path.exists(save_path):
            self.logger.warning(f"no dir named {save_path}")
            return
        
        save_file_path = os.path.join(save_path, self.conf_name+".json")
        if os.path.exists(save_file_path):
            self.logger.warning(f"conf file named {self.conf_name}.json already exist.")
            return
        
        with open(save_file_path, "w+", encoding="utf-8") as save_file_stream:
            save_dict = {}
            # handles
            save_dict["variables"] = self.variables
            save_dict["actuators"] = self.actuators
            save_dict["internal_variables"] = self.internal_variables
            save_dict["meters"] = self.meters
            path_dict = {}
            # path
            path_dict["weather_file"] = self.weather_file
            path_dict["idf_file"] = self.idf_file
            path_dict["out_path"] = self.out_path
            save_dict["path"] = path_dict
            conf_str = json.dumps(save_dict)
            save_file_stream.write(conf_str)

    def add_variable_handle(self, name:str, variable_name:str, variable_key:str) -> None:
        """
        set variable handle using in running energyplus.
        :param variable name: The name of the variable to retrieve, e.g. "Site Outdoor Air DryBulb Temperature",
            or "Fan Air Mass Flow Rate".
        :param variable_key: The instance of the variable to retrieve, e.g. "Environment", or "Main System Fan" 
        """
        if name in self.variables.keys():
            self. loger.warning(f"A variable handel named {name} already exists.")
            return
        variable = {"variable_name":variable_name, "variable_key": variable_key}
        self.variables[name] = variable

    def _load_variable_handle(self, handle_dict: dict) -> None:
        for handle_name, handle_val in handle_dict.items():
            self.variables [handle_name] = handle_val

    def add_actuator_handle(self, name:str, component_type:str, control_type:str, actuator_type:str) -> None:
        """
        set actuator handle.
        :param component_type: The actuator category, e.g. "weather Data"
        :param control_type:. The name of the actuator to retrieve, e.g. "Outdoor Dew Point":param actuator_key: The instance of the variable to retrieve, e.g. "Environment"
        """
        if name in self.actuators.keys():
            self.loger.warning(f"A actuator handle named {name} already exists.")
            return
        actuator = {"component_type":component_type, "control_type":control_type, "actuator_type":actuator_type}
        self.actuators[name] = actuator

    def _load_actuator_handle(self, handle_dict:dict) -> None:
        for handle_name, handle_val in handle_dict.items():
            self.actuators[handle_name] = handle_val

    def add_inteinal_variable_handle(self, name:str, variable_type:str, variable_key:str):
        """    
        :param variable type: The name of the variable to retrieve, e.g. "Zone Air Volume", or "Zone Floor Area"
        :param variable_key: The instance of the variable to retrieve, e.g. "Zone 1"
        """
        if name in self.internal_variables.keys():
            self.loger.warning(f"An internal variable named {name} already exists.")
            return
        interal_variable = {"variable_name":variable_type, "variable_key":variable_key}
        self.internal_variables[name] = interal_variable

    def _load_iternal_variables_handle(self, handle_dict:dict)-> None:
        for handle_name, handle_val in handle_dict.items():
            self.internal_variables[handle_name] = handle_val

    def add_meter_handle(self, name:str, meter_name:str) -> None:
        """
        :param meter_name: The name of the variable to retrieve, e.g. "Electricity:Fancility", or "Fans:Electricity"
        """
        for name in self.meters.keys():
            self.logger.warning(f"meter named {name} already exist.")
        self.meters[name] = meter_name

    def _load_meter_handle(self, handle_dict: Dict) -> None:
        for handle_name, meter_name in handle_dict.items():
            self.meters[handle_name] = meter_name
