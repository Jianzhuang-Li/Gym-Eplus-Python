import os 
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)
from gym_energyplus.generator.generator import Generator
from gym_energyplus.util.constant import DATA_CONFIGURATION_PATH, DATA_BUILDINGS_PATH, DATA_WEATHER_PATH

if __name__ == "__main__":
    weather = os.path. join(DATA_WEATHER_PATH, 'USA_NY_New.York-John.F.Kennedy.Intl.AP.744860_TMY3.epw')
    idf_file = os.path.join(DATA_BUILDINGS_PATH,'ASHRAE9O1_officeLarge_STD2022_NewYork.idf')
    out_path = "D:\lijianzhuang\Reaserch\new-research\Gym-EnergyPlus\DRL-EnergyPlus\gym_eplus\out"
    model = Generator()
    model.idf_file = idf_file
    model.weather_file = weather
    model.out_path = out_path
    model.add_variable_handle("OAT", "Site Outdoor Air Drybulb Temperature", "Environment")
    model.add_variable_handle("CHILLER1_E","Chiller Electricity Energy", "CoolSys1 Chiller1")
    model.add_variable_handle("HeatSysl_Boiler_E", "Boiler NaturalGas Energy", "HeatSys1 Boiler")
    model.add_variable_handle("Core_top_temp", "Zone Mean Air Temperature", "Core_top")
    model.add_variable_handle("CoolingsetPoint", "Schedule Value", "CLGSETP_SCH_YES_OPTIMUN")
    model.add_variable_handle("HeatingSetPoint", "Schedule Value", "HTGSETP_SCH_YES_OPTIMUM")
    # model.add_actuator_handle('Basement_Light_Actuator', "Lights","Electricity Rate", "Basement_lights")
    model.add_actuator_handle('CoolSys1_Loop_Plant_Demand_Inlet_Setpoint', "System Node Setpoint", "Temperature Setpoint", "Coolsysl Demand Inlet Node")
    model.add_actuator_handle('CoolSys1_Loop_Setpoint', "System Node Setpoint", "Temperature Setpoint", "Coolsys1 Supply outlet Node")
    print(DATA_CONFIGURATION_PATH)
    model.save_to_file(DATA_CONFIGURATION_PATH)
