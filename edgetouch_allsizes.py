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

channel_mins = [4000, 5000, 6000, 7000, 8000, 9400, 11000, 13000, 15600, 18600, 
                21700, 26100, 32100, 40000, 50000]

#area ratio theshold
area_ratio = 0.3

#add percent area ratio above 0.3. then above 0.5

totals      = []
count_no  = []
count_yes = []
count_03  = []
count_05  = []

for x in range(len(flight_list)):

    #open file
    data = nc.Dataset(flight_list[x])    
    size_data = data['xsize'][:]
    edge_data = data['edgetouch'][:]
    arto_data = data['arearatio'][:]

    #total_particles_all     = []
    total_particles_channel = []

    #edge_touch_all     = []
    edge_no_channel  = [] #no edge touch
    edge_yes_channel = [] #yes it touches edge

    #above_03_all     = []
    above_03_channel = []
    
    #above_05_all     = []
    above_05_channel = []
    
    for c in range(len(channel_mins)-1): 
        
        #retrieve number of particles for each channel for each attribute
        
        total_ea_channel    = np.where( (size_data >= channel_mins[c]) &
                                        (size_data <= channel_mins[c+1]) )[0].shape[0]  

        edge_no_ea_channel  = np.where( (size_data >= channel_mins[c]) &
                                        (size_data <= channel_mins[c+1]) &
                                        (edge_data == 0) )[0].shape[0]  
            
        edge_yes_ea_channel = np.where( (size_data >= channel_mins[c]) &
                                        (size_data <= channel_mins[c+1]) &
                                        (edge_data > 0) )[0].shape[0]  
            
        ar03_ea_channel     = np.where( (size_data >= channel_mins[c]) &
                                        (size_data <= channel_mins[c+1]) &
                                        (arto_data >= 0.3) )[0].shape[0]  
        
        ar05_ea_channel     = np.where( (size_data >= channel_mins[c]) &
                                        (size_data <= channel_mins[c+1]) &
                                        (arto_data >= 0.5) )[0].shape[0]  




        total_particles_channel.append(total_ea_channel)
        
        edge_no_channel.append(edge_no_ea_channel)
        edge_yes_channel.append(edge_yes_ea_channel)
        
        above_03_channel.append(ar03_ea_channel)
        above_05_channel.append(ar05_ea_channel)


    totals.append(total_particles_channel)
    count_no.append(edge_no_channel)
    count_yes.append(edge_yes_channel)
    count_03.append(above_03_channel)
    count_05.append(above_05_channel)


#summing across all flights so that it's still per channel, but now its one 
#thing of data rather than trying to show 14

totals_all      = np.sum(np.array(totals), axis=0)
count_no_all  = np.sum(np.array(count_no), axis=0)
count_yes_all = np.sum(np.array(count_yes), axis=0)
count_03_all  = np.sum(np.array(count_03), axis=0)
count_05_all  = np.sum(np.array(count_05), axis=0)

#percentages and how many times more
percent_no_all  = np.round(((count_no_all  / totals_all) * 100), 1)
percent_yes_all = np.round(((count_yes_all / totals_all) * 100), 1)
percent_03_all  = np.round(((count_03_all  / totals_all) * 100), 1)
percent_05_all  = np.round(((count_05_all  / totals_all) * 100), 1)


    
   

#print(f'Total particles: {total_particles}')
#print(f'No edge touch cases: {percent_no}')
#print(f'Yes edge touch cases: {percent_yes}')
      