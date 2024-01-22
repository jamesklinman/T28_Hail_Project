# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 20:48:14 2023

@author: james.klinman

Pre-requisites to run:
    Programs to run before this one:
        -Aircraft_Plotting.py
    
    Files required:
        -Param_Info/File_Runner_Info.txt
        -Param_Info/Flight_*FlightNum*_Indexs.pkl
        -Param_Info/*FlightNum*_paramInfo.txt
        -Flight_Plots/*YYYYMMDD*/*SomeVariable1_and_SomeVariable2*/*plots*
            -Need multiple of the SomeVariable1 and 2 folders if you're
             combining them


notes to self:
need to create an organization scheme that identifies what is available
and what should be plotted next to each other
so something like a priority order so if two variables are plotted and in the 
list of plots available then those are assigned to be next to each other and
so on for the second and third place option. and any stragglers just get put
to the bottom I guess
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pandas as pd
import pickle
import os
import json


#getting flight num
#------------------
flight_programs_file = 'Param_Info/File_Runner_Info.txt'
#flight_programs_info = pd.read_csv(flight_programs_file, sep=' * ', engine='python')
with open(flight_programs_file, 'r') as file:
    flight_programs_info = file.read()  
flight_programs_info = json.loads(flight_programs_info)
flight_num = str(flight_programs_info['flight_num'][0])

#Getting file names
#------------------
param_file = 'Param_Info/' + flight_num + '_paramInfo.txt'
indexInfo = 'Param_Info/Indexs/Flight_' + flight_num + '_Indexs.pkl'
iteration_track_file = 'Automated_Files/Iteration_Tracker.txt'
variables_track_file = 'Automated_Files/Variable_Tracker.txt'

#Reading in files
#----------------
#initParameters = pd.read_csv(param_file, sep=' * ', engine='python')
with open(param_file, 'r') as file:
    initParameters = file.read()  
initParameters = json.loads(initParameters)
iterationTracker = pd.read_csv(iteration_track_file, sep=' * ', engine='python')
variablesTracker = pd.read_csv(variables_track_file, sep=' * ', engine='python')
with open(indexInfo, "rb") as file:   # Unpickling
   indexs = pickle.load(file)
print(indexs)

#Getting useful information from parameter files
#-----------------------------------------------
time_index_to_use = iterationTracker['Iteration'][0] #* \
    #iterationTracker['Skip_Num'][0]

initTime = str(initParameters['Time_Start'][time_index_to_use])
finTime = str(initParameters['Time_End'][time_index_to_use])
time_range = initTime + ':' + finTime

start_time_period = indexs[time_range][0][0][0]
end_time_period = indexs[time_range][0][1][0]

#Tracking which variables to plot. Does all variables for each time
#period. Then goes back to first combination for next time period
#------------------------------------------------------------------
"""variables_counter_up = variablesTracker['Variable_Iteration'][0]
var1index = 0#variables_counter_up
var2index = 1#variables_counter_up + 1

if type(initParameters['Variables_Plot'][variables_counter_up][var2index]) is str:
    second_axis_check = 'yes'

yaxis1 = initParameters['Variables_Plot'][variables_counter_up][var1index]

if second_axis_check == 'yes':
    yaxis2 = initParameters['Variables_Plot'][variables_counter_up][var2index]
"""
#Finding the plots and creating a list of them
#---------------------------------------------    
latest_folder = 0
for folder in os.listdir('Flight_Plots/'):
    if int(folder) > int(latest_folder):
        latest_folder = folder
    
name_list = []
for folder in os.listdir('Flight_Plots/' + str(latest_folder)):
    if folder == 'Combined_Plots':
        pass
    else:
        name_list.append(folder)

plt_list = []
for plot_variables in name_list:
    plt_name = 'Flight_Plots/' + latest_folder +'/'+ plot_variables + \
        '/Flight' + flight_num + '_' + str(initTime)+'_'+ str(finTime) + '.png'
    plt_list.append(plt_name)

"""
#trying to organize plots
#for plot in plt_list:
#NEEEDEDEDEDEEDSSSSSSSSST O BE UPDATESD
plt_list = ['Flight_Plots/20231107/FSSP_LIQUID_WATER_and_UPDRAFT/Flight757_' + initTime + '_' + finTime + '.png',
            'Flight_Plots/20231107/HAIL_AVERAGE_DIAMETER_and_UPDRAFT/Flight757_' + initTime + '_' + finTime + '.png',
            'Flight_Plots/20231107/TEMPERATURE_REVERSE_FLOW_SENSOR_and_UPDRAFT/Flight757_' + initTime + '_' + finTime + '.png',
            'Flight_Plots/20231107/GPS_ALTITUDE_and_UPDRAFT/Flight757_' + initTime + '_' + finTime + '.png',
            'Flight_Plots/20231107/PITCH_and_UPDRAFT/Flight757_' + initTime + '_' + finTime + '.png',
            'Flight_Plots/20231107/ROLL_and_UPDRAFT/Flight757_' + initTime + '_' + finTime + '.png'
            ]    
"""
#figuring how many plots there are
#for the final combined plot
#---------------------------------
axes_num = []
counter = 0
for plots in range(len(plt_list)):
    axes_num.append(counter)
    counter += 1

#This assumes that there are 6 different plots max. Creating the figure 
#here by putting each plot which is a png into one of the axs spots
#----------------------------------------------------------------------
x_plots = 3
y_plots = 2
fig, axs = plt.subplots(x_plots, y_plots)
fig.set_size_inches(24, 24)
x_tracker = 0
y_tracker = 0
for x in range(len(plt_list)):
    img = mpimg.imread(str(plt_list[x]))
    axs[x_tracker][y_tracker].imshow(img)
    axs[x_tracker][y_tracker].axis('off')
    y_tracker += 1
    if y_tracker == y_plots:
        y_tracker = 0
        x_tracker += 1
# https://stackoverflow.com/questions/10035446/how-can-i-make-a-blank-subplot-in-matplotlib
fig.tight_layout()
plt.savefig('cool.png')

#Creating the variable folder if needed and saving the data
#----------------------------------------------------------    
if os.path.exists('Flight_Plots/' + latest_folder + '/' + \
                  'Combined_Plots/') is False:
    os.mkdir('Flight_Plots/' + latest_folder + '/' + \
                      'Combined_Plots/')

plt.savefig('./Flight_Plots/' + latest_folder + '/Combined_Plots/' + \
            '/Flight' + flight_num + '_' + str(initTime)+'_'+ str(finTime) +\
            '.png')