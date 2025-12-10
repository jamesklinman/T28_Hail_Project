#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 23:15:39 2025

@author: jamesklinman
"""


import netCDF4 as nc
import numpy as np
import glob


version_plot = '20251006'
probe_plot   = ['HAIL-2D', 'HAIL-1D']
redo_case = False #i believe this is just to mask out certain bins

#hvps case against 670
#version_plot = '20250702_HVPS'
#probe_plot   = ['HVPS1', 'HAIL-1D']
#redo_case = True


#calling in whole path to all filenames that contain the relevant data
"""flight_list = glob.glob('../../yr*/f*/Code_Files_and_Outputs/Sensor_Information/'
                        'Count_Conc_Ref_Data/' + version_plot +
                        '/*/*/*_PBP_Processed_*.nc')
"""
flight_list = glob.glob('../../yr*/f*/SODA_Outputs/*HAIL.pbp.nc')


#loop that open one file at a time
#then get the total number of edge touch
#and total number of not edge touch
#save that number to an array. once all flights
#processed, can then just add up the array values

no_touch_all    = []
left_touch_all  = []
right_touch_all = []
both_touch_all  = []
for x in range(len(flight_list)):
    
    #open file
    data = nc.Dataset(flight_list[x])
    
    #believe this is correct
    #0 is none, 1 is left, 2, is right, 3 is both (from soda manual)
    edge_data = data['edgetouch'][:]
    
    #using xsize
    size_data = data['xsize'][:]
    size_threshold = 13000
    
    no_touch    = np.where((edge_data == 0) & (size_data >= size_threshold))[0].shape[0]
    left_touch  = np.where((edge_data == 1) & (size_data >= size_threshold))[0].shape[0]
    right_touch = np.where((edge_data == 2) & (size_data >= size_threshold))[0].shape[0]
    both_touch  = np.where((edge_data == 3) & (size_data >= size_threshold))[0].shape[0]
    
    #save data
    no_touch_all.append(no_touch)
    left_touch_all.append(left_touch)
    right_touch_all.append(right_touch)
    both_touch_all.append(both_touch)
    
#np array for easy math    
no_touch_all    = np.array(no_touch_all)
left_touch_all  = np.array(left_touch_all)
right_touch_all = np.array(right_touch_all)
both_touch_all  = np.array(both_touch_all)


#combine all edge touch for simple comparison
all_touch_all = left_touch_all+right_touch_all+both_touch_all


#merge every flight to a single number
#or do i do mdeian with uncert?


#each flight compare
#percentage of no edge touch in a flight
#and the mean and std dev
no_touch_percent_all  = (no_touch_all / (no_touch_all + all_touch_all)) * 100
no_touch_mean         = np.round(np.mean(no_touch_percent_all), 3)
no_touch_stdv         = np.round(np.std(no_touch_percent_all), 3)

#percentage of yes edge touch in a flight
#and the mean and std dev
yes_touch_percent_all = (all_touch_all / (no_touch_all + all_touch_all)) * 100
yes_touch_mean        = np.round(np.mean(yes_touch_percent_all), 3)
yes_touch_stdv        = np.round(np.std(yes_touch_percent_all), 3)



#read data so i can copy and paste lol
print(f'No edge touch cases: {no_touch_mean} +- {no_touch_stdv}')
print(f'Yes edge touch cases: {yes_touch_mean} +- {yes_touch_stdv}')


#total numbers cause yeah
no_touch_total  = np.sum(no_touch_all)
yes_touch_total = np.sum(all_touch_all)
total_particles = no_touch_total + yes_touch_total

percent_no  = no_touch_total / total_particles
percent_yes = yes_touch_total / total_particles

print(f'Total particles: {total_particles}')
print(f'No edge touch cases: {percent_no}')
print(f'Yes edge touch cases: {percent_yes}')
      