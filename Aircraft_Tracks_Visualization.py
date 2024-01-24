#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 18 14:47:20 2023

@author: james.klinman

Plots the aircraft track for a given time period over the 
sweep that is closest in elevation to the airplane during that time

Pre-requisites to run:
    Programs to run before this one:
        -Aircraft_Track_Data.py
    
    Files required:
        -Param_Info/File_Runner_Info.txt
        -Flight_Files/*FlightNum*.nc 
        -Radar_Files/*radar file* .nc
            -only tested for netcdf CFRadial files
        -Param_Info/*FlightNum*_paramInfo.txt
        -Sensor_Information/*FlightNum*_Track_and_Plots/FLight*FlightNum*_
            TrackDara_*timestart*_*timeend*.txt
"""

#FIND A PLACE FOR THIS
fontsizeParam = 80
zoomargv = 1

import matplotlib.pyplot as plt
import pyart
import os
import numpy as np
import cartopy.crs as ccrs
import sys
import netCDF4 
import math
import statistics as stat
import pandas as pd
import re
import Top_Hail_Methods as hail
from datetime import datetime, timedelta, date
import glob
import fnmatch
import json


#All the file calling and reading stuff
#--------------------------------------
flight_programs_file = 'Param_Info/File_Runner_Info.txt'
#flight_programs_info = pd.read_csv(flight_programs_file, sep=' * ', engine='python')
with open(flight_programs_file, 'r') as file:
    flight_programs_info = file.read()  
flight_programs_info = json.loads(flight_programs_info)
flight_num = str(flight_programs_info['flight_num'][0])
#needed to get flight num to access other files

#To keep track of the correct time period to use
#-----------------------------------------------
iteration_track_file = 'Automated_Files/Iteration_Tracker.txt'
iterationTracker = pd.read_csv(iteration_track_file, sep=' * ', engine='python')
time_index_to_use = iterationTracker['Iteration'][0]# * iterationTracker['Skip_Num'][0]

#Reading in more files
#---------------------
planefile = 'Flight_Files/' + flight_num + '.nc'
airplanedata = netCDF4.Dataset(planefile)
paramInfo = 'Param_Info/' + flight_num + '_paramInfo.txt'

#Reading in the parameter file. Need the start and end time periods
#to read in the rest of the files.
#------------------------------------------------------------------
#initParameters = pd.read_csv(paramInfo, sep=' * ', engine='python')
with open(paramInfo, 'r') as file:
    initParameters = file.read()  
initParameters = json.loads(initParameters)
initTime = str(initParameters['Time_Start'][time_index_to_use])
finTime = str(initParameters['Time_End'][time_index_to_use])

#Converting to datetime so that times can be used
#and compared using datetime
#------------------------------------------------
initTime_dt = datetime.strptime(initTime, "%H%M%S")
finTime_dt = datetime.strptime(finTime, "%H%M%S")
average_time_dt = initTime_dt + (finTime_dt - initTime_dt) / 2
middle_time_period = average_time_dt.strftime("%H%M%S")

#Below is the same process for getting the radar file as used in
#"Aircraft_Track_Data.py"
#--------------------------------------------------------------
#Onto getting the closest radar file to use. May not always be the best
#one however. Reading in files and updating the datetime
#----------------------------------------------------------------------
radar_files_list = glob.glob('Radar_Files/*')
flightdate = str(getattr(airplanedata, 'FlightDate'))
radardate_format = str(flightdate[6:10] + flightdate[0:2] + flightdate[3:5])

middle_time_period = datetime.strptime(middle_time_period, "%H%M%S").replace(year=int(radardate_format[:4]), 
                                                                   month=int(radardate_format[4:6]), 
                                                                   day=int(radardate_format[6:]))

#Finding closest radar file here. Does this through the start and
#end times for both the radar file and the time period specified
#----------------------------------------------------------------
difference_list = []
relevant_files_list = []
for file in radar_files_list:
    filename_base = os.path.basename(file)
    if fnmatch.fnmatch(filename_base, 'cfrad.' + str(flightdate[6:10] +
                                                     flightdate[0:2]) + 
                                                     flightdate[3:5] +'*.nc')\
        or fnmatch.fnmatch(filename_base, 'cfrad.' + 
                           str(flightdate[6:10] + 
                           flightdate[0:2]) + 
                           str(int(flightdate[3:5]) + 1) +'*.nc'):
        
        relevant_files_list.append(filename_base)
        
        # Extract timestamps from filenames
        timestamp_start = filename_base[6:21]
        timestamp_end = filename_base[29:44]

        # Convert timestamps to datetime objects
        time_start = datetime.strptime(timestamp_start, "%Y%m%d_%H%M%S")
        time_end = datetime.strptime(timestamp_end, "%Y%m%d_%H%M%S")

        # Set radardate_format as the date for testtime_dt
        testtime_dt = middle_time_period.replace(year=int(radardate_format[:4]),
                                                 month=int(radardate_format[4:6]), 
                                                 day=int(radardate_format[6:]))

        # Check if testtime_dt has a time component starting with '00', '01',
        #'02', or '03', add a day
        testtime_str = middle_time_period.strftime("%H%M%S")
        if testtime_str.startswith(('00', '01', '02', '03')):
            testtime_dt += timedelta(days=1)

        # Calculate time differences
        difference_1 = abs((time_start - testtime_dt).total_seconds())
        difference_2 = abs((time_end - testtime_dt).total_seconds())

        difference_list.append(difference_1)
        difference_list.append(difference_2)


#Figuring out which index corresponds to the
#closest radar file time wise
#-------------------------------------------
counter = 0
for x in difference_list:
    if x == min(difference_list):
        break
    counter += 1

radar_file_to_use = relevant_files_list[counter//2]

#time of period 
#time_start_file = radar_file_to_use[15:21]
#time_end_file = radar_file_to_use[38:44]

radarfile = 'Radar_Files/' + radar_file_to_use
trackfile = 'Sensor_Information/' + flight_num + '_Track_and_Plots/Flight' \
            + flight_num + '_TrackData_' + str(initTime) + '_' +\
            str(finTime) + '.txt'

    


#Finally finishing reading in the data from the files
#----------------------------------------------------
radar = pyart.io.read(radarfile)
trackData = pd.read_pickle(trackfile)
zoomfactor = int(zoomargv)

#Used if doing points of interest on the plot
#--------------------------------------------
latitudedata = airplanedata.variables['LATITUDE_DECIMAL_DEG_20Hz']
longitudedata = airplanedata.variables['LONGITUDE_DECIMAL_DEG_20Hz']

#Starting the set up plot
#getting the radar data prepped for use
#--------------------------------------
paramUse = str(initParameters['Radar_Variable'][0])

display = pyart.graph.RadarMapDisplay(radar)
#
# Next makes thresholding available
gatefilter = pyart.filters.GateFilter(radar)
# Basic threshold removes gates with missing reflectivity (DZ)
gatefilter.exclude_invalid(paramUse)
gatefilter.exclude_outside('DZ', 10, 100)
if paramUse == 'RX':
    gatefilter.exclude_above('RX', 1.05)
#gatefilter.exclude_outside('DZ', -3, 100)

# Centers a lat - lon based plotting domain on the radar:
#--------------------------------------------------------
projection = ccrs.LambertConformal(central_latitude=radar.latitude['data'][0],
                                   central_longitude=radar.longitude['data'][0])

# Size arguments are width, height in inches
#-------------------------------------------
fig = plt.figure(figsize = [25.0,25.0])

FlightNum = str(getattr(airplanedata, 'FlightNumber'))
FlightDate = str(getattr(airplanedata, 'FlightDate'))
FlightDate = FlightDate.split('/')
FlightDate = FlightDate[2]+''+FlightDate[0]+''+FlightDate[1]
label= str(initParameters['Time_Start'][0]) + '-' + str(initParameters['Time_End'][0]) + 'MT 22 June 1995, '\
     '\n Radar Variable: ' + str(paramUse)
#
# PPI plot specification
#paramuse is DZ, DR, LDR etc.    Sweep is closest sweep to aircraft.
#vmin/max are colorbar ranges.   cmap is color table to use
# here I'm using the Carbone42 color sequence (dates back to the NCAR RDSS software). 


#get auto graph limits and lines
#-------------------------------
airlatlist = trackData[0][3]
airlonlist = trackData[0][4]

upperLat = round(max(airlatlist) + (.05 / zoomfactor), 2)
lowerLat = round(min(airlatlist) - (.05 / zoomfactor), 2)
upperLon = round(max(airlonlist) + (.05 / zoomfactor), 2)
lowerLon = round(min(airlonlist) - (.05 / zoomfactor), 2)
 
#generating color limits and small marker colors for each variable
#-----------------------------------------------------------------
if paramUse == 'DZ':
    vminHolder, vmaxHolder = 10, 70
    colorHolder = 'blue'
    varName = 'Reflectivity'
    cbtickiter = 10
    units = 'dBZ'
elif paramUse == 'DR':
   vminHolder, vmaxHolder = -1, 5
   colorHolder = 'red' 
   varName = 'Differential\nReflectivity'
   cbtickiter = 1
   units = 'dB'
elif paramUse == 'LD':
   vminHolder, vmaxHolder = -30, -5
   colorHolder = 'yellow'
   varName = 'Linear Depolarization\nRatio'
   cbtickiter = 5
   units = 'dB'
elif paramUse == 'RX':
   vminHolder, vmaxHolder = .75, 1
   colorHolder = 'blue' 
   varName = 'Correlation\nCoeffiecient'
   cbtickiter = .05
   units = ''

#lat_lines2=np.array(hail.sizechange(np.arange(lowerLat, upperLat, abs(upperLat - lowerLat)/3), 5))

#Displaying the plot
#-------------------
sweepnumtouse = int(trackData[0][1][1])
display.plot_ppi_map(paramUse, sweepnumtouse, vmin=vminHolder, vmax=vmaxHolder,
                      min_lon=upperLon, max_lon=lowerLon, min_lat=lowerLat, max_lat=upperLat,
                      lat_lines=np.array(hail.sizechange(np.arange(lowerLat, upperLat, abs(upperLat - lowerLat)/3), 5)), 
                      resolution='10m',
                      lon_lines=np.arange(upperLon, lowerLon, -abs(lowerLon - upperLon)/3),
                      projection=projection,
                      fig=fig, lat_0=radar.latitude['data'][0],
                      lon_0=radar.longitude['data'][0],
                      cmap = pyart.graph.cm.Carbone42, gatefilter = gatefilter,
                      )

#Stuff to customize the plot
#---------------------------
cbar = display.cbs[0]
cbar.set_ticklabels(np.arange(vminHolder, vmaxHolder+cbtickiter, cbtickiter), fontsize=fontsizeParam) # [0.75, '0.80' , 0.85, '0.90' , 0.95, '1.00'  , 1.05]
cbar.set_label(label=units, fontsize=fontsizeParam)

#
# Draw the range rings (in km)
#display.plot_range_rings([30., 40.])

plt.title(varName, fontsize=fontsizeParam) 
plt.xticks(fontsize=fontsizeParam, rotation=20)
plt.yticks(fontsize=fontsizeParam)

#displaying all the lat long location of the plane for the time range
#--------------------------------------------------------------------
display.plot_point([airlonlist[:]], [airlatlist[:]], markersize=16, color="black")

#plotting the points of interet if they were specified in the parameter file
#---------------------------------------------------------------------------
if trackData[0][5].shape[0] == 0 and trackData[0][6].shape[0] == 0 \
                                 and trackData[0][7] == None:
    pass
else:
    #points of interest lists
    interestlat = trackData[0][5]
    interestlon = trackData[0][6]
    #displaying start and end point of manual relevant time periods
    display.plot_point(interestlat, interestlon, \
                        marker="x", markersize=50, mew=8, color="white")
    
    #This loop finds the reflectivities for the gates inbetween the interesting 
    #aircraft points and averages them
    Interesting_Point_Lower_Loc = trackData[0][7][0]
    Interesting_Point_Upper_Loc = trackData[0][7][2] #                                                                                  NOT AUTOMATIC HAS THE GLOBAL VARS
    radarInfo = []
    tempiter = 0
    #for x in range(len(interestingPoints)):
    for x in range(Interesting_Point_Lower_Loc, Interesting_Point_Upper_Loc):
        #radarInfo.append([])
        radarInfo.append(float(pyart.util.get_field_location(radar, 
                     float(latitudedata[x, 0]), float(longitudedata[x, 0]))
                     [paramUse][sweepnumtouse]))
        tempiter += 1
    

    """
    For RX because some values are erronous
    summedradarInfo1RX = 0
    tempiter = 0
    for x in radarInfo[0:10]:
        if x <= 1.05:
            summedradarInfo1RX += x
            tempiter += 1
    summedradarInfo1RX = summedradarInfo1RX/tempiter
    
    summedradarInfo2RX = 0
    tempiter = 0
    for x in radarInfo[10:21]:
        if x <= 1.05:
            summedradarInfo2RX += x
            tempiter += 1
    summedradarInfo2RX = summedradarInfo2RX/tempiter
    """
        
    summedradarInfo1 = sum(radarInfo[0:10]) / len(radarInfo[0:10])
    summedradarInfo2 = sum(radarInfo[10:21]) / len(radarInfo[10:21])
    
    plt.annotate(str(round(summedradarInfo1, 2)), 
                 xy=(8900, 37200), 
                 xytext=(0.78, .08), fontsize=fontsizeParam-34, textcoords='axes fraction',
                 #arrowprops=dict(facecolor='black', shrink=0.25, width=8, headwidth=25),
                 horizontalalignment='left',
                 verticalalignment='top')
    plt.annotate(str(round(summedradarInfo2, 2)), 
                 xy=(9800, 37500), 
                 xytext=(0.78, .18), fontsize=fontsizeParam-34, textcoords='axes fraction',
                 #arrowprops=dict(facecolor='black', shrink=0.25, width=8, headwidth=25),
                 horizontalalignment='left',
                 verticalalignment='top')
    
plt.show()
 
#fig.savefig('./T28_22jun1995_track' + paramUse + '.png')#, bbox_inches = 'tight')
fig.savefig('./Sensor_Information/757_Track_and_Plots/PPI_Plot_' + initTime +
            '_' + finTime + '.png')#, bbox_inches = 'tight')
