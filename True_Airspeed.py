#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon July 24 10:30:12 2023

@author: James Klinman

Gets true airspeed in format for soda to use
    
Pre-requisites to run:
    Programs to run before this one:
        -None
        
    Files required:
        -Flight_Files/*FlightNum*.nc
        

"""

# Note: This module import list is historical,
# possibly not all are required
import os
import sys
import netCDF4 
import pandas as pd
import json
#print (sys.getdefaultencoding())


"""
Below contains the files being accessed and creates the data file to be made
"""
#Getting flight number and file
#------------------------------
flight_programs_file = 'Param_Info/File_Runner_Info.txt'
#flight_programs_info = pd.read_csv(flight_programs_file, sep=' * ', engine='python')
with open(flight_programs_file, 'r') as file:
    flight_programs_info = file.read()  
flight_programs_info = json.loads(flight_programs_info)
flight_num = str(flight_programs_info['flight_num'][0])

flightfile = 'Flight_Files/' + flight_num + '.nc'

flight1 = netCDF4.Dataset(flightfile)


"""  
Below creates the lat and long lists for the airplane for both flights
"""
#This is pulling in the data and making empty lists
#HHMMSS commented out through nb but you can uncomment if you want
#you just need to comment all the seconds stuff instead
HH = flight1.variables['TIME_HOURS_20Hz']
MM = flight1.variables['TIME_MINUTES_20Hz']
SS = flight1.variables['TIME_SECONDS_20Hz']
#Seconds = flight1.variables['time']
airspeed = flight1.variables['TRUE_AIRSPEED_CALCULATED']


HHy = HH.shape[0]
MMy = MM.shape[0]
SSy = SS.shape[0]
#secondsy = Seconds.shape[0]
airspeedy = airspeed.shape[0]


HHFirstlist = []
MMlist = []
SSlist = []
#Secondslist = []
airspeedlist = []

#These loops write out the data points for the whole data file and for each second
for x in range(0, HHy):
    if len(str(int(HH[x,0]))) != 2:
        HHloop = "0" + str(int(HH[x,0]))
        HHFirstlist.append(HHloop)
    else:
        HHFirstlist.append(str(int(HH[x,0])))

for x in range(0, MMy):
    if len(str(int(MM[x,0]))) != 2:
        MMloop = "0" + str(int(MM[x,0]))
        MMlist.append(MMloop)
    else:
        MMlist.append(str(int(MM[x,0])))
    
for x in range(0, SSy):
    if len(str(int(SS[x,0]))) != 2:
        SSloop = "0" + str(int(SS[x,0]))
        SSlist.append(SSloop)
    else:
        SSlist.append(str(int(SS[x,0])))
"""
for x in range(0, secondsy):
    Secondslist.append(float(Seconds[x,0]))
"""    
"""
#just takes first hertz of airspeed measurements
for x in range(0, airspeedy):
    airspeedlist.append(float(airspeed[x,0]))
"""
#averages over 20hz
for x in range(0, airspeedy):
    templist = [] #a list to store each hertz of data so it can be averaged
    for y in range(0, 19):
        templist.append(airspeed[x, y])
    avg_airspeed = sum(templist) / len(templist) 
    airspeedlist.append(avg_airspeed)
    
    
   
HHlist = []
#correcting for colorado timezone
#currently -0 because for soda it needs the uncorrected time
for x in HHFirstlist:
    HHloop = int(x)
    if HHloop >= 24:
        HHloop = HHloop - 24
    if len(str(HHloop)) != 2:
        HHloop = int(HHloop)
        HHloop = "0" + str(HHloop)
        HHlist.append(HHloop)
    else:
        HHloop = str(int(x))
        HHlist.append(HHloop)
    
MasterTimeList = []
for x, y, z in zip(HHlist, MMlist, SSlist):
    MasterTimeList.append(str(x) + str(y) + str(z))
   

#change seconds to HHMMSS if doing HHMMSS and vice versa
#changes the secondslist to Masterlist
FlightNum = str(getattr(flight1, 'FlightNumber'))

TestFile = open('Sensor_Information/HHMMSS_True_Calc_Airspeed_' + str(FlightNum) +'.txt', "w+")
TestFile.write('{a:<9}{j:<14}'.format(a='HHMMSS', j='Calc_Airspeed'))
TestFile.write('\n')

for x in range(airspeedy):    
    TestFile.write('{a:<9}{j:<14}'.format\
                   (a=str(MasterTimeList[x]), j=round(airspeedlist[x], 4)))
    TestFile.write('\n')

TestFile.close()

#Closing the file
#----------------
flight1.close()
    
