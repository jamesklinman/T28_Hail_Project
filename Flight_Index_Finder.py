# -*- coding: utf-8 -*-
"""
Created on Mon Oct 23 15:08:55 2023

@author: james.klinman

purpose is to get the index in the array for the start and end time 
for the time range to look at

creates file for each flight
dict keys are time period in HHMMSS:HHMMSS
and values are the indexs 

Pre-requisites to run:
    Programs to run before this one:
        -NA
    
    Files required:
        -Param_Info/File_Runner_Info.txt
        -Flight_Files/*FlightNum*.nc
        -Automated_Files/Iteration_Tracker.txt
            -should be produced automatically when running "Rile_Runner"
        -Param_Info/*FlightNum*_paramInfo.txt
"""

import netCDF4
import pandas as pd
import sys
import Top_Hail_Methods as hail
import pickle
import os
from datetime import date
import json


#All the file calling and reading stuff
#--------------------------------------
flight_programs_file = 'Param_Info/File_Runner_Info.txt'
with open(flight_programs_file, 'r') as file:
    flight_programs_info = file.read()  
flight_programs_info = json.loads(flight_programs_info)
#flight_programs_info = pd.read_csv(flight_programs_file, sep=' * ', engine='python')
flight_num = str(flight_programs_info['flight_num'][0])
#needed to get flight num to access other files

file_airplane = 'Flight_Files/' + flight_num + '.nc'
param_file = 'Param_Info/' + flight_num + '_paramInfo.txt'
iteration_track_file = 'Automated_Files/Iteration_Tracker.txt'

airplanedata = netCDF4.Dataset(file_airplane)
timedata = airplanedata.variables['TIME_GPS_DECIMAL']
#initParameters = pd.read_csv(param_file, sep=' * ', engine='python')
with open(param_file, 'r') as file:
    initParameters = file.read()  
initParameters = json.loads(initParameters)
iterationTracker = pd.read_csv(iteration_track_file, sep=' * ', engine='python')

#This bit is the time period to use from the paramFile
#It is tracked while File_Runner is looping through it's code
time_index_to_use = iterationTracker['Iteration'][0] #* iterationTracker['Skip_Num'][0]

initTime = str(initParameters['Time_Start'][time_index_to_use])
finTime = str(initParameters['Time_End'][time_index_to_use])
timeZone = int(initParameters['Timezone'][0])

flight_number = str(getattr(airplanedata, 'FlightNumber'))
time = initTime + ":" + finTime

current_date = date.today()
file_created_date = current_date.strftime("%Y%m%d")


#The if else statements are where the the indexs are found. 
#It checks to see if the file has already been created, and
#if it has, then it just adds/appends the new time ranges
#into the file. So, for each flight, the start and end index
#for each specified time period should only be found once 
#which should save on some processing time.
#-----------------------------------------------------------
if os.path.isfile('./Param_Info/Indexs/Flight_' + \
                  flight_number + '_Indexs.pkl') is True:
    with open('Param_Info/Indexs/Flight_' + \
              flight_number + '_Indexs.pkl', "rb") as file:   # Unpickling
       indexFile = pickle.load(file)
    print(indexFile)
      
    #Skips already found times if they exist
    if time in indexFile:
        pass
        print('time')
    else:    
        #Time range converted to decimal because that was initially 
        #the easiest array to look through for time. 
        timeConverted = hail.HHMMSS_2_Dec(HHMMSS=[initTime, finTime], timeCorrect=timeZone)
        timeStart, timeEnd = timeConverted[0], timeConverted[1]

        startArray = hail.find_loc_in_array(dataset=timedata, valueToFind=timeStart)
        endArray = hail.find_loc_in_array(dataset=timedata, valueToFind=timeEnd)

        #pull out the start and end xy coordinates
        startxvar = startArray[0]
        startyvar = startArray[1]
        endxvar = endArray[0]
        endyvar = endArray[1]

        #adding the start and end index's to the dictionary
        #with the given time range as the dict key
        indexFile[time] = [[[startxvar, startyvar], [endxvar, endyvar]]]

else:
    #initializing a new dictionary to store all the 
    #index's if the file doesn't exist yet
    indexFile = {}
    
    #read if statement code for comments on code below
    timeConverted = hail.HHMMSS_2_Dec(HHMMSS=[initTime, finTime], timeCorrect=timeZone)
    timeStart, timeEnd = timeConverted[0], timeConverted[1]

    startArray = hail.find_loc_in_array(dataset=timedata, valueToFind=timeStart)
    endArray = hail.find_loc_in_array(dataset=timedata, valueToFind=timeEnd)

    startxvar = startArray[0]
    startyvar = startArray[1]
    endxvar = endArray[0]
    endyvar = endArray[1]
    
    indexFile[time] = [[[startxvar, startyvar], [endxvar, endyvar]]]



"""
if os.path.exists('./Param_Info/Indexs/' + file_created_date) is False:
    os.mkdir('./Param_Info/Indexs/' + file_created_date)
"""

#saving the data
#---------------
with open('Param_Info/Indexs/Flight_' + flight_number +\
          '_Indexs.pkl', 'wb+') as file:
    pickle.dump(indexFile, file)