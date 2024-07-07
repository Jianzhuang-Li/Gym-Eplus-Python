import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from queue import Queue
import threading
import logging
# import gymnasium as gym
import json
import sys
import os
# from gymnasium import spaces
from queue import Queue
from typing import Dict, Any
from ..util.constant import ENERGYPLUS_DIR
from ..util.logger import Logger
from ..generator.generator import Generator
sys.path.append(ENERGYPLUS_DIR)
import pyenergyplus.api


class GymEnergyPlus:

    def __init__(self, logger, generator:Generator, obs_queue: Queue, info_queue:Queue, act_queue:Queue):
        """
        Init the EnergyPlus Simutation environment.
        """
        self.name = "eplus"
        self.logger:logging = logger

        # gym communication queue
        self.obs_queue = obs_queue
        self.info_queue = info_queue
        self.act_queue = act_queue
        self.warmup_queue =Queue(maxsize=1)

        # api
        self.api_version = pyenergyplus.api.EnergyPlusAPI.api_version()
        self.api_path = pyenergyplus.api.api_path()
        self.api = pyenergyplus.api.EnergyPlusAPI()

        # generator
        self.generator:Generator = generator

        # create a new state
        self.eps_state = self.api.state_manager.new_state()

        # set count value
        self.episode: int = 0
        self.timestep: int = 0

        # Simulation thread
        self.energyplus_thread: Optional[threading.Thread] = None
        self.sim_results: Dict[str, Any] = {}
        self.initialized_handlers = False
        self.system_ready = False
        self.simulation_complete = False
        self.finish_warmup: bool = False
        self.is_running: bool = False

        # handles
        self.var_handlers: Optional[Dict[str,int]] = None
        self.meter_handlers: Optional[Dict[str, int]] = None
        self.actuator_handlers: Optional[Dict[str, int]] = None
        self.internal_var_handlers: Optional[Dict[str, int]] = None

    def _init_handlers(self, state_argument) -> None:
        """
        initialize sensors/actuators handlers to interact with during simulation.
        Args:
        state_argument (int): Energyplus API state.
        """
        if self.api.exchange.api_data_fully_ready(state_argument) and not self.initialized_handlers:
            if self.var_handlers is None or self.actuator_handlers is None \
                or self.meter_handlers is None or self.internal_var_handlers is None: 
            # Save available_data information
                self.available_data = self.api.exchange.list_available_api_data_csv(
                    state_argument).decode('utf-8')

                # write available_data.csv in parent output_path
                data = self.available_data.splitlines()
                with open(self.generator.current_path + '/data_available.txt', "w") as txt_file:
                    txt_file.writelines([line + '\n' for line in data])

            # Get variable handlers. using variables info
                self.var_handlers ={
                    key: self.api.exchange.get_variable_handle(state=state_argument,\
                    variable_name=var_map["variable_name"], variable_key=var_map["variable_key"])
                for key, var_map in self.generator.variables.items()}

            # Get.actuator handlers using actuators info
            self.actuator_handlers = {
                key: self.api.exchange.get_actuator_handle(state=state_argument, \
                component_type=act_map["component_type"], control_type=act_map["control_type"], actuator_key=act_map["actuator_type"])
                for key, act_map in self.generator.actuators.items()}
            
            # Get meter handlers using meters info
            self.meter_handlers= {
                key: self.api.exchange.get_meter_handle(state=state_argument, \
                meter_name=meter_map["meter_name"])
                for key, meter_map in self.generator.meters.items()}
            
            # Get internal handlers -using internal variables info
            self.internal_var_handlers={
                key: self.api.exchange.get_internal_variable_handle(state=state_argument,\
                variable_name=var_map["variable_name"], variable_key=var_map["variable_key"])
                for key, var_map in self.generator.internal_variables.items()}
            
            # Check handlers specified exists
            for variable_name, handle_value in self.var_handlers.items():
                if handle_value <= 0:
                    raise Exception(f"variable handler: {variable_name} is not an available variable.")
            
            for actuator_name, handle_value in self.actuator_handlers.items():
                if handle_value < 0:
                    raise Exception(f"actuator handler: {actuator_name} is not an available actuator.")
                
            for meter_name, handle_value in self.meter_handlers.items():
                if handle_value < 0:
                    raise Exception(f"meter handler:{meter_name} is not an available meter.")
            
            for internal_var_name, handle_value in self.internal_var_handlers.items():
                if handle_value < 0:
                    raise Exception(f"internal variable handler: {internal_var_name} is not an available internal variable.")
                
            self.logger.info("got all handle successfully.")
            self.logger.info("handlers are ready.")
            self.initialized_handlers = True
        

    def _get_variable_value(self, key:str, state_argument):
        try:
            assert self.initialized_handlers
            assert self.system_ready
            assert key in self.var_handlers.keys()
        except AssertionError as err:
            self.logger.warning(f"get variable {key} error.")
            sys.exit(1)
        return self.api.exchange.get_variable_value(state_argument, self.var_handlers[key])
    
    def _get_actuator_value(self, key:str, state_argument):
        try:
            assert self.initialized_handlers
            assert self.system_ready
            assert key in self.actuator_handlers.keys()
        except AssertionError as err:
            self.logger.warning(f"get actuator {key} error.")
            sys.exit(1)
        return self.api.exchange.get_actuator_value(state_argument, self.actuator_handlers[key])
    
    def _get_meter_value(self, key:str, state_argument):
        try:
            assert self.initialized_handlers
            assert self.system_ready
            assert key in self.meter_handlers.keys()
        except AssertionError as err:
            self.logger.warning(f"get meter {key} error.")
            sys.exit(1)

        return self.api.exchange.get_meter_value(state_argument, self.meter_handlers[key])
    
    def _get_internal_var_value(self, key:str, state_argument):
        try:
            assert self.initialized_handlers
            assert self.system_ready
            assert key in self.internal_var_handlers.keys()
        except AssertionError as err:
            self.logger.warning(f"get internal value {key} error.")
            sys.exit(1)
        return self.api.exchange.get_internal_variable_value(state_argument, self.internal_var_handlers[key])
    
    def _init_system(self, state_argument):
        """
        Indicate wheather the system are ready to work.
        After waiting to api data is available, handlers are initialized, and warmup flag is current.
        Args:
            state_argument: energyplus api state.
        """
        if not self.system_ready:
            if not self.initialized_handlers:
                self._init_handlers(state_argument)
            self.system_ready = self.initialized_handlers and not self.api.exchange.warmup_flag(state_argument)
            if self.system_ready:
                self.logger.info("System is ready.")

    def reset(self, seed=None, options=None):
        """
        resets an existing state instance, thus resetting the simulation, including any registered callback functions.
        """
        if self.is_running:
            self.stop()
        self.eps_state = self.api.state_manager.new_state()
        # self.api.state_manager.reset_state(self.eps_state)
        # disabling  of console output (stdout and stderr) when calling EnergyPlus as a library
        self.api.runtime.set_console_output_status(self.eps_state, False)
        self.sim_results:Dict[str, Any] = {}
        self.system_ready = False
        self.finish_warmup = False
        self.initialized_handlers = False
        self.simulation_complete = False
        self.timestep = 0
        self._flush_queue()
        self.set_callback()
        # make a new output dir
        self.generator.make_new_out_dir(self.name, self.episode)
        self.logger.info("Finish reset.")
    
    
    def _collect_obs_and_info(self, state_argument) -> None:
        """
        energyplus callback that collects output variables and info
        values and enquene them in each simulation timstep.
        Args:
            state argument (int): EnergyPlus API state.
        """
        if self.simulation_complete:
            return
        # init system
        self._init_system(state_argument)
        if not self.system_ready:
            return
        
        # obtain observation 
        self.next_obs = {
            # variables
            **{
                key: self._get_variable_value(key, state_argument)
                for key, handle in self.var_handlers.items()
            },
            # meter
            **{
                key: self._get_meter_value(key, state_argument)
                for key, handle in self.meter_handlers.items()
            },
            # internal variables
            **{
                key: self._get_internal_var_value(key, state_argument)
                for key, handle in self.internal_var_handlers.items()
            },
            # actuator value
            **{
                key: self._get_actuator_value(key, state_argument)
                for key, handle in self.actuator_handlers.items()
            }
        }

        # mount the info dict in queue
        self.next_info = {
            "time_elapsed(hour)": self.current_sim_time,
            "month": self.month,
            "day": self.day_of_month,
            "hour": self.hour
        }

        # put in the queues the observation and info
        self.obs_queue.put(self.next_obs)
        self.info_queue.put(self.next_info)

    def _process_action(self, state_argument: int) -> None:
        """
        EnergyPlus callback that sets output actuators values from last received action.
        Args:
            state argument (int): EnergyPlus API state.
        """
        # if simulation is complete or not initialized -> do nothing
        if self.simulation_complete:
            return
        # check system is ready
        self._init_system(state_argument)
        if not self.system_ready:
            return
        
        # if not value in action queue -> do nothing
        if self.act_queue.empty():
            # self.logger.warning("enpty action queue.")
            return
        self.timestep = self.timestep + 1
        # get next action from queue and check type
        next_action = self.act_queue.get()

        # set the action values obtained in actuator handlers
        for i, (act_name, actuator_handle) in  enumerate(self.actuator_handlers.items()):
            self.api.exchange.set_actuator_value(
                state=state_argument,
                actuator_handle=actuator_handle,
                actuator_value=next_action[i]
            )

    def _callback_prograss(self, percent:int) -> None:
        bar_length = 100
        filled_length = int(bar_length*(percent/100.0))
        bar = "*" * filled_length + "-"*(bar_length-filled_length-1)
        if self.system_ready:
            print(f"\repisode:{self.episode}:|{bar}|{percent}%", end="\r")

    def _callback_after_environment_warmup_is_complete(self, state_argument) -> None:
        self.finish_warmup = True
        if self.warmup_queue.empty():
            self.warmup_queue.put(True)
        return None

    def _callable_begin_new_environment(self, state_argument):
        """
        1. Occurs once near the beginning of each environment period. 
        2. Environment periods include sizing periods, design days, and run periods.
        3. This calling point will not be useful for control actions, but is useful for initializing
        variables and calculations that do not need to be repeated during each timestep.
        """
        return None
    
    def _callback_begin_zone_timestep_before_init_heat_balance(self, state_argument)->None:
        """
        1. This calling point is useful for controlling components that affect the building envelope 
        including surface constructions, window shades, and shading surfaces.
        2. Programs called from this point might actuate the building envelope or internal gains based
        on current weather or on the results from the previous timestep.
        3. Demand management routines might use this calling point to operate window shades, 
        change active window constructions, activate exterior shades, etc.
        """
        return None

    def _callback_begin_zone_timestep_after_init_heat_balance(self, state_argument)->None:
        """
        2. This calling point is useful for controlling components that affect the building envelope
        including surface constructions and window shades. 
        3. Programs called from this point might actuate the building envelope or internal gains based 
        on current weather or on the results from the previous timestep. 
        4. Demand management routines might use this calling point to operate window shades, change active window constructions, etc. 
        5. This calling point would be an appropriate place to modify weather data values.
        """
        self._init_system(state_argument)
        # hour = self.hour
        # num_timestep = self.num_time_steps_in_hour
        # timestep = self.zone_time_step_number
       
        # if self.system_ready and  hour == 23 and timestep == num_timestep:
            # day = self.day_of_year
            # OAT_v = self._get_variable_value( "OAT", state_argument)
            # ZMT_BOT_v = self._get_variable_value("ZMT_BOT", state_argument)
            # ZMT_MID_v = self._get_variable_value("ZMT_MID", state_argument)
            # ZMT_TOP_v = self._get_variable_value("ZMT_TOP", state_argument)
            # ZMT_BASE_v = self._get_variable_value("ZMT_BASE", state_argument)
            # chiller_1_e =self._get_variable_value("CHILLER1_E", state_argument)
            # self.logger.info(f"current day :{day}, temp:{OAT_v, ZMT_BOT_v, ZMT_MID_v, ZMT_TOP_v, ZMT_BASE_v}")
        """
        if hour == 23:
            if not self.got_handle:
                return 
            temp1 = self.api.exchange.get_variable_value(state_arguement, self.handle_map['T1'])
            current_sim_time = self.current_sim_time()
            self.logger.info(f"call back state: {self.callback_state}, sim_time:{current_sim_time}, temp:{temp1}")
            self.callback_state = self.callback_state + 1
        """

    def _callback_after_predictor_before_hvac_managers(self, state_argument)->None:
        """
        1. It occurs at each timestep just after the predictor executes but before SetpointManager and AvailabilityManager models are called.
        2. It is useful for a variety of control actions.
        3. However, if there are conflicts, the EMS control actions could be overwritten by other SetpointManager or AvailabilityManager actions.
        """
        return None

    def _callback_after_predictor_after_hvac_managers(self, state_argument)->None:
        """
        1. It occurs at each timestep after the predictor executes and after the SetpointManager 
        and AvailabilityManager models are called. 
        2. It is useful for a variety of control actions. 
        3. However, if there are conflicts, SetpointManager or AvailabilityManager actions may be
        overwritten by EMS control actions.
        """
        self._init_system(state_argument)
        # hour = self.hour
        # num_timestep = self.num_time_steps_in_hour
        # timestep = self.zone_time_step_number
       
        # if self.system_ready and  hour == 23 and timestep == num_timestep:
        #     day = self.day_of_year
        #     rate = self._get_actuator_value('Basement_Light_Actuator', state_argument)
        #     # self.logger.info(f"current day :{day}, basement_light_electricity_rate:{rate}")
        self._process_action(state_argument)
        return None
    
    def _callback_end_zone_timestep_after_zone_reporting(self, state_argument) ->None:
        self._collect_obs_and_info(state_argument)
        return None
    
    def _callback_begin_system_timestep_before_predictor(self, state_argument)->None:
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
        self.api.runtime.callback_after_new_environment_warmup_complete \
            (self.eps_state, self._callback_after_environment_warmup_is_complete)

        self.api.runtime.callback_begin_new_environment \
            (self.eps_state, self._callable_begin_new_environment)
        
        self.api.runtime.callback_begin_zone_timestep_before_init_heat_balance \
            (self.eps_state, self._callback_begin_zone_timestep_before_init_heat_balance)
        
        self.api.runtime.callback_begin_zone_timestep_after_init_heat_balance \
            (self.eps_state, self._callback_begin_zone_timestep_after_init_heat_balance)
        
        self.api.runtime.callback_begin_system_timestep_before_predictor \
            (self.eps_state, self._callback_begin_system_timestep_before_predictor)

        self.api.runtime.callback_after_predictor_before_hvac_managers \
            (self.eps_state, self._callback_after_predictor_before_hvac_managers)
        
        self.api.runtime.callback_after_predictor_after_hvac_managers \
            (self.eps_state, self._callback_after_predictor_after_hvac_managers)
        
        self.api.runtime.callback_end_zone_timestep_after_zone_reporting \
            (self.eps_state, self._callback_end_zone_timestep_after_zone_reporting)
        
        self.api.runtime.callback_progress(self.eps_state, self._callback_prograss)
        
    def _make_eplus_agrs(self) -> List[str]:
        """
        Transform attributes defined in class instance into energyplus bash command.
        Returns:
            List[str]: List of the argument components for energyplus bash command.
        """
        eplus_argus = []
        eplus_argus += ["-w",
                        self.generator.weather_file,
                        "-d",
                        self.generator.current_path,
                        self.generator.idf_file]
        return eplus_argus
    
    def _run_simulation(self, cmd_argus, state, results)->None:
        # run energyplus in a no blocking way
        self.logger.info(f"Runinf EnergyPlus with args: {cmd_argus}")
        self.is_running = True
        results["exit_code"] = self.api.runtime.run_energyplus(state, cmd_argus)
        self.is_running = False
        self.simulation_complete = True
        self.api.state_manager.delete_state(state)
        self.episode = self.episode + 1
        print("") 

    def failed(self) ->bool:
        """
        Method to determine if simulation has failed.
        Returns:
            bool: Flag to describe this state.
        """
        return self.sim_results.get("exit_code", -1) > 0
    
    
    def run(self)->None:
        """
        run an energyplus simulation.
        """
        if self.is_running:
            self.logger.warning("energyplus is running.")
            return
        self.energyplus_thread = threading.Thread(
            target=self._run_simulation,
            name=self.name,
            args=(
                self._make_eplus_agrs(),
                self.eps_state,
                self.sim_results
            ),
            daemon=True
        )
        self.logger.info("EnergyPlus thread started.")
        self.energyplus_thread.start()
        return None
    
    def stop(self):
        """
        it forces the simulation thread ends.
        """
        if self.is_running:
            self.simulation_complete = False
            self.energyplus_thread.join()
            self.energyplus_thread = None
            self.api.runtime.clear_callbacks()
            self.api.state_manager.delete_state(self.eps_state)
            self.sim_results:Dict[str, Any] = {}
            self.finish_warmup = False
            self.system_ready = False
            self.is_running = False
            self._flush_queue()
            self.logger.info("Energyplus Thread stop.")

    def _flush_queue(self) -> None:
        """
        It empty all values allocated in observation, action and warmup queue.
        """
        for q in [
            self.obs_queue,
            self.act_queue,
            self.info_queue,
            self.warmup_queue]:
            while not q.empty():
                q.get()
        self.logger.debug("simulator queues emptied.")

    @property
    def year(self)->int:
        """
        Get the "current" year of the simutation.
        """
        return self.api.exchange.year(self.eps_state)
    
    @property
    def month(self)->int:
        """
        Get the current month of the simutation(1-12).
        """
        return self.api.exchange.month(self.eps_state)
    
    @property
    def day_of_year(self)->int:
        """
        Get the current day of the year (1-366).
        """
        return self.api.exchange.day_of_year(self.eps_state)
    
    @property
    def day_of_month(self)->int:
        """
        Get the current day of the month (1-31).
        """
        return self.api.exchange.day_of_month(self.eps_state)
    
    @property
    def day_of_week(self):
        """
         Get the current day of the week (1-7).
        """
        return self.api.exchange.day_of_week(self.eps_state)
    
    @property
    def hour(self)->int:
        """
        Get the current hour of the simulation (0-23).
        """
        return self.api.exchange.hour(self.eps_state)
    
    @property
    def minutes(self)->int:
        """
        Get the current minutes into the hour (1-60).
        """
        return self.api.exchange.minutes(self.eps_state)
    
    @property
    def current_time(self)->float:
        """
        Get the current time of day in hours, where current time represents the end time of the current time step.
        (e.g., 0.5, 0.75, 1.5)
        """
        return self.api.exchange.current_time(self.eps_state)
    
    @property
    def current_sim_time(self)->float:
        """
        Returns the cumulative simulation time from the start of the environment, in hours.
        """
        return self.api.exchange.current_sim_time(self.eps_state)
    
    @property
    def num_time_steps_in_hour(self)->int:
        """
        Get number of zone time step in an hour, a constant value throughout a simulation.
        """
        return self.api.exchange.num_time_steps_in_hour(self.eps_state)
    
    @property
    def zone_time_step(self)->float:
        """
        Get the current zone time step value.
        """
        return self.api.exchange.zone_time_step(self.eps_state)
    
    @property
    def zone_time_step_number(self)->int:
        """
        Get current zone time step index, from 1 to the number of zone time steps per hour.
        """
        return self.api.exchange.zone_time_step_number(self.eps_state)
    