#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 30 10:02:23 2025

@author: james.klinman


"""

import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np

#------------------------------------------------------------------------------
#define bin midpoints since I forgot to read them out into the output files :(
#------------------------------------------------------------------------------
hail_o_binmid = np.array(['4000', '5000', '6000', '7000', '8000', '9400',
                               '11000', '13000', '15600', '18600', '21700', '26100', 
                               '32100', '40000', '50000']).astype(np.float32) 

hail_a_binmid = np.array(['4000', '5000', '6000', '7000', '8000', '9000',
                               '10000', '11800', '14600', '19200', '24400', 
                               '31800', '42400', '50000']).astype(np.float32)#50000

hvps_o_binmid = np.array(['200', '400', '600', '800', '1000',
                               '1200', '1400', '1600', '1800', '2200', '2600',
                               '3000', '3400', '3800', '4200', '4600', '5000',
                               '6000', '7000', '8000', '9000', '10000', '15000',
                               '20000', '25000', '30000']).astype(np.float32) #30000

hvps_a_binmid = np.array(['200', '600', '1200', '1800', '2400',
                               '3000', '4000', '5000', '6000', '7000', '8000',
                               '9400', '11000', '13000', '15600', '18600', '21700', 
                               '26100', '32100', '40000', '50000']).astype(np.float32) #50000

#calculate bin midpoints
bin_midpoints = []
for probebins in [hail_o_binmid, hail_a_binmid, hvps_o_binmid, hvps_a_binmid]:
    probe_midpoints = []
    for eabin in range(probebins.shape[0]):
        if eabin == probebins.shape[0]-1:
            continue
        binsize = probebins[eabin+1] - probebins[eabin]
        midpoint = (probebins[eabin] + binsize/2) / 10000
        probe_midpoints.append(midpoint)
    bin_midpoints.append(probe_midpoints)

#------------------------------------------------------------------------------
#reading in all the data
#------------------------------------------------------------------------------
"""
filepath = "../../yr2000/f757/Code_Files_and_Outputs/Sensor_Information/"\
           + "Count_Conc_Ref_Data/20250530/20000622/"

#o stands for original, a stands for adjusted
hail_o_file1 = filepath + '240700_240900/757_PBP_Processed_HAIL-2D_original.nc'
hail_a_file1 = filepath + '240700_240900/757_PBP_Processed_HAIL-2D_adjustedbins.nc'
hail_o_file2 = filepath + '241800_242300/757_PBP_Processed_HAIL-2D_original.nc'
hail_a_file2 = filepath + '241800_242300/757_PBP_Processed_HAIL-2D_adjustedbins.nc'

hvps_o_file1 = filepath + '240700_240900/757_PBP_Processed_HVPS1_defaultbins.nc'
hvps_a_file1 = filepath + '240700_240900/757_PBP_Processed_HVPS1_adjustedbins.nc'
hvps_o_file2 = filepath + '241800_242300/757_PBP_Processed_HVPS1_defaultbins.nc'
hvps_a_file2 = filepath + '241800_242300/757_PBP_Processed_HVPS1_adjustedbins.nc'
"""

filepath1 = "../../yr1995/f670/Code_Files_and_Outputs/Sensor_Information/"\
           + "Count_Conc_Ref_Data/20250605/19950627/"

filepath2 = "../../yr2000/f757/Code_Files_and_Outputs/Sensor_Information/"\
           + "Count_Conc_Ref_Data/20250605/20000622/"

#o stands for original, a stands for adjusted
#hail_o_file1 = filepath1 + '213000_213500/670_PBP_Processed_HAIL-2D_original.nc'
#hail_a_file1 = filepath1 + '213000_213500/670_PBP_Processed_HAIL-2D_adjustedbins.nc'
#hail_o_file2 = filepath2 + '241835_241905/757_PBP_Processed_HAIL-2D_original.nc'
#hail_a_file2 = filepath2 + '241835_241905/757_PBP_Processed_HAIL-2D_adjustedbins.nc'

filepath = "../../yr2000/f757/Code_Files_and_Outputs/Sensor_Information/"\
           + "Count_Conc_Ref_Data/20250530/20000622/"

#o stands for original, a stands for adjusted
hail_o_file1 = filepath + '240700_240900/757_PBP_Processed_HAIL-2D_original.nc'
hail_a_file1 = filepath + '240700_240900/757_PBP_Processed_HAIL-2D_adjustedbins.nc'
hail_o_file2 = filepath + '241800_242300/757_PBP_Processed_HAIL-2D_original.nc'
hail_a_file2 = filepath + '241800_242300/757_PBP_Processed_HAIL-2D_adjustedbins.nc'

hvps_o_file1 = filepath1 + '213000_213500/670_PBP_Processed_HVPS1_defaultbins.nc'
hvps_a_file1 = filepath1 + '213000_213500/670_PBP_Processed_HVPS1_adjustedbins.nc'
hvps_o_file2 = filepath2 + '241835_241905/757_PBP_Processed_HVPS1_defaultbins.nc'
hvps_a_file2 = filepath2 + '241835_241905/757_PBP_Processed_HVPS1_adjustedbins.nc'



hail_o_data1 = nc.Dataset(hail_o_file1)
hail_a_data1 = nc.Dataset(hail_a_file1)
hail_o_data2 = nc.Dataset(hail_o_file2)
hail_a_data2 = nc.Dataset(hail_a_file2)

hvps_o_data1 = nc.Dataset(hvps_o_file1)
hvps_a_data1 = nc.Dataset(hvps_a_file1)
hvps_o_data2 = nc.Dataset(hvps_o_file2)
hvps_a_data2 = nc.Dataset(hvps_a_file2)



#------------------------------------------------------------------------------
#pull the counts and average them
#------------------------------------------------------------------------------

#already binned in 10s
hail_o_counts1 = hail_o_data1['counts'][:] 
hail_a_counts1 = hail_a_data1['counts'][:] 
hail_o_counts2 = hail_o_data2['counts'][:] 
hail_a_counts2 = hail_a_data2['counts'][:] 

hvps_o_counts1 = hvps_o_data1['counts'][:] 
hvps_a_counts1 = hvps_a_data1['counts'][:] 
hvps_o_counts2 = hvps_o_data2['counts'][:] 
hvps_a_counts2 = hvps_a_data2['counts'][:] 

#hail_counts averaged. sum the bins then divide by shape
#doing 10s interval average rather than all the way down to 1 second
hail_o_avg1 = np.sum(hail_o_counts1, axis=0) / hail_o_counts1.shape[0]
hail_a_avg1 = np.sum(hail_a_counts1, axis=0) / hail_a_counts1.shape[0]
hail_o_avg2 = np.sum(hail_o_counts2, axis=0) / hail_o_counts2.shape[0]
hail_a_avg2 = np.sum(hail_a_counts2, axis=0) / hail_a_counts2.shape[0]

hvps_o_avg1 = np.sum(hvps_o_counts1, axis=0) / hvps_o_counts1.shape[0]
hvps_a_avg1 = np.sum(hvps_a_counts1, axis=0) / hvps_a_counts1.shape[0]
hvps_o_avg2 = np.sum(hvps_o_counts2, axis=0) / hvps_o_counts2.shape[0]
hvps_a_avg2 = np.sum(hvps_a_counts2, axis=0) / hvps_a_counts2.shape[0]



#------------------------------------------------------------------------------
#Plot the data as individual 10s and average 10s Count Spectrum
#------------------------------------------------------------------------------

#plot individual 10s count spectrum
#----------------------------------

#Making Panels of plots for two time periods

#hail
x1 = bin_midpoints[0] #hail original
x2 = bin_midpoints[1] #hail adjusted

#hvps
x3 = bin_midpoints[2] #hvps original
x4 = bin_midpoints[3] #hvps adjusted

for t in range(hail_o_counts1.shape[0]):  #t is time interval
    fig, axes = plt.subplots(1, 2, figsize=(20, 10), sharey=True)

    fig.suptitle('Hail Spectrometer Count Comparison, June 22, 2000', fontsize=35)

    # Left panel: Counts 1
    axes[0].scatter(x1, hail_o_counts1[t], s=200, c='r', marker='.', label='Default Bins')
    axes[0].scatter(x2, hail_a_counts1[t], s=200, c='b', marker='*', label='Adjusted Bins')
    axes[0].set_title('240700–240900 Counts', fontsize=30)
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Bin Midpoints (cm)", fontsize=30)
    axes[0].set_ylabel("Counts (#)", fontsize=30)
    axes[0].set_xlim(0, 5)
    axes[0].set_ylim(1e-1, 500)
    axes[0].tick_params(labelsize=25)
    axes[0].legend(fontsize=25)
    axes[0].grid()

    # Right panel: Counts 2
    axes[1].scatter(x1, hail_o_counts2[t], s=200, c='r', marker='.', label='Default Bins')
    axes[1].scatter(x2, hail_a_counts2[t], s=200, c='b', marker='*', label='Adjusted Bins')
    axes[1].set_title('241800–242300 Counts', fontsize=30)
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Bin Midpoints (cm)", fontsize=30)
    axes[1].set_xlim(0, 5)
    axes[1].tick_params(labelsize=25)
    axes[1].legend(fontsize=25)
    axes[1].grid()

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()
    
#hvps
x3 = bin_midpoints[2] #hvps original
x4 = bin_midpoints[3] #hvps adjusted

for t in range(hvps_o_counts1.shape[0]):  #t is time interval
    fig, axes = plt.subplots(1, 2, figsize=(20, 10), sharey=True)

    fig.suptitle('HVPS1 Count Comparison, June 22, 2000', fontsize=35)

    # Left panel: Counts 1
    axes[0].scatter(x3, hvps_o_counts1[t], s=200, c='r', marker='.', label='Default Bins')
    axes[0].scatter(x4, hvps_a_counts1[t], s=200, c='b', marker='*', label='Adjusted Bins')
    axes[0].set_title('240700–240900 Counts', fontsize=30)
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Bin Midpoints (cm)", fontsize=30)
    axes[0].set_ylabel("Counts (#)", fontsize=30)
    axes[0].set_xlim(0, 5)
    axes[0].set_ylim(1e-1, 500)
    axes[0].tick_params(labelsize=25)
    axes[0].legend(fontsize=25)
    axes[0].grid()

    # Right panel: Counts 2
    axes[1].scatter(x3, hvps_o_counts2[t], s=200, c='r', marker='.', label='Default Bins')
    axes[1].scatter(x4, hvps_a_counts2[t], s=200, c='b', marker='*', label='Adjusted Bins')
    axes[1].set_title('241800–242300 Counts', fontsize=30)
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Bin Midpoints (cm)", fontsize=30)
    axes[1].set_xlim(0, 5)
    axes[1].tick_params(labelsize=25)
    axes[1].legend(fontsize=25)
    axes[1].grid()

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()
    
    
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
 
    
#10s average plots
#-----------------
#and 5min avg i think

#label font size
lfontsize = 37
xlim_right = 3
ylim_top = 1000
symbol_size = 300
figx = 20


#hail spec
fig, axes = plt.subplots(1, 2, figsize=(figx, 10), sharey=True)

fig.suptitle('Hail Spectrometer Count Comparison, June 22, 2000', fontsize=lfontsize+5)

# Left panel: Counts 1
axes[0].scatter(x1, hail_o_avg1, s=symbol_size, c='r', marker='*', label='Selected')
axes[0].scatter(x2, hail_a_avg1, s=symbol_size, c='b', marker='.', label='Alternative')
axes[0].set_title('240700–240900 Counts', fontsize=lfontsize)
axes[0].set_yscale("log")
axes[0].set_xlabel("Diameter (cm)", fontsize=lfontsize)
axes[0].set_ylabel("Counts (#)", fontsize=lfontsize)
axes[0].set_xlim(0, xlim_right)
axes[0].set_xticks(ticks=[0, 0.5, 1, 1.5, 2, 2.5, 3], labels=['0', '', '1', '', '2', '', '3'])
axes[0].set_ylim(1e-1, ylim_top)
axes[0].tick_params(labelsize=lfontsize)
axes[0].legend(fontsize=lfontsize)
axes[0].grid()

# Right panel: Counts 2
axes[1].scatter(x1, hail_o_avg2, s=symbol_size, c='r', marker='*', label='Selected')
axes[1].scatter(x2, hail_a_avg2, s=symbol_size, c='b', marker='.', label='Alternative')
axes[1].set_title('241800–242300 Counts', fontsize=lfontsize)
axes[1].set_yscale("log")
axes[1].set_xlabel("Diameter (cm)", fontsize=lfontsize)
axes[1].set_xlim(0, xlim_right)
axes[1].set_xticks(ticks=[0, 0.5, 1, 1.5, 2, 2.5, 3], labels=['0', '', '1', '', '2', '', '3'])
axes[1].tick_params(labelsize=lfontsize)
axes[1].legend(fontsize=lfontsize)
axes[1].grid()

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()

#hvps
fig, axes = plt.subplots(1, 2, figsize=(figx, 10), sharey=True)

fig.suptitle('HVPS1 Count Comparison, June 27, 1995', fontsize=lfontsize+5)

# Left panel: Counts 1
axes[0].scatter(x4, hvps_a_avg1, s=symbol_size, c='r', marker='*', label='Selected')
axes[0].scatter(x3, hvps_o_avg1, s=symbol_size, c='b', marker='.', label='Alternative')

axes[0].set_title('213000–213500 Counts', fontsize=lfontsize)
axes[0].set_yscale("log")
axes[0].set_xlabel("Diameter (cm)", fontsize=lfontsize)
axes[0].set_ylabel("Counts (#)", fontsize=lfontsize)
axes[0].set_xlim(0, xlim_right)
axes[0].set_xticks(ticks=[0, 0.5, 1, 1.5, 2, 2.5, 3], labels=['0', '', '1', '', '2', '', '3'])
axes[0].set_ylim(1e-1, ylim_top)
axes[0].tick_params(labelsize=lfontsize)
axes[0].legend(fontsize=lfontsize)
axes[0].grid()

# Right panel: Counts 2
axes[1].scatter(x4, hvps_a_avg2, s=symbol_size, c='r', marker='*', label='Selected')
axes[1].scatter(x3, hvps_o_avg2, s=symbol_size, c='b', marker='.', label='Alternative')

axes[1].set_title('241835–241905 Counts', fontsize=lfontsize)
axes[1].set_yscale("log")
axes[1].set_xlabel("Diameter (cm)", fontsize=lfontsize)
axes[1].set_xticks(ticks=[0, 0.5, 1, 1.5, 2, 2.5, 3], labels=['0', '', '1', '', '2', '', '3'])
axes[1].set_xlim(0, xlim_right)
axes[1].tick_params(labelsize=lfontsize)
axes[1].legend(fontsize=lfontsize)
axes[1].grid()

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()


#only doing the one period now
fig, axes = plt.subplots(1, 2, figsize=(figx, 10), sharey=True)

fig.suptitle('Count Comparisons', fontsize=lfontsize+5)

#left panel for hvps
axes[0].scatter(x4, hvps_a_avg1, s=symbol_size, c='r', marker='*', label='Selected')
axes[0].scatter(x3, hvps_o_avg1, s=symbol_size, c='b', marker='.', label='Alternative')

#June 27 1995,
axes[0].set_title('HVPS, 213000–213500', fontsize=lfontsize)
axes[0].set_yscale("log")
axes[0].set_xlabel("Diameter (cm)", fontsize=lfontsize)
axes[0].set_ylabel("Counts (#)", fontsize=lfontsize)
axes[0].set_xlim(0, xlim_right)
axes[0].set_xticks(ticks=[0, 0.5, 1, 1.5, 2, 2.5, 3], labels=['0', '', '1', '', '2', '', '3'])
axes[0].set_ylim(1e-1, ylim_top)
axes[0].tick_params(labelsize=lfontsize)
axes[0].legend(fontsize=lfontsize)
axes[0].grid()

#June 22 2000,
#right panel for hail spec
axes[1].scatter(x1, hail_o_avg2, s=symbol_size, c='r', marker='*', label='Selected')
axes[1].scatter(x2, hail_a_avg2, s=symbol_size, c='b', marker='.', label='Alternative')
axes[1].set_title('HS, 241800–242300', fontsize=lfontsize)
axes[1].set_yscale("log")
axes[1].set_xlabel("Diameter (cm)", fontsize=lfontsize)
axes[1].set_xlim(0, xlim_right)
axes[1].set_xticks(ticks=[0, 0.5, 1, 1.5, 2, 2.5, 3], labels=['0', '', '1', '', '2', '', '3'])
axes[1].tick_params(labelsize=lfontsize)
axes[1].legend(fontsize=lfontsize)
axes[1].grid()

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()





 
    
    
    
    
    
    
    
fig, axes = plt.subplots(1, 2, figsize=(figx, 10), sharey=True)

fig.suptitle('Count Comparisons', fontsize=lfontsize+5)

# Left panel: Counts 1
axes[0].scatter(x4, hvps_a_counts1[17], s=symbol_size, c='r', marker='*', label='Selected')
axes[0].scatter(x3, hvps_o_counts1[17], s=symbol_size, c='b', marker='.', label='Alternative')

#June 27 1995, 
axes[0].set_title('HVPS, ' + str(hvps_a_data1['time_start'][17]) +'-'+ str(hvps_a_data1['time_start'][21]), fontsize=lfontsize)
axes[0].set_yscale("log")
axes[0].set_xlabel("Diameter (cm)", fontsize=lfontsize)
axes[0].set_ylabel("Counts (#)", fontsize=lfontsize)
axes[0].set_xlim(0, xlim_right)
axes[0].set_xticks(ticks=[0, 0.5, 1, 1.5, 2, 2.5, 3], labels=['0', '', '1', '', '2', '', '3'])
axes[0].set_ylim(1e-1, ylim_top)
axes[0].tick_params(labelsize=lfontsize)
axes[0].legend(fontsize=lfontsize)
axes[0].grid()

# Right panel: Counts 2
axes[1].scatter(x4, hvps_a_counts1[20], s=symbol_size, c='r', marker='*', label='Selected')
axes[1].scatter(x3, hvps_o_counts1[20], s=symbol_size, c='b', marker='.', label='Alternative')

# June 27 1995,
axes[1].set_title('HVPS, ' + str(hvps_a_data1['time_start'][20]) +'-'+ str(hvps_a_data1['time_start'][21]), fontsize=lfontsize)
axes[1].set_yscale("log")
axes[1].set_xlabel("Diameter (cm)", fontsize=lfontsize)
axes[1].set_xlim(0, xlim_right)
axes[1].set_xticks(ticks=[0, 0.5, 1, 1.5, 2, 2.5, 3], labels=['0', '', '1', '', '2', '', '3'])
axes[1].tick_params(labelsize=lfontsize)
axes[1].legend(fontsize=lfontsize)
axes[1].grid()

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()


#hail
fig, axes = plt.subplots(1, 2, figsize=(figx, 10), sharey=True)

fig.suptitle('Count Comparisons', fontsize=lfontsize+5)

# Left panel: Counts 1
#June 22 2000, 
axes[0].scatter(x1, hail_o_counts2[19], s=symbol_size, c='r', marker='*', label='Selected')
axes[0].scatter(x2, hail_a_counts2[19], s=symbol_size, c='b', marker='.', label='Alternative')
axes[0].set_title('HS, ' + str(hail_a_data2['time_start'][19]) +'-'+ str(hail_a_data2['time_start'][20]), fontsize=lfontsize)
axes[0].set_yscale("log")
axes[0].set_xlabel("Diameter (cm)", fontsize=lfontsize)
axes[0].set_ylabel("Counts (#)", fontsize=lfontsize)
axes[0].set_xlim(0, xlim_right)
axes[0].set_xticks(ticks=[0, 0.5, 1, 1.5, 2, 2.5, 3], labels=['0', '', '1', '', '2', '', '3'])
axes[0].set_ylim(1e-1, ylim_top)
axes[0].tick_params(labelsize=lfontsize)
axes[0].legend(fontsize=lfontsize)
axes[0].grid()

#June 22 2000,
# Right panel: Counts 2
axes[1].scatter(x1, hail_o_counts2[20], s=symbol_size, c='r', marker='*', label='Selected')
axes[1].scatter(x2, hail_a_counts2[20], s=symbol_size, c='b', marker='.', label='Alternative')
axes[1].set_title('HS, ' + str(hail_a_data2['time_start'][20]) +'-'+ str(hail_a_data2['time_start'][21]), fontsize=lfontsize)
axes[1].set_yscale("log")
axes[1].set_xlabel("Diameter (cm)", fontsize=lfontsize)
axes[1].set_xlim(0, xlim_right)
axes[1].set_xticks(ticks=[0, 0.5, 1, 1.5, 2, 2.5, 3], labels=['0', '', '1', '', '2', '', '3'])
axes[1].tick_params(labelsize=lfontsize)
axes[1].legend(fontsize=lfontsize)
axes[1].grid()

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()