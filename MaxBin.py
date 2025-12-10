#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 25 09:50:44 2025

@author: james.klinman
"""

import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import glob


#which version of data to plot
version_plot = '20251006'
probe_plot   = ['HAIL-2D', 'HAIL-1D']


#calling in whole path to all filenames that contain the relevant data
flight_list = glob.glob('../../yr*/f*/Code_Files_and_Outputs/Sensor_Information/'
                        'Count_Conc_Ref_Data/' + version_plot +
                        '/*/*/*_PBP_Processed_*.nc')

#get the flight numbers which gives us info on the year
#get the flight years as well from the directory structure
flight_nums_2 = []
flight_years  = []
for f in range(len(flight_list)):
    f_num   = flight_list[f].find('/f')
    f_numss = flight_list[f][f_num+2:f_num+5]
    
    f_year  = flight_list[f].find('Ref_Data/')
    f_year2 = flight_list[f][f_year+18:f_year+22]
    
    flight_nums_2.append(f_numss)
    flight_years.append(f_year2)
    
#remove duplicates
flight_nums_3 = sorted(list(set(flight_nums_2)))
flight_years2 = sorted(list(set(flight_years)))



#get all available flight dates
flight_dates_names = glob.glob('../../yr*/f*/Code_Files_and_Outputs/Sensor_Information/'
                         'Count_Conc_Ref_Data/' + version_plot + '/*')
flight_dates = []
for f in range(len(flight_dates_names)):
    f_days = flight_dates_names[f][-8:]
    flight_dates.append(f_days)

#remove duplicates
flight_dates = sorted(list(set(flight_dates)))




#first read in flight and get main concentration data
#testing for flight 757
#Nums for them......
#23 and 22 for 815
#11 and 10 for 757


flight_data_2d = nc.Dataset(flight_list[27]) #12 and 13 are 2d 1d f757
flight_conc_2d = flight_data_2d['psd_2d_xsize']

flight_data_1d = nc.Dataset(flight_list[26]) #23 and 22 for f815
flight_conc_1d = flight_data_1d['psd_1D']


#then compare datasets
#first find percentage of cases where the following bin is larger than the preceding bin
#do for first 1-2, then 2-3, then 3-4
def compare_adjacent_bins(data, compare_low, compare_high):
    #compare smaller bin against larger bin
    all_bin_comps = []
    for t in range(len(data)):
        bin_comparisons = []
        for b in range(compare_low, compare_high):
            small_bin = data[t][b]
            big_bin   = data[t][b+1]
            
            times_larger = big_bin / small_bin
            bin_comparisons.append(times_larger)
        all_bin_comps.append(bin_comparisons)
    all_bin_comps.append(times_larger)
    
    return all_bin_comps


bin_comps_1d = compare_adjacent_bins(flight_conc_1d, 0, 3)

#print('hi')
#now i want to find where the max particle size is each type each interval
def max_bin(data1, data2):
    largest_particle_1 = []
    largest_particle_2 = []
    for t in range(len(data1)):
        #need to handle masks in my data. idk why they're there :(
        #try:
        #    if len(data1[t].mask) > 0:
                
        
        type1_nodata = np.where(data1[t] == 0)
        type2_nodata = np.where(data2[t] == 0)
        #print(type1_nodata[0] == type2_nodata[0])
        #print(type1_nodata, 'fdajklhaf')
        #figure out last data point with a value greater than 0
        skipped_locations_1 = []
        for x in range(len(type1_nodata[0])-1):
            upper = type1_nodata[0][x+1]
            lower = type1_nodata[0][x]
            diff  = upper-lower
            if diff > 1:
                skipped_locations_1.append(x)
                
        skipped_locations_2 = []
        for x in range(len(type2_nodata[0])-1):
            upper = type2_nodata[0][x+1]
            lower = type2_nodata[0][x]
            diff  = upper-lower
            if diff > 1:
                skipped_locations_2.append(x)
                
        if len(skipped_locations_1) == 0:
            skipped_locations_1.append(0)#type1_nodata[0][0])
            #print(type1_nodata)
            if len(type1_nodata[0]) == 0:
                type1_bin = len(data1[t]) - 1
            else:
                type1_bin = type1_nodata[0][skipped_locations_1[-1]]
            
        else:
            type1_bin = type1_nodata[0][skipped_locations_1[-1]+1]
            
        if len(skipped_locations_2) == 0:
            skipped_locations_2.append(0)#type2_nodata[0][0])
            if len(type2_nodata[0]) == 0:
                type2_bin = len(data2[t]) - 1
            else:
                type2_bin = type2_nodata[0][skipped_locations_2[-1]]
        else:
            type2_bin = type2_nodata[0][skipped_locations_2[-1]+1]
        
        
        #handle masks where np where originally returns an empty array
        if len(type1_nodata[0]) == 0:
            type1_bin = 0
        if len(type2_nodata[0]) == 0:
            type2_bin = 0
        
        
        #print(skipped_locations_1)#, skipped_locations_2)
        #print('breal')
        #print(type1_nodata[0], skipped_locations_1)
                
        #type1_bin = type1_nodata[0][skipped_locations_1[-1]+1]
        #type2_bin = type2_nodata[0][skipped_locations_2[-1]+1]
        #print(type1_bin, type2_bin)

        
        largest_particle_1.append(type1_bin)
        largest_particle_2.append(type2_bin)
    
    return largest_particle_1, largest_particle_2


#retrieve alrgest particles and the bin
largest_particle_1d, largest_particle_2d = max_bin(flight_conc_1d[:], flight_conc_2d[:])




#now to quickly plot the data as whole flight spectrum

#getting times for xzxis
#had chatgpt write the time thing
times_np = flight_data_2d['time_start'][:]  # load all data into memory

n = len(times_np)
indices = [0, n//4, n//2, (3*n)//4, -1]

selected_times = times_np[indices]
#print(selected_times)

time_locations = np.array([0, n//4, n//2, (3*n)//4, n])



bin_midpoints = np.array([0.45, 0.55, 0.65, 0.75, 0.87, 1.02, 1.20, 1.43, 1.71, 2.01, 2.39, 2.91, 3.60, 4.50])
bin_midpoints_plot = np.array([0.45, 0.87, 1.20, 1.71, 2.01, 2.39, 2.91, 3.60, 4.50])
#took out 0.65 and 1.43

#convert bin index locations to bin midpoints for more intuitive plotting
largest_particle_1d = np.array(largest_particle_1d, dtype=int)
largest_particle_2d = np.array(largest_particle_2d, dtype=int)

new_largest_size_1d = bin_midpoints[largest_particle_1d]
new_largest_size_2d = bin_midpoints[largest_particle_2d]


fontsize = 16
#for t in range(len(largest_particle_1d)):
fig = plt.figure(figsize=[9.0, 5.0], dpi=100)
plt.plot(new_largest_size_1d, color="black", linewidth=.75, linestyle='-', label='1D')
plt.plot(new_largest_size_2d, color="blue", linewidth=.75, linestyle='--', label='2D')
plt.yticks(bin_midpoints_plot, fontsize=fontsize-1)
plt.xticks(time_locations, labels=selected_times, rotation=45, ha='right', fontsize=fontsize-1)

plt.ylim(0.4, 5)
plt.grid(which='major', axis='y')
plt.xlabel('Time (HH:MM:SS)', fontsize=fontsize) #'10-second Intervals For Entire Flight
plt.ylabel('Largest Particle Size (cm)', fontsize=fontsize)
plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=fontsize-1)
#plt.title(f'Flight {flight_data_2d.Flight} Maximum Particle Sizes',fontsize=fontsize+2)
#plt.title(f'Flight {flight_data_2d.Flight} Maximum Particle Sizes',fontsize=fontsize+2)

plt.show()



#attempting to quickly plot the first vs second bin for 1d data
fig = plt.figure(figsize=[9.0, 5.0], dpi=100)
plt.plot(flight_conc_1d[:, 0], label='First Channel', color="black", linewidth=.75, linestyle='-')
plt.plot(flight_conc_1d[:, 1], label='Second Channel', color="blue", linewidth=.75, linestyle='--')

plt.xticks(time_locations, labels=selected_times, rotation=45, ha='right', fontsize=fontsize-1)
plt.yscale('log')
plt.grid(which='major', axis='y')
plt.yticks(fontsize=fontsize-1)

plt.xlabel('Time (HH:MM:SS)', fontsize=fontsize) #10-second Intervals For Entire Flight 
plt.ylabel(r'dN/dD (#/$m^4$)', fontsize=fontsize)
plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=fontsize-3)
#plt.title(f'Flight {flight_data_2d.Flight} 1D Hail Spectrometer Bin Comparisons', fontsize=fontsize+2)

plt.show()













#Make histogram for all






























#closing data
#flight_data_2d.close()
#flight_data_1d.close()