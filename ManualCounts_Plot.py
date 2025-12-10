#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 30 18:26:11 2025

@author: james.klinman
"""

import numpy as np
import matplotlib.pyplot as plt

#10 second count data for f757 ivan period

oned_original = np.array([13, 18, 3, 23, 36, 12, 4, 0, 1, 2, 2, 0, 0, 0])
twod_soda     = np.array([47., 28., 16.,  5.,  5.,  0.,  0.,  1.,  0.,  0.,  0.,  0.,  0.,
                          0.])

#accept all
image_wbits1         = np.array([71, 60, 32, 15, 19, 13, 5, 6, 2, 0, 2, 0, 0, 0])
image_wobits1        = np.array([100, 76, 23, 6, 13, 0, 2, 4, 0, 1, 0, 0, 0, 0])
image_nocoincidence1 = np.array([71, 46, 17, 5, 8, 0, 0, 1, 0, 0, 0, 0, 0, 0])

#reject straight line main particle
image_wbits2         = np.array([54, 43, 23, 11, 16, 10, 4, 6, 2, 0, 1, 0, 0, 0])
image_wobits2        = np.array([69, 55, 23, 6, 11, 0, 2, 3, 0, 1, 0, 0, 0, 0])
image_nocoincidence2 = np.array([54, 36, 18, 5, 6, 0, 0, 1, 0, 0, 0, 0, 0, 0])

#now add in area ratio threshold
image_wbits3         = np.array([47, 39, 17, 10, 9, 8, 2, 2, 0, 0, 0, 0, 0, 0])
image_wobits3        = np.array([65, 40, 19, 4, 4, 0, 1, 1, 0, 0, 0, 0, 0, 0])
image_nocoincidence3 = np.array([47, 31, 13, 3, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0])


#data list now
data_list1_10s = [oned_original, twod_soda, image_wbits1, image_wobits1, image_nocoincidence1]
data_list2_10s = [oned_original, twod_soda, image_wbits2, image_wobits2, image_nocoincidence2]
data_list3_10s = [oned_original, twod_soda, image_wbits3, image_wobits3, image_nocoincidence3]

all_data_lists = [data_list1_10s, data_list2_10s, data_list3_10s]


#plot data
#fig, ax = plt.subplots(figsize=[12.0, 10.0])
#plt.title('title', fontsize=30)
temp_markers = ['.', '*', '+', 'p', 'X', '+', '.', '+']
legend_labels = ['Original Counts', 'SODA Generated Counts', 'Including Satellite Particles', 'Excluding Satellite Particles', 'Excluding All Coincidence'] 

#legend_labels = ['1D Original', '2D SODA', ]

bin_midpoints = np.array([.45, .55, .65, .75, .87, 1.02, 1.2, 1.43, 1.71, 2.015, 2.39, 2.91, 3.605, 4.5])
colors = ['black', 'blue', 'red', 'green', 'orange']
"""
for y in range(len(all_data_lists)):
    fig, ax = plt.subplots(figsize=[12.0, 10.0], dpi=100)
    for x in range(len(all_data_lists[y])):
        print(x)
        zero_bins = ~(all_data_lists[y][x] == 0)
        
        ax.scatter(bin_midpoints[zero_bins], \
                    all_data_lists[y][x][zero_bins], \
                    label=legend_labels[x],s=300,
                    facecolors=colors[x], edgecolors=colors[x], marker=temp_markers[x],
                    zorder=3)
        ax.plot(bin_midpoints[zero_bins], \
                    all_data_lists[y][x][zero_bins],
                    color=colors[x], linewidth = 1.5,
                    zorder=3)
    
    #counts stuff
    try:
        #ax.set_yscale("log")
        ax.tick_params(labelsize=30)
        ax.set_ylim(bottom=0, top=105)
        ax.set_xlim(left=0.4, right=2.5)
        
        ax.set_xticks([0.5, 1, 1.5, 2, 2.5])
        ax.set_yticks([0, 20, 40, 60, 80, 100])
        
        #ax.set_yticks([1, 10, 100])
        #ax.set_xticks([1, 2, 3])
        
        ax.grid(which='both', axis='both')
        
        ax.set_xlabel("Bin Size (cm)", fontsize=30)
        ax.set_ylabel(r'Counts (#)', fontsize=30)
        ax.legend(fontsize=20)
    except:
        print('error plotting')
        
    plt.show()
    plt.clf()
"""



#calculate concentration
SV_1d = 10.4
SV_2d = 5.2
binsizes = np.array([ 1000,  1000,  1000,  1000,  1400,  1600,  2000,  2600,  3000,
                   3100,  4400,  6000,  7900, 10000]) / 10000



concs_all = []
for y in range(len(all_data_lists)):
    conc_ea = []
    for x in range(len(all_data_lists[y])):
        if x == 0:
            conc_calc= all_data_lists[y][x] / SV_1d / binsizes
        else:
            conc_calc = all_data_lists[y][x] / SV_2d / binsizes
        conc_ea.append(conc_calc)
    concs_all.append(conc_ea)
    

legend_labels = ['Original Concentration', 'SODA Generated Concentration', 'Including Satellite Particles', 'Excluding Satellite Particles', 'Excluding All Coincidence'] 
"""
for y in range(len(concs_all)):
    fig, ax = plt.subplots(figsize=[12.0, 10.0], dpi=100)
    for x in range(len(concs_all[y])):
        zero_bins = ~(concs_all[y][x] == 0)
        
        ax.scatter(bin_midpoints[zero_bins], \
                    concs_all[y][x][zero_bins], \
                    label=legend_labels[x],s=300,
                    facecolors=colors[x], edgecolors=colors[x], marker=temp_markers[x],
                    zorder=3)
        ax.plot(bin_midpoints[zero_bins], \
                    concs_all[y][x][zero_bins],
                    color=colors[x], linewidth = 1.5,
                    zorder=3)
    
    #counts stuff
    try:
        ax.set_yscale("log")
        ax.tick_params(labelsize=30)
        ax.set_ylim(bottom=0.3, top=250)
        ax.set_xlim(left=0.4, right=2.5)
        
        #ax.set_xticks([1, 2, 3])
        #ax.set_xticks([0.5, 1, 1.5, 2, 2.5])
        #ax.set_yticks([0, 20, 40, 60, 80, 100])
        
        ax.set_yticks([1, 10, 100])
        ax.set_xticks([0.5, 1, 1.5, 2, 2.5])
        
        ax.grid(which='both', axis='both')
        
        ax.set_xlabel("Bin Size (cm)", fontsize=30)
        ax.set_ylabel(r'Concentration (#/$m^4$)', fontsize=30)
        ax.legend(fontsize=20)
    except:
        print('error plotting')
        
    print(y, x)
    plt.show()
    plt.clf()
"""
"""try:

    ax.set_yscale("log")

    #ax.xticks(fontsize=40) 
    #ax.yticks(fontsize=40)  
    ax.tick_params(labelsize=30)
    ax.set_ylim(bottom=10**0, top=10000)
    ax.set_xlim(left=0, right=5)
    
    ax.set_xlabel("Bin Size (cm)", fontsize=30)
    ax.set_ylabel(r'Concentration (#/$m^4$)', fontsize=30)
    ax.legend(fontsize=25)
except:
    print('error plotting')"""
    
    
    
    
        
    
temp_markers = ['.', '*', '+', 'p', 'X', '+', '.', '+']
temp_markers = ['+', 'p', 'X']
legend_labels = ['Including Satellite Particles', 'Excluding Satellite Particles', 'Excluding All Coincidence'] 
colors = ['red', 'green', 'orange']

labels_excluding = ['Method 1', 'Method 2', 'Method 3']
titles = ['Manually Sized Particles Including Satellite Particles',
          'Manually Sized Particles Excluding Satellite Particles',
          'Manually Sized Particles Excluding Coincident Cases']

labels_excluding = ['Minimal', 'Straight Line', 'Area Ratio']
titles = ['Including Satellite Particles',
          'Excluding Satellite Particles',
          'Excluding Coincident Cases']
    
#plotting by inclusion case insetad
for x in range(2, 5):
    fig, ax = plt.subplots(figsize=[15.75, 8], dpi=100)
    for y in range(len(all_data_lists)):
        zero_bins = ~(concs_all[y][x] == 0)
        
        ax.scatter(bin_midpoints[zero_bins], \
                    concs_all[y][x][zero_bins], \
                    label=labels_excluding[y],s=300,
                    facecolors=colors[y], edgecolors=colors[y], marker=temp_markers[y],
                    zorder=3)
            
            
        ax.plot(bin_midpoints[zero_bins], \
                    concs_all[y][x][zero_bins],
                    color=colors[y], linewidth = 1.5,
                    zorder=3)
    
    zero_bins1d = ~(concs_all[0][0] == 0)
    zero_bins2d = ~(concs_all[0][1] == 0)
    ax.scatter(bin_midpoints[zero_bins1d], \
                concs_all[0][0][zero_bins1d], \
                label='1D Original', s=300,
                facecolors='black', edgecolors='black', marker='*',
                zorder=3)
        
    ax.plot(bin_midpoints[zero_bins1d], \
                concs_all[0][0][zero_bins1d],
                color='black', linewidth = 1.5,
                zorder=3)
    
    ax.scatter(bin_midpoints[zero_bins2d], \
                concs_all[0][1][zero_bins2d], \
                label='2D SODA', s=300,
                facecolors='blue', edgecolors='blue', marker='.',
                zorder=3)
        
    ax.plot(bin_midpoints[zero_bins2d], \
                concs_all[0][1][zero_bins2d],
                color='blue', linewidth = 1.5,
                zorder=3)
    
    #counts stuff
    try:
        ax.set_yscale("log")
        ax.tick_params(labelsize=25)
        ax.set_ylim(bottom=0.3, top=250)
        ax.set_xlim(left=0.4, right=2.5)
        
        #ax.set_xticks([1, 2, 3])
        #ax.set_xticks([0.5, 1, 1.5, 2, 2.5])
        #ax.set_yticks([0, 20, 40, 60, 80, 100])
        
        ax.set_yticks([1, 10, 100])
        ax.set_xticks([0.5, 1, 1.5, 2, 2.5])
        
        ax.grid(which='major', axis='both')
        
        ax.set_xlabel("Diameter (cm)", fontsize=25)
        ax.set_ylabel(r'dN/dD (#/$m^4$)', fontsize=25)
        ax.legend(fontsize=20)
        
        ax.set_title(titles[x-2], fontsize = 30)
    except:
        print('error plotting')
        
    print(y, x)
    plt.show()
    plt.clf()