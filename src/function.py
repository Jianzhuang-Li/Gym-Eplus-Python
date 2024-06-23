import os
import warnings
from timer import WEEKDAY_ENCODING,  get_delta_seconds
YEAR = 1991

class EnergyPlusEnv():

    def __init__(self, idf_path, weather_path) -> None:
        self.idf_path = idf_path
        self.weather_path = weather_path
        self.timestep = self.get_eplus_run_timestep(self.idf_path)
        self.run_period = {}
        self.run_period['WinterDay'] = self.get_eplus_run_period(self.idf_path, 'WinterDay')
        self.run_period['SummerDay'] = self.get_eplus_run_period(self.idf_path, 'SummerDay')
        self.run_period['AllObject'] = self.get_eplus_run_period(self.idf_path, '')

    def get_eplus_run_timestep(self, idf_path):
        """
        This method read the .idf file and find the timstep
        Args:
            idf_path: String
                The .idf file path.
        
        Return:
            timesep: int
        """
         
        with open(idf_path, encoding = 'ISO-8859-1') as idf:
            contents = idf.readlines()
        step_size = None
        # Step size
        line_count = 0
        for line in contents:
            effectiveContent = line.strip().split('!')[0] # Ignore contents after '!'
            effectiveContent = effectiveContent.strip().split(',')
            if effectiveContent[0].strip().lower() == 'timestep':
                if len(effectiveContent) > 1 and len(effectiveContent[1]) > 0:
                    step_size = int(effectiveContent[1]
                                   .split(';')[0]
                                   .strip())
                else:
                    step_size = int(contents[line_count + 1].strip()
                                                  .split('!')[0]
                                                  .strip()
                                                  .split(',')[0])
                break
            line_count += 1
        return step_size

    def get_eplus_run_period(self, idf_path, run_period_name):
        """
        This method read the .idf file and find the running start month, start
        date, end month, end date etc.
        
        Args:
            idf_path: String
                The .idf file path.
            run_period_name: String
        
        Return: (int, int, int, int, int, int)
            (start month, start date, end month, end date, start weekday, 
            step size)
        """
        ret = []
        
        with open(idf_path, encoding = 'ISO-8859-1') as idf:
            contents = idf.readlines()
        
        # Run period
        tgtIndex = None
        find_run_period = False
        
        for i in range(len(contents)):
            line = contents[i]
            effectiveContent = line.strip().split('!')[0] # Ignore contents after '!'
            effectiveContent = effectiveContent.strip().split(',')[0]
                                                          # Remove tailing ','
            if effectiveContent.lower() == 'runperiod':
                print(contents[i+1])
                tgtIndex = i
                name = contents[tgtIndex+1].strip().split('!')[0].strip().split(',')
                if len(name) > 0:
                    if name[0] == run_period_name:
                        find_run_period = True
                        break
                else:
                   if run_period_name == '':
                       find_run_period = True
                       break

        if not find_run_period:
            warnings.warn(f"no run period name {run_period_name}")
            return None
        
        # begin month, day, year and end month, date and year
        for i in range(2, 8):
            content = contents[tgtIndex + i].strip().split('!')[0].strip().split(',')[0]
            if content != '':
                content = int(content)
            else:
                content = None
            ret.append(content)
       
        # Start weekday
        ret.append(WEEKDAY_ENCODING[contents[tgtIndex + i + 1].strip()
                                                          .split('!')[0]
                                                          .strip()
                                                          .split(',')[0]
                                                          .strip()
                                                          .lower()])            
        return tuple(ret)
    
    def _get_one_epi_len(self, st_mon, st_day, ed_mon, ed_day):
        """
        Get the length of one episode (One EnergyPlus process run to the end).
        
        Args:
            st_mon, st_day, ed_mon, ed_day: int
                The EnergyPlus simulation start month, start day, end month, 
                end day.
        
        Return: int
            The simulation time step that the simulation ends. 
        """
        return get_delta_seconds(YEAR, st_mon, st_day, ed_mon, ed_day)
    
   


if __name__ == '__main__':
    weather_path_ = 'E:\\lijianzhuang\\NewResarch\\EnergyPlus-Gym\\Gym-Eplus-Python\\weather\\USA_CO_Golden-NREL.724666_TMY3.epw'
    idf_path_ = 'E:\\lijianzhuang\\NewResarch\\EnergyPlus-Gym\\Gym-Eplus-Python\model\\5Zone_Transformer.idf'
    env = EnergyPlusEnv(idf_path_, weather_path_)
    print(env.run_period['SummerDay'])
