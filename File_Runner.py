# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 20:55:14 2023

@author: james.klinman

to run, make sure to set up:
    -File_Runner_Info.txt
    -*flightnum*_paramInfo.txt
    
runfile('File_Runner.py', 'Param_Info/File_Runner_Info.txt Param_Info/757_paramInfo.txt')
"""

import subprocess
import os
import sys
import pandas as pd
import json


#Getting flight number and the list of programs to run
#-----------------------------------------------------
flight_programs_file = sys.argv[1]
param_file = sys.argv[2]
"""
flight_programs_file = 'Param_Info/File_Runner_Info.txt'
"""
with open(flight_programs_file, 'r') as file:
    flight_programs_info = file.read()
    
flight_programs_info = json.loads(flight_programs_info)
"""
#flight_programs_info = pd.read_csv(flight_programs_file, sep=' * ', engine='python')

flight_num = str(flight_programs_info['flight_num'][0])
"""
programs_to_use = flight_programs_info['programs_to_run']
"""

param_file = 'Param_Info/' + flight_num + '_paramInfo.txt'
"""
with open(param_file, 'r') as file:
    initParameters = file.read()
initParameters = json.loads(initParameters)

#initParameters = pd.read_csv(param_file, sep=' * ', engine='python')

#these were implemented to help define if the program needed to track
#through different time periods, but it seems to work without
#so maybe need to do some testing and see if they're needed or not
#but some do work now. just ignore
aircraft_plotting_check = None
aircraft_tracks_check = None
singlerun = None

#Makes a list of the programs so that 
#they can be run in the correct order
#------------------------------------
program_list = []
for x in programs_to_use:
    program_list.append(x)

#This function runs a program for each time period.
#It does not work yet if it has to iterate over other variables.
#I think by "other variables" I meant radar variables but am unsure    
#------------------------------------------------------------------
def run_program(program_to_run):
    global aircraft_plotting_check, singlerun
    
    counter = 0
    number_of_time_periods = 0
    #Skip is 3 because of the way the paramInfo file is formatted. 
    #Likewise the counter%4 is a result of the formatting as well
    #skip is now useless with the new parameter file formatting. But leaving
    #it in for now until it all gets worked out.
    skip = 3
    for x in initParameters['Time_Start']:
        #if counter%4 == 0:
        #    number_of_time_periods +=1
        #counter+=1
        number_of_time_periods += 1
    print(number_of_time_periods)
    
    print("singlerun: ", singlerun)
    if singlerun == True:
        subprocess.run([sys.executable, program_to_run])
        singlerun = False
        
    else:
        for time_period in range(number_of_time_periods):
            print('time period: ', time_period)
            f = open('Automated_Files/Iteration_Tracker.txt', "w+")
            f.write('{a:<11}{b:<10}'.format(a='Iteration', b='Skip_Num'))
            f.write('\n')
            f.write('{a:<11}{b:<10}'.format(a=time_period, b=skip)) #skip here too
            f.close()
            
            if aircraft_plotting_check == 'y':
                num_of_vars_to_plot = 0
                for x in range(0, len(initParameters['Variables_Plot'])+1):
                    #if initParameters['Variables_Plot'][x] != '.':
                        #num_of_vars_to_plot += 1
                    num_of_vars_to_plot += 1
                #variable_iter_tracker -= 1
                
                variables_index = 0
                #honestly idk why rn but the +1 is important and makes it so the
                #code actually does all the plotting
                for x in range(num_of_vars_to_plot):
                    f = open('Automated_Files/Variable_Tracker.txt', "w+")
                    f.write('{c:<11}'.format(c='Variable_Iteration'))
                    f.write('\n')
                    f.write('{c:<11}'.format(c=variables_index))
                    
                    subprocess.run([sys.executable, program_to_run])
                    
                    variables_index += 1
                
            else:
                subprocess.run([sys.executable, program_to_run])
    return singlerun


        #subprocess.run([sys.executable, program_to_run])

#All the programs that can be run as part of the processing package
#They are loosely ordered so that programs that need to be run first
#in order for other programs to function are run first
#-------------------------------------------------------------------


if 'Flight_Index_Finder.py' in program_list:
    run_program('Flight_Index_Finder.py')
    
if 'Aircraft_Track_Data.py' in program_list:
    run_program('Aircraft_Track_Data.py')

if 'Aircraft_Plotting.py' in program_list:
    aircraft_plotting_check = 'y'
    run_program('Aircraft_Plotting.py')
    aircraft_plotting_check = None
    #set to none so that it doesn't start the if loops again above

if 'Aircraft_Plots_Combined.py' in program_list:
    run_program('Aircraft_Plots_Combined.py')

if 'Aircraft_Tracks_Visualization.py' in program_list:
    aircraft_tracks_check = 'y'
    run_program('Aircraft_Tracks_Visualization.py')

if 'Spectrometer_HVPS_Comparison.py' in program_list:
    run_program('Spectrometer_HVPS_Comparison.py')
    
if 'Spectrometer_Comparison.py' in program_list:
    run_program('Spectrometer_Comparison.py')

if 'Lat_Lon_Alt.py' in program_list:
    singlerun = True
    run_program('Lat_Lon_Alt.py')

if 'True_Airspeed.py' in program_list:
    singlerun = True
    run_program('True_Airspeed.py')

    
    
    