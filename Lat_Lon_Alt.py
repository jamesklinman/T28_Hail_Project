#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon July 24 10:30:12 2023

@author: James Klinman

Need the *FlightNum*.nc file to run this.
This version of the program is run using File_Runner.py
"""

import os
import numpy as np
import sys
import netCDF4 
from netCDF4 import Dataset
import math
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
#This is pulling all the data and storing in lists to be  
#used in the track file creation
#-------------------------------------------------------
HH = flight1.variables['TIME_HOURS_20Hz']
MM = flight1.variables['TIME_MINUTES_20Hz']
SS = flight1.variables['TIME_SECONDS_20Hz']
lat1 = flight1.variables['LATITUDE_DECIMAL_DEG_20Hz']
long1 = flight1.variables['LONGITUDE_DECIMAL_DEG_20Hz']
alt = flight1.variables['GPS_ALTITUDE']

HHx = HH.shape[1]
HHy = HH.shape[0]
MMx = MM.shape[1]
MMy = MM.shape[0]
SSx = SS.shape[1]
SSy = SS.shape[0]

lat1x = lat1.shape[1]
lat1y = lat1.shape[0]

long1x = long1.shape[1]
long1y = long1.shape[0]

altx = alt.shape[1]
alty = alt.shape[0]

HHFirstlist = []
MMFirstlist = []
SSFirstlist = []
lat1list = []
long1list = []
altlist = []



#This function forces the time to be two characters
#since if it's 01, 02, etc it can crop out the 0
#This is just a formatting thing (i think)
#--------------------------------------------------
def twocharacters(time):
    timestr = str(time)
    if len(timestr) == 2:
        pass
    elif len(timestr) < 2:
        timestr = '0' + timestr
    return timestr


#These loops write out the data points for the 
#whole data file and for each second
#It averages the hertz data into 1 second
#---------------------------------------------
for x in range(0, lat1y):
    temp_sum = []
    for y in range(lat1x):
        temp_sum.append(float(lat1[x,y]))
        temp_avg = sum(temp_sum) / len(temp_sum)
    lat1list.append(temp_avg) 
       
#The below chunk is a copy of the latitude but for longitude
for x in range(0, long1y):
    temp_sum = []
    for y in range(long1x): 
        temp_sum.append(float(long1[x,y]))
        temp_avg = sum(temp_sum) / len(temp_sum)
    long1list.append(temp_avg)
    
#The below chunk is a copy of the latitude but for altitude
for x in range(0, alty):
    temp_sum = []
    for y in range(altx):
        temp_sum.append(float(alt[x,y]))
        temp_avg = sum(temp_sum) / len(temp_sum)
    altlist.append(temp_avg) 
    
#Collects all the time into an initial list, then it
#goes through the new list and enforces the formatting
#of two characters for each time variable
#-----------------------------------------------------
for x in range(0, HHy):
    HHFirstlist.append(int(float(HH[x,0])))
for x in range(0, MMy):
    MMFirstlist.append(int(float(MM[x,0])))
for x in range(0, SSy):
    SSFirstlist.append(int(float(SS[x,0])))
    
HHlist = []
MMlist = []
SSlist = []
for x in HHFirstlist:
    #HHlist.append(x - 6)
    if int(float(x)) >= 24:
        newtime = int(float(x)) - 24
        HH2char = str(twocharacters(newtime))
        HHlist.append(HH2char) 
    elif int(float(x)) < 24:
        HH2char = str(twocharacters(x))
        HHlist.append(HH2char) 
for x in MMFirstlist:
    MM2char = str(twocharacters(x))
    MMlist.append(MM2char)
for x in SSFirstlist:
    SS2char = str(twocharacters(x))
    SSlist.append(SS2char)


#Getting flight data for naming
#------------------------------
FlightNum = str(getattr(flight1, 'FlightNumber'))

#Creating the output file
#------------------------        
TestFile = open('Sensor_Information/FlightTrack_' + FlightNum + '.txt', "w+")
TestFile.write('{a:<3}{b:<3}{c:<3}{d:<15}{e:<17}{f:<9}'.format(a='HH', b='MM',\
               c='SS', d='Lat', e='Long', f='Alt(m)'))
TestFile.write('\n')
#i did the range as HHy, but if there's ever a different y value in the data
#then that will have to be manually altered for the shortest array/list/etc
for x in range(HHy):    
    TestFile.write('{a:<3}{b:<3}{c:<3}{d:<15}{e:<17}{f:<9}'.format\
                   (a=HHlist[x], b=MMlist[x], c=SSlist[x],\
                    d=round(lat1list[x], 11), e=round(long1list[x], 11),\
                        f=round(altlist[x], 9)))
    TestFile.write('\n')

TestFile.close()

#Closing the file
#----------------
flight1.close()
    