#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 11:26:28 2025

@author: james.klinman

purpose is to plot periods with times that are interesting, and to cut out the
rest of a plot
that way we can quickly look at the reflectivity plot to get 
general information about a flight
"""


"""
sketching out what i want to do

read in year
read in types of data to plot
keep it to two for now
save year
do for all years
merge all years together
"""


import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import glob

#define the min reflectivity to include
min_ref  = 20
min_plot = 20

#which version of data to plot
version_plot = '20250519'

#Read in the data
#flight_data = nc.Dataset('757_Conc_Count_Ref2.nc')
#flight_data2 = nc.Dataset('761_test_output2.nc')

#need to glob this in when going to server
#flight_list = ['757_Conc_Count_Ref2.nc', '761_test_output2.nc']
#flight_list = ['../../yr1995/f670/Code_Files_and_Outputs/Sensor_Information/670_10s_data.nc']
#flight_list = ['../../yr2000/f757/Code_Files_and_Outputs/Sensor_Information/757_10s_data.nc']

#calling in whole path to all filenames that contain the relevant data
flight_list = glob.glob('../../yr*/f*/Code_Files_and_Outputs/Sensor_Information/'
                        'Count_Conc_Ref_Data/' + version_plot +
                        '/*/*/*_PBP_Processed_*.nc')
#flight_list = ['../../yr2000/f757/Code_Files_and_Outputs/Sensor_Information/Count_Conc_Ref_Data/20250519/20000622/234840_243400/757_PBP_Processed_HAIL-2D.nc',
#               '../../yr2000/f757/Code_Files_and_Outputs/Sensor_Information/Count_Conc_Ref_Data/20250519/20000622/234840_243400/757_PBP_Processed_HAIL-1D.nc']

#get the flight numbers which gives us info on the year
flight_nums_2 = []
for f in range(len(flight_list)):
    f_num   = flight_list[f].find('/f')
    f_numss = flight_list[f][f_num+2:f_num+5]
    flight_nums_2.append(f_numss)
    
#remove duplicates
flight_nums_3 = list(set(flight_nums_2))

"""
def flight_num(file_list):
    #gets flight numbers from file names
    f_num_list = []
    for f in file_list:
        f_num = f[0:3]
        f_num_list.append(f_num)
    return f_num_list
"""

flight_numbers = flight_num(flight_list)
#hardcoding lfight dates because its easy and i don't want to add to in files
#flight_dates = ['20000622', '20000629']
#flight_dates = ['19950627']
flight_dates = ['20000622']
#flight_dates = ['19950620', '19950622', '19950627', '20000611', '20000621',
#                '20000622', '20000623', '20000629', '20020611', '20030516', 
#                '20030601', '20030726', '20030729', '20030730']

flight_num_plot = ['757']
#flight_num_plot = ['667', '668', '670', '754', '756', '757', '759', '761',
#                   '781', '798', '803', '815', '819', '820']

#it should read in the file, pull in the reflectivies
#then do the isinf and nan thing and then make a mask for everything that is nan and 2d1d<35
#and then read out that quality controlled data
def data_quality_assurance(file_list):
    """
    Parameters
    ----------
    file_list : list of strings
        The file location and name.

    Returns
    -------
    Quality assured reflectivity.

    """
    #will read in the file, replace and inf with nan, and then mask out all
    #the cases where either the 1d or 2d have a nan reflectivity, it will 
    #also mask out cases where reflectivity is <35 for the 1D and 2D to normalize
    #the data to work primarily with potential to certain hail cases.
    
    global min_ref
    
    #looping through to store reflectivities
    data_list = []
    #f is file
    for f in range(len(file_list)):
        data = nc.Dataset(file_list[f])
        data_list.append(data)
    
    ref_list = []
    #f is flight
    for f in range(len(data_list)):
        #reading in ref's
        ref_1d = data_list[f]['ref_HAIL-1D'][:]
        ref_2d = data_list[f]['ref_HAIL-2D'][:]
        
        #turning -inf's to nan
        ref_1d[np.isinf(ref_1d)] = np.nan
        ref_2d[np.isinf(ref_2d)] = np.nan
        
        #creating and applying a mask to get rid of any cases where either the 
        #1d or 2d data has a nan value. Also masks out cases where ref
        #is less than 35 for the 1d to normalize for hail cases and cases
        #with more particles.
        nanmask = ~np.isnan(ref_2d) & ~np.isnan(ref_1d) \
                & ~(ref_1d < min_ref) & ~(ref_2d < min_ref)
        ref_2d_nonan = ref_2d[nanmask]
        ref_1d_nonan = ref_1d[nanmask]    
        
        ref_list.append([ref_1d_nonan, ref_2d_nonan])
        
    return ref_list
    
reflectivities = data_quality_assurance(flight_list)  #!!!!

#do the polyfit for each individual flight
#f stands for flight
slopes = []
yints  = []
for f in range(len(reflectivities)):
    print(len(reflectivities[f][0]))
    if len(reflectivities[f][0]) == 0:
        #need to check if not reflectivities met the 35 min threshold. If so
        #have to skip or np polyfit get mad
        slopes.append(1)
        yints.append(0)
    else:
        refs = reflectivities[f]
        slope, yint = np.polyfit(refs[0], refs[1], deg=1) #hard coded to 1 degree
        slopes.append(slope)
        yints.append(yint)
    
#do polyfit for all the flights combined
#ignore error message it spits out. it still works. not sure why it gives
#error message but my best guess is that it doesn't like that its lists not 
#arrays but also this might not apply idk even know rn
#r stands for reflectivities
all_1d_refs = [r[0] for r in reflectivities]
all_2d_refs = [r[1] for r in reflectivities]

#now stacking the 1d and 2d reflectivities together
#ACTUALLY IM NOT SURE THAT THIS IS NECESSARY BUT IM KEEPING IT BC I WANT TO
all_1d_refs_flat = np.concatenate(all_1d_refs)
all_2d_refs_flat = np.concatenate(all_2d_refs)


#setting up x and y axis data now for the fits
xaxis = np.linspace(0, 70, 8) #x values for best fit
yaxis = []
#f stands for flight
for f in range(len(slopes)):#range(len(all_1d_refs)):
    y_values = slopes[f] * xaxis + yints[f]
    yaxis.append(y_values)

#all refs yaxis
slope_all, yint_all = np.polyfit(all_1d_refs_flat, all_2d_refs_flat, deg=1)
all_yaxis = slope_all * xaxis + yint_all


#then test it out with plotting all the individual flights
#then plot the suber combined flight. need to figure out a pretty and useful color scheme for this
#     i think black can be base line throuogh it all?

#plotting the individual flights and their reflectivity data
#setting up some global variables
axlims = (min_plot,70)



#f stands for flight
for f in range(len(all_1d_refs)):
    fig, ax = plt.subplots(figsize=[13.0, 10.0])
    ax.scatter(all_1d_refs[f], all_2d_refs[f], label='Reflectivity')
    ax.plot([0, 70], [0, 70], color='black', label='Slope 1 Line')
    ax.plot(xaxis, yaxis[f], color='black', label='Best Fit', linestyle=':')
    ax.set_xlim(axlims)
    ax.set_ylim(axlims)
    ax.set_xlabel('Estimated dBZ 1D', fontsize=25)
    ax.set_ylabel('Estimated dBZ 2D', fontsize=25)
    ax.set_title(f"Flight {flight_num_plot[f]}, {flight_dates[f]}", fontsize=25)  
    
    ax.tick_params(axis='both', labelsize=25)
    
    ax.grid(alpha=.4)
    ax.legend(fontsize=25, loc='upper left')
    
    #plt.show()
    plt.savefig(f"Quantitative_Folder/Flight_{flight_num_plot[f]}_{flight_dates[f]}")


#setting up colors for all the different flights
#https://matplotlib.org/stable/gallery/color/individual_colors_from_cmap.html
#color set up magically worked by copy and pasting from matplotlib docs lmao
#cmap = matplotlib.colormaps['spring']
cmap = matplotlib.colormaps['magma']
colors = cmap(np.linspace(0, 1, len(all_1d_refs)))
colors_project = [colors[0], colors[0], colors[0],
                  colors[6], colors[6], colors[6], colors[6], colors[6],
                  colors[8],
                  colors[10], colors[10],
                  colors[12], colors[12], colors[12]]
markers_project= ['o', 'o', 'o',
                  '^', '^', '^', '^', '^',
                  's',
                  'X', 'X',
                  '*', '*', '*']

fig_all, ax_all = plt.subplots(figsize=[13.0, 10.0])
#ax_all.set_title(f"All Reflectivity")
for f in range(len(all_1d_refs)):
    ax_all.scatter(all_1d_refs[f], all_2d_refs[f], \
                   label='Reflectivity, f'+flight_num_plot[f], 
                   color=colors_project[f], marker=markers_project[f])
    

ax_all.plot(xaxis, all_yaxis, label='Best Fit', color='black', linestyle=':')
ax_all.plot([0, 70], [0, 70], color='black', label='Slope 1 Line')

ax_all.set_xlim(axlims)
ax_all.set_ylim(axlims)
ax_all.set_xlabel('Estimated dBZ 1D', fontsize=25)
ax_all.set_ylabel('Estimated dBZ 2D', fontsize=25)
ax_all.set_title(f"All Flights", fontsize=25)
    




ax_all.tick_params(axis='both', labelsize=25)

ax_all.grid(alpha=.4)
ax_all.legend(fontsize=10, loc='upper left')

#plt.show()
plt.savefig(f"Quantitative_Folder/Flight_All")






#paper temp
cmap = matplotlib.colormaps['magma']
colors = cmap(np.linspace(0, 1, len(all_1d_refs)))
colors_project = [colors[0], colors[0], colors[0],
                  colors[6], colors[6], colors[6], colors[6], colors[6],
                  colors[8],
                  colors[10], colors[10],
                  colors[12], colors[12], colors[12]]
markers_project= ['o', 'o', 'o',
                  '^', '^', '^', '^', '^',
                  's',
                  'X', 'X',
                  '*', '*', '*']

fig_all, ax_all = plt.subplots(figsize=[13.0, 10.0])
#ax_all.set_title(f"All Reflectivity")
for f in range(len(all_1d_refs)):
    ax_all.scatter(all_1d_refs[f], all_2d_refs[f], \
                   label='Reflectivity, f'+flight_num_plot[f], 
                   color=colors_project[f], marker=markers_project[f])
    

ax_all.plot(xaxis, all_yaxis, label='Best Fit', color='black', linestyle=':')
ax_all.plot([0, 70], [0, 70], color='black', label='1 to 1 Line')

ax_all.set_xlim(axlims)
ax_all.set_ylim(axlims)
ax_all.set_xlabel('1D Estimated dBZ', fontsize=25)
ax_all.set_ylabel('2D Estimated dBZ', fontsize=25)
ax_all.set_title(f"1D vs 2D Estimated Reflectivity Comparison", fontsize=25)     

ax_all.tick_params(axis='both', labelsize=25)
 
ax_all.grid(alpha=.4)
ax_all.legend(fontsize=15, loc='upper left')

plt.show()
plt.savefig(f"Quantitative_Folder/Flight_All_temp")

