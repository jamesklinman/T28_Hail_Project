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


import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt


#Read in the data
flight_data = nc.Dataset('757_test_output2.nc')

#Store reflectivities and time
time    = flight_data['time_start'][:]
ref_1d  = flight_data['ref_HAIL-1D'][:]
ref_2d  = flight_data['ref_HAIL-2D'][:]

#Manually defining time periods of interest ohhhhhhhhhh
#I can totally automate this in my code lets go
#but for now just manual
#757
periods_of_interest = [['234850', '241000'],
                       ['241730', '242300'],
                       ['242930', '243400']]
#761
#periods_of_interest = [['225830', '230000'],
#                       ['231200', '231500'],
#                       ['233350', '233630'],
#                       ['234010', '234230']]
periods_of_interest = np.array(periods_of_interest)

#Now creating a mask using the start and end times
masks_list = []
for x in periods_of_interest:
    mask_lowerbound = np.ma.masked_where(time.astype(np.int64)<int(x[0]), time.astype(np.int64))
    mask_upperbound = np.ma.masked_where(time.astype(np.int64)>int(x[1]), time.astype(np.int64))
    mask_combined = mask_lowerbound.mask == mask_upperbound.mask
    masks_list.append(mask_combined)

#combining all the masks so that only the periods of interest will show
final_mask = np.logical_or.reduce(masks_list) #chatgpt ftw found this command for me

#creating a mask to only show the first and last true value for each period
#so that I can plot it with only the first and last time so that
#it's not overwhelmed with data when plotting a whole flight
true_locs = np.where(final_mask == True)[0]
time_locs_plot = []
for x in periods_of_interest:
    for y in x:
        time_loc_to_store = np.where(time == y)[0]
        if int(y) < int(time[0]):
            time_loc_to_store = np.array([0], dtype=np.int64)
        if int(y) > int(time[-1]):
            time_loc_to_store = np.array([len(time)-1], dtype=np.int64)
        time_locs_plot.append(time_loc_to_store[0])
time_startstop_mask = np.zeros_like(time, dtype=bool)
time_startstop_mask[time_locs_plot] = True


#applying masks to the np arrays to set them up for plotting
time_masked   = np.ma.array(time, mask=~time_startstop_mask)
#time_masked   = time_masked.filled(np.nan)
ref_1d_masked = np.ma.array(ref_1d, mask=~final_mask)
ref_2d_masked = np.ma.array(ref_2d, mask=~final_mask)








#When plotting, need to be careful to explicitly show that there's a time
#gap, also to figure out how to crop the image
#Setting up the plot 
plt.figure(figsize=(16,10))

#plt.plot(time_masked, ref_1d_masked, label='HAIL1D')
#plt.plot(time_masked, ref_2d_masked, label='HAIL2D')

#plotting all data because i can't think of a good way to 
#break the data and compress it. so all the masking was pointless
plt.plot(time, ref_1d, label='HAIL1D', linestyle=':', linewidth='2.5')
plt.plot(time, ref_2d, label='HAIL2D', linestyle='-')

#ticks = time_loc_plot is how we can pick specific times to show
plt.xticks(ticks=time_locs_plot, fontsize=25, rotation=50)
plt.xlabel('Time (HHMMSS)', fontsize=25)
plt.ylabel('Estimated dBZ', fontsize=25)
plt.yticks(fontsize=25)
plt.ylim((15, 70))
plt.grid(alpha=.4)
plt.legend(fontsize=25)
plt.title('Flight 757, 06222000', fontsize=25)
plt.show()
