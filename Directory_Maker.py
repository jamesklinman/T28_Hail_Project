#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 14:16:38 2024

@author: james.klinman

This code creates the directories to store the different outputs from
the T28 Processing code.
It can also be extended to make the soda output folder too
SODA_Concs
"""

#have to go through all the scripts to reroute the directory pathways to their respective folders.
#can copy the directory finder from here
#yeah i think ill just do that. just make sure it's all organized

import os
import json

#creating a file path to the different years directories 
dir_up = '../../'
dir_list = os.listdir(dir_up)
year_dirs = []
for direc in dir_list:
    if direc.startswith('yr'):
        yr_path = os.path.join(dir_up, direc)
        year_dirs.append(yr_path)

print(year_dirs)

#creating a list of the file paths to each flight in each year
fdict = {}
for year in year_dirs:
    year_sub = os.listdir(year)
    fdict[year[6:12]] = []
    for subdir in year_sub:
        if subdir.startswith('f'):
            fpath = os.path.join(year, subdir)
            fdict[year[6:12]].append(fpath)

#count is enforcing just the first two years for now hwile i get this set up
#count = 0
#Makes all the main directories for all the outputs
main_file = '/Code_Files_and_Outputs'
for year in fdict:
    for flight in fdict[year]:
        print(flight + main_file)
        if os.path.exists(flight + main_file) is False:
            os.mkdir(flight + main_file)
        if os.path.exists(flight + main_file + '/PSD_Plots') is False:
            os.mkdir(flight + main_file + '/PSD_Plots')
        if os.path.exists(flight + main_file + '/PSD_Tables') is False:
            os.mkdir(flight + main_file + '/PSD_Tables')
        if os.path.exists(flight + main_file + '/Flight_Plots') is False:
            os.mkdir(flight + main_file + '/Flight_Plots')
        if os.path.exists(flight + main_file + '/Random') is False:
            os.mkdir(flight + main_file + '/Random')
        if os.path.exists(flight + main_file + '/Sensor_Information') is False:
            os.mkdir(flight + main_file + '/Sensor_Information')
        if os.path.exists(flight + main_file + '/Sensor_Information/Count_Conc_Ref_Data') is False:
            os.mkdir(flight + main_file + '/Sensor_Information/Count_Conc_Ref_Data')

    #count+=1
    #if count == 2:
    #    break


#saving dictionary of filepath name so they don't need to be refound 
#for every file that needs access to different flight files.
with open('Random/filepaths.json', 'w') as json_file:
    json.dump(fdict, json_file)
