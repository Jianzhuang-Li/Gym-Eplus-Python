"""
Gymnasium environment for simulation with energyplus
"""
import numpy as np
from queue import Empty, Full, Queue
from typing import Any, Dict, List, Optional, Tuple, Union

from ..generator.generator import Generator
from ..simulators.gym_energyplus import GymEnergyPlus
from ..util.logger import Logger
from ..util.constant import LOG_LEVEL_GYM_ENV

class EplusEnv:

    logger =  Logger().getLogger("enplus_env", LOG_LEVEL_GYM_ENV)

    def __init__(self,
        configure_path: str,
        reward_func,        
        ) -> None:
        # env info
        self.env_name = "eplus-env-v1"
        # conf
        self.conf_path = configure_path
        self.generator = Generator()
        self.generator.load_by_data(self.conf_path)

        # variables
        self.variables = self.generator.variables
        self.meters = self.generator.meters
        self.internal_variables = self.generator.internal_variables

        # actuator
        self.actuators = self.generator.actuators

        # observation
        self.observation_variables = list(self.variables.keys()) \
            + list(self.meters.keys()) \
            + list(self.internal_variables.keys())
        
        # action
        self.action_variables = list(self.actuators.keys())

        # simulation info
        self.timestep = 0
        self.episode = 0

        # queues for comunicating with eplus
        self.obs_queue = Queue(maxsize=1)
        self.info_queue = Queue(maxsize=1)
        self.act_queue = Queue(maxsize=1)

        # last obs, action and info
        self.last_obs: Optional[Dict[str, float]] = None
        self.last_info: Optional[Dict[str, Any]] = None
        self.last_action: Optional[Dict[float]] = None

        # reward function
        self.reward_func = reward_func

        self.energyplus_simulator = GymEnergyPlus(
            self.logger,
            self.generator,
            self.obs_queue,
            self.info_queue,
            self.act_queue
        )

    def reset(self):
        """
        reset the environment.
        """
        self.episode += 1
        self.timestep = 0

        # ------------preparation for new episode --------------
        print("#-----------------------------------------------#")
        self.logger.info(f"start a new episode... [{self.env_name}][episode {self.episode}]")
        self.energyplus_simulator.reset()
        self.logger.debug(f"out path: {self.energyplus_simulator.generator.current_path}")
        # start the simulator
        self.energyplus_simulator.run()
        self.logger.debug(f"episode {self.episode} started.")

        # wait for simulator warmup complete
        if not self.energyplus_simulator.system_ready:
            self.logger.debug("waiting for finish warmup process.")
            # self.energyplus_simulator.warmup_queue.get()
            self.logger.debug("warmup process finished.")

        # wait for receive simulation first observation and info
        try:
            obs = self.obs_queue.get()
        except Empty:
            self.logger.warning("Reset: Observation queue empty.")
        
        try:
            info = self.info_queue.get()
        except Empty:
            self.logger.warning("Reset: info queue empty.")

        info.update({"timestep": self.timestep})
        self.last_obs = obs
        self.last_info = info

        self.logger.debug(f"Reset: observation received: {obs}")
        self.logger.debug(f"Reset: info received: {info}")

        return np.array(list(obs.values()), dtype=np.float32), info

    def step(self, action):
        # timestep + 1 and flags initialization
        self.timestep += 1
        terminated = truncated = False
        # check if action is contained for the current action space

        # check if episode existed an is not terminated or truncated
        
        # check for simulation errors
        try:
            assert not self.energyplus_simulator.failed()
        except AssertionError as err:
            # self.logger.critical(f"energyplus failed with exit code {self.energyplus_simulator.sim_results["exit_code"]}")
            raise err
        
        if self.energyplus_simulator.simulation_complete:
            self.logger.debug(
                'trying step in a completed simulator, changing truncated flag to true')
            terminated = True
            obs = self.last_obs
            info = self.last_info
        else:
            time_out = 2
            try:
                self.act_queue.put(action, timeout=time_out)
                self.last_obs = obs = self.obs_queue.get(timeout=time_out)
                self.last_info = info = self.info_queue.get(timeout=time_out)
            except (Full, Empty):
                self.logger.debug(
                    "step queue not receive value, simualtion must be compeleted. Change truncated flag to True")
                truncated = True
                obs = self.last_obs
                info = self.last_info
        # Calculate reward
        reward, rw_terms = self.reward_func(obs)

        # update info
        info.update({"action": action})
        info.update({"timestep": self.timestep})
        info.update(rw_terms)

        # debug
        self.logger.debug(f"step observation: {obs}")
        self.logger.debug(f"step reward: {reward}")
        self.logger.debug(f"step terminated: {terminated}")
        self.logger.debug(f"step info: {info}")

        return np.array(list(obs.values()), dtype=np.float32), reward, terminated, truncated, info
    
    def render(self, model:str = 'human') -> None:
        """
        Environemt rendering.
        Args:
            mode (str, optional): Model for rendering. Defaults to 'human'.
        """
        pass

    # ------------------simulator----------------------------- #

    @property
    def var_handlers(self) -> Optional[Dict[str, int]]:
        return self.energyplus_simulator.var_handlers
    
    @property
    def meter_handlers(self) -> Optional[Dict[str, int]]:
        return self.energyplus_simulator.meter_handlers

    @property
    def actuator_handlers(self) -> Optional[Dict[str, int]]:
        return self.energyplus_simulator.actuator_handlers

    @property
    def internal_var_handlers(self) -> Optional[str]:
        return self.energyplus_simulator.internal_var_handlers

    @property
    def is_running(self) -> bool:
        return self.energyplus_simulator.is_running
    
    # ----------------path -------------------#
