#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 14:01:38 2024

@author: james.klinman

Attempting to stich together pbp searching and aircraft data searching such 
as liquid water content in order to determine whether buffers are good or not

this code will work for the hail spectrometer since that starty and stopy are
just the buffer start and stop points. For all other probes that do have 
accurate boundaries for the particle images, this might not work.

Actually I might be able to replace it with buffertime instead. I'm going to 
try that and see if it lines up with the indices i get using the
starty and stopy method. if so, ill go with the buffertime since that would 
work for other probes as well

yup, going with buffertime
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
import math
import netCDF4
from datetime import date
import pickle
import json
import re
from statistics import mode
import statistics 
import scipy
import time

filenamePBP   = 'Particle_Image_20240916/06222000_232921_HAIL.pbp.nc'

#for a hail period
starttime = '242030'
endtime   = '242400'

#specifying different rejections                    
rejection_flags_accept = [0, 4, 8]#, 4]      
reject_below_arearatio = 0.3

#adding options for area ratio
area_ratio_indv_check = False #true for different area ratios for different datasets
area_ratio_indv = [0.3, 0.3, None, 0.1] #leave empty if option is false
#must be in same order as files 
#put None for files that aren't processed by soda

#options are 'diam', 'xsize', 'ysize', 'xextent', 'areasize' for \/
sizes_to_plot = ['diam', 'xsize', 'ysize', 'xextent', 'areasize']
sizes_to_plot = ['xextent']



#Getting flight number and file
#------------------------------
flight_num = '757'

#getting path to access file
#--------------------------
filepath_file = 'Random/filepaths.json'
with open(filepath_file, 'r') as file:
    filepaths = file.read()  
filepaths = json.loads(filepaths)
for year in filepaths:
    for flight in filepaths[year]:
        if flight_num in flight:
            path_to_flight = flight
flightpath = path_to_flight + '/' + flight_num + '.nc'

aircraft_data = netCDF4.Dataset(flightpath)



#some definitions
#------------------
def SDSMT_disp_txt_read(dispfile):  
    file_read = 0
    try:
        strToDelete = 'F l i g h t  ...  ........  Hail Info'
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
        file_read = 1
    except:
        pass

    if file_read == 0:
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
        data_temp.close
    
    return probename



#Data searching and alteration relevant definitions
#-------------------------------------------------

def find_index_of_closest_value(array, valueToFind):
    differences = np.abs(array - valueToFind)
    closest_index = differences.argmin()
    return closest_index







#reading in the pbp data now
pbp_data = netCDF4.Dataset(filenamePBP)


#group particles by the second
#only accept if it meets the rejection criteria
#then group by size bins in that second
fastcircle_diam = pbp_data['diam']
xsize_diam      = pbp_data['xsize']
ysize_diam      = pbp_data['ysize']
xextent_diam    = pbp_data['xextent']
areasize_diam   = pbp_data['areasize']
particle_times  = pbp_data['time']
part_arearatios = pbp_data['arearatio']
part_rejectflags = pbp_data['rejectionflag']

#timing element
testing_time_use = time.time()

#finding buffer border indices in the pbp data
part_buffertimes = pbp_data['buffertime']
buffertime_indices = []
temp_time = part_buffertimes[0] 
counter = 0
for x in part_buffertimes:
    if x != temp_time:
        buffertime_indices.append(counter)
        temp_time = x
    counter += 1
    

testing_time_use_end = time.time()
elapsed_time = testing_time_use_end - testing_time_use


#note to self for future coding
"""
need to probably bring in the pbp normalize/sorting fuction
will want to store them in 1d array now i think since it's still pbp data and
im not having to deal with bins and specific time chunks now
but need to make sure particles are sorted by thir buffer, which means I need 
to store the time in similar arrays as the accepted/rejected. this is just
oh wait instead of [t, ,t, t, t, t, ], [y, n, y, n, y, n, y, n] i could do
[t, total y, total n] actually i think i need to do the first one and then i can 
shorten to the second one it will just probide more information which will be useful.




from there i can take the start and end time for a buffer and find the liquid water content
at that time or any other measurement from the aircraft and can make a table to 
show the data.



also would be good if there was a way to more efficiently sort through the data
at any step really but at least at the first one
"""
