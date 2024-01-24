#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 13:57:46 2023

@author: james.klinman

can plot one or two plane variables

requires flight index finder to be run so that it can use the index's from it
if you changed the time period, then you have to run Flight_Index_Finder again

Pre-requisites to run:
    Programs to run before this one:
        -File_Runner.py
        -Flight_Index_Finder
    
    Files required:
        -File_Runner_Info.txt
        -Flight_Files/*FlightNum*.nc
        -Param_Info/*FlightNum*_paramInfo.txt
        -Param_Info/Flight_*FlightNum*_Indexs.pkl
        -Sensor_Information/FlightInfo_*FlightNum*.txt
        -Automated_Files/Iteration_Tracker.txt
            -should be produced automatically when running "file runner"
        -Automated_Files/Variable_Tracker.txt
            -should be produced automatically when running "file runner"

notes to self:
need to add thing for when time period is shorter so that it does second ticks 
as well and so that the minute ticks are calculated properly cause rn it ends up
saying it just needs one tick
"""

import matplotlib.pyplot as plt
from matplotlib.dates import HourLocator, MinuteLocator, DateFormatter
from matplotlib.ticker import AutoMinorLocator
import numpy as np
import pandas as pd
import Top_Hail_Methods as hail
import netCDF4 
from datetime import datetime, timedelta, date
import sys
import pickle
import os
import json


#Reading in all the files
#------------------------
flight_programs_file = 'Param_Info/File_Runner_Info.txt'
#flight_programs_info = pd.read_csv(flight_programs_file, sep=' * ', engine='python')
with open(flight_programs_file, 'r') as file:
    flight_programs_info = file.read()  
flight_programs_info = json.loads(flight_programs_info)
flight_num = str(flight_programs_info['flight_num'][0])


file_airplane = 'Flight_Files/' + flight_num + '.nc'
param_file = 'Param_Info/' + flight_num + '_paramInfo.txt'
indexInfo = 'Param_Info/Indexs/Flight_' + flight_num + '_Indexs.pkl'
iteration_track_file = 'Automated_Files/Iteration_Tracker.txt'
variables_track_file = 'Automated_Files/Variable_Tracker.txt'

airplanedata = netCDF4.Dataset(file_airplane)
#initParameters = pd.read_csv(param_file, sep=' * ', engine='python')
with open(param_file, 'r') as file:
    initParameters = file.read()  
initParameters = json.loads(initParameters)
iterationTracker = pd.read_csv(iteration_track_file, sep=' * ', engine='python')
variablesTracker = pd.read_csv(variables_track_file, sep=' * ', engine='python')
with open(indexInfo, "rb") as file:   # Unpickling
   indexs = pickle.load(file)
print(indexs)


#Specifying the start and end time to use
#Index Finder got the indexs to be used for this
#-----------------------------------------------
time_index_to_use = iterationTracker['Iteration'][0] #* \
    #iterationTracker['Skip_Num'][0]

initTime = str(initParameters['Time_Start'][time_index_to_use])
finTime = str(initParameters['Time_End'][time_index_to_use])
time_range = initTime + ':' + finTime

start_time_period = indexs[time_range][0][0][0]
end_time_period = indexs[time_range][0][1][0]


#Defining some of the stuff for plotting here
#If you want to change things like the number of ticks or
#the line colors or the spacing for the yticks, do it here
#---------------------------------------------------------
variables_counter_up = variablesTracker['Variable_Iteration'][0]
var1index = 0#variables_counter_up
var2index = 1#variables_counter_up + 1

if type(initParameters['Variables_Plot'][variables_counter_up][var2index]) is str:
    second_axis_check = 'yes'

yaxis1 = initParameters['Variables_Plot'][variables_counter_up][var1index]
dependent_var1 = airplanedata[yaxis1][:]
if second_axis_check == 'yes':
    yaxis2 = initParameters['Variables_Plot'][variables_counter_up][var2index]
    dependent_var2 = airplanedata[yaxis2][:]


num_of_xticks = 6
y_axis_tick_spacing1 = 5
y_axis_tick_spacing2 = 5

color_left = 'blue'
color_right = 'red'


#Getting the time for the whole flight and enforcing it as HHMMSS format
#the data file being read in is assumed to be in UTC time
#Should work if your data is any number of hertz
#-----------------------------------------------------------------------
time2 = []
counter = 0
index_to_add_date2 = None
for x in range(start_time_period, end_time_period+1):
    for y in range(airplanedata['TIME_HOURS_20Hz'].shape[1]):
        hours = str(int(airplanedata['TIME_HOURS_20Hz'][x][y]))
        minutes = str(int(airplanedata['TIME_MINUTES_20Hz'][x][y]))
        seconds = float(airplanedata['TIME_SECONDS_20Hz'][x][y])
        
        #this is to get the index when the clock goes over 24hrs
        if index_to_add_date2 == None:  
            if int(hours) == 24:
                print('hi')
                index_to_add_date2 = start_time_period + counter
        counter += 1
        
        if int(hours) >= 24:
            hours = str(int(hours) - 24)
        if len(hours) != 2:
            hours = '0' + hours
        if len(minutes) != 2:
            minutes = '0' + minutes
        seconds = str(round(seconds, 2))
        if seconds[1] == '.':
            seconds = '0' + seconds
        HHMMSS = hours + minutes + seconds
        time2.append(HHMMSS)


#Getting flight date so that datetime can create the datetime format
#This is required for plotting the times on an axis since it seems
#like matplotlib requires datetime format for plotting times.
#-------------------------------------------------------------------
flightdate = str(getattr(airplanedata, 'FlightDate'))
flightdate = datetime.strptime(flightdate, '%m/%d/%Y')
datetime_times = []
counter = start_time_period
for x in range(len(time2)):
    if counter == index_to_add_date2:
        print(x)
        flightdate = flightdate + timedelta(days=1)
    counter +=1
    datetime_times.append(datetime.combine(flightdate, datetime.strptime(time2[x], '%H%M%S.%f').time()))

#resetting flight date to what it was before in case it gets used elsewhere
#spoiler alert, i don't think it does...
flightdate = str(getattr(airplanedata, 'FlightDate'))
    

#Pulling the data for the variable(s) that are being plotted
#-----------------------------------------------------------
yaxis1data = []
for x in range(start_time_period, (end_time_period + 1)):
    for y in range(airplanedata[initParameters['Variables_Plot'][variables_counter_up][var1index]].shape[1]):
        yaxis1data.append(dependent_var1[x][y])

if second_axis_check == 'yes':    
    yaxis2data = []
    for x in range(start_time_period, (end_time_period + 1)):
        for y in range(airplanedata[initParameters['Variables_Plot'][variables_counter_up][var2index]].shape[1]):
            yaxis2data.append(dependent_var2[x][y])


#--------------------------------------------------------
#Herein lies the plotting code now that we have the data
#--------------------------------------------------------

#Here's I useful link I used for formatting xaxis
#https://stackoverflow.com/questions/43368302/matplotlib-hourlocator-steals-my-x-labels


#Getting the amount of minutes between x-ticks
#It attempts to get enough time between the ticks
#so that they're not crowded together
#------------------------------------------------
flight_period_total_seconds = datetime_times[-1] - datetime_times[0]
flight_period_total_seconds = flight_period_total_seconds.total_seconds()
minutes_between_ticks = int(flight_period_total_seconds / 60 // num_of_xticks + 1)


#y-tick functions to either make the ticks better spaced,
#or to make them set to a 0 somewhere or something like that
#-----------------------------------------------------------
def ytick_checker_thing(axis, axis_data):
    if axis == 'UPDRAFT':
        max_yaxis, min_yaxis = max(axis_data), min(axis_data)
        if abs(max_yaxis) >= (min_yaxis):
            max_range = max_yaxis
        else:
            max_range = min_yaxis
        max_tick = max_range
        min_tick = -max_range
        zero_tick = 0
        middle_tick_pos, middle_tick_neg = (max_tick / 2), (-max_tick / 2) 
        axis_ticks = [min_tick, middle_tick_neg, zero_tick, \
                      middle_tick_pos, max_tick]
        yminlim = min_yaxis
        ymaxlim = max_yaxis
        
    if axis == 'ROLL':
        max_yaxis, min_yaxis = max(axis_data), min(axis_data)
        if abs(max_yaxis) >= (min_yaxis):
            max_range = max_yaxis
        else:
            max_range = min_yaxis
        max_tick = max_range
        min_tick = -max_range
        zero_tick = 0
        middle_tick_pos, middle_tick_neg = (max_tick / 2), (-max_tick / 2) 
        axis_ticks = [min_tick, middle_tick_neg, zero_tick, \
                      middle_tick_pos, max_tick]
        yminlim = min_yaxis
        ymaxlim = max_yaxis
    
    if axis == 'PITCH':
        max_yaxis, min_yaxis = max(axis_data), min(axis_data)
        if abs(max_yaxis) >= (min_yaxis):
            max_range = max_yaxis
        else:
            max_range = min_yaxis
        max_tick = max_range
        min_tick = -max_range
        zero_tick = 0
        middle_tick_pos, middle_tick_neg = (max_tick / 2), (-max_tick / 2) 
        axis_ticks = [min_tick, middle_tick_neg, zero_tick, \
                      middle_tick_pos, max_tick]
        yminlim = min_yaxis
        ymaxlim = max_yaxis
    """    
    if min(axis_data) >= 0:
        max_yaxis, min_yaxis = max(axis_data), min(axis_data)
        maxmin_difference = max_yaxis1 - min_yaxis1
        tick_spacing = maxmin_difference / (y_axis_tick_spacing1 - 1)
        #now that the tick spacing is determined, making a list of the ticks to use
        ticks_yaxis1 = [min_yaxis1]
        ticks_counting_up = min_yaxis1
        for x in range(y_axis_tick_spacing1 - 2):
            ticks_counting_up += tick_spacing
            ticks_yaxis1.append(ticks_counting_up)
        ticks_yaxis1.append(max_yaxis1)
    """    
    return axis_ticks, yminlim, ymaxlim


#Setting number of yticks for left axis to use
#---------------------------------------------
max_yaxis1, min_yaxis1 = max(yaxis1data), min(yaxis1data)
maxmin_difference = max_yaxis1 - min_yaxis1
tick_spacing = maxmin_difference / (y_axis_tick_spacing1 - 1)
#now that the tick spacing is determined, making a list of the ticks to use
ticks_yaxis1 = [min_yaxis1]
ticks_counting_up = min_yaxis1
for x in range(y_axis_tick_spacing1 - 2):
    ticks_counting_up += tick_spacing
    ticks_yaxis1.append(ticks_counting_up)
ticks_yaxis1.append(max_yaxis1)

if initParameters['Variables_Plot'][0] == 'UPDRAFT':
    ticks_yaxis1 = ytick_checker_thing(axis=initParameters['Variables_Plot'][0],\
                                       axis_data=yaxis1data)[0]
if initParameters['Variables_Plot'][1] == 'ROLL':
    ticks_yaxis2 = ytick_checker_thing(axis=initParameters['Variables_Plot'][1],\
                                           axis_data=yaxis2data)[0]
if initParameters['Variables_Plot'][1] == 'PITCH':
   ticks_yaxis2 = ytick_checker_thing(axis=initParameters['Variables_Plot'][1],\
                                           axis_data=yaxis2data)[0]

#Setting number of yticks for right axis to use
#----------------------------------------------
if second_axis_check == 'yes':
    max_yaxis2, min_yaxis2 = max(yaxis2data), min(yaxis2data)
    maxmin_difference = max_yaxis2 - min_yaxis2
    tick_spacing = maxmin_difference / (y_axis_tick_spacing2 - 1)
    #now that the tick spacing is determined, making a list of the ticks to use
    ticks_yaxis2 = [min_yaxis2]
    ticks_counting_up = min_yaxis2
    for x in range(y_axis_tick_spacing2 - 2):
        ticks_counting_up += tick_spacing
        ticks_yaxis2.append(ticks_counting_up)
    ticks_yaxis2.append(max_yaxis2)
    
    if initParameters['Variables_Plot'][1] == 'UPDRAFT':
        ticks_yaxis2 = ytick_checker_thing(axis=initParameters['Variables_Plot'][1],\
                                           axis_data=yaxis2data)[0]
    if initParameters['Variables_Plot'][1] == 'ROLL':
        ticks_yaxis2 = ytick_checker_thing(axis=initParameters['Variables_Plot'][1],\
                                           axis_data=yaxis2data)[0]
    if initParameters['Variables_Plot'][1] == 'PITCH':
        ticks_yaxis2 = ytick_checker_thing(axis=initParameters['Variables_Plot'][1],\
                                           axis_data=yaxis2data)[0]


    
#Altering the units to be more concise
#-------------------------------------
def unitShortener(name):
    if 'meter' in name:
        name = name.replace('meter', 'm')
        return name
    elif 'gram' in name:
        name = name.replace('gram', 'g')
        return name
    elif 'hour' in name:
        name = name.replace('hour', 'hr')
        return name
    elif 'minute' in name:
        name = name.replace('minute', 'min')
        return name
    elif 'Event Trigger' in name:
        return 'Event_Trig'
    elif 'sec' in name:
        name = name.replace('sec', 's')
        return name
    else:
        return name

#twice if two units needs to be shortened
#the way the func is set up it can only do one at a time   
yaxis1units = unitShortener(airplanedata[yaxis1].units)
yaxis1units = unitShortener(yaxis1units)
if second_axis_check == 'yes':
    yaxis2units = unitShortener(airplanedata[yaxis2].units)  
    yaxis2units = unitShortener(yaxis2units)  

    
#Initializing plot and setting labels
#------------------------------------
fig, ax = plt.subplots(figsize=(12, 8))
plt.grid(axis = 'y')
ax.set_xlabel('Time (HH:MM:SS)') 
ax.set_ylabel(airplanedata[yaxis1].title  + ' (' + yaxis1units + ')')
if second_axis_check != 'yes':
    plot_title = str(airplanedata[yaxis1].title)
elif second_axis_check == 'yes':
    plot_title = str(airplanedata[yaxis1].title) + ' and ' +\
                 str(airplanedata[yaxis2].title)
ax.set_title(plot_title)


#Formatting the x axis
#---------------------
ax.xaxis.set_major_locator(MinuteLocator(interval=minutes_between_ticks))
ax.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
minor_locator = AutoMinorLocator(2)
ax.xaxis.set_minor_locator(minor_locator)
ax.xaxis.set_minor_formatter(DateFormatter("%H:%M:%S"))
#fig.autofmt_xdate(rotation=30)
ax.tick_params(axis="x", which="both", rotation=30)
print('here')


#Formatting the first yaxis (and second if applicable)
#Then plotting the data
#-----------------------------------------------------
ax.set_yticks(ticks=ticks_yaxis1)
left_axis_plot = ax.plot(datetime_times, yaxis1data, color=color_left, label=airplanedata[yaxis1].title)

#Doing all the plotting stuff for the second y axis
if second_axis_check == 'yes':
    secax = ax.twinx() #instantiate a second axis that shares same xaxis
    secax.set_ylabel(airplanedata[yaxis2].title + ' (' + yaxis2units + ')')
    secax.set_ylim(ymax=ticks_yaxis2[2], ymin=ticks_yaxis2[1])
    secax.set_yticks(ticks=ticks_yaxis2)
    right_axis_plot = secax.plot(datetime_times, yaxis2data, color=color_right, label=airplanedata[yaxis2].title)

#got code from here on how to combine axes for the legend. it has more
#links and useful info in case needed for different types of plots
#https://stackoverflow.com/questions/5484922/secondary-axis-with-twinx-how-to-add-to-legend
combine_for_legend = left_axis_plot + right_axis_plot
labs = [l.get_label() for l in combine_for_legend]
ax.legend(combine_for_legend, labs, loc='upper right')


#Making a new folder for the current date that the plots are being created
#-------------------------------------------------------------------------
current_date = date.today()
file_created_date = current_date.strftime("%Y%m%d")

if os.path.exists('Flight_Plots/' + file_created_date) is False:
    os.mkdir('Flight_Plots/' + file_created_date)


#Creating the name for the folder that stores the plots. Makes sure the
#variables are organized alphabetically so that if they're ever
#flipped around, it's still saving what are essentially the same plots
#into the same folder to make everything a tad more tidy
#----------------------------------------------------------------------
variable_string = ''
if second_axis_check != 'yes': 
    variable_string = str(yaxis1)
elif second_axis_check == 'yes':
    if len(str(yaxis1)) >= len(str(yaxis2)):
        range_string = len(str(yaxis2))
    else:
        range_string = len(str(yaxis1))
    for letter in range(range_string):
        if str(yaxis1)[letter] == str(yaxis2)[letter]:
            pass
        elif str(yaxis1)[letter] > str(yaxis2)[letter]:
            variable_string = str(yaxis2) + '_and_' + str(yaxis1)
            break
        elif str(yaxis1)[letter] < str(yaxis2)[letter]:
            variable_string = str(yaxis1) + '_and_' + str(yaxis2)
            break


#Creating the variable folder if needed and saving the data
#----------------------------------------------------------    
if os.path.exists('Flight_Plots/' + file_created_date + '/' + \
                  variable_string) is False:
    os.mkdir('Flight_Plots/' + file_created_date + '/' + variable_string)

plt.savefig('./Flight_Plots/' + file_created_date + '/' + variable_string + \
            '/Flight' + flight_num + '_' + str(initTime)+'_'+ str(finTime) +\
            '.png')
