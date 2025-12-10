#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initial program created on Mon Nov 27 11:54:20 2023
Big rework on Mon Apr 15 13:25:39 2024
Big rework #2 on Wed Sept 18 12:00:00 2024
#3 in October 20 2024
#Adding output file stuff and updating so much 05/13/2025

@author: james.klinman

#numpy is v2.?. different from package installation required for pbp viewer
#numpy v2 has stddev with the option to provide a mean
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#from matplotlib.collections import PatchCollection
#from matplotlib.patches import Rectangle
import math
import netCDF4
from datetime import date
import pickle
import json
import re
from statistics import mode, stdev
#import statistics 
#import scipy
#import sympy as sy
import xarray as xr
import glob
import stat
import matplotlib
import gc

#------------------
#self defining stuff
#------------------

#all this stuff needs to go in config file
units = 'meter'
specified_timezone = 'utc' #'utc'  #could be local or utc
                            #for the time specified in config file or at start here
                            #local for 1995 flights and utc for 2000 flights
                            

#specifying different rejections                    
rejection_flags_accept = [0, 4]#, 8]#, 4]      
reject_below_arearatio = 0.5#3

#adding options for area ratio
area_ratio_indv_check = True #true for different area ratios for different datasets
#area_ratio_indv = [0.3, 0.3, 0.5] #leave empty if option is false
area_ratio_indv = [0.5, 0.5]
#must be in same order as files 
#put None for files that aren't processed by soda

#These flights have startimes after midnight. For some reason the code prefers
#when these are marked in a new day eg... 241830 would become 001830. HOWEVER
#the disp files aren't always reset to a new day, so they might start and run
#over or already be over 240000. For some reason this is different for different
#cases with both SODA and DISP files. I'm not sure why. I'm too lazy to actually
#look into it futher. But, for the flights where this is an issue, they are noted
#and the program just subtracts 86400 from the flight time in seconds when
#finding the start and end index in the array for the disp file. It's a quick 
#and easy manual fix. Not automatic but whatever at this point.
#If other datasets are to be processed, this may need to be updated
starts_after_midnight_list = ['781', '759', '756']
flight_timezone_probe_mismatch = []#['670']#[]#['670'] #i think this is only if including hvps
flight_timezone_probe_mismatch_668 = False #for when inluding hvps  seems to also be needed for 670?
probe_local_to_utc_all = [['HAIL-2D', 'HAIL-1D']]

plot_hvps_case = False #should only be needed for flightt 668 in conjunction iwth timezone mismatch

#options are 'diam', 'xsize', 'ysize', 'xextent', 'areasize' for \/
sizes_to_plot = ['diam', 'xsize', 'ysize', 'areasize', 'xextent'] #xextent not included rn it was excluded in the below chunk where it reads in the files as well. like do a ctrl f and search for all xextent to verify
#sizes_to_plot = ['xsize']
             
#true means exclude particles that aren't all in
#to include all in counts, need to adjust rejection flag accepts above
use_all_in = True
        



corr_fac = 1#.1#.1 #!!!!!
active_time = 5 #!!!!!!


diode_size_SPEC = .0009 #.9mm to meter
diode_size_HVPS = .0002 #.2mm -xres  or .8mm-yres to meter
diodes_1DSPEC = 128
diodes_2DSPEC = 64
diodes_HVPS = 190 #256     #190 is how much soda uses
length_SPEC_u = 0.9# 0.9 to match field     .93#.93 #meters    #.99 is from soda
length_SPEC_s = 0.9# 0.9 is expected reading theses     .99#soda version
length_HVPS = .2 #meters
Area_1DSPEC = diode_size_SPEC * diodes_1DSPEC * length_SPEC_u
Area_2DSPEC = diode_size_SPEC * diodes_2DSPEC * length_SPEC_u
Area_HVPS = diode_size_HVPS * diodes_HVPS * length_HVPS

#SA_1D = .0009 * 128 * .93  #diode size in m * diode number * length of probe
#SA_2D = .0009 * 64 * .93


Area_2DC = 0.000025 * 25 * 0.061



#--------------------------------
#reading in config file information

#make a switch that either true for import from config file or false 
#for input by self !!!!!!!!!!!!
#--------------------------------



#getting flight num
#------------------
flight_programs_file = 'Param_Info/File_Runner_Info.txt'
flight_programs_info = pd.read_csv(flight_programs_file, sep=' * ', engine='python')
with open(flight_programs_file, 'r') as file:
    flight_programs_info = file.read()  
flight_programs_info = json.loads(flight_programs_info)
flight_num = str(flight_programs_info['flight_num'][0])

#can get flight num from sys.argv by including in subprocess run instead
#is treated like command line argument
flight_num = sys.stdin.read().strip()   #comment out if running manually rather than from file_runner.py
print('F L I G H T N U M ', flight_num)
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
flight_num = '670'

#file running files
#------------------
paramInfo = 'Param_Info/' + flight_num + '_paramInfo.txt'
indexInfo = 'Param_Info/Indexs/Flight_' + flight_num + '_Indexs.pkl'
iteration_track_file = 'Automated_Files/Iteration_Tracker.txt'



#getting path to save file
#------------------------
filepath_file = 'Random/filepaths.json'
with open(filepath_file, 'r') as file:
    filepaths = file.read()  
filepaths = json.loads(filepaths)
for year in filepaths:
    for flight in filepaths[year]:
        if flight_num in flight:
            path_to_flight = flight
flightpath = path_to_flight + '/' + flight_num + '.nc'
path_to_folder = path_to_flight + '/Code_Files_and_Outputs/'

#Calling and reading in plane files for data and naming information
#-----------------------------------------------------------------
TASfilename = path_to_folder + 'Sensor_Information/HHMMSS_True_Calc_Airspeed_'\
               + flight_num + '.txt'
planefile = flightpath

#TASfilename = 'HHMMSS_True_Calc_Airspeed_761.txt'
#planefile = '761.nc'
#TASfilename = '../../Flight_Data/yr2000/HHMMSS_True_Calc_Airspeed_' + flight_num + '.txt'
#planefile = '../../Flight_Data/yr2000/T28_STEPS2000_' + flight_num + '.nc'

TASfile = pd.read_csv(TASfilename, sep=' * ', dtype={'HHMMSS': str}, engine='python')
airplanedata = netCDF4.Dataset(planefile)

#Getting the flight data and other data for file naming and plot title making.
#Needed up here since SODA file names require date
#-----------------------------------------------------------------------------
FlightNum = str(getattr(airplanedata, 'FlightNumber'))

FlightDate = str(getattr(airplanedata, 'FlightDate'))
FlightDateSplit = FlightDate.split('/')
FlightDate = FlightDateSplit[2]+''+FlightDateSplit[0]+''+FlightDateSplit[1]
FlightDate_File = FlightDateSplit[0]+''+FlightDateSplit[1]+''+FlightDateSplit[2]

FlightTime = str(getattr(airplanedata, 'TimeInterval'))
FlightTimeStart = str(FlightTime)[0:8]
FlightTimeStart = FlightTimeStart.split(':')
FlightTimeStart = FlightTimeStart[0] + FlightTimeStart[1] + FlightTimeStart[2]

#duplicate method not used anywhere else i think 
#!!!
plane_time_start = getattr(airplanedata, 'TimeInterval')[0:8]
for char in plane_time_start:
    if char == ':':
        plane_time_start = plane_time_start.replace(':', '')

#Calling start and end time before reading in the 
#rest of the files since they're time dependent
#------------------------------------------------
initParameters = pd.read_csv(paramInfo, sep=' * ', engine='python')
with open(paramInfo, 'r') as file:
    initParameters = file.read()  
initParameters = json.loads(initParameters)

iterationTracker = pd.read_csv(iteration_track_file, sep=' * ', engine='python')
with open(indexInfo, "rb") as file:   # Unpickling
   indexs = pickle.load(file)


time_index_to_use = iterationTracker['Iteration'][0]# * \
    #iterationTracker['Skip_Num'][0]
#time_index_to_use =  0                                      #  to only do first one. 

#this updated version is not mutlitple time compatible yet
#!!!        
#final temporal resolution of particle size distribution
TimeResolution = int(initParameters['PSD_Time_Res'][0])

starttime = str(initParameters['Time_Start'][time_index_to_use])
endtime = str(initParameters['Time_End'][time_index_to_use])
timeZone = int(initParameters['Timezone_true'][0])


#TimeResolution = 10
#timeZone = 6 #6 is for local, 0 is utc

#manual doing the start and end times 
#starttime = '241800' #!!!!!!!!!!time_low
#endtime = '241940'
#starttime = '240701'
#endtime = '240901'
#starttime = '241801'
#endtime = '241941'
#starttime = '240701'
#endtime = '242301'
#starttime = '242100'
#endtime = '242300'
#starttime = '234626'
#endtime = '234926'
#starttime = '243000'
#endtime = '243400'
#starttime = '242000'
#endtime = '242500'

#starttime = '241800'
#endtime = '241920'

#hvps periods aligned with hailspec finder


#starttime = '234830'
#endtime   = '234920'

#starttime = '235030'
#endtime   = '235050'

#starttime = '235220'
#endtime   = '235240'

#starttime = '235940'
#endtime   = '240010'

#starttime = '240600'
#endtime   = '240650'

#starttime = '241820'
#endtime   = '241930'

#fakdjsfljkaskjl;
#starttime = '241800'
#endtime   = '242310'

#starttime = '235111' 
#endtime   = '235808'

#uhhh matchin gpaul field
#starttime = '235600'
#endtime = '235750'

#for a hail period
#starttime = '242100'
#endtime   = '242210'

#starttime = '241840'
#endtime   = '241910'

#starttime = '242100'
#endtime = '242300'


#whole flight?????
#starttime = '233000'
#endtime   = '244000'


#whole f668 flight
#starttime = '230300'
#endtime   =  '241000'



#f754 time whole interval
#starttime = '214400'
#endtime   = '222400'

#f756
#starttime = '004550'#'244550' 
#endtime   = '013720'#'253720'

#f757
#starttime = '234840'
#endtime   = '243400'
#starttime = '235500'
#endtime   = '235700'

#f759
#starttime = '010500'
#endtime   = '015700'

#f761
#starttime = '225800'
#endtime   = '234300'

#f781
#starttime = '011215'
#endtime   = '011500'

#f798
#starttime = '183800'
#endtime   = '190500'


#f803
#starttime = '204300'
#endtime   = '205100'

#f815
#starttime = '240230'
#endtime   = '244530'

#f819
#starttime = '194230'
#endtime   = '195740'

#f820
#starttime = '211200'
#endtime   = '212700'


#bin determinations times for 757 and 670
#starttime = '241835'
#endtime   = '241905'

#starttime = '213000'
#endtime = '213500'


#670
starttime = '152700'
endtime = '152830'


#-------------------------------------------------------
#Defining all the definitions used in the plotting program
#-------------------------------------------------------



def SDSMT_disp_txt_read(dispfile):  
    file_read = 0
    try:

        strToDelete = 'F l i g h t  ...  ........  Hail Info'
        endoffiletodelete = '-=-  Hail Dump Complete  -=-'
        fin = open(dispfile, "r")
        fout = open("Random/Spec_Corrected_File", "w+")
        print('TYPE ONE')
        for line in fin:
            line = re.sub(strToDelete, '' , line)
            line = re.sub(endoffiletodelete, '', line)
            fout.write(line)
        fin.close()
        fout.close()

        #first loop from https://pynative.com/python-count-number-of-lines-in-file/
        #gets length of file and get reads in just the spec data
        with open(r"Random/Spec_Corrected_File", 'r') as file:
            for count, line in enumerate(file):
                pass
            FileLen = count + 1
        Spacing = 55          #these skips are hardcoded in. They're specific to
        RowsToSkip = []       #this type of file so it shouldn't matter that they 
        RowsToSkip.append(57) #aren't dynamically found
        NewHeadSkip = 57
        while NewHeadSkip <= FileLen:
            NewHeadSkip += Spacing
            RowsToSkip.append((NewHeadSkip))
        SpecFile = "Random/Spec_Corrected_File"
        SpecData = pd.read_csv(SpecFile, sep=' * ', header=0, skiprows=RowsToSkip, engine='python')
        file_read = 1
    except:
        pass

    if file_read == 0:
        print('type 2')
        try:
            strToDelete = 'F l i g h t  ...  .........  Hail Info'
            endoffiletodelete = '-=-  Hail Dump Complete  -=-'
            fin = open(dispfile, "r")
            fout = open("Random/Spec_Corrected_File", "w+")
            for line in fin:
                line = re.sub(strToDelete, '' , line)
                line = re.sub(endoffiletodelete, '', line)
                fout.write(line)
            fin.close()
            fout.close()

            #first loop from https://pynative.com/python-count-number-of-lines-in-file/
            #gets length of file and get reads in just the spec data
            with open(r"Random/Spec_Corrected_File", 'r') as file:
                for count, line in enumerate(file):
                    pass
                FileLen = count + 1
            Spacing = 55          #these skips are hardcoded in. They're specific to
            RowsToSkip = []       #this type of file so it shouldn't matter that they 
            RowsToSkip.append(57) #aren't dynamically found
            NewHeadSkip = 57
            while NewHeadSkip <= FileLen:
                NewHeadSkip += Spacing
                RowsToSkip.append((NewHeadSkip))
            SpecFile = "Random/Spec_Corrected_File"
            SpecData = pd.read_csv(SpecFile, sep=' * ', header=0, skiprows=RowsToSkip, engine='python')
        except:
            pass


    return SpecData


def data_hertz(data_time):
    """
    data_time should be a numpy array
    might update to include lists
    """
    #hopefully this doesn't create an error if crossing from midnight to next day
    
    #20 comparisons in case of any momentary glitches in recording the time period
    time_list = []
    for time_indx in range(20):
        time_list.append(float(data_time[time_indx + 1]) - float(data_time[time_indx]))
        
    common_hertz = mode(time_list)
    return common_hertz


def txt_Header_Search_bins(file, searchterm):
    fn = open(file, "r")
    error_message = None  
    bin_track = 0
 
    for line in fn:
        if bin_track == 1:
            try:
                bin_information = line
                bin_track = 2
            except:
                print('debugging header search bins')        
        if line.find(searchterm) != -1:
            bin_track += 1
        
        if bin_track >= 2:
            fn.close
            return bin_information
    
    if error_message != None:
        fn.close
        return print(error_message)
    

def txt_Header_Search(file, searchterm):
    fn = open(file, "r")
    error_message = None  
    bin_track = 0
 
    for line in fn:
        if line.find(searchterm) != -1 and bin_track != 2:
            bin_track += 1
        
        if bin_track == 1:
            try:
                line_information = line
                bin_track = 2
                continue
            except:
                print('debugging header search bins')        
        
        if bin_track == 2:
            try:
                next_line_information = line
                bin_track += 1
            except:
                print('no next line? at end of file?')
        
        if bin_track >= 3:
            fn.close
            return line_information, next_line_information
    
    if error_message != None:
        fn.close
        return print(error_message)
    
    
def probename_retrieve(filetype, file): #!!!not tested for ADPAA case yet!
    probename = None    
    if filetype == 0: #soda case
        with open(file, 'r') as file:
            # Read and print each line
            for line in file:
                #the_line = line.strip()
                indxstart = line.find('for the') + 8
                indexend = line.find('probe') - 1
                probename = line[indxstart:indexend]
                if probename == 'HAIL':
                    probename = 'HAIL-2D' #!!!!true for T28 case, may not be true for other projects
                break #just need to read first line so can break here
    if filetype == 1: #adpaa case
        with open(file, 'r') as file:
            # Read and print each line
            for line in file:
                #the_line = line.strip()
                if line.find('SN:') != -1:
                    indexend = line.find(' (')
                    probename = line[0:indexend]
                if probename != None:
                    break
    if filetype == 2: #disp case
        probename = 'HAIL-1D'
    if filetype == 3: #.dat case
        probename = file.data['op'][0]['probetype'][0].decode('utf-8')
        if probename == 'HAIL':
            probename = 'HAIL-2D' #!!!!true for T28 case, may not be true for other projects
    if filetype == 4: #soda pbp case
        data_temp = netCDF4.Dataset(file)
        probename = data_temp.SHORTNAME
        if probename == 'HAIL':
            probename = 'HAIL-2D' #!!!!true for T28 case, may not be true for other projects
        data_temp.close
    
    return probename


#Data searching and alteration relevant definitions
#-------------------------------------------------

def find_index_of_closest_value(array, valueToFind):
    differences = np.abs(array - valueToFind)
    closest_index = differences.argmin()
    return closest_index
    
    
#Time relevant definitions
#------------------------
    
def forceHHMMSS(data):
    #ISSUE, this probably only effective for the HH
    if type(data) is int or type(data) is str:
        if len(str(data)) != 6:
            if len(str(data)) == 5:
                HHMMSS = '0' + str(data)
            if len(str(data)) == 4:
                HHMMSS = '00' + str(data)
            if len(str(data)) == 3:
                HHMMSS = '000' + str(data)
            if len(str(data)) == 2:
                HHMMSS = '0000' + str(data)
            if len(str(data)) == 1:
                HHMMSS = '00000' + str(data)
        elif len(str(data)) == 6:
            HHMMSS =str(data)
        return HHMMSS
    elif type(data) is list:
        datalist = []
        for entry in data:
            if type(entry) is int or type(entry) is str:
                if len(str(entry)) != 6:
                    if len(str(entry)) == 5:
                        HHMMSS = '0' + str(entry)
                        datalist.append(HHMMSS)
                    if len(str(entry)) == 4:
                        HHMMSS = '00' + str(entry)
                        datalist.append(HHMMSS)
                    if len(str(entry)) == 3:
                        HHMMSS = '000' + str(entry)
                        datalist.append(HHMMSS)
                    if len(str(entry)) == 2:
                        HHMMSS = '0000' + str(entry)
                        datalist.append(HHMMSS)
                    if len(str(entry)) == 1:
                        HHMMSS = '00000' + str(entry)
                        datalist.append(HHMMSS)
                elif len(str(entry)) == 6:
                    HHMMSS =str(entry)
                    datalist.append(HHMMSS)
        return datalist


def HHMMSS_adjustHH(time, adjust_amount):
     #changes the HH value by the amount specified
     newhour = int(str(time)[0:2]) + adjust_amount
     newtime = str(newhour) + str(time)[2:6]
     return newtime


def HHMMSS_2_SS(time):
    #Assumes HHMMSS format. No Decimal. No colons. Should be str
    #assumes time is a string of a value
    
    HH = (int(time[0:2]) * 3600)#get HH and converts to sec
    MM = (int(time[2:4]) * 60)
    SS = (int(time[4:6]))
    time_sec = HH + MM + SS

    return(time_sec)

       
def time_timezoneadjusted(time, timezone, hours_adjust):
    if timezone == 'utc':
        timeout = time
    elif timezone == 'local':
        timeout = HHMMSS_adjustHH(time, hours_adjust)  
        timeout = forceHHMMSS(timeout)
        
    return timeout


def seconds_HHMMSS(time):
    #takes interger values, not strings. idk if floats work
    #floats do not work as it makes the seconds default to 0
    #okay now 
    try: 
        decimal = str(time).split('.')[1][:5] #saves decimal out to 5 places
    except:
        decimal = ''
    time = int(float(time))
    HH = str(math.floor(time/3600))
    temp = time % 3600
    MM = str(math.floor((temp/60)))
    SS = str(temp%60)
    #print(HH, MM, SS)
    if len(HH) != 2:
        if len(HH) == 1:
            HH = str(0) + HH
        else:
            HH ='00'
    if len(MM) != 2:
        if len(MM) == 1:
            MM = str(0) + MM
        else:
            MM ='00'
    if len(SS) != 2:
        if len(SS) == 1:
            SS = str(0) + SS
        else:
            SS ='00'
            
    if decimal == '':
        final_time = str(HH+MM+SS)
    else:
        final_time = str(str(HH+MM+SS)+'.'+str(decimal))
    return final_time


def HHMMSS_adjust(time, adjust_amount, adjust_type):
    #adjust type is 's' 'm' or 'h' S M H work too
    #does not work with fractions of a second
    
    adjust_amount = int(adjust_amount)
    
    if type(time) == int:
        time = str(time)
    elif type(time) == float:
        time = str(int(time))
    elif type(time) == str:
        pass
    elif type(time) == list:
        print('Time should be single variable not a list')
        return

    temp_SS = int(time[4:6])
    temp_MM = int(time[2:4])
    temp_HH = int(time[0:2])

    if adjust_type == 's' or adjust_type == 'S':
        temp_SS = temp_SS + adjust_amount
    elif adjust_type == 'm' or adjust_type == 'M':     
        temp_MM = temp_MM + adjust_amount
    elif adjust_type == 'h' or adjust_type == 'H':     
        temp_HH = temp_HH + adjust_amount

    while temp_SS >= 60:
        temp_MM = temp_MM + 1
        temp_SS = temp_SS - 60
    while temp_MM >= 60:
        temp_HH = temp_HH + 1
        temp_MM = temp_MM - 60
        
    temp_SS = str(temp_SS)
    temp_MM = str(temp_MM)
    temp_HH = str(temp_HH)
    if len(temp_SS) != 2:
        temp_SS = '0' + temp_SS
    if len(temp_MM) != 2:
        temp_MM = '0' + temp_MM
    if len(temp_HH) != 2:
        if len(temp_HH) > 2:
            pass
        elif len(temp_HH) < 2:
            temp_HH = '0' + temp_HH
    
    final_time = temp_HH + temp_MM + temp_SS
    return final_time



#------------------------------------------------------------------------------
#Reading in data files and
#retrieving all metadata information
#------------------------------------------------------------------------------



#!!!!!!!!!!!!!!!!!!!!!
#filenameDISP = path_to_flight + '/disp' + FlightNum + '.0'
#filenamePBP_V  = 'Particle_Image_20240916/06222000_232921_HVPS1.pbp.nc'
#filenamePBP_V   = 'Particle_Image_20240916/hvpsmorebins/06222000_232921_HVPS1.pbp.nc'
#filenamePBP_H   = 'Particle_Image_20240916/06222000_232921_HAIL.pbp.nc'
#filenamePBP_2DC =  'Particle_Image_20240916/hvpsmorebins/06222000_232921_2DC.pbp.nc'


#filenameJamesPBP = 'James_pbp_file7.pbp.nc'
#filenameSODAPBP  = '06222000_232921_HAIL.pbp.nc'

#filenameJamesDISP = 'James_pbpdisp_file3.pbp.nc'
#filenameOldDISP   = 'disp757.0'
#filenameHVPS      = '06222000_232921_HVPS1.pbp.nc'

#f668 case
#filenameDISP = '../../yr1995/f668/DISP668.0'
#filenamePBP_V   = '../../yr1995/f668/SODA_Outputs/20241108/06221995_231519_HVPS1.pbp.nc'



#filename_list = [filenamePBP_V, filenamePBP_H, filenameDISP]
#filename_list = [filenameJamesPBP, filenameSODAPBP]
#filename_list = [filenameJamesDISP, filenameJamesPBP]#, filenameOldDISP]
#filename_list = [filenameSODAPBP, filenameJamesDISP]
#filename_list = [filenameHVPS, filenameSODAPBP, filenameOldDISP]
#filename_list = [filenameSODAPBP, filenameOldDISP]
#filename_list = [
#filename_list = [filenamePBP_V]
#filename_list = [filenamePBP_H]
#filename_list = [filenamePBP_V, filenamePBP_2DC]


#New processed everything ugh case
#filename_2DHAIL = '../../Flight_Data/yr2000/f754/06112000_212622_HAIL.pbp.nc'
#filename_2DHAIL = '../../Flight_Data/yr2000/f756/06202000_001707_HAIL.pbp.nc'
#filename_2DHAIL = '../../Flight_Data/yr2000/f757/06222000_232921_HAIL.pbp.nc'
#filename_2DHAIL = '../../Flight_Data/yr2000/f759/06252000_004856_HAIL.pbp.nc'
#filename_2DHAIL = '../../Flight_Data/yr2000/f761/06292000_223303_HAIL.pbp.nc'
#filename_2DHAIL = '../../Flight_Data/yr2002/f781/06122002_002546_HAIL.pbp.nc'
#filename_2DHAIL = '../../Flight_Data/yr2003/f798/05162003_180329_HAIL.pbp.nc'
#filename_2DHAIL = '../../Flight_Data/yr2003/f803/06012003_194450_HAIL.pbp.nc'
#filename_2DHAIL = '../../Flight_Data/yr2003/f815/07262003_233942_HAIL.pbp.nc'
#filename_2DHAIL = '../../Flight_Data/yr2003/f819/07292003_191032_HAIL.pbp.nc'
#filename_2DHAIL = '../../Flight_Data/yr2003/f820/07302003_204613_HAIL.pbp.nc'

#filename_1DHAIL = '../../Flight_Data/yr2000/f757/disp757.0'
#filename_1DHAIL = '../../Flight_Data/yr2000/f761/DISP761.0'

#filename_list = [filename_2DHAIL, filename_1DHAIL]


filename_1DHAIL = path_to_flight + '/disp' + FlightNum + '.0'
twod_pattern_HS = path_to_flight + '/SODA_Outputs/*HAIL.pbp.nc'
filename_2DHAIL = glob.glob(twod_pattern_HS)[0]#path_to_flight + '/SODA_Outputs/.....................pbp.nc'
#twod_pattern_HV = path_to_flight + '/SODA_Outputs/*HVPS1.pbp.nc'
#filename_2DHVPS = glob.glob(twod_pattern_HV)[0]
#filename_list = [filename_2DHAIL, filename_1DHAIL, filename_2DHVPS]
#filename_list = [filename_2DHAIL, filename_1DHAIL]
#filename_list = [filename_2DHVPS]
#filename_list = [filename_2DHAIL]
#filename_list = [filename_1DHAIL]
#filename_list = [filename_1DHAIL, filename_2DHAIL, filename_2DHVPS]
filename_list = [filename_1DHAIL, filename_2DHAIL]

counter = 0
file_read_check = 0
dat_file_check = 0
dataframes_list = []
dataframes_dat_info= []
dataframes_hertz = []
dataframes_types = [] #0 denotes soda conc, 4 denotes soda pbp file , 2 is disp
dataframes_binsize = []
dataframes_probename = []
dataframes_fullinterval = []   #filled below when adjusting data hertz
dataframes_bin_midpoints = []
dataframes_bin_endpoints = []
dataframes_bin_startpoints = []
dataframes_plot_legend_labels = []
for file in filename_list:
    #creating dataframes    
    try:
        try:
            pbp_data = netCDF4.Dataset(file)
            if pbp_data != None:
                data_type = 4 #soda pbp file
                dataframes_types.append(data_type)
                bin_info = list(pbp_data.getncattr('ENDBINS'))
                
                #if you want to set manual bin sizes you can do it here
                #bin_info = list(np.array(['4000', '5000', '6000', '7000', '8000', '9000',
                #            '10000', '11800', '14600', '19200', '24400', 
                #            '31800', '42400', '50000']).astype(np.float32))
                
                #bin_info = list(np.array(['200', '400', '600', '800', '1000',
                #            '1200', '1400', '1600', '1800', '2200', '2600',
                #            '3000', '3400', '3800', '4200', '4600', '5000',
                #            '6000', '7000', '8000', '9000', '10000', '15000',
                #            '20000', '25000', '30000']).astype(np.float32))
                
                
                #group particles by the second
                #only accept if it meets the rejection criteria
                #then group by size bins in that second
                fastcircle_diam = pbp_data['diam']
                xsize_diam      = pbp_data['xsize']
                ysize_diam      = pbp_data['ysize']
                xextent_diam    = pbp_data['xextent']#pbp_data['xextent']
                areasize_diam   = pbp_data['areasize']
                particle_times  = pbp_data['time']
                part_arearatios = pbp_data['arearatio']
                part_rejectflags = pbp_data['rejectionflag']
                
                #next make the above info into a series of datasets
                dataframe = [fastcircle_diam, xsize_diam, ysize_diam, 
                             xextent_diam, areasize_diam, particle_times,
                             part_arearatios, part_rejectflags] #XEXTENT
                dataframes_list.append(dataframe)
                hertz = 1 #data_hertz(dataframe['Time'])
                dataframes_hertz.append(hertz)
        except:
            pass

        try:
            file_check_type = txt_Header_Search(file, 'F l i g h t')
            if file_check_type != None:
                data_type = 2
                dataframes_types.append(data_type)
                bin_info = ['4000', '5000', '6000', '7000', '8000', '9400', \
                            '11000', '13000', '15600', '18600', '21700', \
                            '26100', '32100', '40000', '50000'] 
                
                print('HIHII')
                dataframe = SDSMT_disp_txt_read(file)

                dataframes_list.append(dataframe)
                hertz = data_hertz(dataframe['Time'])
                dataframes_hertz.append(hertz)
        except:
            pass

        
    except:
        print('Couldnt determine type of file or bins')
  
    #Can get bin start, end, midpoint and size now that all bins are retrieved
    try:
        num_bins = len(bin_info)
        bin_start_points = bin_info[0:num_bins-1]
        bin_end_points = bin_info[1:num_bins]
        bin_size = []
        bin_mid_points = []
        for x in range(num_bins-1):
            startpoint = int(float(bin_start_points[x]))
            endpoint = int(float(bin_end_points[x]))
            size = endpoint - startpoint
            midpoint = startpoint + (size/2)
            bin_size.append(size)
            bin_mid_points.append(midpoint)
        
        dataframes_bin_startpoints.append(bin_start_points)
        dataframes_bin_midpoints.append(bin_mid_points)
        dataframes_bin_endpoints.append(bin_end_points)
        dataframes_binsize.append(bin_size)
    except:
        print('Issue getting bin size or midpoint')

    try:
       probename_retrieved = probename_retrieve(dataframes_types[counter], file) 
       dataframes_probename.append(probename_retrieved)
       #print(dataframes_probename)
    except:
       print("probename/type was not retrieved properly")
       
    
    try:
        dataframes_plot_legend_labels.append('')
    except:
        print('Issue encountered while retrieving or not retrieving SODA dat' \
              + ' processing information')
       
    
    print('File read in check, (nothing below means everything was read in correctly)')
    print('Checking for file:  ', file)
    if data_type == None:
        print('No data type retrieved')
    if bin_info == None:
        print('No bin information retrieved')
    if type(dataframe) == None:
        print('No particle count/conc data retrieved')
    if hertz == None:
        print('No hertz retrieved')
    if probename_retrieved == None:
        print('No probename retrieved')
    print('File read in check complete')
    
    #for spot in range(dataframes_bins[counter].shape[0]):
     #   binstart = dataframes_bins[counter][spot]
      #  binend = dataframes_bins[counter][spot+1]
    data_type = None
    dat_file = None    
    bin_info = None
    dataframe = None
    hertz = None
    probename_retrieved = None
    #dat_file_check = 0    
    counter += 1
    print('Finished retrieving data file information')
       
#getting midpoints out of loop


#storing everying in a numpy array format
for x in range(len(dataframes_list)):
    #dataframes_list[x] = np.array(dataframes_list[x])
    dataframes_bin_midpoints[x] = np.array(dataframes_bin_midpoints[x])
    dataframes_bin_endpoints[x] = np.array(dataframes_bin_endpoints[x])
    dataframes_bin_startpoints[x] = np.array(dataframes_bin_startpoints[x])
    dataframes_binsize[x] = np.array(dataframes_binsize[x])
dataframes_hertz = np.array(dataframes_hertz)
dataframes_types = np.array(dataframes_types)


#------------------------------------------------------------------------------
#Sorting through and finding where the start and end time for the given
#time interval is in the data arrays
#------------------------------------------------------------------------------


#The DISP files are inconsistent and switch bewtween local time and utc time
#throughout the years, so this little bit of code is meant to adjust
#any local time to utc
for x in range(len(dataframes_list)):
    if dataframes_types[x] == 2: #disp case
        if specified_timezone == 'local':
            adj_times = [int(float(HHMMSS_adjustHH(str(item), timeZone))) for item in dataframes_list[x]['Time']]
            dataframes_list[x]['Time'] = adj_times

#specifying which probes need to be adjusted to utc
#liekly to match hvps or something honestly im just tired and this is annoying
if flight_num == '670':
    probe_local_to_utc = probe_local_to_utc_all[0]


#check if utc. if not then convert
#Force 24+ hours. no 00 stuff
#Verifies that all the time start/end line up
#Then collects the start and end indices in the data files
#so first enforce utc. then everything to seconds. compare all time. collect start and end indices
#so, starttime, disp, and soda/adpaa all need to be sfm
#--------------------------------------------------------------------------
midnight_check = 0 # means data starts after midnight if 0
counter = 0 #tracking which dataframe is accessed 
array_start_indices = []
array_end_indices = []
start_time_list = []
end_time_list = []
start_time_seconds = [] #for comparing all times as seconds in case any indidces need to be adjusted
end_time_seconds = []
for data in dataframes_list:
    if dataframes_types[counter] == 2: #disp
        if len(str(int(float(data['Time'][10])))) == 6:
            file_time = np.array([float(HHMMSS_2_SS(str(int(float(item))))) for item in data['Time']])
            if flight_num in starts_after_midnight_list:
                file_time = np.array(file_time) - 86400 #setting into new day. Explanation located at "starts_after_midnight_list" defining
        
        else:
            file_time = [float(item) for item in data['Time']]
            if flight_num in starts_after_midnight_list:
                file_time = np.array(file_time) - 86400 #setting into new day. Explanation located at "starts_after_midnight_list" defining
        
        #need to adjust some probes timezone. 
        #example, f670 has local time for spec2d and 1d, but utc for hvps.
        #this all to  utc
        if flight_num in flight_timezone_probe_mismatch:
            if dataframes_probename[counter] in probe_local_to_utc[counter]:
                file_time[:] += timeZone*3600
                
        #print(file_time, '\n\n\n\n')
        #if specified_timezone == 'local': #not fully tested? dont remember
        #    seconds_adjust = timeZone * 3600
        #    print(seconds_adjust, 'seconds adjust')
        #    file_time_temp = [float(HHMMSS_2_SS(str(item)))+seconds_adjust for item in data['Time']]
        #    file_time = file_time_temp
    if dataframes_types[counter] == 4: #soda pbp
        print(';hiuhihifhjufgghsdfjksadkjsdjk')
        #file_time = [float(item) for item in data[5]]
        file_time = np.array(list(data[5][:]))
        #copied from above but honestly maybe it'll break things but also maybe it will fix the lack of data.
        #if flight_num in starts_after_midnight_list:
        #    file_time = file_time - 86400 #setting into new day. Explanation located at "starts_after_midnight_list" defining
        #need to adjust some probes timezone. 
        #example, f670 has local time for spec2d and 1d, but utc for hvps.
        #this all to  utc
        if flight_num in flight_timezone_probe_mismatch:
            if dataframes_probename[counter] in probe_local_to_utc:
                file_time[:] += timeZone*3600
                
            
    if flight_timezone_probe_mismatch_668 is True:
        if dataframes_probename[counter] == 'HVPS1':
            file_time[:] -= timeZone*3600
                
    

    files_starttime = starttime
    files_endtime = endtime   
    """     
    if float(starttime[0:2]) <= float('04'):
        files_starttime = str(int(float(starttime[0:2])) + 24) + starttime[2:6]
        files_starttime = str(HHMMSS_2_SS(files_starttime))
    if float(endtime[0:2]) <= float('04'):
        files_endtime = str(int(float(endtime[0:2])) + 24) + endtime[2:6]
        files_endtime = str(HHMMSS_2_SS(files_endtime))
    """
    if len(files_starttime) == 6:
        files_starttime = str(HHMMSS_2_SS(files_starttime))
    if len(files_endtime) == 6:
        files_endtime = str(HHMMSS_2_SS(files_endtime))
    
    index_start = find_index_of_closest_value(np.array(file_time), float(files_starttime))
    index_end = find_index_of_closest_value(np.array(file_time), float(files_endtime))
    print(index_start, index_end)
    array_start_indices.append(index_start)
    array_end_indices.append(index_end)
    
    try:
        #if dataframes_types[counter] == 2: #disp and for local timezone
        #    if specified_timezone == 'local': #not fully tested? dont remember
        #        seconds_adjust = timeZone * 3600
        #        print(seconds_adjust, 'seconds adjust')
        #        file_time_temp = [float(HHMMSS_2_SS(str(item)))+seconds_adjust for item in data['Time']]
        #        file_time = file_time_temp
        #else: #for every other case
        pass
        #if dataframes_types[counter] == 2: #disp case
        #    start_time_list.append(file_time[index_start]) #(data['Time'][index_start])
        #    end_time_list.append(file_time[index_end]) #(data['Time'][index_end])
        #    while float(start_time_list[counter]) < float(starttime):
        #        index_start += 1
        #        start_time_list[counter] = file_time[index_start] #data['Time'][index_start]
        #        array_start_indices[counter] = index_start
    except:
        try:
            if dataframes_types[counter] == 3: #.dat file needs to be read in differently
                #start_time_list.append(time_array[index_start])
                #end_time_list.append(time_array[index_end])
                pass
        except:
            print('No start/end time find. File type not readable for some reason. Could be pbp file. If so, ignore this message.')
    print(index_start, index_end)
    if dataframes_types[counter] == 2: #disp
        start_time_list.append(file_time[index_start]) #(data['Time'][index_start])
        end_time_list.append(file_time[index_end]) #(data['Time'][index_end])
        if specified_timezone == 'local':
            start_time_list[counter] = HHMMSS_adjustHH(data['Time'][index_start], timeZone)
            end_time_list[counter] = HHMMSS_adjustHH(data['Time'][index_end], timeZone)
    if dataframes_types[counter] == 4: #pbp nc soda
        start_time_list.append(seconds_HHMMSS(file_time[index_start]))#data[5][index_start]))
        end_time_list.append(seconds_HHMMSS(file_time[index_end]))#data[5][index_end]))
        while float(start_time_list[counter]) < float(starttime):
            print(start_time_list, starttime)
            index_start += 1
            start_time_list[counter] = seconds_HHMMSS(file_time[index_start])#seconds_HHMMSS(data[5][index_start])
            array_start_indices[counter] = index_start
        while float(end_time_list[counter]) > float(endtime):
            index_end -= 1
            end_time_list[counter] = seconds_HHMMSS(file_time[index_end])
            array_end_indices[counter] = index_end
        
    
    start_time_seconds.append(file_time[index_start])
    end_time_seconds.append(file_time[index_end])

    #print(start_time_list, 'timecheck')
    #print(end_time_list)
    #print(start_time_seconds)

    counter += 1

#!! warning this assumes no shorter than 1hz data
#the if statement checks for time values/indices that are offset
#since data from soda typically comes chunked in 5 seconds already (or your specified time chunks)
#and the disp files are on a 1 second basis, so the soda files may not land
#exactly on the time specified in the config file, and the higher hertz disp
#needs to adjust for that
#update note,,,,,,,,,,,,,,,,,
#A general explanation is that if one file has a lower hertz than the other,
#then the below block of code will make sure that the starttime for the higher
#hertz data lines up with the lower hertz data. This just makes sure that the 
#starttimes are the same and not offset by a number of seconds.
#However, it is rigged to adjust the hertz to the first file in the file list, which
#means it's not actally doing what's described above.

#check which one has the lowest hertz, then use that one as the base starttime
#adjust the others to start on the same intervals as the lowest hertz. basically, if they're the same, do nothing.
#if one is 241831, and the other is 241800, then recognize that the 241831 is on 5 seconds
# and count backwards 31 26 21 16 11 6 1 56, once you have a value smaller, compare
#the smaller value and the previous value and check which is closer, and that
#is the new starttime.



#below is code that is useful if using soda conc or dat files. didn't finish developing
#it since this code is specfically for using soda pbp files and 1 second hertz
#file such as the  Hail Spectrometer disp file.
#So, below block could be further developed to support other file types
"""
#first check which file has the lowest hertz
max_hertz_file = 0
max_hertz_check = 0
counter = 0
for t in dataframes_hertz:
    if t > max_hertz_check:
        max_hertz_check = t
        max_hertz_file = counter
    counter += 1

#checking if the start time for each file is aligned with the smallest hertz
#this ensures the time intervals will all be aligned and start at the same
#second
time_adjust = []
counter = 0
for file_hertz in dataframes_hertz:
    if counter == max_hertz_file:
        time_adjust.append(0)
    else:
        if file_hertz != max_hertz_check:
            
            
    
    specified_timezone
#now check which file is closest to the start time a
smallest_time_difference = 0
smallest_time_file      = 0
counter = 0
for t in start_time_seconds:
    if float(t) != float(starttime_seconds):
        time_dif = t - starttime_seconds
    if time_dif > smallest_time_difference:
        smallest_time_difference = time_dif
        smallest_time_file = counter
    counter += 1
    
#now to adjust the time closest to the start time, so that it's start time 
#aligns with the longest hertz.
if max_hertz_file != smallest_time_file:
    #get time difference between the  file with the smallest hertz and each file
    #file closest 
    
if max_hertz_file == smallest_time_file
""" 

#old time offset check. not useful for this pbp version
"""
time_offset_check = set([int(float(item)) for item in start_time_seconds])   
if len(time_offset_check) > 1:
    for file_index in range(len(start_time_seconds)):
        if dataframes_types[file_index] == 2: #only for disp case
            disp_time = start_time_seconds[file_index]
            disp_time2 = end_time_seconds[file_index]
            non_disptime_indexes = [index for index, value in enumerate(start_time_seconds) if value != disp_time]
            non_disptime = start_time_seconds[non_disptime_indexes[0]]
            
            seconds_adjust = int(non_disptime) - int(disp_time)
            disp_time = disp_time + seconds_adjust  #no - sPBP",ince can go up or down
            disp_time2 = disp_time2 + seconds_adjust
            disp_time = seconds_HHMMSS(disp_time)
            disp_time2 = seconds_HHMMSS(disp_time2)
            
            start_time_list[file_index] = disp_time
            end_time_list[file_index] = disp_time2 
            array_start_indices[file_index] = array_start_indices[file_index] + seconds_adjust
            array_end_indices[file_index] = array_end_indices[file_index] + seconds_adjust
"""

#Making lists of the start time intervals
#----------------------------------------
"""time_var = str(start_time_list[0])#seconds_HHMMSS(float(start_time_list[0]))
time_interval_amount = (array_end_indices[0] - array_start_indices[0]) / \
                        (TimeResolution / dataframes_hertz[0])
"""                        
"""           
smallest_start_time = 99999
smallest_start_time_index = None
counter = 0
for t in start_time_seconds:
    if t < smallest_start_time:
        smallest_start_time = t
        smallest_start_time_index = counter
    counter += 1
"""
"""                 
starttime_HHMMSS = []
endtime_HHMMSS = []
for index in range(int(time_interval_amount)):
    starttime_HHMMSS.append(time_var)
    time_var = HHMMSS_adjust(time_var, TimeResolution, 's') #assumes intervals are seconds #!!!!! need to make adjust time adjustab;e or just do a time resolution check and make it different for if it's over in seconds
    endtime_HHMMSS.append(time_var)
"""    
#start and end time in seconds since seconds is easier to do math
#with than HHMMSS
specified_starttime_seconds = HHMMSS_2_SS(starttime)
specified_endtime_seconds   = HHMMSS_2_SS(endtime)

#getting the start and end time for each interval based on the input time interval
total_seconds_specified = specified_endtime_seconds - specified_starttime_seconds
total_periods_specified = math.ceil(total_seconds_specified / TimeResolution)

#creating a start and end time to display on the plot and table for each period
starttime_HHMMSS = []
endtime_HHMMSS   = []
time_temp = specified_starttime_seconds
for interval in range(total_periods_specified):
    interval_startstop = seconds_HHMMSS(time_temp)
    starttime_HHMMSS.append(str(interval_startstop))
    time_temp += 10
    interval_startstop = seconds_HHMMSS(time_temp)
    endtime_HHMMSS.append(str(interval_startstop))
    
    

    
#getting tas file indices in for concentration calculations
#---------------------------------------------------------
try:
    #first checking which time format, seconds or HHMMSS to use when filtering 
    #through the tas file
    if dataframes_types[0] == 0 or dataframes_types[0] == 1:
        data_time_type = 'seconds'  
    elif dataframes_types[0] == 2 or dataframes_types[0] == 4:
        data_time_type = 'hhmmss'
    elif dataframes_types[0] == 3:
        data_time_type = 'seconds'
    
    #everythings assumes 'Time' name for true airspeed time column
    if len(str(TASfile['Time'][0])) <= 5: #86400 seconds is 240000. hopefully the starttime isn't greater than 034639
        tas_type = 'seconds'    
        pass#not written for this yet but should be similar to HHMMSS case
    if len(str(TASfile['Time'][0])) == 6:
        tas_type = 'hhmmss'

    if tas_type == data_time_type:
        tas_time_start = starttime_HHMMSS[0]#start_time_list[0]
        tas_time_end = endtime_HHMMSS[-1]#end_time_list[0]
    else:
        if data_time_type == 'seconds':
            tas_time_start = seconds_HHMMSS(int(float(starttime_HHMMSS[0])))   #start_time_list[0])))
            tas_time_end = seconds_HHMMSS(int(float(endtime_HHMMSS[-1])))      #end_time_list[0])))
        elif data_time_type == 'hhmmss': 
            #tas_time_start = HHMMSS_2_SS(str(start_time_list[0]))
            #tas_time_end = HHMMSS_2_SS(str(end_time_list[0]))
            tas_time_start = starttime_HHMMSS[0]#start_time_list[0]
            tas_time_end = endtime_HHMMSS[-1]#end_time_list[0]
    
    #if tas time isn't filled out for full 10 seconds, do so
    
    
    if flight_num in flight_timezone_probe_mismatch:
        pass
        """
        backtime  = str(int(tas_time_start[0:2]) - int(timeZone))
        backtime2 = str(int(tas_time_end[0:2]) - int(timeZone))
        
        tas_time_start = backtime + tas_time_start[2:]
        tas_time_end   = backtime2 + tas_time_end[2:]
        """
    
    #!!!
    #curretly only setup with tas time set up as  
    tas_start_index = find_index_of_closest_value(TASfile['Time'], float(tas_time_start))
    tas_end_index = find_index_of_closest_value(TASfile['Time'], float(tas_time_end))
    
    #getting tas data
    TAS_array = []
    for tas in range(tas_start_index, tas_end_index+1):
        TAS_array.append(TASfile['Calc_Airspeed'][tas])
    TAS_array = np.array(TAS_array)
except Exception as e:
    print(f'Error: {e}')
    

#input('pause)')
#------------------------------------------------------------------
#Normalizing the data arrays so that they're all in the same format  
#and easier to work with
#------------------------------------------------------------------



def DISP_Counts_Normalize(data, startindex, endindex, bin_amount):
    array_len = endindex - startindex
    normalized_data_array = np.zeros((array_len, bin_amount), dtype=float)
    row_counter = 0
    #print(startindex, endindex, bin_amount)
    for indexes in range(startindex, endindex):
        #now we're into each row
        array_binnum = 0 #the array we're making starts with 0 but the channels start with 1
        for binnum in range(1, bin_amount):
            #now we;re looping through each channel
            #print(binnum, indexes)
            counts = int(round(data[str(binnum)][indexes])) #hail counts should be int anyways
            normalized_data_array[row_counter, array_binnum] = int(counts)  
            array_binnum += 1
        row_counter += 1
        #print('notice meeeeeeeeeeee', normalized_data_array)
    return normalized_data_array




def Adjust_Data_Hertz(data, hertz, desired_hertz):
    #desired hertz should be higher (slower) than hertz
    hertz_factor = int(desired_hertz/hertz)
    if len(data.shape) == 2:
        # Check if padding is needed
        #rows, cols = data.shape
        #if rows % hertz_factor != 0:
        #    padding_length = hertz_factor - (rows % hertz_factor)
        #    # Pad with zeros for simplicity
        #    data = np.pad(data, ((0, padding_length), (0, 0)), 'constant') #this bit is from chatgpt. too tired to do self
        #print(data.shape)
        reshaped_array = data.reshape(-1, hertz_factor, data.shape[1])
        summed_array = np.sum(reshaped_array, axis=1)
    elif len(data.shape) == 1:
        reshaped_array = data.reshape(-1, hertz_factor)
        summed_array = np.sum(reshaped_array, axis=1)
    
    return summed_array    
    






def SODA_PBP_Normalize_np(data, startindex, endindex, bin_amount, bins_mins, \
                       bins_maxs, sizes_to_plot, starttimesec, endtimesec, fileindex):
    global rejection_flags_accept, reject_below_arearatio, area_ratio_indv_check, area_ratio_indv
    
    global flight_timezone_probe_mismatch_668, dataframes_probename
    #chatgpt helped shorten this function by aboiut 100 lines of code

    # Define length of normalized data array based on user-specified time
    array_len = math.ceil(specified_endtime_seconds - specified_starttime_seconds)
    start_time_difference = math.floor(starttimesec - specified_starttime_seconds)
    if flight_timezone_probe_mismatch_668 is True:
        if dataframes_probename[fileindex] == 'HVPS1':
            tempstarttimesec = starttimesec - 3600*6
            start_time_difference = math.floor(tempstarttimesec - specified_starttime_seconds)
            #print(tempstarttimesec)
    #print(array_len, start_time_difference)
    
    #print("Array length. Tiem intervals  -  ", array_len)
    #print("Start time difference probe/specififed  -  ", starttimesec, "/", specified_starttime_seconds)
    # Set area ratio threshold
    area_ratio_threshold = area_ratio_indv[fileindex] if area_ratio_indv_check \
                                                     else reject_below_arearatio
    min_bin_size = dataframes_bin_startpoints[fileindex][0]
    max_bin_size = dataframes_bin_endpoints[fileindex][-1]
    #print("Area ratio threshold  -  ", area_ratio_threshold)

    #sizing_data_arrays_sorted contains each of the different sizing methods 
    sizing_data_arrays_sorted = []
    counter = 0  # Initialize counter to use for indexing sizing methods
    
    
    # Loop through particle types
    for part_type in ['diam', 'xsize', 'xextent', 'ysize', 'areasize']:
        if part_type in sizes_to_plot:
            print("doing size")
            
            #make data mask filtering out all particles that aren't greater than the area ratio threshold and bigger than the smallest possible size
            datamask = (data[6][:]>area_ratio_threshold) & (data[counter][:]>=min_bin_size)\
                       & (data[counter][:]<=max_bin_size)
            datamask = np.array(datamask)

            # Apply the mask to filter data arrays
            masked_data = [np.array(arr)[datamask] for arr in data]
            time_data = masked_data[5]  # Assumed to be time column
            diam_data = masked_data[counter]
            reject_data = masked_data[7]
            #arto_data = masked_data[6]
            
            #print(time_data[10])
            #print(starttimesec)
            

            # Initialize normalized data array for this particle type
            normalized_data_array = np.zeros((array_len, bin_amount), dtype=float)
            #print("Sizing method initilized array:  Not shown, very long")#, normalized_data_array)

            # Skip to next if no data is within the specified range
            #specified_endtime_seconds is global idk why i never made it an input
            if float(data[5][startindex]) > specified_endtime_seconds or float(data[5][endindex]) < specified_starttime_seconds:
                if flight_timezone_probe_mismatch_668 is True:
                    if dataframes_probename[fileindex] == 'HVPS1':
                        temp_specified_starttime = specified_starttime_seconds + 6*3600
                        temp_specified_endtime = specified_endtime_seconds + 6*3600
                        if float(data[5][startindex]) > temp_specified_endtime or float(data[5][endindex]) < temp_specified_starttime:
                            sizing_data_arrays_sorted.append(normalized_data_array)
                            print("No data found for this sizing method in the given start and end time.")
                            continue #skips to next sizing method
                    else:
                        pass

                else:
                    sizing_data_arrays_sorted.append(normalized_data_array)
                    print("No data found for this sizing method in the given start and end time.")
                    continue #skips to next sizing method

            # Initialize row counters and time boundaries
            time_low = math.floor(HHMMSS_2_SS(starttime))
            time_high = time_low + 1
            row_counter = start_time_difference  # Start from the calculated start time difference
            #print("Time low and high before adjust  -  ", time_low, time_high)            

            if flight_timezone_probe_mismatch_668 is True:
                if dataframes_probename[fileindex] == 'HVPS1':
                    time_low = math.floor(HHMMSS_2_SS(starttime))
                    time_low += 6*3600
                    time_high = time_low + 1
                    row_counter = start_time_difference  # Start from the calculated start time difference

            # Fill the initial rows of normalized_data_array with zeros until data starts
            normalized_data_array[:start_time_difference] = 0
            time_low += start_time_difference #these adjustments should make it so the time updates as well
            time_high += start_time_difference
            #print("Time low, time high, row counter  -  ", time_low, time_high, row_counter)
            #print("The high and low time and the row we're in before getting into sorting particles.")

            # Vectorize bins_mins and bins_maxs to avoid repetitive array indexing
            bins_mins_array = np.array(bins_mins)
            bins_maxs_array = np.array(bins_maxs)
            #print("Not sure what bins_mins and bins_maxs are, ", bins_mins_array, bins_maxs_array)

            # Process each particle
            for part_time, part_diam, part_rjct in zip(time_data, diam_data, reject_data):
                # Only process if the particle meets rejection criteria
                if flight_timezone_probe_mismatch_668 is True:
                    if dataframes_probename[fileindex] == 'HVPS1':
                        #print(part_time, time_low, time_high)
                        pass
                if part_rjct in rejection_flags_accept:
                    while part_time >= time_high:
                        row_counter += 1
                        if row_counter >= array_len:
                            break
                        time_low += 1
                        time_high += 1
        
                    # Bin the particle if within current time window
                    if time_low <= part_time < time_high:
                        in_bin = (bins_mins_array <= part_diam) & (part_diam < bins_maxs_array)
                        normalized_data_array[row_counter, in_bin] += 1
        
            # Append sorted array for this particle type
            sizing_data_arrays_sorted.append(normalized_data_array)
        
        counter += 1

    #Calculate averages across all sizing methods
    fake_total_counts = np.sum(sizing_data_arrays_sorted, axis=0)
    averages_normalized_array = fake_total_counts / len(sizing_data_arrays_sorted)

    #!!!---------------
    #before i average all the sizes to get a central conc. now i'm switching it
    #to xsize as the central conc, overwriting the average, but all the other
    #sizing methods still remain in the second returned variable so it
    #should still be usable for the sizing uncertainty
    #!!!---------------
    xsize_counts = sizing_data_arrays_sorted[1] #1 is the hardcoded location of xsize


    #put out sizing data arrays sorted so that the program can calculate 
    #the standard deviation later on
    return xsize_counts, sizing_data_arrays_sorted








#normalizing dataframes so that they all look the same
#-----------------------------------------------------
dataframes_normalized_original = []
dataframes_sizingmethod_counts = []
for counter in range(len(dataframes_list)):
    if dataframes_types[counter] == 2: #DISP case
        normalized_array = DISP_Counts_Normalize(data=dataframes_list[counter],
                                                 startindex=array_start_indices[counter], 
                                                 endindex=array_end_indices[counter],
                                                 bin_amount=dataframes_bin_midpoints[counter].shape[0])
        if normalized_array.shape[0] == 0:
            print('Likely there was an issue reading in DISP data')
        dataframes_normalized_original.append(normalized_array)
        dataframes_sizingmethod_counts.append(None)
    print(counter, 'counter before the organinzing pbp function')
    if dataframes_types[counter] == 4: #soda pbp
        #(data, startindex, endindex, bin_amount, bins_mins, bins_maxs, sizes_to_plot):
        if flight_timezone_probe_mismatch_668 is True:
            if dataframes_probename[counter] == 'HVPS1':
                temp_starttime = start_time_seconds[counter] + timeZone*3600
                temp_endtime   = end_time_seconds[counter] + timeZone*3600
                import time
                testing_time_use = time.time()
                normalized_array, each_sizing_method = SODA_PBP_Normalize_np(data=dataframes_list[counter],
                                                         startindex=array_start_indices[counter], 
                                                         endindex=array_end_indices[counter],
                                                         bin_amount=dataframes_bin_midpoints[counter].shape[0],
                                                         bins_mins=dataframes_bin_startpoints[counter],
                                                         bins_maxs=dataframes_bin_endpoints[counter],
                                                         sizes_to_plot=sizes_to_plot,
                                                         starttimesec=temp_starttime,
                                                         endtimesec=temp_starttime,
                                                         fileindex=counter)
            else:
                import time
                testing_time_use = time.time()
                normalized_array, each_sizing_method = SODA_PBP_Normalize_np(data=dataframes_list[counter],
                                                         startindex=array_start_indices[counter], 
                                                         endindex=array_end_indices[counter],
                                                         bin_amount=dataframes_bin_midpoints[counter].shape[0],
                                                         bins_mins=dataframes_bin_startpoints[counter],
                                                         bins_maxs=dataframes_bin_endpoints[counter],
                                                         sizes_to_plot=sizes_to_plot,
                                                         starttimesec=start_time_seconds[counter],
                                                         endtimesec=end_time_seconds[counter],
                                                         fileindex=counter)
        else:
            
            import time
            testing_time_use = time.time()
            normalized_array, each_sizing_method = SODA_PBP_Normalize_np(data=dataframes_list[counter],
                                                     startindex=array_start_indices[counter], 
                                                     endindex=array_end_indices[counter],
                                                     bin_amount=dataframes_bin_midpoints[counter].shape[0],
                                                     bins_mins=dataframes_bin_startpoints[counter],
                                                     bins_maxs=dataframes_bin_endpoints[counter],
                                                     sizes_to_plot=sizes_to_plot,
                                                     starttimesec=start_time_seconds[counter],
                                                     endtimesec=end_time_seconds[counter],
                                                     fileindex=counter)
        testing_time_use_end = time.time()
        elapsed_time = testing_time_use_end - testing_time_use
        print(f"Elapsed time: {elapsed_time} seconds")
        if list(normalized_array) == 0:
            print('Likely there was an issue sorting the pbp data data')
        dataframes_normalized_original.append(normalized_array)
        dataframes_sizingmethod_counts.append(each_sizing_method)


#print(dataframes_normalized_original[0], 'tttttttttttttesssssssssssssssssssst')





#the order of dataframes sizing methods counts is,
#['diam', 'xsize', 'xextent', 'ysize', 'areasize']

#dataframes_normalized original will include the 1D and 2D xsize data

#the mean is to be created

dataframes_normalized_mean = []
for x in range(len(dataframes_sizingmethod_counts)):
    if dataframes_sizingmethod_counts[x] == None:
        dataframes_normalized_mean.append(None)
    else:
        avg_counts = np.mean(dataframes_sizingmethod_counts[x], axis=0)

        dataframes_normalized_mean.append(avg_counts)







#---------------------------------------------------------------
#Saving a copy of the counts in 1 second hertz
#in order to do the sliding uncertainty
#no sliding but now just keeping copy just in case
#---------------------------------------------------------------
#[:] copies data where as just = variable refeerences the variable
dataframes_counts_1hz = dataframes_normalized_original[:]
#print(dataframes_counts_1hz[0])





#------------
#hertz update
#------------


#bruh why didn't i comment this better
#all comments are a year post creation :( now
def Adjust_Hertz2(data, hertz, desired_hertz):
    #uhhh with a time resolution of 10 this would be 10 / 1 since the data is 1 hz
    adjusted_res = int(desired_hertz / hertz)
    
    adjusted_dataframe = []
    num_seconds_per_bins = []
    sum_low = 0 #i believe these sum"" are indices. just weirdly named
    sum_max = adjusted_res #so then this would be 10.   sum low to max is then 0 to 10
    final_interval_amount = int(math.ceil(data.shape[0] / adjusted_res))
    for x in range(final_interval_amount):
        #adds the times to the adjusted damtaframe for the index range
        #it just sums them tho? no averaging?
        adjusted_dataframe.append(np.sum(data[sum_low:sum_max], axis=0))
        sum_low = sum_max #adjusting upwards, 
        sum_max += adjusted_res
    
    #checking if not enough seconds to fully fill final interval
    data_less = False
    if (data.shape[0] / adjusted_res) < final_interval_amount:
        data_less = True
    
    return np.array(adjusted_dataframe), num_seconds_per_bins






#checking the data for each file and making sure 
#the hertz matching the timeresolution specified
#----------------------------------------------
#filling it with false. if it becomes true then the final interval isn't full 
for x in range(len(dataframes_normalized_original)):
    dataframes_fullinterval.append(False)

for counter in range(len(dataframes_normalized_original)):
    #print('counter', counter)
    if int(dataframes_hertz[counter]) != int(TimeResolution):
        dataframes_normalized_original[counter], dataframes_fullinterval[counter] = \
            Adjust_Hertz2(data=dataframes_normalized_original[counter],
            hertz=int(dataframes_hertz[counter]),
            desired_hertz=int(TimeResolution))
            
        if dataframes_sizingmethod_counts[counter] != None:
            for eachmethod in range(len(dataframes_sizingmethod_counts[counter])):
                dataframes_sizingmethod_counts[counter][eachmethod], dumpvar = \
                    Adjust_Hertz2(data=dataframes_sizingmethod_counts[counter][eachmethod],
                    hertz=int(dataframes_hertz[counter]),
                    desired_hertz=int(TimeResolution))

        if dataframes_normalized_mean[counter] is not None:
            dataframes_normalized_mean[counter], dump = \
                Adjust_Hertz2(data=dataframes_normalized_mean[counter],
                hertz=int(dataframes_hertz[counter]),
                desired_hertz=int(TimeResolution))

            

#prepping a tas array for the hertz that soda was processed using
try:            
    TAS_hertz = data_hertz(TASfile['Time'])
    TAS_array_chunked, trash_var = Adjust_Hertz2(data=TAS_array, 
                                          hertz=int(TAS_hertz),
                                          desired_hertz=int(TimeResolution))
    #should be summed speeds which gets rid of the seconds
    #ok ok i think i figured it out. since we're doing 10s intervals, then 
    #we're doing 10 100m/s things. to get so its likek 10x10=100 counts/10seconds
    #and the tas it 100x10=1000 meters/10seconds so the 10 seconds cancel
    #or a better way to think of it is 1000m was traveled in those 10 seconds
    #so it's the sample volume times that 1000 m
    
    #TAS_array_chunked = TAS_array_chunked / (TimeResolution / TAS_hertz) 
    #it's likely theres an extra second of time at the end. that should be
    #fine i think it gets ignored but Im too lazy to run tests to see if I 
    #can remove it
except:
    print('could not calculate tas averages')


#-------------------------------------------------------
#
#Calculating concentration if any of the files are counts
#
#-------------------------------------------------------

def resize_reshape_array(data, row_length, column_height):
    #honestly not sure anymore but I think it resizes a single number to a x by y array
    data = np.tile(data, row_length)
    data = data.reshape(row_length, column_height).T
    return data


#!!!!!!!!!!!!!!! assumes bins from file were read in as micrometer
#Also saving conc as 1hz data as well for the sliding uncertainty.
dataframes_normalized_conc = []
dataframes_sizingmethod_conc = []
dataframes_mean_conc = []
dataframes_conc_1hz = []
for counter in range(len(dataframes_normalized_original)):
    corr_fac = 1 #!!!!!
    activetime = 5 #!!!!!
    

    if dataframes_types[counter] == 2 or dataframes_types[counter] == 4: #Disp case and pbp case
        #print(dataframes_normalized_original[counter].shape, dataframes_binsize[counter].shape, TAS_array_extended)#TAS_array_chunked[:, np.newaxis].shape)
        range_tas_use = dataframes_normalized_original[counter].shape[0]
        print(len(dataframes_normalized_original[counter]))
        TAS_array_extended = resize_reshape_array(TAS_array_chunked[0:range_tas_use],\
                                                  dataframes_normalized_original[counter].shape[1],\
                                                  dataframes_normalized_original[counter].shape[0])
        #print(range_tas_use, TAS_array_extended, 'ooping the tassf dsafa')
        #print(TAS_array_extended)
        #area to use should be all in for the hail and hvps now
        if dataframes_probename[counter] == 'HAIL-1D': 
            if use_all_in == True:
                #plus 1 accounts for sepaartion from edge
                area_to_use = diode_size_SPEC * length_SPEC_u * \
                             (diodes_1DSPEC - np.ceil(dataframes_bin_midpoints[counter].astype(int) / (diode_size_SPEC * 1000000)) -1)
            elif use_all_in == False:
                area_to_use = Area_1DSPEC
        if dataframes_probename[counter] == 'HAIL-2D':   
            if use_all_in == True:
                if use_all_in == True:
                    area_to_use = diode_size_SPEC * length_SPEC_u * \
                                 (diodes_2DSPEC - np.ceil(dataframes_bin_midpoints[counter] / (diode_size_SPEC * 1000000)) -1)
            elif use_all_in == False:
                area_to_use = Area_2DSPEC
        if dataframes_probename[counter] == 'HVPS1':
            if use_all_in == True:
                if use_all_in == True:
                    area_to_use = diode_size_HVPS * length_HVPS * \
                                 (diodes_HVPS - np.ceil(dataframes_bin_midpoints[counter] / (diode_size_HVPS * 1000000)) -1)
            elif use_all_in == False:
                area_to_use = Area_HVPS
        if dataframes_probename[counter] == '2DC':
            if use_all_in == True:
                pass #too lazy to develop atm
            elif use_all_in == False:
                area_to_use = Area_2DC
        #print(TAS_array_extended)
        calc_conc = dataframes_normalized_original[counter] / area_to_use / \
                    TAS_array_extended / (dataframes_binsize[counter]/1000000)                            #!!! not sure if this is best way to get surface area :| ...
                    #TAS_array_chunked[:, np.newaxis]
                    #np.newaxis seperates it from a continous array [x,x,x,x]
                    #into [x],[x],[x],[x],[x]
        dataframes_normalized_conc.append(calc_conc)
    
        if dataframes_sizingmethod_counts[counter] is not None: #if pbp case and not disp case
            allmethods_onefile = []
            for eachmethod in range(len(dataframes_sizingmethod_counts[counter])):
                eachmethod_conc = dataframes_sizingmethod_counts[counter][eachmethod] / area_to_use / \
                             TAS_array_extended / (dataframes_binsize[counter]/1000000)
                allmethods_onefile.append(eachmethod_conc)
            dataframes_sizingmethod_conc.append(allmethods_onefile)
            
            mean_conc = dataframes_normalized_mean[counter] / area_to_use / \
                        TAS_array_extended / (dataframes_binsize[counter]/1000000)  
            dataframes_mean_conc.append(mean_conc)
        else:
            dataframes_sizingmethod_conc.append(None)
            dataframes_mean_conc.append(None)
    
        #calculating the one second concentration
        #revamping calculation with list comprehension. im scared
        #but it saves me from having to reshape the tas array
        calc_1hz_conc = [dataframes_counts_1hz[counter][tas[0]] / tas[1] for tas in enumerate(TAS_array[0:-2])] \
                        / area_to_use / (dataframes_binsize[counter]/1000000) / TimeResolution
                        #divide by timeresolution to normalize to per second idk where i did it up 
                        #above but i must of done it somewhere
        dataframes_conc_1hz.append(calc_1hz_conc)

    else: #for all cases that are already conc
        dataframes_normalized_conc.append(dataframes_normalized_original[counter])
    #print(TAS_array_extended.shape)





#------------------------------------------------------------------------
#Calculating count uncertainty and calculating conc uncertainty from that
#Uses the formula    counts / sqrt(counts)   which is basically SNR

#move count uncertainty before the conc calc so that it can just be included with it
#------------------------------------------------------------------------





dataframes_count_uncertainty = [] #should be poisson
dataframes_sizingmethod_count_std = [] #this is not used anywhere but im scared to take it out
dataframes_mean_poisson = []
dataframes_sizemethod_poisson = []
for counter in range(len(dataframes_normalized_original)):
    #No SODA case since the SODA method is already in concentration. Don't get
    #counts from it.
            
    if dataframes_types[counter] == 2 or dataframes_types[counter] == 4: #DISP case or pbp soda case
        uncertainty_values = dataframes_normalized_original[counter] / \
                             np.sqrt(dataframes_normalized_original[counter])
        dataframes_count_uncertainty.append(uncertainty_values)
        
        if dataframes_sizingmethod_counts[counter] != None: #if pbp case and not disp case
            sizingmethods_count_stddev = np.std(dataframes_sizingmethod_counts[counter], axis=0)
            dataframes_sizingmethod_count_std.append(sizingmethods_count_stddev)
            
            sizemethod_uncert = np.sqrt(dataframes_sizingmethod_counts[counter])
            dataframes_sizemethod_poisson.append(sizemethod_uncert)
            
            uncert_mean = np.sqrt(dataframes_normalized_mean[counter])
            dataframes_mean_poisson.append(uncert_mean)
        else:
            dataframes_sizingmethod_count_std.append(None)
            dataframes_mean_poisson.append(None)
            dataframes_sizemethod_poisson.append(None)


dataframes_conc_uncertainty = []

dataframes_meanconc_uncertainty = []
dataframes_sizemethod_poisson_uncertainty = [] 

dataframes_conc_lower_uncertainty = [] #ends up not being used now
dataframes_conc_upper_uncertainty = [] #ends up not being used now
dataframes_conc_stddev = [] #this ends up getting re done down below
sizingmethod_concs_reorganized = [] #is used below to calculate the std dev
dataframes_conc_totallower_uncertainty = [] #ends up not being used now
dataframes_conc_totalupper_uncertainty = [] #ends up not being used now
for counter in range(len(dataframes_normalized_original)):
    #No SODA case since the SODA method is already in concentration. Don't get
    #counts from it.
           
    if dataframes_probename[counter] == 'HAIL-1D': 
        if use_all_in == True:
            area_to_use = diode_size_SPEC * length_SPEC_u * \
                         (diodes_1DSPEC - np.ceil(dataframes_bin_midpoints[counter].astype(int) / (diode_size_SPEC * 1000000)) -1)
        elif use_all_in == False:
            area_to_use = Area_1DSPEC
    if dataframes_probename[counter] == 'HAIL-2D':   
        if use_all_in == True:
            if use_all_in == True:
                area_to_use = diode_size_SPEC * length_SPEC_u * \
                             (diodes_2DSPEC - np.ceil(dataframes_bin_midpoints[counter] / (diode_size_SPEC * 1000000)) -1)
        elif use_all_in == False:
            area_to_use = Area_2DSPEC
    if dataframes_probename[counter] == 'HVPS1':
        if use_all_in == True:
            if use_all_in == True:
                area_to_use = diode_size_HVPS * length_HVPS * \
                             (diodes_HVPS - np.ceil(dataframes_bin_midpoints[counter] / (diode_size_HVPS * 1000000)) -1)
        elif use_all_in == False:
            area_to_use = Area_HVPS
    if dataframes_probename[counter] == '2DC':
        if use_all_in == True:
            pass #too lazy to develop atm
        elif use_all_in == False:
            area_to_use = Area_2DC
    
    if dataframes_types[counter] == 2 or dataframes_types[counter] == 4: #DISP case and pbp soda case
        range_tas_use = dataframes_normalized_original[counter].shape[0]
        TAS_array_extended = resize_reshape_array(TAS_array_chunked[0:range_tas_use],\
                                                  dataframes_normalized_original[counter].shape[1],\
                                                  dataframes_normalized_original[counter].shape[0])
        conc_uncertainty = dataframes_count_uncertainty[counter] / \
                            area_to_use / \
                            (dataframes_binsize[counter]/ 1000000) / \
                            TAS_array_extended#TAS_array_chunked[:, np.newaxis])

        conc_uncertainty = np.nan_to_num(conc_uncertainty, nan=0)
        dataframes_conc_uncertainty.append(conc_uncertainty)
        
        upper_uncertainty = dataframes_normalized_conc[counter] + conc_uncertainty
        lower_uncertainty = dataframes_normalized_conc[counter] - conc_uncertainty
        dataframes_conc_upper_uncertainty.append(upper_uncertainty)
        dataframes_conc_lower_uncertainty.append(lower_uncertainty)     
        
        if dataframes_sizingmethod_counts[counter] != None: #if pbp case and not disp case
            #getting std dev of the sizing method concentrations
            sizingmethod_stddev = np.std(dataframes_sizingmethod_conc[counter][0], axis=0)
            totallower_uncertainty = lower_uncertainty - sizingmethod_stddev
            totalupper_uncertainty = upper_uncertainty + sizingmethod_stddev
            #the above doens't get used anymore i believe
            
            
            #need to reorganize how the data is structured in order to perform
            #np.std on the the array. otherwise it does it for all the times
            #and not for all the sizing methods it's weird and idk how to
            #explain it but the std before was wildy off so this is needed
            
            #first getting the sizes/shapes of each array
            databins  = dataframes_sizingmethod_conc[counter][0].shape[1]
            datatime  = dataframes_sizingmethod_conc[counter][0].shape[0]
            datasizes = len(dataframes_sizingmethod_conc[counter])
            
            #initialzing the new  3d array to store the data
            reorganized_concs = np.zeros((datatime, datasizes, databins))
            for m in range(len(dataframes_sizingmethod_conc[counter])):
                #for method (m)
                for t in range(dataframes_sizingmethod_conc[counter][m].shape[0]):
                    #for time interval (t)
                    reorganized_concs[t, m] = dataframes_sizingmethod_conc[counter][m][t]
            sizingmethod_concs_reorganized.append(reorganized_concs)
            
            
            #adding to data arrays to plot
            dataframes_conc_stddev.append(sizingmethod_stddev)
            dataframes_conc_totallower_uncertainty.append(totallower_uncertainty)
            dataframes_conc_totalupper_uncertainty.append(totalupper_uncertainty)
            
            sm_uncerts_all = []
            for s in range(len(dataframes_sizemethod_poisson[counter])):
                smconc_uncert = dataframes_sizemethod_poisson[counter][s] / \
                            area_to_use / (dataframes_binsize[counter]/ 1000000) / \
                            TAS_array_extended#TAS_array_chunked[:, np.newaxis])
                smconc_uncert = np.nan_to_num(smconc_uncert, nan=0)
                sm_uncerts_all.append(smconc_uncert)
                
            dataframes_sizemethod_poisson_uncertainty.append(sm_uncerts_all)
            
            meanconc_uncert = dataframes_mean_poisson[counter] / \
                                area_to_use / \
                                (dataframes_binsize[counter]/ 1000000) / \
                                TAS_array_extended#TAS_array_chunked[:, np.newaxis])
            meanconc_uncert = np.nan_to_num(meanconc_uncert, nan=0)
            dataframes_meanconc_uncertainty.append(meanconc_uncert)
            
            
        else:
            #just making the same as the the poisson uncertainty for plotting
            array_x, array_y = dataframes_normalized_original[counter].shape
            empty_array = np.empty((array_x, array_y))
            empty_array[:] = np.nan
            empty_array = np.zeros((array_x, array_y), dtype=int)
            dataframes_conc_stddev.append(empty_array)
            dataframes_conc_totallower_uncertainty.append(upper_uncertainty)
            dataframes_conc_totalupper_uncertainty.append(lower_uncertainty)
            sizingmethod_concs_reorganized.append(None)
            dataframes_meanconc_uncertainty.append(None)
            dataframes_sizemethod_poisson_uncertainty.append(None)

    else:
        array_x, array_y = dataframes_normalized_original[counter].shape
        empty_array = np.empty((array_x, array_y))
        empty_array[:] = np.nan
        empty_array = np.zeros((array_x, array_y), dtype=int)
        dataframes_conc_uncertainty.append(empty_array)
        dataframes_conc_upper_uncertainty.append(empty_array)
        dataframes_conc_lower_uncertainty.append(empty_array)  
        #!!!NEED TO MAKE A CASE THAT JUST MAKES AN EMPTRY ARRAY OF NANS THE SIZE OF IT



#sizing method uncertainty is now the total possible range
#rather than the standard deviation which is commented out above.
#upper and lower are total values, not plus or minus values
dataframes_conc_sizinguncert_upper = []
dataframes_conc_sizinguncert_lower = []

#now the plus and minus per bin per interval per probe
dataframes_conc_sizinguncert_plus  = []
dataframes_conc_sizinguncert_minus = []

#now the total range which is used later for selecting which sizing method to use
dataframes_conc_sizinguncert_range = []

for probe in range(len(dataframes_normalized_original)):
    if dataframes_types[[probe]] == 4: #if pbp case and not disp case
        #getting sizing method total tangeof the concentration
        sizingmethod_upper = []
        sizingmethod_lower = []
        sizingmethod_plus  = []
        sizingmethod_minus = []
        sizingmethod_range = []
        for interval in range(sizingmethod_concs_reorganized[probe].shape[0]):
            #get min and max values per bin
            max_values = np.max(sizingmethod_concs_reorganized[probe][interval], axis=0)
            min_values = np.min(sizingmethod_concs_reorganized[probe][interval], axis=0)

            #get plus/minus values
            #was xsize conc. switched to mean. hopefully that fixes this weirdness
            plus  = max_values - dataframes_mean_conc[probe][interval] #dataframes_normalized_conc[probe][interval]
            minus = dataframes_mean_conc[probe][interval] - min_values #dataframes_normalized_conc[probe][interval] - min_values
            
            #get total range
            range_uncert = max_values - min_values
            
            sizingmethod_upper.append(max_values)
            sizingmethod_lower.append(min_values)
            sizingmethod_plus.append(plus)
            sizingmethod_minus.append(minus)
            sizingmethod_range.append(range_uncert)
        
        dataframes_conc_sizinguncert_upper.append(sizingmethod_upper)
        dataframes_conc_sizinguncert_lower.append(sizingmethod_lower)
        dataframes_conc_sizinguncert_plus.append(sizingmethod_plus)
        dataframes_conc_sizinguncert_minus.append(sizingmethod_minus)
        dataframes_conc_sizinguncert_range.append(sizingmethod_range)
        
        
    elif dataframes_types[probe] == 2: #disp case
        print('uhhhhhhhhhhohhhhhhhhhhhhhhh')
        #lmfao idk why uhoh was included but its funny so im leaving it
        array_x, array_y = dataframes_normalized_original[counter].shape
        empty_array = np.empty((array_x, array_y))
        empty_array[:] = np.nan
        empty_array = np.zeros((array_x, array_y), dtype=int)
        
        #1d gets same conc values as data since we can use sizng method on it
        dataframes_conc_sizinguncert_upper.append(dataframes_normalized_conc[probe])
        dataframes_conc_sizinguncert_lower.append(dataframes_normalized_conc[probe])
        
        #plus, minus, and range are all 0 or nan
        dataframes_conc_sizinguncert_plus.append(empty_array)
        dataframes_conc_sizinguncert_minus.append(empty_array)
        dataframes_conc_sizinguncert_range.append(empty_array)


#need to make sure no uncertainties go below 0
for counter in range(len(dataframes_normalized_original)):
    dataframes_conc_lower_uncertainty[counter][dataframes_conc_lower_uncertainty[counter]<1] = 0
    dataframes_conc_totallower_uncertainty[counter][dataframes_conc_totallower_uncertainty[counter]<1] = 0
       
    
    
    
#-------------------------------------------
#The newest and shiniest uncertainty yayyyyy
#10 second sliding uncertainty
#-------------------------------------------    

#First calculate 10 second concentrations, then orient self to the center
#10 second interval, can likely use dataframes_normalized_concs
#then figure out which of the surrounding 10 (+/-) 5 10 second intervals
#has the highest spread for each of the bins.

#First, get all 1hz 10s intervals
#because the 1hz conc is calculated separate from 10s conc, the values are slightly
#different, up to 1 it seems, but only when there are counts. likely due to
#higher res tas vs tas averaging.
#I beleive this is for every single 1hz spot and does not exclude the middle
dataframes_10s_sliding_conc = []
#s stands for sliding, p stands for probe
for p in range(len(dataframes_conc_1hz)):
    probe_10s_concs = []
    for s in range(len(dataframes_conc_1hz[p])):
        try:
            tensec_conc = np.sum(dataframes_conc_1hz[p][s:s+TimeResolution], axis=0)
            probe_10s_concs.append(tensec_conc)
        except:
            print("Reached end of final normal 10s period?")
    dataframes_10s_sliding_conc.append(probe_10s_concs)
 


#Remaking the sliding window groups with and without center
#Going to include the first and last main intervals as arrays of 0's or nan's
#Including the first and last will allow for all the arrays to be the same 
#otherwise it's a pain to deal with
#!!!!!!!!!!!!!!!!!assumes 10 second window/resolution!!!!! can't divide 5 nicely by 2
#------------------
total_specified_intervals = len(dataframes_normalized_conc[0])
#specified index is the center 10s interval that is normal
specified_index = 10 * np.arange(0,total_specified_intervals)  
sliding_groups = []
sliding_groups_withcenter = []
for p in range(len(dataframes_normalized_conc)):
    temp_sliding_groups         = [] #each probe
    temp_sliding_groups_wcenter = [] #each probe
    for idx, i in enumerate(specified_index):
        #these are positionings for the 1Hz conc's
        adjust_updown = np.ceil(TimeResolution/2).astype(np.int32)
        low_index     = -TimeResolution + adjust_updown
        high_index    =  TimeResolution - adjust_updown +1 #+1 for python indexing
        
        group_intervals         = []
        group_intervals_wcenter = []
        
        #start of flight
        if i == 0:
            #first 5 intervals. Filler intervals since they don't exist
            for s in range(adjust_updown):
                group_intervals.append(dataframes_normalized_conc[p][idx])
                group_intervals_wcenter.append(dataframes_normalized_conc[p][idx])
        
            #middle
            group_intervals_wcenter.append(dataframes_normalized_conc[p][idx])
            
            #last 5 intervals
            #i+1 skips the 1st interval which is technically the middle conc here
            for s in range(i+1, i+high_index):
                #print('start', s)
                group_intervals.append(dataframes_10s_sliding_conc[p][s])
                group_intervals_wcenter.append(dataframes_10s_sliding_conc[p][s])
            
        #end of flight    
        elif i == specified_index[-1]:
            #first 5 intervals. Filler intervals since they don't exist
            for s in range(i+low_index, i):
                #print('end', s)
                group_intervals.append(dataframes_10s_sliding_conc[p][s])
                group_intervals_wcenter.append(dataframes_10s_sliding_conc[p][s])
        
            #middle
            group_intervals_wcenter.append(dataframes_normalized_conc[p][idx])
            
            #last 5 intervals
            for s in range(adjust_updown):
                group_intervals.append(dataframes_normalized_conc[p][idx])
                group_intervals_wcenter.append(dataframes_normalized_conc[p][idx])
              
                
        #now to do all the normal, non edge cases
        else:
            for s in range(i+low_index, i+high_index):
                #without center
                #these are all the surrounding/non-main intervals
                if s not in specified_index:
                    group_intervals.append(dataframes_10s_sliding_conc[p][s])    
                    group_intervals_wcenter.append(dataframes_10s_sliding_conc[p][s])
                elif s in specified_index:
                    #this is the index of the middle intervals
                    group_intervals_wcenter.append(dataframes_10s_sliding_conc[p][s])

        temp_sliding_groups.append(group_intervals)
        temp_sliding_groups_wcenter.append(group_intervals_wcenter)
    sliding_groups.append(temp_sliding_groups)
    sliding_groups_withcenter.append(temp_sliding_groups_wcenter)

    
#calculate uncertainty from the groups. I'm doing average. Dave just 
#recommended the biggest spread. Idk, this should be easily adjustable
#so whatev. Im pretty sure i use largest sandn smallest possibilty now
#including center in case center is the min or max
dataframes_sliding_uncertainty = []
dataframes_mean_sliding_uncert = []
dataframes_sliding_uncertainty_upper = []
dataframes_sliding_uncertainty_lower = []
for p in range(len(dataframes_normalized_conc)): #each probe
    probe_uncertainty     = []
    probe_uncertainty_avg = []
    probe_uncert_upper    = []
    probe_uncert_lower    = []
    for t in range(len(dataframes_normalized_conc[p])): #each time interval
        #first, need to add uncertainty of np.nan for first and last interval
        #so that the data is filled out but nan
        if t == 0 or t == len(dataframes_normalized_conc[p])-1:
            #this is adding 14 bin or whatever nans 
            edge_intervals = np.zeros(len(dataframes_bin_startpoints[p]))
            edge_intervals[:] = np.nan
            combo_uncert = np.stack((edge_intervals, edge_intervals), axis=1)
            probe_uncertainty.append(combo_uncert)
            
            #filling with data values rather than nan since it won't give 
            #a real uncertainty
            probe_uncert_upper.append(dataframes_normalized_conc[p][t])
            probe_uncert_lower.append(dataframes_normalized_conc[p][t])
        #average high and low compared to the specified interaval
        else:
            specified_value = dataframes_normalized_conc[p][t]
            #need to find which values are higher and which are lower
            #getting true and false masks
            #t-1 aligns with t because sliding_groups skips the first index
            higher_values_m   = specified_value <= sliding_groups_withcenter[p][t-1]
            lower_values_m    = specified_value >= sliding_groups_withcenter[p][t-1]
            #can replace nan with 0 if desired
            higher_values     = np.where(higher_values_m, \
                                         np.array(sliding_groups_withcenter[p][t-1]), np.nan)  #t-2??
            lower_values      = np.where(lower_values_m, \
                                         np.array(sliding_groups_withcenter[p][t-1]), np.nan)  #t-2??
            #retrievig the max and lowest for each bin
            max_uncert = np.nanmax(higher_values, axis=0)
            max_uncert = np.maximum(max_uncert, specified_value)
            #ensure no silliness from tas making it slightly less
            min_uncert = np.nanmin(lower_values, axis=0)
            #combining into groups for each bin
            combo_uncert = np.stack((min_uncert, max_uncert), axis=-1)
            probe_uncertainty.append(combo_uncert)
            
            if t==29:
                #print('higher', higher_values, '\n\n', 'lower', lower_values)
                test1= np.nan_to_num(higher_values, nan=0, posinf=0, neginf=0)
                test2= np.nan_to_num(sliding_groups_withcenter[p][t-1], nan=0, posinf=0, neginf=0)
                test3= np.nan_to_num(higher_values_m, nan=0, posinf=0, neginf=0)
                test4= np.nan_to_num(lower_values_m, nan=0, posinf=0, neginf=0)
                test5= np.nan_to_num(lower_values, nan=0, posinf=0, neginf=0)
                test6= specified_value
                test7= max_uncert
                test8= min_uncert
                #print(test1 - test2)
            
            #getting the mean uncertainty per bin
            #does not include the zeros/nan's.... that might be an issue
            #can change nan's to zero somewhere? at least for the lower
            #for upper fill with the normal concentration? nah that is wrong cause then it's just forcing the center on everything else
            upper_avg_uncert = np.nanmean(higher_values, axis=0)
            lower_avg_uncert = np.nanmean(lower_values, axis=0)
            range_avg_uncert = upper_avg_uncert + lower_avg_uncert
            
            probe_uncertainty_avg.append([lower_avg_uncert, upper_avg_uncert, range_avg_uncert])
            
            zeros_max_uncert = np.nan_to_num(max_uncert, nan=0, posinf=0, neginf=0)
            zeros_min_uncert = np.nan_to_num(min_uncert, nan=0, posinf=0, neginf=0)
            probe_uncert_upper.append(zeros_max_uncert)
            probe_uncert_lower.append(zeros_min_uncert)
            
            
    dataframes_sliding_uncertainty.append(probe_uncertainty)
    dataframes_mean_sliding_uncert.append(probe_uncertainty_avg)    
    dataframes_sliding_uncertainty_upper.append(probe_uncert_upper)
    dataframes_sliding_uncertainty_lower.append(probe_uncert_lower)
    




#Redoing since i redid the other thing so index;s have hcnaged
#calculate uncertainty from the groups. I'm doing average. Dave just 
#recommended the biggest spread. Idk, this should be easily adjustable
#so whatev. Im pretty sure i use largest sandn smallest possibilty now
#including center in case center is the min or max
dataframes_sliding_uncertainty = []
dataframes_mean_sliding_uncert = []
dataframes_sliding_uncertainty_upper = []
dataframes_sliding_uncertainty_lower = []
for p in range(len(dataframes_normalized_conc)): #each probe
    probe_uncertainty     = []
    probe_uncertainty_avg = []
    probe_uncert_upper    = []
    probe_uncert_lower    = []
    for t in range(len(dataframes_normalized_conc[p])): #each time interval
        #first identify the concentration values of the primary 10s interval
        primary_concs= dataframes_normalized_conc[p][t]
        
        #now need to find all the higher and lower values in order to 
        #identify what the maximum and minimum possible value were
        #this is done across all 1hz intervals rather than per 1hz intervals
        #I believe the reasoning for this is that the uncertainty represesnts
        #what could have been observed, so it's possible it could have
        #observed any of the larger or lower values
        #----
        #Only doing this with the groups that have the center
        #That should ensure upper and lower errors are at the
        #very least the same as the main concentration
        highest_values = np.max(sliding_groups_withcenter[p][t], axis=0)
        lowest_values  = np.min(sliding_groups_withcenter[p][t], axis=0)
        
        """
        old stuff
        
        #combining into groups for each bin
        #this is an old method
        combo_uncert = np.stack((min_uncert, max_uncert), axis=-1)
        probe_uncertainty.append(combo_uncert)
        
    
        #getting the mean uncertainty per bin
        #does not include the zeros/nan's.... that might be an issue
        #can change nan's to zero somewhere? at least for the lower
        #for upper fill with the normal concentration? nah that is wrong cause then it's just forcing the center on everything else
        upper_avg_uncert = np.nanmean(higher_values, axis=0)
        lower_avg_uncert = np.nanmean(lower_values, axis=0)
        range_avg_uncert = upper_avg_uncert + lower_avg_uncert
        
        probe_uncertainty_avg.append([lower_avg_uncert, upper_avg_uncert, range_avg_uncert])
        
        zeros_max_uncert = np.nan_to_num(max_uncert, nan=0, posinf=0, neginf=0)
        zeros_min_uncert = np.nan_to_num(min_uncert, nan=0, posinf=0, neginf=0)
        """
        
        #just a little bit of quality assurance
        zeros_max_uncert = np.nan_to_num(highest_values, nan=0, posinf=0, neginf=0)
        zeros_min_uncert = np.nan_to_num(lowest_values, nan=0, posinf=0, neginf=0)
        
        probe_uncert_upper.append(zeros_max_uncert)
        probe_uncert_lower.append(zeros_min_uncert)
            
            
    dataframes_sliding_uncertainty.append(probe_uncertainty)
    dataframes_mean_sliding_uncert.append(probe_uncertainty_avg)    
    dataframes_sliding_uncertainty_upper.append(probe_uncert_upper)
    dataframes_sliding_uncertainty_lower.append(probe_uncert_lower)
    
    
    

#For if the picked uncertainty type desired is just the greatest of the three.
#getting range of uncertainty for the sliding uncertatinties since it's just min and max
sliding_total_uncerts  = []
sliding_total_uncerts2 = []

for p in range(len(dataframes_normalized_conc)): #each probe
    total_uncert  = []
    total_uncert2 = []
    for t in range(len(dataframes_sliding_uncertainty_upper[p])): #each 10s interval
        #print('uhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh')
        #bin_uncert  = []
        bin_uncert2 = []
        #for b in range(len(dataframes_sliding_uncertainty [p][t])): #each bin
        #    upper = dataframes_sliding_uncertainty[p][t][b][1]
        #    lower = dataframes_sliding_uncertainty[p][t][b][0]
        #    total_difference = upper - lower
        
        #    bin_uncert.append(total_difference)
            
        upper2 = dataframes_sliding_uncertainty_upper[p][t]
        lower2 = dataframes_sliding_uncertainty_lower[p][t]
        total_difference2 = upper2 - lower2    
        
        #print(dataframes_sliding_uncertainty_upper[p][t] - dataframes_sliding_uncertainty_lower[p][t])
        #print(total_difference2, '\n')

        
        #total_uncert.append(bin_uncert)
        total_uncert2.append(total_difference2)
    sliding_total_uncerts.append(total_uncert)
    sliding_total_uncerts2.append(total_uncert2)
    





#Now getting the biggest range of uncertainty
#Notes/list on all the things that will be used counts/conc/uncertinty

#Counts,
#   dataframes_normalized_original  |  is the 1D counts and 2D xsize counts
#   dataframes_sizingmethod_counts  |  is the counts for each sizing method from
#                                   |   SODA in this order ['diam', 'xsize', 'xextent', 'ysize', 'areasize']
#   dataframes_normalized_mean      |  is the mean counts of the 5 sizing methods
#
#Count uncertainty,
#   dataframes_count_uncertainty   |  is the count poisson uncertainty
#   dataframes_mean_poisson        |      for the mean of the 5 size methods
#   dataframes_sizemethod_poisson  |      for the 5 2D size methods
#
#
#Concentration,
#   dataframes_normalized_conc     |  concentration for xsize and 1D
#   dataframes_sizingmethod_conc   |    for all 5 size methods 2D
#   dataframes_mean_conc           |    for mean of those 5 size methods
#
#
#
#Concentration uncertainty
#   dataframes_conc_uncertainty                |  is the count uncertainty
#   dataframes_meanconc_uncertainty            |  propogated through the 
#   dataframes_sizemethod_poisson_uncertainty  |  concentration calculation
#
#
#   dataframes_conc_sizinguncert_upper    |  these are the actual min and
#   dataframes_conc_sizinguncert_lower    |  max range of values across the
#   dataframes_conc_sizinguncert_plus     |  sizing methods which is different
#   dataframes_conc_sizinguncert_minus    |  than a poisson uncertainty and is
#   dataframes_conc_sizinguncert_range    |  only intended to be used with the mean
#
#
#Biggest uncertainty stuff
#    all_lower_uncertainty = []
#    all_upper_uncertainty = []
#    uncertainty_type      = []
#    
#    all_lower_plusminus   = []
#    all_upper_plusminus   = []

#setting up uncertianty for easch uncertainty method for later plotting
#and reflectivity calculations. Just more data that's readily available 
#for use this way that will be read out into the netcdf file later
#also used when doing the biggest uncertainty

#these are true values, not the plus or minus values
try:
    spatial_upper = []
    spatial_lower = []
    poisson_upper = []
    poisson_lower = []
    sizing_upper  = []
    sizing_lower  = []
    for p in range(len(dataframes_normalized_conc)): #each probe
        
        #adding or subtracting to get the value rather than the plus or minus
        #middle_concs = np.array(dataframes_normalized_conc[p][:])

        if dataframes_probename[p] == 'HAIL-1D':
            middle_concs = np.array(dataframes_normalized_conc[p][:])
        elif dataframes_probename[p] == 'HAIL-2D':
            middle_concs = np.array(dataframes_mean_conc[p][:])
    
        ## Get the second column (index 1) from each array in the list
        #from chatgpt to get the first and second oclumns isolated.
        #the way i set it up was really stupid but I don't want to change the
        #data structure and everything that uses it, so here's a fix for this section
        
        #first_columns  = np.array([arr[:, 0] for arr in dataframes_sliding_uncertainty[p]])
        #second_columns = np.array([arr[:, 1] for arr in dataframes_sliding_uncertainty[p]])
        
        
        #spatial - already the highest and lowest value in 11 second window
        #spatial_u = second_columns #dataframes_sliding_uncertainty[p][:][:][1]
        #spatial_l = first_columns #dataframes_sliding_uncertainty[p][:][:][0]
        
        # the two spatial below are the og's which are good to go but have
        #been commented out since we're not using the spatial uncertainty anymore
        #spatial_u = np.array(dataframes_sliding_uncertainty_upper[p])
        #spatial_l = np.array(dataframes_sliding_uncertainty_lower[p])
        #spatial_u = dataframes_normalized_conc[p]#np.zeros(dataframes_normalized_conc[p].shape)
        #spatial_l = dataframes_normalized_conc[p]#np.zeros(dataframes_normalized_conc[p].shape)
        spatial_u = middle_concs
        spatial_l = middle_concs #not using this anymore
        
        #poisson
        #poisson_u = middle_concs + np.array(dataframes_conc_uncertainty[p])
        #poisson_l = middle_concs - np.array(dataframes_conc_uncertainty[p])
        if dataframes_probename[p] == 'HAIL-1D':                        
            poisson_u = middle_concs + np.array(dataframes_conc_uncertainty[p])
            poisson_l = middle_concs - np.array(dataframes_conc_uncertainty[p])
        elif dataframes_probename[p] == 'HAIL-2D':
            poisson_u = middle_concs + np.array(dataframes_meanconc_uncertainty[p])
            poisson_l = middle_concs - np.array(dataframes_meanconc_uncertainty[p])
        
        print('here upper loop?')
        #sizing
        #sizing_u = middle_concs + np.array(dataframes_conc_stddev_v2[p])
        #sizing_l = middle_concs - np.array(dataframes_conc_stddev_v2[p])
        if dataframes_types[p] == 4: #pbp
            sizing_u = np.array(dataframes_conc_sizinguncert_upper[p])
            sizing_l = np.array(dataframes_conc_sizinguncert_lower[p])
        elif dataframes_types[p] == 2: #disp
            #sizing_u = np.array(dataframes_conc_sizinguncert_upper[p])
            #sizing_l = np.array(dataframes_conc_sizinguncert_lower[p])
            sizing_u = middle_concs
            sizing_l = middle_concs
        
        
        #making sure nothing is below 0
        spatial_u[spatial_u[:] < 0] =  0
        spatial_l[spatial_l[:] < 0] =  0 
        poisson_u[poisson_u[:] < 0] =  0 
        poisson_l[poisson_l[:] < 0] =  0 
        sizing_u[sizing_u[:] < 0] =  0
        sizing_l[sizing_l[:] < 0] =  0
        
        spatial_upper.append(np.round(spatial_u, 4))
        spatial_lower.append(np.round(spatial_l, 4))
        poisson_upper.append(np.round(poisson_u, 4))
        poisson_lower.append(np.round(poisson_l, 4))
        sizing_upper.append(np.round(sizing_u, 4))
        sizing_lower.append(np.round(sizing_l, 4))
    
    
    
    
    
    
    

    #UPDATED TO USE THE
    #MEAN SIZE RATHER
    #THAN THE XSIZE SINCE
    #THIS IS JUST USED
    #FOR THE MEAN IN 
    #THIS VERSION OF
    #THE CALCULATION
    
    
    #lower and upper uncertainty are the concentration with the uncertainty added
    #or subtracted already. so they're not +/- values but rather the final concentration
    #upper and lower range. This is nice for calculating reflectivity and shows
    #the upper and lower range via text
    #the plusminus is the plus and minus values for the plot since matplotlib is +- 
    #rather than the upper and lower true value. hopefully this all makes sense
        
    #sliding_total_uncerts          3     is total uncertainty      spatial
    #dataframes_conc_uncertainty    1     is +/- uncertainty        poisson        
    #dataframes_conc_stddev         2     is +/- uncert too         sizing
    all_lower_uncertainty = []
    all_upper_uncertainty = []
    uncertainty_type      = []
    
    all_lower_plusminus   = []
    all_upper_plusminus   = []
    
    for p in range(len(dataframes_mean_conc)): #each probe
        
        #masking for which total uncertainty is the greatest
        #can use location data to determine value to use and yeah which method
        #multiply by 2 since poisson and **no->sizing ranges are +/-
        #spatial_uncert = np.array(sliding_total_uncerts[p][:])
        
        #spatial_uncert = np.array(sliding_total_uncerts2[p][:])
        #spatial uncert is set to 0 for the range so that its not included in 
        #the uncertainty !!!
        spatial_uncert = np.zeros(dataframes_conc_uncertainty[p].shape)
       
        #poisson_uncert = np.array(dataframes_conc_uncertainty[p][:]) * 2
        if dataframes_probename[p] == 'HAIL-1D':
            poisson_uncert = np.array(dataframes_conc_uncertainty[p][:] * 2)
        elif dataframes_probename[p] == 'HAIL-2D':
            poisson_uncert = np.array(dataframes_meanconc_uncertainty[p][:] * 2)
        
        #sizing_uncert  = np.array(dataframes_conc_stddev_v2[p][:]) * 2    #v2
        sizing_uncert = np.array(dataframes_conc_sizinguncert_range[p][:])
                
        #turn nan to 0
        spatial_uncert = np.nan_to_num(spatial_uncert, nan=0)
        sizing_uncert  = np.nan_to_num(sizing_uncert,  nan=0)
        
        final_uncert_values = np.zeros(spatial_uncert.shape)
        final_uncert_type   = np.zeros(spatial_uncert.shape)
        #don't need loop. can just do np magic
        

        print('here second loop')

        #new method for comparing arrays that should work a lot better
        #and will be a lot cleaner
        def test_truth_largest(data1, data2, data3):
            #first compare data with the other two datas
            #data1 is the uncertainty type in focus
            #eg: poisson vs the sizing and spatial
            mask1 = data1 > data2
            mask2 = data1 > data3
            
            #now compare the two boolean arrays with &. Will only keep "True"
            #if true for both cases
            #I think & is a bitwise and opertaor that performs element wise (google)
            final_mask = mask1 & mask2
            return final_mask
        
        #retrieve mask for each probe
        #will be true for locations where the uncertainty type for the one in focus
        #was larger than the other two types (seconday and third)
        poisson_mask = test_truth_largest(poisson_uncert, sizing_uncert, spatial_uncert)
        sizing_mask  = test_truth_largest(sizing_uncert, spatial_uncert, poisson_uncert)
        spatial_mask = test_truth_largest(spatial_uncert, sizing_uncert, poisson_uncert)
        
        #need to make a mask for when there's no data across all three methods
        #i believe it should be when everything is just 0's
        #the ~ flips the boolean stuff so false becomes true and vice versa
        #and now all the 0's that were false the whole time are true can be 
        #logged as true in a new mask
        no_data_mask = ~poisson_mask & ~sizing_mask & ~spatial_mask
        
        #applying mask to the data
        def mask_data(mask, upper_uncert, lower_uncert):
            upper = np.ma.masked_array(upper_uncert, mask)
            lower = np.ma.masked_array(lower_uncert, mask)
            return upper, lower
        
        poisson_masked_data = mask_data(~poisson_mask, poisson_upper[p], poisson_lower[p])
        sizing_masked_data = mask_data(~sizing_mask, sizing_upper[p], sizing_lower[p])
        spatial_masked_data = mask_data(~spatial_mask, spatial_upper[p], spatial_lower[p])
        
        #fill the masked spots with 0 and then add arrays together
        poisson_filled_u = np.ma.filled((poisson_masked_data[0]), 0) 
        poisson_filled_l = np.ma.filled((poisson_masked_data[1]), 0)
        sizing_filled_u  = np.ma.filled((sizing_masked_data[0]), 0)
        sizing_filled_l  = np.ma.filled((sizing_masked_data[1]), 0)
        spatial_filled_u = np.ma.filled((spatial_masked_data[0]), 0)
        spatial_filled_l = np.ma.filled((spatial_masked_data[1]), 0)
        
        #biggest is dependent on biggest range, not individual values where plus 
        #and minus are treated separately
        biggest_u = poisson_filled_u + sizing_filled_u + spatial_filled_u
        biggest_l = poisson_filled_l + sizing_filled_l + spatial_filled_l
        
        
        #can figure out uncertainty type using same method of filling, excpet now
        #fill using different values from 1 or 0
        #1 will be poisson, 2 sizing, 3 spatial, and 0 is none which should indicate no concentration
        zeros_array = np.zeros(poisson_mask.shape)
        
        #its weird, but == True is the locations where the data gets filled in,
        #however, np where seems to fill in the opposite spots, hence the !=
        poisson_type = np.where(poisson_mask != True, zeros_array, 1)
        sizing_type = np.where(sizing_mask != True, zeros_array, 2)
        spatial_type = np.where(spatial_mask != True, zeros_array, 3)
        
        final_types = poisson_type + sizing_type + spatial_type
        
        
        all_upper_uncertainty.append(biggest_u)
        all_lower_uncertainty.append(biggest_l)
        uncertainty_type.append(final_types)
        
        #calculating the upper and lower plus minus values now
        
        if dataframes_probename[p] == 'HAIL-1D':
            middle_concs = np.array(dataframes_normalized_conc[p][:])
        elif dataframes_probename[p] == 'HAIL-2D':
            middle_concs = np.array(dataframes_mean_conc[p][:])
        
        def plus_minus_calculator(middle, upper, lower):
            #calculates the plus and minus values for plotting later
            #only used for one thing here but if i have to redo the indv
            #uncertainties i can port this up there
            plus  = upper - middle
            minus = middle - lower
            
            #checks to make sure that there aren't any pesky -0.0001 type of things
            #that will break the plotting since you cant have a error range of (-)
            #mostly this is needed if the error value is ~ the same as the normal value
            #again, idk why np.where reverses it, but it making everything lower than 0
            #be forced to 0
            if np.any(np.less(plus, 0)) == np.True_:
                plus = np.where(plus > 0, plus, 0)
            if np.any(np.less(minus, 0)) == np.True_:
                minus = np.where(minus > 0, minus, 0)
                
            return plus, minus
        
        biggest_upper_plusminus = plus_minus_calculator(middle_concs, 
                                                        biggest_u, 
                                                        biggest_l)
        
        all_upper_plusminus.append(biggest_upper_plusminus[0])
        all_lower_plusminus.append(biggest_upper_plusminus[1])
    
        
        
        """
        #The lower uncerainties won't plot as errorbars if they're negative. So,
        #replacing anything that's negative with a zero.
        #HOWEVER, zero doesn't work, so replacing all zeros with 0.1
        lower_uncertainty[lower_uncertainty < 0] = int(0)
        #lower_uncertainty[lower_uncertainty == 0] = 0.1sizing_u = np.array(dataframes_conc_sizinguncert_plus[p])
        sizing_l = np.array(dataframes_conc_sizinguncert_minus[p])
        
        lower_plus_minus[lower_plus_minus < 0] = 0
        #upper_plus_minus[upper_plus_minus == 0] = 0.1
        
        #need to do the same with normalized conc
        #middle_conc[middle_conc == 0] = 1
    
        all_lower_uncertainty.append(np.round(lower_uncertainty, 4))
        all_upper_uncertainty.append(np.round(upper_uncertainty, 4))
        uncertainty_type.append(final_uncert_type)
        
        all_lower_plusminus.append(lower_plus_minus)
        all_upper_plusminus.append(upper_plus_minus)
     """
except:
    print('likely running code with probes with two different total number of bins. this try except section would need to be updated to include that functionality')






#-------------------------------------------------------------------------
#
#Reflectivity Calculations
#
#-------------------------------------------------------------------------




#now to compute reflectivity
#will do so for the 5 sizing methods, the mean, and the 1d
#will need to do a probename check for the 1d
#will also need to calculate for all the uncertainties both poisson for everything
#and biggest of the two for the mean

def compute_z(D_bs, N_d):
    indv_ref = D_bs**6 * N_d
    summed_ref = np.nansum(indv_ref, axis=1)
    #power_sum = np.nansum(D_bs**6 * N_d, axis=1)
    #return -np.inf if power_sum == 0 else power_sum
    return indv_ref, summed_ref#power_sum

def compute_z_uncert(D_bs, N_d_u, N_d_l, dielectric):

    per_bin_u = D_bs**6 * (N_d_u)
    per_bin_l = D_bs**6 * (N_d_l)
    
    summed_u = np.sum(per_bin_u)
    summed_l = np.sum(per_bin_l)
    
    out_u = -np.inf if summed_u == 0 else summed_u
    out_l = -np.inf if summed_l == 0 else summed_l
    
    return per_bin_u, per_bin_l, out_u, out_l
    #return -np.inf if summedterm == 0 else summedterm


z_e_bins_all = []
Z_e_mid_all  = []
Z_e_upp_all  = []
Z_e_low_all  = []
for p in range(len(dataframes_normalized_conc)):
    
    #set some constants
    #equation is K_i/K_w * SUM[ D_i * C_i ]   and to get lgoatirithmic 10*log10
    #"_u" will stand for uncertainty

    #convert bin midpoints into millimeters
    D_i   = dataframes_bin_midpoints[p].astype('f8') / 1000
    #need uncertainty not total range, so /2 is for the +/-
    #if you want to include bin size uncertainty then you can work in the below variable
    #D_i_u = dataframes_binsize[p].astype('f8') / 1000 / 2
    
    #ice water dielectric is used to allow for slightly mixed phase environment
    #values come from Chandra's radar textbook and the internet
    ice_water_dielectric = 0.197 / 0.93
    
    #bin conversion is the dD which turns the PSD from differential into 
    #a more normal/basic concentration per bin??? honestly idk but thats the 
    #math. dD is the binsize
    bin_conversion = (dataframes_binsize[p]/1e6)
    

    
    #Now to start doing math
    #Below converts PSD to non_normlaized concentration (the C in the equation)
    if dataframes_probename[p] == 'HAIL-1D':
        C_i = dataframes_normalized_conc[p] * bin_conversion
        
        #_e is equivalent reflectivity (means it includes the dielectric stuff)
        z_bins, z = compute_z(D_i, C_i)
        
        z_e_bins = ice_water_dielectric * z_bins
        z_e      = ice_water_dielectric * z
        
        #zeros is for when log10 is of a value <=10 
        #Z_e is logarithmic reflectivity
        #zeros = np.zeros_like(z_e, dtype=float)
        zeros = np.zeros(z_e.shape, dtype=float)
        Z_e = 10*np.log10(z_e, out=zeros, where=~(z_e <= 0))
        
        #-------------------------------------------------------
        #The above but for uncertainty. Just poisson for 1D data
        C_i_u = (dataframes_normalized_conc[p] + dataframes_conc_uncertainty[p]) * bin_conversion
        C_i_l = (dataframes_normalized_conc[p] - dataframes_conc_uncertainty[p]) * bin_conversion
        
        #not storing uncertainty bin information to reduce clutter
        dump, z_u = compute_z(D_i, C_i_u)
        dump, z_l = compute_z(D_i, C_i_l)
    
        z_e_u     = ice_water_dielectric * z_u
        z_e_l     = ice_water_dielectric * z_l   
        
        Z_e_u = 10*np.log10(z_e_u, out=zeros, where=~(z_e_u <= 0))
        Z_e_l = 10*np.log10(z_e_l, out=zeros, where=~(z_e_l <= 0))


        #--------------------------------------------------------
        #read out the data now
        #not reading everything out to reduce clutter and time
        #can use math to un-logarithmic stuff if need be or un-dielectric it
        
        #read out the bins. will organize together rather than by z, ze
        #since it's only done for two sets
        zeros_out = np.zeros(z_e.shape, dtype=float)
        
        z_e_bins_all.append([z_e_bins, None])
        
        Z_e_mid_all.append([Z_e, zeros_out, zeros_out, zeros_out, zeros_out, zeros_out])
        Z_e_upp_all.append([Z_e_u, zeros_out, zeros_out, zeros_out, zeros_out, zeros_out])
        Z_e_low_all.append([Z_e_l, zeros_out, zeros_out, zeros_out, zeros_out, zeros_out])

    elif dataframes_probename[p] == 'HAIL-2D':
        #COMMENTS ON THE VARIABLE NAMES AND WHATS HAPPENING ARE WRITTEN IN 
        #THE 1D SECTION DIRECTLY ABOVE
        #With 2D data there are a lot of different options,
        #m=mean, c=circlefit, xs=xsize, xe=xextent, a=areasize
        
        C_i_m  = dataframes_mean_conc[p] * bin_conversion
        C_i_c  = dataframes_sizingmethod_conc[p][0] * bin_conversion
        C_i_xs = dataframes_sizingmethod_conc[p][1] * bin_conversion
        C_i_xe = dataframes_sizingmethod_conc[p][2] * bin_conversion
        C_i_y  = dataframes_sizingmethod_conc[p][3] * bin_conversion
        C_i_a  = dataframes_sizingmethod_conc[p][4] * bin_conversion
        
        
        #only keeping mean and xsize bins to reduce clutter
        z_m_bins, z_m   = compute_z(D_i, C_i_m)
        _, z_c       = compute_z(D_i, C_i_c)
        z_xs_bins, z_xs = compute_z(D_i, C_i_xs)
        _, z_xe      = compute_z(D_i, C_i_xe)
        _, z_y       = compute_z(D_i, C_i_y)
        _, z_a       = compute_z(D_i, C_i_a)
        
        
        z_e_m_bins  = ice_water_dielectric * z_m_bins
        z_e_xs_bins = ice_water_dielectric * z_xs_bins
        
        z_e_m       = ice_water_dielectric * z_m
        z_e_c       = ice_water_dielectric * z_c
        z_e_xs      = ice_water_dielectric * z_xs
        z_e_xe      = ice_water_dielectric * z_xe
        z_e_y       = ice_water_dielectric * z_y
        z_e_a       = ice_water_dielectric * z_a
        
        zeros = np.zeros_like(z_e_m, dtype=float)
        
        #testing what it's like to leave log(0) as inf when plotting ref. hopefully it works
        #nah gotta make 0 because it's 0 reflectivity which is weird for a logarithmic scale but oh well
        Z_e_m  = 10*np.log10(z_e_m)#, out=zeros, where=~(z_e_m <= 0))
        Z_e_c  = 10*np.log10(z_e_c)#, out=zeros, where=~(z_e_c <= 0))
        Z_e_xs = 10*np.log10(z_e_xs)#, out=zeros, where=~(z_e_xs <= 0))
        Z_e_xe = 10*np.log10(z_e_xe)#, out=zeros, where=~(z_e_xe <= 0))
        Z_e_y  = 10*np.log10(z_e_y)#, out=zeros, where=~(z_e_y <= 0))
        Z_e_a  = 10*np.log10(z_e_a)#, out=zeros, where=~(z_e_a <= 0))


        #-------------------------------------------------------
        #The above but for uncertainty. Just poisson for 1D data
        C_i_m_u = (dataframes_mean_conc[p] + all_upper_plusminus[p]) * bin_conversion
        C_i_m_l = (dataframes_mean_conc[p] - all_lower_plusminus[p]) * bin_conversion
        C_i_c_u = (dataframes_sizingmethod_conc[p][0] + dataframes_sizemethod_poisson_uncertainty[p][0]) * bin_conversion
        C_i_c_l = (dataframes_sizingmethod_conc[p][0] - dataframes_sizemethod_poisson_uncertainty[p][0]) * bin_conversion
        C_i_xs_u = (dataframes_sizingmethod_conc[p][1] + dataframes_sizemethod_poisson_uncertainty[p][1]) * bin_conversion
        C_i_xs_l = (dataframes_sizingmethod_conc[p][1] - dataframes_sizemethod_poisson_uncertainty[p][1]) * bin_conversion
        C_i_xe_u = (dataframes_sizingmethod_conc[p][2] + dataframes_sizemethod_poisson_uncertainty[p][2]) * bin_conversion
        C_i_xe_l = (dataframes_sizingmethod_conc[p][2] - dataframes_sizemethod_poisson_uncertainty[p][2]) * bin_conversion
        C_i_y_u = (dataframes_sizingmethod_conc[p][3] + dataframes_sizemethod_poisson_uncertainty[p][3]) * bin_conversion
        C_i_y_l = (dataframes_sizingmethod_conc[p][3] - dataframes_sizemethod_poisson_uncertainty[p][3]) * bin_conversion
        C_i_a_u = (dataframes_sizingmethod_conc[p][4] + dataframes_sizemethod_poisson_uncertainty[p][4]) * bin_conversion
        C_i_a_l = (dataframes_sizingmethod_conc[p][4] - dataframes_sizemethod_poisson_uncertainty[p][4]) * bin_conversion
        
        #not storing uncertainty bin information to reduce clutter
        #just gonna have chatgpt fill out the rest this is so tedious
        _, z_m_u  = compute_z(D_i, C_i_m_u)
        _, z_m_l  = compute_z(D_i, C_i_m_l)
        
        _, z_c_u  = compute_z(D_i, C_i_c_u)
        _, z_c_l  = compute_z(D_i, C_i_c_l)
        
        _, z_xs_u = compute_z(D_i, C_i_xs_u)
        _, z_xs_l = compute_z(D_i, C_i_xs_l)
        
        _, z_xe_u = compute_z(D_i, C_i_xe_u)
        _, z_xe_l = compute_z(D_i, C_i_xe_l)
        
        _, z_y_u  = compute_z(D_i, C_i_y_u)
        _, z_y_l  = compute_z(D_i, C_i_y_l)
        
        _, z_a_u  = compute_z(D_i, C_i_a_u)
        _, z_a_l  = compute_z(D_i, C_i_a_l)
        
        # dielectric adjustment
        z_e_m_u  = ice_water_dielectric * z_m_u
        z_e_m_l  = ice_water_dielectric * z_m_l
        
        z_e_c_u  = ice_water_dielectric * z_c_u
        z_e_c_l  = ice_water_dielectric * z_c_l
        
        z_e_xs_u = ice_water_dielectric * z_xs_u
        z_e_xs_l = ice_water_dielectric * z_xs_l
        
        z_e_xe_u = ice_water_dielectric * z_xe_u
        z_e_xe_l = ice_water_dielectric * z_xe_l
        
        z_e_y_u  = ice_water_dielectric * z_y_u
        z_e_y_l  = ice_water_dielectric * z_y_l
        
        z_e_a_u  = ice_water_dielectric * z_a_u
        z_e_a_l  = ice_water_dielectric * z_a_l
        
        #log10 reflectivities i think makes 0 if log0 cause cant log0
        Z_e_m_u  = 10*np.log10(z_e_m_u)#,  out=zeros, where=~(z_e_m_u <= 0))
        Z_e_m_l  = 10*np.log10(z_e_m_l)#,  out=zeros, where=~(z_e_m_l <= 0))
        
        Z_e_c_u  = 10*np.log10(z_e_c_u)#,  out=zeros, where=~(z_e_c_u <= 0))
        Z_e_c_l  = 10*np.log10(z_e_c_l)#,  out=zeros, where=~(z_e_c_l <= 0))
        
        Z_e_xs_u = 10*np.log10(z_e_xs_u)#, out=zeros, where=~(z_e_xs_u <= 0))
        Z_e_xs_l = 10*np.log10(z_e_xs_l)#, out=zeros, where=~(z_e_xs_l <= 0))
        
        Z_e_xe_u = 10*np.log10(z_e_xe_u)#, out=zeros, where=~(z_e_xe_u <= 0))
        Z_e_xe_l = 10*np.log10(z_e_xe_l)#, out=zeros, where=~(z_e_xe_l <= 0))
        
        Z_e_y_u  = 10*np.log10(z_e_y_u)#,  out=zeros, where=~(z_e_y_u <= 0))
        Z_e_y_l  = 10*np.log10(z_e_y_l)#,  out=zeros, where=~(z_e_y_l <= 0))
        
        Z_e_a_u  = 10*np.log10(z_e_a_u)#,  out=zeros, where=~(z_e_a_u <= 0))
        Z_e_a_l  = 10*np.log10(z_e_a_l)#,  out=zeros, where=~(z_e_a_l <= 0))




        #enforcing all cases where there is 0 concentration recorded
        #to force a "logarithmic" reflectivity value of 0
        #it's weird because you can't take the log of 0
        #but i still have to represent the data, so as long as its not
        #being plotted with logarithmic axes, it should be okay
        Z_e_m[z_e_m <= 0] = 0
        Z_e_c[z_e_c <= 0] = 0
        Z_e_xs[z_e_xs <= 0] = 0
        Z_e_xe[z_e_xe <= 0] = 0
        Z_e_y[z_e_y <= 0] = 0
        Z_e_a[z_e_a <= 0] = 0
        
        Z_e_m_u[z_e_m_u <= 0] = 0
        Z_e_m_l[z_e_m_l <= 0] = 0
        
        Z_e_c_u[z_e_c_u <= 0] = 0
        Z_e_c_l[z_e_c_l <= 0] = 0
        
        Z_e_xs_u[z_e_xs_u <= 0] = 0
        Z_e_xs_l[z_e_xs_l <= 0] = 0
        
        Z_e_xe_u[z_e_xe_u <= 0] = 0
        Z_e_xe_l[z_e_xe_l <= 0] = 0
        
        Z_e_y_u[z_e_y_u <= 0] = 0
        Z_e_y_l[z_e_y_l <= 0] = 0
        
        Z_e_a_u[z_e_a_u <= 0] = 0
        Z_e_a_l[z_e_a_l <= 0] = 0



        #--------------------------------------------------------
        #read out the data now
        #not reading everything out to reduce clutter and time
        #can use math to un-logarithmic stuff if need be or un-dielectric it
        
        #read out the bins. will organize together rather than by z, ze
        #since it's only done for two sets
        z_e_bins_all.append([z_e_m_bins, z_e_xs_bins])
        
        Z_e_mid_all.append([Z_e_m, Z_e_c, Z_e_xs, Z_e_xe, Z_e_y, Z_e_a])
        Z_e_upp_all.append([Z_e_m_u, Z_e_c_u, Z_e_xs_u, Z_e_xe_u, Z_e_y_u, Z_e_a_u])
        Z_e_low_all.append([Z_e_m_l, Z_e_c_l, Z_e_xs_l, Z_e_xe_l, Z_e_y_l, Z_e_a_l])
        




"""
below code is for manually checking how the reflectivities perform

i = 120 
p = 1
tconc = dataframes_normalized_conc[p][i] * bin_conversion
t_u   = dataframes_conc_upper_uncertainty[p][i] * bin_conversion
t_l   = dataframes_conc_lower_uncertainty[p][i] * bin_conversion
tz    = compute_z(D_bs, tconc, ice_water_dielectric)
tz_upper, tz_lower = compute_z_uncert(D_bs, t_u, t_l, ice_water_dielectric)
tdbz = 10*np.log10(ice_water_dielectric*tz)
tdbz_u = 10*np.log10(ice_water_dielectric*tz_upper)
tdbz_l = 10*np.log10(ice_water_dielectric*tz_lower)
print(tz, tz_upper, tz_lower, '\n', tdbz, tdbz_u, tdbz_l)
"""






#-------------------------------------------------------------------
#
#Saving the data to files
#
#-------------------------------------------------------------------

plot_times_final_s = starttime_HHMMSS
plot_times_final_f = endtime_HHMMSS


interval_starttime = starttime_HHMMSS[0]
interval_endtime = endtime_HHMMSS[-1]

FlightNum = str(getattr(airplanedata, 'FlightNumber'))
FlightDate = str(getattr(airplanedata, 'FlightDate'))
FlightDate = FlightDate.split('/')
FlightDate = FlightDate[2]+''+FlightDate[0]+''+FlightDate[1]

current_date = date.today()
file_created_date = current_date.strftime("%Y%m%d")

main_pathway_table = path_to_folder + 'PSD_Tables/'

main_pathway_table2 = main_pathway_table + 'PSD_Tables/'
if os.path.exists(main_pathway_table2) is False:   
    os.mkdir(main_pathway_table2)

main_pathway_table3 = main_pathway_table2 + file_created_date
if os.path.exists(main_pathway_table3) is False:   
    os.mkdir(main_pathway_table3)

main_pathway_table4 = main_pathway_table3 + '/' + str(FlightDate) + '/'
if os.path.exists(main_pathway_table4) is False:   
    os.mkdir(main_pathway_table4)

main_pathway_table5 = main_pathway_table4 + str(interval_starttime) + '_' + str(interval_endtime) +'/'
if os.path.exists(main_pathway_table5) is False:   
    os.mkdir(main_pathway_table5)
    
main_pathway_table6 = main_pathway_table5 + 'Individual_Intervals' +'/'
if os.path.exists(main_pathway_table6) is False:   
    os.mkdir(main_pathway_table6)

pathname_tables = main_pathway_table5



print("Start and final particle times pulled from the data,")
for counter in range(len(dataframes_normalized_conc)):
    if dataframes_types[counter] == 4: #pbp files
        probename_l = dataframes_probename[counter]
        processing_method = dataframes_plot_legend_labels[counter]
        legend_name = probename_l + ' ' + processing_method

        first_part_time = dataframes_list[counter][5][array_start_indices[counter]]
        last_part_time = dataframes_list[counter][5][array_end_indices[counter]]
        
        first_part_time = seconds_HHMMSS(first_part_time)
        last_part_time = seconds_HHMMSS(last_part_time)

        print(legend_name, " first particle time - ", first_part_time,
              ", last particle time - ", last_part_time)
    if dataframes_types[counter] == 2: #disp files
        probename_l = dataframes_probename[counter]
        processing_method = dataframes_plot_legend_labels[counter]
        legend_name = probename_l + ' ' + processing_method

        first_part_time = dataframes_list[counter]['Time'][array_start_indices[counter]]
        last_part_time = dataframes_list[counter]['Time'][array_end_indices[counter]]

        print(legend_name, " first particle time - ", first_part_time,
              ", last particle time - ", last_part_time)


#create a function to compare the counting vs sizing uncertainty
#make a final list that is the biggest uncertainty
#store whether it was the sizing or counts uncertainty that was larger as an extra column
def pick_highest_uncertainty(counting_uncertainty, sizing_uncertainty):
    uncertainty_list   = []
    type_uncertainties = []
    for x in range(len(counting_uncertainty)):
        bigger_uncertainty = sizing_uncertainty[x]
        uncertainty_check  = 'sizing'
        if counting_uncertainty[x] > sizing_uncertainty[x]: #updates to other uncertainty if larger
            bigger_uncertainty = counting_uncertainty[x]
            uncertainty_check  = 'counting'
        if counting_uncertainty[x] == sizing_uncertainty[x]:
            uncertainty_check  = 'equal'
            
        uncertainty_list.append(bigger_uncertainty)
        type_uncertainties.append(uncertainty_check)
            
    return uncertainty_list, type_uncertainties

#NEED TO VERIFY THAT IM USING THE SIZING METHOD ONC TO USE#!!!!!!!!!!!!!!!!!





#Making old style table
try:
    for y in range(len(dataframes_types)): #for probe
        counter = array_start_indices[y]
        for x in range(dataframes_normalized_conc[0].shape[0]): #for time intervals
            """
            #determining conc uncertainty value and type
            conc_uncertainty_table, conc_uncertainty_type = \
                pick_highest_uncertainty(dataframes_conc_uncertainty[y][x], dataframes_conc_stddev[y][x])
                #above is in plus or minus, so need to calculate the plus minus here
                #and then also add to the table a lower and upper uncertainty
        
            
            l_uncert                = all_lower_uncertainty[y][x]
            l_uncert[l_uncert==0.1] = 0
            u_uncert                = all_upper_uncertainty[y][x]
            center_val              = dataframes_normalized_conc[y][x]
            plus_minus              = np.abs((u_uncert - center_val)) 
            type_uncert             = []
            """
            #rewriting how uncertainty is defined for the table since the 
            #comparisons all happen above the plot now
            
            
            #naming and the uncertainty and retrieving values for interval
            type_uncert = []
            u_uncert    = []
            l_uncert    = []
            for idx, ea_bin in enumerate(uncertainty_type[y][x]):
                #define uncertainty type
                #if dataframes_normalized_conc[y][x][idx] == 0 and\
                #   all_upper_uncertainty[y][x][idx] == 0:
                #    #is no concentration, then no particles, then no uncertainty type
                #    type_uncert.append('NA')
                if ea_bin == 0:
                    type_uncert.append('NA')
                elif ea_bin == 1:
                    type_uncert.append('poisson')
                elif ea_bin == 2:
                    type_uncert.append('sizing')
                elif ea_bin == 3:
                    type_uncert.append('spatial')
    
            #retrieve uncertainty values
            u_uncert.append(all_upper_uncertainty[y][x])
            l_uncert.append(all_lower_uncertainty[y][x])
                
            #not sure if this is still applicable but keeping it in case 
            #it's still necessary
            #l_uncert[l_uncert==0.1] = 0
            
            #pseudo plus minus in case anyone wants it
            plus_minus = (np.array(u_uncert) - np.array(l_uncert)) / 2
            
            #getting rid of surrounding extra list.array whatever
            u_uncert   = u_uncert[0]
            l_uncert   = l_uncert[0]
            plus_minus = plus_minus[0]
                    
        
        
            starttime_file = starttime_HHMMSS[x]
            #starttime_file = seconds_HHMMSS(starttime_file)
            counter += 1
            #endtime_file = dataframes_list[y]['Time'][counter]
            endtime_file = endtime_HHMMSS[x]
            
            #tableName = main_pathway_table6 + "PSD_Conc_" +\
             #                str(dataframes_probename[y]) + '_' + starttime_file +'-'+ \
              #               endtime_file +'.txt'
            tableName = main_pathway_table6 + str(dataframes_probename[y]) +\
                        "_Conc_per_bin_" + FlightDate + '_' +\
                        starttime_file +'-'+ endtime_file +'.txt'
                             
            filein = open(tableName, "w+") #assumes bins are micrometer below
            filein.write('{z:<7}{q:<18}{d:<13}{b:<21}{c:<22}{f:<18}{g:<18}{e:<12}'.format\
                           (z='Bin', q='Bin_Size_Min(cm)', \
                            d='Bin_Size(+)', \
                            b=dataframes_probename[y]+'_Conc(#/m^4)', \
                            c='Conc_Uncertainty(+/-)',\
                            f='Conc_Lower_Uncert',\
                            g='Conc_Upper_Uncert',\
                            e='Uncertainty_Type'))
            filein.write('\n\n')
            for z in range(dataframes_bin_startpoints[y].shape[0]): #for channels            
                filein.write('{z:<7}{q:<18}{d:<14}{b:<21}{c:<22}{f:<18}{g:<18}{e:<12}'.format(\
                              z=int(z+1), q=float(float(dataframes_bin_startpoints[y][z])/10000),\
                              d=round(dataframes_binsize[y][z]/10000, 2),\
                              b=round(dataframes_normalized_conc[y][x][z], 4), \
                              c=np.round((plus_minus[z]), 4),\
                              f=np.round(l_uncert[z], 4),\
                              g=np.round(u_uncert[z], 4),\
                              e=type_uncert[z]))
                filein.write('\n')
            filein.close()
    
        filein.close()
except:
    print("Couldn't make table")


#reflectivity stuff is below
#also take time to read out the tables into a np format or something
#so that it's easy to manipulate the data later without
#having to rerun this program every single time




#Checking if the file exists. If it does, then add new times to it. But
#don't write over old times. Will need to be careful with this. If wanting
#to write over old times, then it's probably better to just make a new file.
#---------------------------------------------------------------------------
#Do for each probe. Separating each file to be for a single probe/data type



#same as plot and table section. Using similar/repeated variable names
main_pathway_data = path_to_folder + 'Sensor_Information/'

main_pathway_data2 = main_pathway_data + 'Count_Conc_Ref_Data/'
if os.path.exists(main_pathway_data2) is False:   
    os.mkdir(main_pathway_data2)

main_pathway_data3 = main_pathway_data2 + file_created_date
if os.path.exists(main_pathway_data3) is False:   
    os.mkdir(main_pathway_data3)

main_pathway_data4 = main_pathway_data3 + '/' +str(FlightDate) + '/'
if os.path.exists(main_pathway_data4) is False:   
    os.mkdir(main_pathway_data4)

main_pathway_data5 = main_pathway_data4 + str(interval_starttime) + '_' + str(interval_endtime) +'/'
if os.path.exists(main_pathway_data5) is False:   
    os.mkdir(main_pathway_data5)
    

pathname_data = main_pathway_data5
        

print(pathname_data)

filenames_data = []
for p in range(len(dataframes_probename)):
    output_file = pathname_data + flight_num + '_PBP_Processed_' +\
                  dataframes_probename[p] + '.nc'
    filenames_data.append(output_file)            

#output_file = pathname_data + flight_num + '_PBP_Processed.nc'
#filename_outdata = glob.glob(output_file)



for p in range(len(dataframes_normalized_original)): #p is probe
    #making lists of reflectivities for each probe into the same
    #dimension as the time dimension and seperating them out.
    #this comment in convoluted. probes ref stored in same list in list of lists
    #need to seperate. so seperating happening
    #reflectivities_indv   = np.array(reflectivities)[:, p]
    #ref_uncert_indv       = np.array(reflectivities_uncert)[:, p]
    
    #reflectivities_u_indv = np.array(reflectivities_u)[:, p]
    #reflectivities_l_indv = np.array(reflectivities_l)[:, p]
    
    #ref_spatial_u_indv    = np.array(ref_spatial_u)[:, p]
    #ref_spatial_l_indv    = np.array(ref_spatial_l)[:, p]
    #ref_poisson_u_indv    = np.array(ref_poisson_u)[:, p]
    #ref_poisson_l_indv    = np.array(ref_poisson_l)[:, p]
    #ref_sizing_u_indv     = np.array(ref_sizing_u)[:, p]
    #ref_sizing_l_indv     = np.array(ref_sizing_l)[:, p]


    #new ref ordering


    #making dataset with the 10s concs, counts, time, and reflectivities
    #define coordinates using NumPy
    #time_out = np.arange(len(dataframes_normalized_conc[0]))  #12 time steps 
    #bins_out = np.arange(len(dataframes_normalized_conc[0][0]))  # 14 bins
    time_out = np.arange(dataframes_normalized_original[p].shape[0])
    bins_out = np.arange(dataframes_normalized_original[p].shape[1])

    #uncertainties are plus minus for the counts and concentration/PSD
    #uncertainties are upper value and lower value for the reflectivity
    #the mean 
    #     count uncertainty is poisson
    #     psd uncertainty is bigget of poisson vs sizing
    #     ref uncertainty is based off biggest uncertainty
    if dataframes_probename[p] == 'HAIL-1D':
        #create initial dictionary for the dataset
        data_vars = {
            'time_start':(['time'], plot_times_final_s),
            
            'counts_1D':            (['time', 'bins'], dataframes_normalized_original[p]),
            'counts_1D_uncertainty':(['time', 'bins'], dataframes_count_uncertainty[p]),
            
            'psd_1D':            (['time', 'bins'], dataframes_normalized_conc[p]),
            'psd_1D_uncertainty':(['time', 'bins'], dataframes_conc_uncertainty[p]),
            
            'z_e_1D_eachbin':          (['time', 'bins'], z_e_bins_all[p][0]),
            'Z_e_1D':                  (['time'], Z_e_mid_all[p][0]),
            'Z_e_1D_upper_uncertainty':(['time'], Z_e_upp_all[p][0]),
            'Z_e_1D_lower_uncertainty':(['time'], Z_e_low_all[p][0]),
                        
            'bin_startpoints':(['bins'], dataframes_bin_startpoints[p]),
            'bin_size':(['bins'], dataframes_binsize[p])
                    }
        
    elif dataframes_probename[p] == 'HAIL-2D':
        #create initial dictionary for the dataset
        data_vars = {
            'time_start':(['time'], plot_times_final_s),
            
            'counts_2D_mean':    (['time', 'bins'], dataframes_normalized_mean[p]),
            'counts_2D_circle':  (['time', 'bins'], dataframes_sizingmethod_counts[p][0]),
            'counts_2D_xsize':   (['time', 'bins'], dataframes_sizingmethod_counts[p][1]),
            'counts_2D_xextent': (['time', 'bins'], dataframes_sizingmethod_counts[p][2]),
            'counts_2D_ysize':   (['time', 'bins'], dataframes_sizingmethod_counts[p][3]),
            'counts_2D_areasize':(['time', 'bins'], dataframes_sizingmethod_counts[p][4]),
            
            'counts_2D_mean_uncertainty':    (['time', 'bins'], dataframes_meanconc_uncertainty[p]),
            'counts_2D_circle_uncertainty':  (['time', 'bins'], dataframes_sizemethod_poisson[p][0]),
            'counts_2D_xsize_uncertainty':   (['time', 'bins'], dataframes_sizemethod_poisson[p][1]),
            'counts_2D_xextent_uncertainty': (['time', 'bins'], dataframes_sizemethod_poisson[p][2]),
            'counts_2D_ysize_uncertainty':   (['time', 'bins'], dataframes_sizemethod_poisson[p][3]),
            'counts_2D_areasize_uncertainty':(['time', 'bins'], dataframes_sizemethod_poisson[p][4]),
            
            'psd_2d_mean':    (['time', 'bins'], dataframes_mean_conc[p]),
            'psd_2d_circle':  (['time', 'bins'], dataframes_sizingmethod_conc[p][0]),
            'psd_2d_xsize':   (['time', 'bins'], dataframes_sizingmethod_conc[p][1]),
            'psd_2d_xextent': (['time', 'bins'], dataframes_sizingmethod_conc[p][2]),
            'psd_2d_ysize':   (['time', 'bins'], dataframes_sizingmethod_conc[p][3]),
            'psd_2d_areasize':(['time', 'bins'], dataframes_sizingmethod_conc[p][4]),
            
            'psd_2d_mean_upper_uncertainty':(['time', 'bins'], all_upper_plusminus[p]),
            'psd_2d_mean_lower_uncertainty':(['time', 'bins'], all_lower_plusminus[p]),
            'psd_2d_circle_uncertainty':    (['time', 'bins'], dataframes_sizemethod_poisson_uncertainty[p][0]),
            'psd_2d_xsize_uncertainty':     (['time', 'bins'], dataframes_sizemethod_poisson_uncertainty[p][1]),
            'psd_2d_xextent_uncertainty':   (['time', 'bins'], dataframes_sizemethod_poisson_uncertainty[p][2]),
            'psd_2d_ysize_uncertainty':     (['time', 'bins'], dataframes_sizemethod_poisson_uncertainty[p][3]),
            'psd_2d_areasize_uncertainty':  (['time', 'bins'], dataframes_sizemethod_poisson_uncertainty[p][4]),
            
            'psd_uncertainty_type':(['time', 'bins'], uncertainty_type[p]),
            
            'z_e_2D_mean_eachbin': (['time', 'bins'], z_e_bins_all[p][0]),
            'z_e_2D_xsize_eachbin':(['time', 'bins'], z_e_bins_all[p][1]),
            
            'Z_e_2D_mean':    (['time'], Z_e_mid_all[p][0]),
            'Z_e_2D_circle':  (['time'], Z_e_mid_all[p][1]),
            'Z_e_2D_xsize':   (['time'], Z_e_mid_all[p][2]),
            'Z_e_2D_xextent': (['time'], Z_e_mid_all[p][3]),
            'Z_e_2D_ysize':   (['time'], Z_e_mid_all[p][4]),
            'Z_e_2D_areasize':(['time'], Z_e_mid_all[p][5]),
            
            'Z_e_2D_mean_upper_uncertainty':    (['time'], Z_e_upp_all[p][0]),
            'Z_e_2D_circle_upper_uncertainty':  (['time'], Z_e_upp_all[p][1]),
            'Z_e_2D_xsize_upper_uncertainty':   (['time'], Z_e_upp_all[p][2]),
            'Z_e_2D_xextent_upper_uncertainty': (['time'], Z_e_upp_all[p][3]),
            'Z_e_2D_ysize_upper_uncertainty':   (['time'], Z_e_upp_all[p][4]),
            'Z_e_2D_areasize_upper_uncertainty':(['time'], Z_e_upp_all[p][5]),
            
            'Z_e_2D_mean_lower_uncertainty':    (['time'], Z_e_low_all[p][0]),
            'Z_e_2D_circle_lower_uncertainty':  (['time'], Z_e_low_all[p][1]),
            'Z_e_2D_xsize_lower_uncertainty':   (['time'], Z_e_low_all[p][2]),
            'Z_e_2D_xextent_lower_uncertainty': (['time'], Z_e_low_all[p][3]),
            'Z_e_2D_ysize_lower_uncertainty':   (['time'], Z_e_low_all[p][4]),
            'Z_e_2D_areasize_lower_uncertainty':(['time'], Z_e_low_all[p][5]),
            
                        
            'bin_startpoints':(['bins'], dataframes_bin_startpoints[p]),
            'bin_size':(['bins'], dataframes_binsize[p])
        
    
                    }

    #create xarray dataset without pandas
    ds_out = xr.Dataset(
        data_vars,
        coords={
            'time': time_out,
            'bins': bins_out
               },
        attrs={'Flight': flight_num,
               'Flight_Date': FlightDate,
               'File_Created_Date': file_created_date,
               'File_Starttime': interval_starttime,
               'File_Endtime': interval_endtime,
               'Probe': dataframes_probename[p]
               }
    )
    
    #save the dataframe now
    ds_out.to_netcdf(filenames_data[p], format='NETCDF4', unlimited_dims='time')
    #make permissions w for all
    # Set permissions: rw-rw-rw- (owner, group, others can read and write)
    #from chatgpt
    #this way you can write over files if changing this code
    os.chmod(filenames_data[p], stat.S_IRUSR | stat.S_IWUSR |  # Owner
                              stat.S_IRGRP | stat.S_IWGRP |  # Group
                              stat.S_IROTH | stat.S_IWOTH)   # Others











