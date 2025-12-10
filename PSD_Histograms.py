#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  3 10:03:37 2025

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
redo_case = True



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


#organize flight lists for consistency in case glob doesn't organize ight in HVPS case
#had chatgpt make this solution. need to write thesessis
def organize_flight_files(flight_list):
    """
    Organizes flight files so that for each flight, the HVPS1 (or 2D) file 
    comes first, followed by the corresponding HAIL-1D file.

    Assumes each flight has one HAIL-1D file and one HVPS-type file.
    """
    hail_files = []
    hvps_files = []

    for f in flight_list:
        if 'HVPS1' in f:
            hvps_files.append(f)
        elif 'HVPS-2D' in f or '2D' in f:  # adjust this condition as needed
            hvps_files.append(f)
        elif 'HAIL-1D' in f:
            hail_files.append(f)

    # Sort both lists to ensure matching order
    hvps_files.sort()
    hail_files.sort()

    # Interleave HVPS/2D and HAIL-1D
    organized = [val for pair in zip(hvps_files, hail_files) for val in pair]

    return organized


flight_list = organize_flight_files(flight_list)








#first read in flight and get main concentration data
#testing for flight 757
#23 and 22 for 815 oppo for this code. organized differently i guess
#11 and 10 for 757


flight_data_2d = nc.Dataset(flight_list[22]) #12 and 13 are 2d 1d f757
flight_conc_2d = flight_data_2d['psd_2d_xsize']

flight_data_1d = nc.Dataset(flight_list[23]) #23 and 22 for f815
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




#print('hi')
#now i want to find where the max particle size is each type each interval
def max_bin(data1, data2):
    largest_particle_1 = []
    largest_particle_2 = []
    for t in range(len(data1)):
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
        
        #print(skipped_locations_1)#, skipped_locations_2)
        #print('breal')
        #print(type1_nodata[0], skipped_locations_1)
                
        #type1_bin = type1_nodata[0][skipped_locations_1[-1]+1]
        #type2_bin = type2_nodata[0][skipped_locations_2[-1]+1]
        #print(type1_bin, type2_bin)

        
        largest_particle_1.append(type1_bin)
        largest_particle_2.append(type2_bin)
    
    return largest_particle_1, largest_particle_2

#compare adjacent bins
bin_comps_1d = compare_adjacent_bins(flight_conc_2d, 0, 3)  #!!!!!!!!!!!!!!

#retrieve alrgest particles and the bin
largest_particle_1d, largest_particle_2d = max_bin(flight_conc_1d[:], flight_conc_2d[:])



#get data
data_list = []
for f in range(len(flight_list)):
    data = nc.Dataset(flight_list[f])
    data_list.append(data)
    #print(data.Probe)



#now get lists of data
conc_data_1d = []
conc_data_2d = []
#bin_data_1d = []
for f in range(len(data_list)):
    if data_list[f].Probe == 'HAIL-1D':
        conc_data_1d.append(data_list[f]['psd_1D'])
    elif data_list[f].Probe == 'HAIL-2D':
        conc_data_2d.append(data_list[f]['psd_2d_xsize'])
    

#now perform the functions on the conc data
first_1d_bin = []
second_1d_bin = []
largest_1d = []
largest_2d = []
for f in range(len(conc_data_1d)):
    #do 1d bin cpomparison
    #temp_compare_1d = compare_adjacent_bins(conc_data_1d[f], 0, 1)
    temp_first = conc_data_2d[f][:, 0] #!!!!!!!!!!!!
    temp_second = conc_data_2d[f][:, 1]
    first_1d_bin.append(temp_first)
    second_1d_bin.append(temp_second)
    
    #do 1d 2d max size
    temp_large_1d, temp_large_2d = max_bin(conc_data_1d[f][:], conc_data_2d[f][:])
    largest_1d.append(temp_large_1d)
    largest_2d.append(temp_large_2d)
    
    
    
#now get percentages on the data to prepare for histograms
#this was supposed to work for both it didn't so oh well
def find_ratio(data1, data2):
    data1_greater_list = []
    data2_greater_list = []
    data_equal_list    = []
    for x in range(len(data1)):
        data1_greater = np.where(data1[x] > data2[x])[0]
        data2_greater = np.where(data1[x] < data2[x])[0]
        data_equal    = np.where(data1[x] == data2[x])[0]
        
        num_data1 = data1_greater.shape[0]
        num_data2 = data2_greater.shape[0]
        num_equal = data_equal.shape[0]
        

        data1_greater_list.append(num_data1)
        data2_greater_list.append(num_data2)
        data_equal_list.append(num_equal)
        
        #equal is equal or nan. just a dump data
    return np.array(data1_greater_list), np.array(data2_greater_list), np.array(data_equal_list)

#number of 1d greater, 2d greater, then equal
bin_comparison_all = find_ratio(first_1d_bin, second_1d_bin)

#number of max bin 1d then 2d then equal
all_1d_max    = []
all_2d_max    = []
all_equal_max = []
for f in range(len(largest_1d)):
    oned_larger = np.where(np.array(largest_1d[f]) > np.array(largest_2d[f]))[0]
    twod_larger = np.where(np.array(largest_1d[f]) < np.array(largest_2d[f]))[0]
    data_equal  = np.where(np.array(largest_1d[f]) == np.array(largest_2d[f]))[0]
    
    all_1d_max.append(oned_larger.shape[0])
    all_2d_max.append(twod_larger.shape[0])
    all_equal_max.append(data_equal.shape[0])
    
max_comparison_all = [np.array(all_1d_max), np.array(all_2d_max), np.array(all_equal_max)]




cbf_colors= ["#000000", "#800000", "#3366CC", "#66CC99"]
fontsize = 17


#now to plot. had chatgpt make the bones of it
# Your data
group1, group2, annotations = bin_comparison_all

x = np.arange(len(group1))  # Positions for each group label ("1", "2", ..., "14")
bar_width = 0.35  # Width of each bar

fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

# Plot the first and second bars side by side
bars1 = ax.bar(x - bar_width/2, group1, width=bar_width, label='First Channel', color=cbf_colors[1])
bars2 = ax.bar(x + bar_width/2, group2, width=bar_width, label='Second Channel', color=cbf_colors[2])

# Annotate values from third array above the bars
for i, value in enumerate(annotations):
    ax.text(x[i], max(group1[i], group2[i]) + 2, str(value), ha='center', va='bottom', fontsize=fontsize-4, fontweight='bold')

# Labeling
ax.set_xticks(x)
ax.set_xticklabels(flight_nums_3, rotation=45, fontsize=fontsize)
ax.set_xlabel('Flight Number', fontsize=fontsize)
ax.set_ylabel('Total Instances', fontsize=fontsize)
ax.tick_params(axis='both', labelsize=fontsize)
ax.set_title('2D HS First vs Second Channel', fontsize=fontsize+2)
ax.grid(which='major')
ax.legend(fontsize=fontsize)

plt.tight_layout()
plt.show()



#now to plot. had chatgpt make the bones of it
# Your data
group1, group2, annotations = max_comparison_all

x = np.arange(len(group1))  # Positions for each group label ("1", "2", ..., "14")
bar_width = 0.35  # Width of each bar

fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

# Plot the first and second bars side by side
bars1 = ax.bar(x - bar_width/2, group1, width=bar_width, label='1D', color=cbf_colors[1])
bars2 = ax.bar(x + bar_width/2, group2, width=bar_width, label='2D', color=cbf_colors[2])

# Annotate values from third array above the bars
for i, value in enumerate(annotations):
    ax.text(x[i], max(group1[i], group2[i]) + 2, str(value), ha='center', va='bottom', fontsize=fontsize-4, fontweight='bold')

# Labeling
ax.set_xticks(x)
ax.set_xticklabels(flight_nums_3, rotation=45, fontsize=fontsize)
ax.set_xlabel('Flight Number', fontsize=fontsize)
ax.set_ylabel('Total Instances', fontsize=fontsize)
ax.tick_params(axis='both', labelsize=fontsize)
ax.set_title('1D vs 2D HS Largest Particle', fontsize=fontsize+2)
ax.grid(which='major')
ax.legend(fontsize=fontsize)

plt.tight_layout()
plt.show()

