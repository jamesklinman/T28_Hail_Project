#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 14:15:18 2023

@author: james.klinman

Finds the start and end location in the array for the time period(s)
specified. Also stores information such as sweep number, sweep height
airplane lat and lon for the time period,  and the latitude and longitude
for the points of interest where you want to draw X's on the map

Pre-requisites to run:
    Programs to run before this one:
        -Flight_Index_Finder
    
    Files required:
        -Flight_Files/*FlightNum*.nc 
        -Radar_Files/*radar file* .nc
            -only tested for netcdf CFRadial files
        -Param_Info/Indexs/Flight_*FlightNum*_Indexs.pkl
        -Param_Info/*FlightNum*_paramInfo.txt

Comments for future:
    -ONLY WORKS FOR THREE POINTS OF INTEREST AT THE MOMENT
"""

import os
import numpy as np
import sys
import netCDF4 
import pandas as pd
import Top_Hail_Methods as hail
import pickle
import glob
import fnmatch
from datetime import datetime, timedelta, date
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
paramInfo = 'Param_Info/' + flight_num + '_paramInfo.txt'
indexInfo = 'Param_Info/Indexs/Flight_' + flight_num + '_Indexs.pkl'

#Getting initial and end time for time period
#--------------------------------------------
#initParameters = pd.read_csv(paramInfo, sep=' * ', engine='python')
with open(paramInfo, 'r') as file:
    initParameters = file.read()  
initParameters = json.loads(initParameters)
initTime = str(initParameters['Time_Start'][time_index_to_use])
finTime = str(initParameters['Time_End'][time_index_to_use])
timeZone = int(initParameters['Timezone'][0])
time = initTime + ":" + finTime

#Converting to datetime so that times can be used
#and compared using datetime
#------------------------------------------------
initTime_dt = datetime.strptime(initTime, "%H%M%S")
finTime_dt = datetime.strptime(finTime, "%H%M%S")
average_time_dt = initTime_dt + (finTime_dt - initTime_dt) / 2
middle_time_period = average_time_dt.strftime("%H%M%S")

#Opening airplane file and reading in relevant arrays
#Also getting date of flight to give datetime more information
#-------------------------------------------------------------
airplanedata = netCDF4.Dataset(planefile)
timedata = airplanedata.variables['TIME_GPS_DECIMAL']
latitudedata = airplanedata.variables['LATITUDE_DECIMAL_DEG_20Hz']
longitudedata = airplanedata.variables['LONGITUDE_DECIMAL_DEG_20Hz']
aircraftalt = airplanedata.variables['GPS_ALTITUDE']
with open(indexInfo, "rb") as file:   # Unpickling
   indexs = pickle.load(file)

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

#Finally reading in radar file and opening the data for use
#----------------------------------------------------------
radarfile = 'Radar_Files/' + radar_file_to_use
radardata = netCDF4.Dataset(radarfile)
radarangle = radardata.variables['fixed_angle']
radarlat = radardata.variables['latitude']
radarlon = radardata.variables['longitude'] 
groundelevation = int(radardata['altitude'][:]) #was named elevation



#NOTE for all of this time stuff. I'm thinking of converting all the time
#dependent code into seconds from midnight as a standard way of operating
#plus that would make it easier to deal with the hertz data I think
#and then anything that is printed out to the user as a presentable format
#can be in HHMMSS
#-------------------------------------------------------------------------

#Determining if there are points of interest where
#user wants to draw x's on the map
#-------------------------------------------------
interestingPoints = []
for x in initParameters['Points_of_Interest']:
    if x == '.':
        pass
    else:
        interestingPoints.append(str(x))
#interestingPoints = ['235400', '235430', '235500']
if x == '.':
    pass
else:
    interestingPoints = hail.forceHHMMSS(interestingPoints)
print('hi')

pInterest = hail.sep_HHMMSS(time=interestingPoints) #points of interest shortend


#Naming some global variables that are later used in a calculation 
#variables for the calculation of radar sweep height. might not be accurate
#--------------------------------------------------------------------------
estH0 = .007 #in km, is the estimated height of the radar. potentially neglible
Rprime = 8483 #in km, the fictious earth radius pulled from the meteorlogical book
errorNum = -99.9

#Getting the start and end indexes in the the array
#--------------------------------------------------
time_range = initTime + ':' + finTime
startxvar = indexs[time_range][0][0][0]
startyvar = indexs[time_range][0][0][1]
endxvar = indexs[time_range][0][1][0]
endyvar = indexs[time_range][0][1][1]

#Get lat and lon coordinates for periods of interest
#---------------------------------------------------
airlatlist = hail.create_dataList(dataset=latitudedata, startxLoc=startxvar,\
                                    endxLoc=endxvar)
airlonlist = hail.create_dataList(dataset=longitudedata, startxLoc=startxvar,\
                                    endxLoc=endxvar)
print('Air track coords found and stored')

#The sweep number containing the airplane or closest to the airplace is found
#It was calculated using the avg og 
#----------------------------------------------------------------------------
sweepData = hail.getSweep(R=Rprime, Hradar=estH0, aircraftAlt=aircraftalt,\
                          radarlat=radarlat, radarlon=radarlon,\
                          radarAngles=radarangle, elevation=groundelevation,\
                          startxloc=startxvar, endxloc=endxvar, \
                          planelat=airlatlist, planelon=airlonlist)
print('Got the sweep data')

#The below chunk is finding the location of the interesting points within the 
#data file 
#----------------------------------------------------------------------------
planeMarkers = hail.HHMMSS_2_Dec(interestingPoints, timeZone)

if planeMarkers == []:
    Mark1Lat = None
    Mark1Lon = None
    Mark2Lat = None
    Mark2Lon = None
    Mark3Lat = None
    Mark3Lon = None
    latList = []
    lonList = []
    interestloc = None
    pass
else:
    if planeMarkers[0] == '.':
        Mark1Lat = None
        Mark1Lon = None
    else:
        Mark1 = hail.find_loc_in_array(dataset=timedata, valueToFind=planeMarkers[0]\
                                               , startLoc=startxvar)
        Mark1Lat = latitudedata[Mark1[0], 0]
        Mark1Lon = longitudedata[Mark1[0], 0]
        
    if planeMarkers[1] == '.':
        Mark2Lat = None
        Mark2Lon = None
    else:
        Mark2 = hail.find_loc_in_array(dataset=timedata, valueToFind=planeMarkers[1]\
                                               , startLoc=startxvar)
        Mark2Lat = latitudedata[Mark2[0], 0]
        Mark2Lon = longitudedata[Mark2[0], 0]
        
    if planeMarkers[2] == '.':
        Mark3Lat = None
        Mark3Lon = None
    else:
        Mark3 = hail.find_loc_in_array(dataset=timedata, valueToFind=planeMarkers[2]\
                                           , startLoc=startxvar)
        Mark3Lat = latitudedata[Mark3[0], 0]
        Mark3Lon = longitudedata[Mark3[0], 0]
   
    latList = [float(Mark1Lat), float(Mark2Lat), float(Mark3Lat)]
    lonList = [float(Mark1Lon), float(Mark2Lon), float(Mark3Lon)]
    interestloc = np.array([Mark1[0], Mark2[0], Mark3[0]])




print("Got positions of interesting points for analysis")

#Creating all the lists of data so that they're stored in rows/their own arrays
#Because creating same sized columns so that the data could be looped through
#sounded like a pain to do.
#it looks so ugly in the txt file but it reads in fine for the programs that
#use the data so ¯\_(ツ)_/¯ 
#------------------------------------------------------------------------------
dataRangearr = np.array([startxvar, startyvar, endxvar, endyvar])
sweepDataarr = np.array([sweepData[0], sweepData[1], sweepData[2]])
sweepheightsarr = np.array(sweepData[3])
airlatlistarr = np.array(airlatlist)
airlonlistarr = np.array(airlonlist)
latlistarr = np.array(latList)
lonlistarr = np.array(lonList)

allinformation = np.array([dataRangearr, sweepDataarr, sweepheightsarr,\
                           airlatlistarr, airlonlistarr, latlistarr,\
                           lonlistarr, interestloc], dtype=object)

df = pd.DataFrame(allinformation)


#Creating the file with all of the data we just pulled
#-----------------------------------------------------
FlightNum = str(getattr(airplanedata, 'FlightNumber'))
FlightDate = str(getattr(airplanedata, 'FlightDate'))
FlightDate = FlightDate.split('/')
FlightDate = FlightDate[2]+''+FlightDate[0]+''+FlightDate[1]

if os.path.exists('./Sensor_Information/'+ flight_num + '_Track_and_Plots/') is False:
    os.mkdir('./Sensor_Information/'+ flight_num + '_Track_and_Plots/')

filesave = str('Sensor_Information/' + flight_num + '_Track_and_Plots/' + 'Flight' + FlightNum + '_TrackData_' +
            initTime + '_' + finTime + '.txt')

df.to_pickle(filesave)

"""
#writing the start and end index into the init param file
#start_index_loc = initParameters.loc[0, 'Index_StartEnd']
#end_index_loc = initParameters.loc[0, 'Index_StartEnd']
initParameters.at[0, 'Index_StartEnd'] = startxvar
initParameters.at[1, 'Index_StartEnd'] = endxvar

initParameters.to_csv('testing', sep=' ', encoding='utf-8')

initParameters.insert(0, 'indxs', startxvar)
"""

