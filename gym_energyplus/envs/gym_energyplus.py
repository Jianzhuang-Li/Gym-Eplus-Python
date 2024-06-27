import numpy as np
# import gymnasium as gym
import json
import sys
import os
# from gymnasium import spaces

current_dir = os.path.dirname(os.path.abspath(__file__))
# add EnergyPlus intall path to the config.json file.
config_path = os.path.join(current_dir, 'config.json')
with open(config_path, 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)
sys.path.append(config['EnergyPlusPath']) 
import pyenergyplus.api


class GymEnergyPlus:

    def __init__(self, weather, out, idf, logger):
        """
        Init the EnergyPlus Simutation environment.
        """
        self.api_version = pyenergyplus.api.EnergyPlusAPI.api_version()
        self.api_path = pyenergyplus.api.api_path()
        self.api = pyenergyplus.api.EnergyPlusAPI()
        self.logger = logger
        self.eps_state = self.api.state_manager.new_state()
        self.weather = weather
        self.out = out
        self.idf = idf
        self.callback_state = 0
        if os.path.exists(self.weather) is False:
            raise Exception(f"Weather data {self.weather} not exist.")
        if os.path.exists(self.idf) is False:
            raise Exception(f"IDF data {self.idf} not exist.")
        if os.path.exists(self.out):
            logger.info(f"Use {self.out} as out dir.")
            if len(os.listdir(self.out)):
                logger.warning(f"Out path not empty, the old files will be overide.")
        else:
            raise Exception(f"Out dir {self.out} not exist")
        logger.info("Init Simulation:")
        logger.info(f"Weather: {self.weather}")
        logger.info(f"IDF: {self.idf}")

        self.run_cout = 0
        # define the handle used in simulation, handle_name:(var_name, var_key)
        self.handle_define_map = {}
        # save the handles got in runing 
        self.handle_map = {}
        self.got_handle = False
        self.set_handle()
        self.set_callback()
    
    def set_handle(self)->None:
        """
        Set handle name, variable name and key.
        The handle define map will be used by get_handle().
        """
        self.handle_define_map['T1'] = ("Zone Mean Air Temperature", "Perimeter_ZN_1")
        self.got_handle = False

    def get_handle(self):
        """
        Get handle via api.exchange.get_variable_handle.
        """
        if not self.got_handle:
            self.handle_map.clear()
            # Check whether the data exchange API is ready
            if not self.api.exchange.api_data_fully_ready(self.eps_state):
                for handle_name, var in self.handle_define_map.items():
                    var_name, var_key = var
                    self.handle_map[handle_name] = self.api.exchange.get_variable_handle(self.eps_state, var_name, var_key)
                    self.logger.info(f"Get handle {handle_name, var_name, var_key}.")
            else:
                return
            # Check if there are invalid handles.
            for handle_na, handle_var in self.handle_map.items():
                if handle_var == -1:
                    self.logger.warning(f"Invalid handle named {handle_na}")
                    sys.exit(1)
            self.got_handle = True
    
    def _get_obs(self):
        pass
    
    def _get_info(self):
        pass
    
    def reset(self, seed=None, options=None):
        """
        resets an existing state instance, thus resetting the simulation, including any registered callback functions.
        """
        self.api.state_manager.reset_state(self.eps_state)
        self.got_handle = False
        self.set_callback()
    
    def step(self):
        pass
    
    def render(self):
        pass

    def callable_begin_new_environment(self, state_argument):
        """
        1. Occurs once near the beginning of each environment period. 
        2. Environment periods include sizing periods, design days, and run periods.
        3. This calling point will not be useful for control actions, but is useful for initializing
        variables and calculations that do not need to be repeated during each timestep.
        """
        return None
    
    def callback_begin_zone_timestep_before_init_heat_balance(self, state_argument)->None:
        """
        1. This calling point is useful for controlling components that affect the building envelope 
        including surface constructions, window shades, and shading surfaces.
        2. Programs called from this point might actuate the building envelope or internal gains based
        on current weather or on the results from the previous timestep.
        3. Demand management routines might use this calling point to operate window shades, 
        change active window constructions, activate exterior shades, etc.
        """
        return None

    def callback_begin_zone_timestep_after_init_heat_balance(self, state_arguement)->None:
        """
        2. This calling point is useful for controlling components that affect the building envelope
        including surface constructions and window shades. 
        3. Programs called from this point might actuate the building envelope or internal gains based 
        on current weather or on the results from the previous timestep. 
        4. Demand management routines might use this calling point to operate window shades, change active window constructions, etc. 
        5. This calling point would be an appropriate place to modify weather data values.
        """
        self.get_handle()
        hour = self.hour()
        if hour == 23:
            if not self.got_handle:
                return 
            temp1 = self.api.exchange.get_variable_value(state_arguement, self.handle_map['T1'])
            current_sim_time = self.current_sim_time()
            self.logger.info(f"call back state: {self.callback_state}, sim_time:{current_sim_time}, temp:{temp1}")
            self.callback_state = self.callback_state + 1

    def callback_after_predictor_before_hvac_managers(self, state_argument)->None:
        """
        1. It occurs at each timestep just after the predictor executes but before SetpointManager and AvailabilityManager models are called.
        2. It is useful for a variety of control actions.
        3. However, if there are conflicts, the EMS control actions could be overwritten by other SetpointManager or AvailabilityManager actions.
        """
        self.get_handle()
        return None

    def callback_after_predictor_after_hvac_managers(self, state_argument)->None:
        """
        1. It occurs at each timestep after the predictor executes and after the SetpointManager 
        and AvailabilityManager models are called. 
        2. It is useful for a variety of control actions. 
        3. However, if there are conflicts, SetpointManager or AvailabilityManager actions may be
        overwritten by EMS control actions.
        """
        self.get_handle()
        return None
    
    def callback_begin_system_timestep_before_predictor(self, state_argument)->None:
        """
        1. The calling point called “BeginTimestepBeforePredictor” occurs near the beginning of each timestep 
        but before the predictor executes. 
        2. “Predictor” refers to the step in EnergyPlus modeling when the zone loads are calculated. 
        3. This calling point is useful for controlling components that affect the thermal loads the
        HVAC systems will then attempt to meet. 
        4. Programs called from this point might actuate internal gains based on current weather or on the results from the previous timestep.
        5. Demand management routines might use this calling point to reduce lighting or process loads, change thermostat settings, etc.
        """
        return None

    def callback_after_component_get_input(self, state_argument)->None:
        return None


    def set_callback(self)->None:
        """
        Register callback function to an active EnergyPlus “state”.
        """
        self.api.runtime.callback_begin_new_environment \
            (self.eps_state, self.callable_begin_new_environment)
        
        self.api.runtime.callback_begin_zone_timestep_before_init_heat_balance \
            (self.eps_state, self.callback_begin_zone_timestep_before_init_heat_balance)
        
        self.api.runtime.callback_begin_zone_timestep_after_init_heat_balance \
            (self.eps_state, self.callback_begin_zone_timestep_after_init_heat_balance)
        
        self.api.runtime.callback_begin_system_timestep_before_predictor \
            (self.eps_state, self.callback_begin_system_timestep_before_predictor)

        self.api.runtime.callback_after_predictor_before_hvac_managers \
            (self.eps_state, self.callback_after_predictor_before_hvac_managers)
        
        self.api.runtime.callback_after_predictor_after_hvac_managers \
            (self.eps_state, self.callback_after_predictor_after_hvac_managers)
        
    
    def run(self)->None:
        """
        run an energyplus simulation.
        """
        self.api.runtime.run_energyplus(self.eps_state,
                                        [
                                            '-w', self.weather,
                                            '-d', self.out,
                                            self.idf
                                        ]
                                        )
        self.run_cout = self.run_cout + 1
    
    def year(self)->int:
        """
        Get the "current" year of the simutation.
        """
        return self.api.exchange.year(self.eps_state)
    
    def month(self)->int:
        """
        Get the current month of the simutation(1-12).
        """
        return self.api.exchange.month(self.eps_state)
    
    def day_of_year(self)->int:
        """
        Get the current day of the year (1-366).
        """
        return self.api.exchange.day_of_year(self.day_of_year)
    
    def day_of_month(self)->int:
        """
        Get the current day of the month (1-31).
        """
        return self.api.exchange.day_of_month(self.eps_state)
    
    def day_of_week(self):
        """
         Get the current day of the week (1-7).
        """
        return self.api.exchange.day_of_week(self.eps_state)
    
    def hour(self)->int:
        """
        Get the current hour of the simulation (0-23).
        """
        return self.api.exchange.hour(self.eps_state)
    
    def minutes(self)->int:
        """
        Get the current minutes into the hour (1-60).
        """
        return self.api.exchange.minutes(self.eps_state)
    
    def current_time(self)->float:
        """
        Get the current time of day in hours, where current time represents the end time of the current time step.
        (e.g., 0.5, 0.75, 1.5)
        """
        return self.api.exchange.current_time(self.eps_state)
    
    def current_sim_time(self)->float:
        """
        Returns the cumulative simulation time from the start of the environment, in hours.
        """
        return self.api.exchange.current_sim_time(self.eps_state)
    
    def num_time_steps_in_hour(self)->int:
        """
        Get number of zone time step in an hour, a constant value throughout a simulation.
        """
        return self.api.exchange.num_time_steps_in_hour(self.eps_state)
    
    def zone_time_step(self)->float:
        """
        Get the current zone time step value.
        """
        return self.api.exchange.zone_time_step(self.eps_state)
    
    def zone_time_step_number(self)->int:
        """
        Get current zone time step index, from 1 to the number of zone time steps per hour.
        """
        return self.api.exchange.zone_time_step_number(self.eps_state)