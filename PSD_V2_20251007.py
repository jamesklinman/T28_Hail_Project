#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 13:40:33 2025

@author: jamesklinman
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#from matplotlib.collections import PatchCollection
#from matplotlib.patches import Rectangle
import math
import netCDF4
from datetime import date
import pickle
import json
import re
from statistics import mode, stdev
#import statistics 
#import scipy
#import sympy as sy
import xarray as xr
import glob
import stat
import matplotlib
import gc



#-
#everything in the read in section might be useless but 
#i dont want to deal with not having it it since
#im copying an pasting so much code
#-



#------------------
#self defining stuff
#------------------

#all this stuff needs to go in config file
units = 'meter'
specified_timezone = 'utc' #'utc'  #could be local or utc
                            #for the time specified in config file or at start here
                            #local for 1995 flights and utc for 2000 flights
                            

#specifying different rejections                    
rejection_flags_accept = [0, 4]#, 8]#, 4]      
reject_below_arearatio = 0.3

#adding options for area ratio
area_ratio_indv_check = True #true for different area ratios for different datasets
area_ratio_indv = [0.3, 0.3, 0.5] #leave empty if option is false
#must be in same order as files 
#put None for files that aren't processed by soda

#These flights have startimes after midnight. For some reason the code prefers
#when these are marked in a new day eg... 241830 would become 001830. HOWEVER
#the disp files aren't always reset to a new day, so they might start and run
#over or already be over 240000. For some reason this is different for different
#cases with both SODA and DISP files. I'm not sure why. I'm too lazy to actually
#look into it futher. But, for the flights where this is an issue, they are noted
#and the program just subtracts 86400 from the flight time in seconds when
#finding the start and end index in the array for the disp file. It's a quick 
#and easy manual fix. Not automatic but whatever at this point.
#If other datasets are to be processed, this may need to be updated
starts_after_midnight_list = ['781', '759', '756']
flight_timezone_probe_mismatch = []#['670']#[]#['670'] #i think this is only if including hvps
flight_timezone_probe_mismatch_668 = False #for when inluding hvps  seems to also be needed for 670?
probe_local_to_utc_all = [['HAIL-2D', 'HAIL-1D']]

plot_hvps_case = False #should only be needed for flightt 668 in conjunction iwth timezone mismatch

#options are 'diam', 'xsize', 'ysize', 'xextent', 'areasize' for \/
sizes_to_plot = ['diam', 'xsize', 'ysize', 'areasize', 'xextent'] #xextent not included rn it was excluded in the below chunk where it reads in the files as well. like do a ctrl f and search for all xextent to verify
#sizes_to_plot = ['xsize']
             
#true means exclude particles that aren't all in
#to include all in counts, need to adjust rejection flag accepts above
use_all_in = True
        
#10s sliding interval that gives biggest uncertainty in time dimension
#!!! IIf using, I recommend adding 10 seconds to both the start and end time 
plot_sliding_uncertainty = False


#plotting 4 panel figure with biggest, poisson, sizing, and alongtrack uncertainties
plot_uncertainties = False

#choice for if you want to make plots with fits
plot_fits = True


#set dpi
#lower is recommended if doing entire flights.
#100 will run significantly faster than 300
dpi = 100


plot_mean_check = False  #For calculating average values of all the probes and plotting
                         #this only works if all probes files are from the same probe
                         #or at the very least if you're mixing probes, then 
                         #they need to have the same number of channels
plot_mean_datarange_check1 = False #fill in area between max and min
plot_mean_datarange_check2 = False #error bar between max and min

plot_poisson_errorbars = True #true for plot and false for not
#plot_errorbars_filled = False
#plot_errorbars_filled_both_axes = False
#plot_poisson_and_stddev_errorbars = False

plot_largest_uncertainty = False #!!! best error plotitng optin

plot_log_scale = True

#uhh idk when this is needed but it's needed for some
#can confirm it's not needed for f757
#why. why didn't i comment what flights this line is supposed to be for
adjust_plottime = False #!!!!!!!!!!!!!!!


force_manual_plot_setup = False #for editing the plot
force_yaxis = None  #not developed
force_xaxis = None  #not developed
force_title = None  #not developed
force_ylabel = None #not developed
force_xlabel = None #not developed
force_legend = None #not developed

corr_fac = 1#.1#.1 #!!!!!
active_time = 5 #!!!!!!


diode_size_SPEC = .0009 #.9mm to meter
diode_size_HVPS = .0002 #.2mm -xres  or .8mm-yres to meter
diodes_1DSPEC = 128
diodes_2DSPEC = 64
diodes_HVPS = 190 #256     #190 is how much soda uses
length_SPEC_u = 0.9# 0.9 to match field     .93#.93 #meters    #.99 is from soda
length_SPEC_s = 0.9# 0.9 is expected reading theses     .99#soda version
length_HVPS = .2 #meters
Area_1DSPEC = diode_size_SPEC * diodes_1DSPEC * length_SPEC_u
Area_2DSPEC = diode_size_SPEC * diodes_2DSPEC * length_SPEC_u
Area_HVPS = diode_size_HVPS * diodes_HVPS * length_HVPS

#SA_1D = .0009 * 128 * .93  #diode size in m * diode number * length of probe
#SA_2D = .0009 * 64 * .93


Area_2DC = 0.000025 * 25 * 0.061



#--------------------------------
#reading in config file information

#make a switch that either true for import from config file or false 
#for input by self !!!!!!!!!!!!
#--------------------------------



#getting flight num
#------------------
flight_programs_file = 'Param_Info/File_Runner_Info.txt'
flight_programs_info = pd.read_csv(flight_programs_file, sep=' * ', engine='python')
with open(flight_programs_file, 'r') as file:
    flight_programs_info = file.read()  
flight_programs_info = json.loads(flight_programs_info)
flight_num = str(flight_programs_info['flight_num'][0])

#can get flight num from sys.argv by including in subprocess run instead
#is treated like command line argument
#flight_num = sys.stdin.read().strip()   #comment out if running manually rather than from file_runner.py
print('F L I G H T N U M ', flight_num)
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
flight_num = '815'

#file running files
#------------------
paramInfo = 'Param_Info/' + flight_num + '_paramInfo.txt'
indexInfo = 'Param_Info/Indexs/Flight_' + flight_num + '_Indexs.pkl'
iteration_track_file = 'Automated_Files/Iteration_Tracker.txt'



#getting path to save file
#------------------------
filepath_file = 'Random/filepaths.json'
with open(filepath_file, 'r') as file:
    filepaths = file.read()  
filepaths = json.loads(filepaths)
for year in filepaths:
    for flight in filepaths[year]:
        if flight_num in flight:
            path_to_flight = flight
flightpath = path_to_flight + '/' + flight_num + '.nc'
path_to_folder = path_to_flight + '/Code_Files_and_Outputs/'

#Calling and reading in plane files for data and naming information
#-----------------------------------------------------------------
TASfilename = path_to_folder + 'Sensor_Information/HHMMSS_True_Calc_Airspeed_'\
               + flight_num + '.txt'
planefile = flightpath

#TASfilename = 'HHMMSS_True_Calc_Airspeed_761.txt'
#planefile = '761.nc'
#TASfilename = '../../Flight_Data/yr2000/HHMMSS_True_Calc_Airspeed_' + flight_num + '.txt'
#planefile = '../../Flight_Data/yr2000/T28_STEPS2000_' + flight_num + '.nc'

TASfile = pd.read_csv(TASfilename, sep=' * ', dtype={'HHMMSS': str}, engine='python')
airplanedata = netCDF4.Dataset(planefile)

#Getting the flight data and other data for file naming and plot title making.
#Needed up here since SODA file names require date
#-----------------------------------------------------------------------------
FlightNum = str(getattr(airplanedata, 'FlightNumber'))

FlightDate = str(getattr(airplanedata, 'FlightDate'))
FlightDateSplit = FlightDate.split('/')
FlightDate = FlightDateSplit[2]+''+FlightDateSplit[0]+''+FlightDateSplit[1]
FlightDate_File = FlightDateSplit[0]+''+FlightDateSplit[1]+''+FlightDateSplit[2]

FlightTime = str(getattr(airplanedata, 'TimeInterval'))
FlightTimeStart = str(FlightTime)[0:8]
FlightTimeStart = FlightTimeStart.split(':')
FlightTimeStart = FlightTimeStart[0] + FlightTimeStart[1] + FlightTimeStart[2]

#duplicate method not used anywhere else i think 
#!!!
plane_time_start = getattr(airplanedata, 'TimeInterval')[0:8]
for char in plane_time_start:
    if char == ':':
        plane_time_start = plane_time_start.replace(':', '')

#Calling start and end time before reading in the 
#rest of the files since they're time dependent
#------------------------------------------------
initParameters = pd.read_csv(paramInfo, sep=' * ', engine='python')
with open(paramInfo, 'r') as file:
    initParameters = file.read()  
initParameters = json.loads(initParameters)

iterationTracker = pd.read_csv(iteration_track_file, sep=' * ', engine='python')
with open(indexInfo, "rb") as file:   # Unpickling
   indexs = pickle.load(file)


time_index_to_use = iterationTracker['Iteration'][0]# * \
    #iterationTracker['Skip_Num'][0]
#time_index_to_use =  0                                      #  to only do first one. 

#this updated version is not mutlitple time compatible yet
#!!!        
#final temporal resolution of particle size distribution
TimeResolution = int(initParameters['PSD_Time_Res'][0])

starttime = str(initParameters['Time_Start'][time_index_to_use])
endtime = str(initParameters['Time_End'][time_index_to_use])
timeZone = int(initParameters['Timezone_true'][0])


  
#Time relevant definitions
#------------------------
    
def forceHHMMSS(data):
    #ISSUE, this probably only effective for the HH
    if type(data) is int or type(data) is str:
        if len(str(data)) != 6:
            if len(str(data)) == 5:
                HHMMSS = '0' + str(data)
            if len(str(data)) == 4:
                HHMMSS = '00' + str(data)
            if len(str(data)) == 3:
                HHMMSS = '000' + str(data)
            if len(str(data)) == 2:
                HHMMSS = '0000' + str(data)
            if len(str(data)) == 1:
                HHMMSS = '00000' + str(data)
        elif len(str(data)) == 6:
            HHMMSS =str(data)
        return HHMMSS
    elif type(data) is list:
        datalist = []
        for entry in data:
            if type(entry) is int or type(entry) is str:
                if len(str(entry)) != 6:
                    if len(str(entry)) == 5:
                        HHMMSS = '0' + str(entry)
                        datalist.append(HHMMSS)
                    if len(str(entry)) == 4:
                        HHMMSS = '00' + str(entry)
                        datalist.append(HHMMSS)
                    if len(str(entry)) == 3:
                        HHMMSS = '000' + str(entry)
                        datalist.append(HHMMSS)
                    if len(str(entry)) == 2:
                        HHMMSS = '0000' + str(entry)
                        datalist.append(HHMMSS)
                    if len(str(entry)) == 1:
                        HHMMSS = '00000' + str(entry)
                        datalist.append(HHMMSS)
                elif len(str(entry)) == 6:
                    HHMMSS =str(entry)
                    datalist.append(HHMMSS)
        return datalist


def HHMMSS_adjustHH(time, adjust_amount):
     #changes the HH value by the amount specified
     newhour = int(str(time)[0:2]) + adjust_amount
     newtime = str(newhour) + str(time)[2:6]
     return newtime


def HHMMSS_2_SS(time):
    #Assumes HHMMSS format. No Decimal. No colons. Should be str
    #assumes time is a string of a value
    
    HH = (int(time[0:2]) * 3600)#get HH and converts to sec
    MM = (int(time[2:4]) * 60)
    SS = (int(time[4:6]))
    time_sec = HH + MM + SS

    return(time_sec)

       
def time_timezoneadjusted(time, timezone, hours_adjust):
    if timezone == 'utc':
        timeout = time
    elif timezone == 'local':
        timeout = HHMMSS_adjustHH(time, hours_adjust)  
        timeout = forceHHMMSS(timeout)
        
    return timeout


def seconds_HHMMSS(time):
    #takes interger values, not strings. idk if floats work
    #floats do not work as it makes the seconds default to 0
    #okay now 
    try: 
        decimal = str(time).split('.')[1][:5] #saves decimal out to 5 places
    except:
        decimal = ''
    time = int(float(time))
    HH = str(math.floor(time/3600))
    temp = time % 3600
    MM = str(math.floor((temp/60)))
    SS = str(temp%60)
    #print(HH, MM, SS)
    if len(HH) != 2:
        if len(HH) == 1:
            HH = str(0) + HH
        else:
            HH ='00'
    if len(MM) != 2:
        if len(MM) == 1:
            MM = str(0) + MM
        else:
            MM ='00'
    if len(SS) != 2:
        if len(SS) == 1:
            SS = str(0) + SS
        else:
            SS ='00'
            
    if decimal == '':
        final_time = str(HH+MM+SS)
    else:
        final_time = str(str(HH+MM+SS)+'.'+str(decimal))
    return final_time


def HHMMSS_adjust(time, adjust_amount, adjust_type):
    #adjust type is 's' 'm' or 'h' S M H work too
    #does not work with fractions of a second
    
    adjust_amount = int(adjust_amount)
    
    if type(time) == int:
        time = str(time)
    elif type(time) == float:
        time = str(int(time))
    elif type(time) == str:
        pass
    elif type(time) == list:
        print('Time should be single variable not a list')
        return

    temp_SS = int(time[4:6])
    temp_MM = int(time[2:4])
    temp_HH = int(time[0:2])

    if adjust_type == 's' or adjust_type == 'S':
        temp_SS = temp_SS + adjust_amount
    elif adjust_type == 'm' or adjust_type == 'M':     
        temp_MM = temp_MM + adjust_amount
    elif adjust_type == 'h' or adjust_type == 'H':     
        temp_HH = temp_HH + adjust_amount

    while temp_SS >= 60:
        temp_MM = temp_MM + 1
        temp_SS = temp_SS - 60
    while temp_MM >= 60:
        temp_HH = temp_HH + 1
        temp_MM = temp_MM - 60
        
    temp_SS = str(temp_SS)
    temp_MM = str(temp_MM)
    temp_HH = str(temp_HH)
    if len(temp_SS) != 2:
        temp_SS = '0' + temp_SS
    if len(temp_MM) != 2:
        temp_MM = '0' + temp_MM
    if len(temp_HH) != 2:
        if len(temp_HH) > 2:
            pass
        elif len(temp_HH) < 2:
            temp_HH = '0' + temp_HH
    
    final_time = temp_HH + temp_MM + temp_SS
    return final_time












#-
#Okay now to read in the data files
#

#!!!!
#must name which day you want to read in files from
date_processed = '20251006'


path_to_proccessed_data = '../../yr' + FlightDate[0:4] + '/f' + FlightNum + \
                           '/Code_Files_and_Outputs/Sensor_Information/Count_Conc_Ref_Data/' +\
                           date_processed + '/' + FlightDate + '/' + starttime + '_' + endtime + '/'

filename_1DHAIL = path_to_proccessed_data + FlightNum + '_PBP_Processed_HAIL-1D.nc'     
filename_2DHAIL = path_to_proccessed_data + FlightNum + '_PBP_Processed_HAIL-2D.nc'

filename_list = [filename_1DHAIL, filename_2DHAIL]
#filename_list = [filename_1DHAIL]

data = []
for p in range(len(filename_list)):
    data.append(netCDF4.Dataset(filename_list[p]))          

#single variable

interval_starttime = data[0]['time_start'][0]
interval_endtime   = HHMMSS_2_SS(data[0]['time_start'][-1])
interval_endtime   = seconds_HHMMSS(interval_endtime + 10)
starttime_HHMMSS   = data[0]['time_start'][:]
endtime_HHMMSS     = [seconds_HHMMSS(HHMMSS_2_SS(x)+10) for x in data[0]['time_start'][:]] #will need adjusting at the individual level

if adjust_plottime == True:
    #adding 6 hours for flight 670
    for x in range(len(starttime_HHMMSS)):
        starttime_HHMMSS[x] = HHMMSS_adjustHH(starttime_HHMMSS[x], 6)
        endtime_HHMMSS[x] = HHMMSS_adjustHH(endtime_HHMMSS[x], 6)

#separate for both maybe
dataframes_types         = []
dataframes_probename     = []
dataframes_bin_midpoints = []
dataframes_binsize       = []
    
dataframes_normalized_conc  = []
dataframes_conc_uncertainty = []


for p in range(len(filename_list)):
    """
    if data[p].Probe == "HAIL-1D":
        
    elif data[p].Probe == 'HAIL-2D':
        
    """
    if data[p].Probe == "HAIL-1D":
        dataframes_probename.append("HAIL-1D")
        dataframes_types.append(2)
        
        dataframes_normalized_conc.append(data[p]['psd_1D'][:])
        dataframes_conc_uncertainty.append(data[p]['psd_1D_uncertainty'])
        
 
        
    elif data[p].Probe == 'HAIL-2D':
        dataframes_probename.append("HAIL-2D")
        dataframes_types.append(4)
        
        dataframes_normalized_conc.append(data[p]['psd_2d_xsize'][:])
        dataframes_conc_uncertainty.append(data[p]['psd_2d_xsize_uncertainty'])
        
        
    mid = data[p]['bin_startpoints'][:].astype(np.float32) + (data[p]['bin_size'][:].astype(np.float32)/2)
    dataframes_bin_midpoints.append(mid)
    
    #size = data[p]['bin_size'][:]
    dataframes_binsize.append(data[p]['bin_size'][:])

dataframes_types         = np.array(dataframes_types)
dataframes_probename     = np.array(dataframes_probename)
dataframes_bin_midpoints = np.array(dataframes_bin_midpoints)
dataframes_binsize       = np.array(dataframes_binsize)
    
dataframes_normalized_conc  = np.array(dataframes_normalized_conc)
dataframes_conc_uncertainty = np.array(dataframes_conc_uncertainty)






    
#----------------------------------------
#Creating directory structure
#!!!This is for the scripting. need to make it optional that if run from command
#line it doesn't require all this and makes the plot in a specfied directory or the current direcotry
#----------------------------------------
dataframes_probename

print('made it here pls')
#generating a starttime and endtime for the folder name

interval_starttime = starttime_HHMMSS[0]
interval_endtime = endtime_HHMMSS[-1]

FlightNum = str(getattr(airplanedata, 'FlightNumber'))
FlightDate = str(getattr(airplanedata, 'FlightDate'))
FlightDate = FlightDate.split('/')
FlightDate = FlightDate[2]+''+FlightDate[0]+''+FlightDate[1]

current_date = date.today()
file_created_date = current_date.strftime("%Y%m%d")


main_pathway_plot = path_to_folder + 'PSD_Plots/'\


main_pathway_plot2 = main_pathway_plot + 'PSD_Plots/'
if os.path.exists(main_pathway_plot2) is False:   
    os.mkdir(main_pathway_plot2)

main_pathway_plot3 = main_pathway_plot2 + file_created_date
if os.path.exists(main_pathway_plot3) is False:   
    os.mkdir(main_pathway_plot3)

main_pathway_plot4 = main_pathway_plot3 + '/' +str(FlightDate) + '/'
if os.path.exists(main_pathway_plot4) is False:   
    os.mkdir(main_pathway_plot4)

main_pathway_plot5 = main_pathway_plot4 + str(interval_starttime) + '_' + str(interval_endtime) +'/'
if os.path.exists(main_pathway_plot5) is False:   
    os.mkdir(main_pathway_plot5)
    


pathname_plots = main_pathway_plot5
        


#new pathways for fit plots
main_pathway_plot6 = main_pathway_plot5 + 'Fit_Plots' +'/'
if os.path.exists(main_pathway_plot6) is False:   
    os.mkdir(main_pathway_plot6)

#new pathways for each uncertainty plots
main_pathway_plot7 = main_pathway_plot5 + 'UncertaintyType_Plots' +'/'
if os.path.exists(main_pathway_plot7) is False:   
    os.mkdir(main_pathway_plot7)








#----------------------------------------
#
#Plotting the data and making data tables
#
#----------------------------------------






#plot the uncertainty types 4panel plot
def retrieve_uncertainty_upperlower(data, all_upper_uncertainty, 
                                    all_lower_uncertainty, 
                                    spatial_upper, 
                                    spatial_lower, 
                                    poisson_upper, 
                                    poisson_lower, 
                                    sizing_upper, 
                                    sizing_lower):
    #biggest is only for one type of uncertainty, not the biggest possible
    biggest_plus  = np.array(all_upper_uncertainty) - np.array(data)
    biggest_minus = np.array(data)                  - np.array(all_lower_uncertainty)
    poisson_plus  = np.array(poisson_upper)         - np.array(data)
    poisson_minus = np.array(data)                  - np.array(poisson_lower)
    sizing_plus   = np.array(sizing_upper)          - np.array(data)
    sizing_minus  = np.array(data)                  - np.array(sizing_lower)
    spatial_plus  = np.array(spatial_upper)         - np.array(data)
    spatial_minus = np.array(data)                  - np.array(spatial_lower)
    
    #clip anything below zero since cant do a matplotlib uncertainty thats negative
    biggest_plus[biggest_plus < 0]     = 0
    biggest_minus[biggest_minus < 0]   = 0
    
    poisson_plus[poisson_plus < 0]     = 0
    poisson_minus[poisson_minus < 0]   = 0
    
    sizing_plus[sizing_plus < 0]       = 0
    sizing_minus[sizing_minus < 0]     = 0
    
    spatial_plus[spatial_plus < 0]     = 0
    spatial_minus[spatial_minus < 0]   = 0
    
    return (biggest_plus, biggest_minus, poisson_plus, poisson_minus,
           sizing_plus, sizing_minus, spatial_plus, spatial_minus)

def plot_all_uncertainties(data, uncertainties, bins, interval, 
                           probeindex, mask):
    #probeindex should be a index, not the actual probetype value
    #bins and data should be read in for the specific probe and interval
    #inclduing the bins to not plot because of nan or 0 or issues
    try:
        fig2, axs = plt.subplots(2, 2)
        fig2.suptitle(f'{plot_times_final_s[y]} - {plot_times_final_f[y]}', fontsize=30)
        fig2.set_figheight(17.5)
        fig2.set_figwidth(18)
        
        #set up titles
        titles = ['Biggest Uncertainty', 'Poisson Uncertainty', 'Sizing Method Uncertainty', 'Along-Flight Track Uncertainty']
        for axes2, title in zip(axs.flat, titles):
            axes2.set_yscale('log')
            axes2.set_ylim(0.1, 1000)
            axes2.grid(True, which='both', linestyle='--', linewidth=0.5)
            axes2.set_title(title, fontsize=30)
            axes2.scatter(bins, data[probeindex][interval], color='black')
            
            axes2.tick_params(labelsize=20)
            
            axes2.set_xlabel("Bin Size (cm)", fontsize=20)
            axes2.set_ylabel(r'Concentration (#/$m^4$)', fontsize=20)
        
        #axs[0,0].scatter(bins, data[probeindex][interval])
        #axs[0,1].scatter(bins, data[probeindex][interval])
        #axs[1,0].scatter(bins, data[probeindex][interval])
        #axs[1,1].scatter(bins, data[probeindex][interval])
        
        #+0.0000001 in case the error is 0. i think it got angry in the past
        #lower then upper error
        axs[0,0].errorbar(bins, 
                     data[probeindex][interval]+0.000000001, 
                     yerr=(uncertainties[1][probeindex][interval], 
                           uncertainties[0][probeindex][interval]), 
                     ecolor='black', ls='none', capsize=4, elinewidth=1,
                     zorder=2)
        axs[0,1].errorbar(bins,
                     data[probeindex][interval]+0.000000001, 
                     yerr=(uncertainties[3][probeindex][interval], 
                           uncertainties[2][probeindex][interval]), 
                     ecolor='black', ls='none', capsize=4, elinewidth=1,
                     zorder=2)
        axs[1,0].errorbar(bins, 
                     data[probeindex][interval]+0.000000001, 
                     yerr=(uncertainties[5][probeindex][interval], 
                           uncertainties[4][probeindex][interval]), 
                     ecolor='black', ls='none', capsize=4, elinewidth=1,
                     zorder=2)
        axs[1,1].errorbar(bins, 
                     data[probeindex][interval]+0.000000001, 
                     yerr=(uncertainties[7][probeindex][interval], 
                           uncertainties[6][probeindex][interval]), 
                     ecolor='black', ls='none', capsize=4, elinewidth=1,
                     zorder=2)
        
        #fig2.show()
        fig2.savefig(main_pathway_plot7 +\
                          str(str(plot_times_final_s[y]) +'_'+ \
                          str(plot_times_final_f[y])) + \
                          str(dataframes_probename[x]) + '.png', dpi=dpi)#, bbox_inches = 'tight')
    except Exception as e:
        print(f"Error in plot_all_uncertainties: {e}")
    finally:
        # CRITICAL: Always close the figure, even if there's an error
        plt.close(fig2)
        del fig2  # Explicitly delete the figure object

def estimate_fit_coef(x, y, mask):
    #number of observations/points
    #don't invert yet for operations
    mask_nan = np.isnan(y)
    mask_uncert = mask

    mask_combined = mask_nan + mask_uncert
    #invert now so that trues allow good data to be used
    mask_combined = ~mask_combined
    
    #  print(mask_nan, 'hi',  mask_uncert, 'hi',  mask_combined)
    
  
    #using formula m = sum((x - xbar)(y - ybar)) / sum((x - xbar)^2)
    #c = ybar - m*xbar
  
    xbar = np.mean(x[mask_combined])
    ybar = np.mean(y[mask_combined])
    
    top_part    = np.sum((x[mask_combined] - xbar) * (y[mask_combined] - ybar))
    bottom_part = np.sum((x[mask_combined] - xbar)**2)
    
    slope = top_part / bottom_part
    
    yint = ybar - slope*xbar
    
    xint = -yint / slope
    
    #total sum of squares
    tss = np.sum((np.exp(y[mask_combined]) - np.exp(ybar))**2)

    return (yint, slope, xint, tss, mask_combined)

def plot_regression_line(xvals, yvals, b, color, marker, probe, cutoffbin, probenum, ax, mask):
    #generating different marker sizes for if data was used or not
    # from chatgpt -> Map True → 200, False → 50
    marker_sizes = np.where(mask, 300, 150)
    alphas = np.where(mask, 1.0, 0.5)   # Fully opaque for valid, more transparent for invalid
    
    #predicted response vector
    y_pred = b[0] + b[1]*xvals
    
    #residual sqaure sum thing
    rss = np.sum((yvals[mask] - np.exp(y_pred[mask]))**2)
    #print(yvals[mask], y_pred[mask])
    r_squared = 1 - rss/b[3] #b[3] is tss
    #print(tss, rss)
    
    
    #making label including information/fit information
    if dataframes_probename[probenum] == 'HAIL-1D':
        pname = 'HS 1D'
    elif dataframes_probename[probenum] == 'HAIL-2D':
        pname = 'HS 2D'
    label_new = f"{pname}: y-int: {round(b[0], 2)}\n" +\
                f"            slope = {round(b[1], 2)}\n"+\
                f"            $R^2$: {round(r_squared, 2)}"
    
    #plotting the actual points as scatter plot
    ax.scatter(xvals, yvals, color = color,
                marker=marker, s=marker_sizes,
                label=label_new, alpha=alphas)

   

    #plotting the regression line
    ax.plot(xvals, np.exp(y_pred), color = color)
            
    #plotting fit information
    #got rid of an am moving into legend
    """props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    fit_information = f"{probe}: y-int: {round(b[0], 2)} \n$R^2$: {round(r_squared, 2)}\n" +\
                      f"slope: {round(b[1], 4)}" +\
                      f"\nFirst 67% error bin: {cutoffbin}"
    ax.text(
        0.97, 0.65 - (0.24 * probenum),  # Adjust y-position to avoid overlap
        fit_information,
        transform=axfit.transAxes, fontsize=20,
        verticalalignment='center', horizontalalignment='right',
        bbox=props)"""


    
def create_uncertainty_probetype_mask(data, uncert, probetype):
    #using poisson uncertainty of sqrt(data),
    #mask bins with uncertainty higher than 67%
    
    #get percentage of data vs uncertiant   
    uncert_percentage = uncert / data
    
    #turn nan into 1 so that np where works
    uncert_percentage2 = np.nan_to_num(uncert_percentage, nan=1, posinf=1, neginf=1)
    
    #find locations of uncertainty greater than 67%
    #first get mask locations
    temp = np.where(uncert_percentage2 >= 0.67)[0]#0.67)[0]
    
    #now mask a binary array using locations
    mask_array = np.zeros(len(uncert_percentage2), dtype=bool)
    mask_array[temp] = True
               
    mask_uncert = mask_array           
    
    mask_uncert = np.array(mask_uncert)
    
    
    #now do probetype mask. should only be necessary for 1D probe
    #hardcoding which bins to ignore
    if probetype == 2: #disp case
        #ignore first 1d bin
        mask_array2 = np.zeros(len(uncert_percentage2), dtype=bool)
        mask_array2[0] = True

    if probetype == 4: #soda pbp case
        mask_array2 = np.zeros(len(uncert_percentage2), dtype=bool)    

    
    #combining masks
    mask_uncert = mask_uncert + mask_array2
    
    #temp[0] should be the first location of the 67% bin
    return mask_uncert, temp[0]+1





plot_times_final_s = starttime_HHMMSS
plot_times_final_f = endtime_HHMMSS

#!!!   a point where it's not generalized
legend_labels = dataframes_probename
legend_labels = ['Hail-2D, Xsize', 'Hail-2D, Xsize, Allin', 'Hail-2D, Circlefit', 'Hail-2D, Circlefit, Allin', 'Hail-1D, Xsize?']
legend_labels = ['HVPS1, Circlefit', 'HVPS1, Circlefit, Allin']
legend_labels = ['HVPS1, Circlefit', 'Hail-2D, Xsize', 'Hail-2D, Circlefit', 'Hail-1D, Xsize']
legend_labels = ['HVPS1, Circlefit', 'Hail-2D, Xsize', 'Hail-1D, Xsize']
legend_labels = ['HVPS1, Circlefit', 'Hail-2D, Xsize']
legend_labels = ['HVPS1, Circlefit', 'Hail-2D, Xsize', 'HVPS1, Circlefit, CONC', 'DISP']
legend_labels = ['HVPS1, ADPAA', 'Hail-2D, SODA', 'spec dat']
legend_labels = ['Hail Spec, 2D, Xsize', 'Hail Spec, 1D', 'HVPS1, 2D, Circlefit']
#legend_labels = ['HVPS1, Circlefit', 'Hail-2D, Xsize']
legend_labels = ['1', '2', '3', '4', '5', '6', '7', '8']

temp_colors = ['black', 'blue', 'red', 'cyan', 'yellow'] 
temp_markers =['.', '*', '+', '^', '3', '+']
#temp_markers = []
colors = 'black'
colors = ['blue', 'black', 'red', 'blue']
colors = ['blue', 'black', 'red', 'green', 'blue', 'black', 'red', 'green']
temp_markers =['.', '*', '^', '+', '3', '+', '.', '*']
facecolors_check = np.array([True, True, True, True, True, True, True, True])
facecolors_check = np.where(facecolors_check, colors, 'none')

#alli empty, cm fill,  
#colors = np.array(['green', 'green', 'magenta', 'magenta', 'blue', 'blue', 'red', 'red', 'black'])
#facecolors_check = np.array([True, False, True, False, True, False, True, False, True])
#facecolors_check = np.where(facecolors_check, colors, 'none')
#temp_markers = ['^', '^', 'o', 'o', 's', 's', 'D', 'D', '*']

#colors = np.array(['green', 'magenta', 'blue', 'red', 'black'])
#facecolors_check = np.array([True, True, True, True, True])
#facecolors_check = np.where(facecolors_check, colors, 'none')
#temp_markers = ['^', 'o', 's', 'D', '*']

#colors = np.array(['black', 'blue'])
#facecolors_check = np.array([True, True])
#facecolors_check = np.where(facecolors_check, colors, 'none')
#temp_markers = ['o', '^']

"""
plot_poisson_errorbars = True #true for plot and false for not
plot_errorbars_filled = False
plot_errorbars_filled_both_axes = False
plot_poisson_and_stddev_errorbars = False
"""

#creating legend names real quick
legend_labels = []
dataframes_plot_legend_labels = ["", "", ""]
legend_labels = ['HVPS1', 'HAILSPEC-2D', 'HAILSPEC-1D']
#dataframes_plot_legend_labels = ["PBP", "DISP"] #f668 one
#dataframes_plot_legend_labels = ['PBP', 'PBP']
for counter in range(len(dataframes_probename)):
    probename_l = dataframes_probename[counter]
    processing_method = dataframes_plot_legend_labels[counter]
    legend_name = probename_l + ' ' + processing_method
    legend_labels.append(legend_name)
legend_labels = ['HVPS1', 'HAILSPEC-2D', 'HAILSPEC-1TrueD']
legend_labels = ['HVPS1', 'HAILSPEC-2D', 'HAILSPEC-1D']
legend_labels = ['HAILSPEC-2D', 'HAILSPEC-1D']
legend_labels = ['HAILSPEC-2D', 'HAILSPEC-1D', 'HVPS1-2D']

legend_labels = ['Hail Spectrometer 1D']
legend_labels = ['Hail Spectrometer 1D', 'Hail Spectrometer 2D']
legend_labels = ['Hail Spectrometer 1D', 'Hail Spectrometer 2D', 'HVPS1']


matplotlib.use('Agg')  # Add this at the top of your script

for y in range(dataframes_normalized_conc[0].shape[0]): #for the time intervals
    #dataframes_normalized_conc[x][y][plotbins_not_logged_0]
    #bins_adjusted[plotbins_not_logged_0]

    fig = None
    fig3 = None

    #try introduced by claude for the try except and finally
    try:
    
        #fig = plt.figure(figsize = [12.0,10.0]) #in x in
        fig, ax = plt.subplots(figsize=[12.0, 10.0])
        
        plt.title(str(str(plot_times_final_s[y]) +' - '+ str(plot_times_final_f[y])), fontsize=30)
        #plt.title("Example Concentrations", fontsize=40)
        #storing the slope, yint, and area ratios
        
        if plot_fits == True:
            #set up fit plots figure
            fig3, axfit = plt.subplots(figsize=[12.0, 10.0])
    

       
        for x in range(dataframes_types.shape[0]): #for each probe/dataset
            #print(x, y, 'gfft')
            
            
            #two options
            #one is to make the nan's where there's no data into nan's
            #two is to make them zeros
            try:
                plotbins_not_logged_0 = np.isfinite(np.log(dataframes_normalized_conc[x][y]), where=True)
            except:
                pass
                #rows = dataframes_normalized_conc[x][0].shape[0]
                cols = dataframes_normalized_conc[x][0].shape[0]
                #plotbins_not_logged_0 = np.zeros(cols, dtype=int)
                #plotbins_not_logged_0 = np.arange()
                plotbins_not_logged_0 = np.full(cols, False)
                print('no data for a probe so just made it all 0s so itd plot')
            if dataframes_types[x] != 2: #need to skip disp case for now for this correction
                bins_adjusted = dataframes_bin_midpoints[x] / 10000
            elif dataframes_types[x] == 2:
                bins_adjusted = dataframes_bin_midpoints[x] / 10000
            
            
         
            if plot_poisson_errorbars == True:
                try:
                    ax.errorbar(bins_adjusted[plotbins_not_logged_0], \
                                 dataframes_normalized_conc[x][y][plotbins_not_logged_0], \
                                 yerr=dataframes_conc_uncertainty[x][y][plotbins_not_logged_0], \
                                 ecolor=colors[x], ls='none', capsize=4, elinewidth=1,
                                 zorder=2)
                    ax.errorbar(bins_adjusted[plotbins_not_logged_0], \
                                 dataframes_normalized_conc[x][y][plotbins_not_logged_0], \
                                 xerr=(dataframes_binsize[x]/2/10000)[plotbins_not_logged_0], \
                                 ecolor=colors[x], ls='none', capsize=4, elinewidth=1,
                                 zorder=2)
                except: #no data case
                    cols = dataframes_normalized_conc[x][0].shape[0]
                    plotbins_not_logged_0 = np.full(cols, False)
                    no_data = np.zeros(cols, dtype=int)
                    
    
    

            
            #main plotting, all others are conditionals
            try:#[plotbins_not_logged_0],\
                ax.scatter(bins_adjusted, \
                            dataframes_normalized_conc[x][y], \
                            label=legend_labels[x],s=300,
                            edgecolors=colors[x],marker=temp_markers[x],facecolors=facecolors_check[x],
                            zorder=3) 
     
                
            except: #if no data
                print('big issue')
                cols = dataframes_normalized_conc[x][0].shape[0]
                no_data = np.zeros(cols, dtype=int)
                ax.scatter(bins_adjusted[plotbins_not_logged_0], \
                            no_data[plotbins_not_logged_0],\
                            label=legend_labels[x],s=300,
                            edgecolors=colors[x],marker=temp_markers[x],facecolors=facecolors_check[x]) 
                    
            
    
                
            

            
            
            
            
            
            
            #adding plots that have a fit and fit information on them now
            #find mask
            if plot_fits == True:
                #names are pretty self descrptive. some more plot set up happens 
                #like 100 lines down
                concentration_mask, cutoffbin = create_uncertainty_probetype_mask(dataframes_normalized_conc[x][y],
                                                                       dataframes_conc_uncertainty[x][y],
                                                                       dataframes_types[x])
                #tss is total sum of squares
                yint, slope, xint, tss, mask_fit = estimate_fit_coef(bins_adjusted, 
                                                np.log(dataframes_normalized_conc[x][y]), 
                                                concentration_mask)
        
                    
                plot_regression_line(bins_adjusted, dataframes_normalized_conc[x][y],
                                     [yint, slope, xint, tss], colors[x], temp_markers[x], 
                                     legend_labels[x], cutoffbin, x, axfit, mask_fit)
            
            
            
          
    
    
        try:
            pass
            if plot_log_scale == True:
                #pass
                ax.set_yscale("log")
                ax.set_ylim(bottom=10**0, top=10000) 
            else:
                ax.set_ylim(bottom=0, top=4000)
            #ax.xticks(fontsize=40) 
            #ax.yticks(fontsize=40)  
            ax.tick_params(labelsize=30)
            #ax.set_ylim(bottom=10**0, top=10000)
            ax.set_xlim(left=0, right=5)
            
            ax.grid(which='major')
            
            ax.set_xlabel("Diameter (cm)", fontsize=30)
            ax.set_ylabel(r'dN/dD (#/$m^4$)', fontsize=30)
            ax.legend(fontsize=25)
            
            #adding fit information
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    
            
            #plt.show()
            #plt.tick_params(axis='both', which='major', pad=10)
            #plt.label_params(axis='both', which='major', pad=10)
            #plt.subplots_adjust(left=0.8, right=0.8)
            
            
            #annoting it to include the type of uncertainty
            #plt.annotate('Uncertainty Type',
            #    xy=(1, 0), xycoords='data',
            #    xytext=(-20, 40), textcoords='offset pixels',)
            #    #horizontalalignment='right',
            #    #verticalalignment='bottom')
            
            #plt.show()
            fig.savefig(pathname_plots +\
                              str(str(plot_times_final_s[y]) +'_'+ \
                              str(plot_times_final_f[y])) + '.png', dpi=dpi)#, bbox_inches = 'tight')
            #plt.tight_layout()
            #fig.savefig('Figures_for_ivan/' +\
            #                  str(str(plot_times_final_s[y]) +'_'+ \
            #                  str(plot_times_final_f[y])) + '.png', dpi=300, bbox_inches = 'tight')
    
        except:
            #passing print statement because it's annoying when 100 pop up cause
            #there's no data for awhile
            #print('Plot ' + str(str(plot_times_final_s[y]) +' - '+ str(plot_times_final_f[y])) \
            #      + ' encountered an error. Could be that no values to plot so log scale broke.'\
            #      'Or it could be that the pathway to save the plot is broken.')
            pass
    
        fig.clf()
        plt.close(fig)
        
        if plot_fits == True:
            try:
                #putting labels
                axfit.tick_params(labelsize=30)
                axfit.set_xlabel("Diameter (cm)", fontsize=30)
                axfit.set_ylabel(r'dN/dD (#/$m^4$)', fontsize=30)
                
                axfit.set_ylim(1, 10000)
                axfit.set_yscale('log')
                #axfit.legend(labelspacing=0.1, borderpad=0.4, handletextpad=0.8, fontsize=25)
                axfit.legend(fontsize=25)
                axfit.grid(True, which='major', linestyle='--', linewidth=0.5)
                axfit.set_xlim(left=0, right=5)
                
                plotname_time = str(str(plot_times_final_s[y]) +'_'+ \
                str(plot_times_final_f[y]))
                axfit.set_title(str(str(plot_times_final_s[y]) +' - '+ str(plot_times_final_f[y])), fontsize=30)
                
                #axfit.show()
                
                fig3.savefig(main_pathway_plot6 +\
                                  str(str(plot_times_final_s[y]) +'_'+ \
                                  str(plot_times_final_f[y])) + '.png', dpi=dpi)#, bbox_inches = 'tight')
                
                fig3.clf()
                plt.close(fig3)
            except Exception as e:
                print(e)
    
    except Exception as e:
        print(f"Error in main plotting loop iteration {y}: {e}")
    
    finally:
        # CRITICAL: Always close figures, even if there's an error
        if fig is not None:
            plt.close(fig)
            del fig
        if fig3 is not None:
            plt.close(fig3)
            del fig3
        
        # Force garbage collection every few iterations
        if y % 10 == 0:
            gc.collect()
            
            
# Final cleanup
plt.close('all')
gc.collect()
  




if plot_hvps_case == True:
    for y in range(dataframes_normalized_conc[0].shape[0]): #for the time intervals
        #dataframes_normalized_conc[x][y][plotbins_not_logged_0]
        #bins_adjusted[plotbins_not_logged_0]

        fig = None

        #try introduced by claude for the try except and finally
        try:
        
            #fig = plt.figure(figsize = [12.0,10.0]) #in x in
            fig, ax = plt.subplots(figsize=[12.0, 10.0])
            
            plt.title(str(str(plot_times_final_s[y]) +' - '+ str(plot_times_final_f[y])), fontsize=30)

            for x in range(dataframes_types.shape[0]): #for each probe/dataset
                #print(x, y, 'gfft')
                
                
                #two options
                #one is to make the nan's where there's no data into nan's
                #two is to make them zeros
                try:
                    plotbins_not_logged_0 = np.isfinite(np.log(dataframes_normalized_conc[x][y]), where=True)
                except:
                    pass
                    #rows = dataframes_normalized_conc[x][0].shape[0]
                    cols = dataframes_normalized_conc[x][0].shape[0]
                    #plotbins_not_logged_0 = np.zeros(cols, dtype=int)
                    #plotbins_not_logged_0 = np.arange()
                    plotbins_not_logged_0 = np.full(cols, False)
                    print('no data for a probe so just made it all 0s so itd plot')
                if dataframes_types[x] != 2: #need to skip disp case for now for this correction
                    bins_adjusted = dataframes_bin_midpoints[x] / 10000
                elif dataframes_types[x] == 2:
                    bins_adjusted = dataframes_bin_midpoints[x] / 10000
                    
                    
                    
                #main plotting, all others are conditionals
                try:#[plotbins_not_logged_0],\
                    ax.scatter(bins_adjusted, \
                                dataframes_normalized_conc[x][y], \
                                label=legend_labels[x],s=200,
                                edgecolors=colors[x],marker=temp_markers[x],facecolors=facecolors_check[x],
                                zorder=3) 
         
                    
                except: #if no data
                    print('big issue')
                    cols = dataframes_normalized_conc[x][0].shape[0]
                    no_data = np.zeros(cols, dtype=int)
                    ax.scatter(bins_adjusted[plotbins_not_logged_0], \
                                no_data[plotbins_not_logged_0],\
                                label=legend_labels[x],s=200,
                                edgecolors=colors[x],marker=temp_markers[x],facecolors=facecolors_check[x]) 
            try:
                pass
                if plot_log_scale == True:
                    #pass
                    ax.set_yscale("log")
                else:
                    pass 
                #ax.xticks(fontsize=40) 
                #ax.yticks(fontsize=40)  
                ax.tick_params(labelsize=30)
                ax.set_ylim(bottom=10**0, top=100000)
                ax.set_xlim(left=0, right=5)
                
                ax.set_xlabel("Bin Size (cm)", fontsize=30)
                ax.set_ylabel(r'Concentration (#/$m^4$)', fontsize=30)
                ax.legend(fontsize=25)
                ax.grid(which='major')
                
                #adding fit information
                props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            
                
                #plt.show()
                #plt.tick_params(axis='both', which='major', pad=10)
                #plt.label_params(axis='both', which='major', pad=10)
                #plt.subplots_adjust(left=0.8, right=0.8)
                
                
                #annoting it to include the type of uncertainty
                #plt.annotate('Uncertainty Type',
                #    xy=(1, 0), xycoords='data',
                #    xytext=(-20, 40), textcoords='offset pixels',)
                #    #horizontalalignment='right',
                #    #verticalalignment='bottom')
                
                #plt.show()
                fig.savefig(pathname_plots +\
                                  str(str(plot_times_final_s[y]) +'_'+ \
                                  str(plot_times_final_f[y])) + '.png', dpi=dpi)#, bbox_inches = 'tight')
                #plt.tight_layout()
                #fig.savefig('Figures_for_ivan/' +\
                #                  str(str(plot_times_final_s[y]) +'_'+ \
                #                  str(plot_times_final_f[y])) + '.png', dpi=300, bbox_inches = 'tight')
            
            except:
                #passing print statement because it's annoying when 100 pop up cause
                #there's no data for awhile
                #print('Plot ' + str(str(plot_times_final_s[y]) +' - '+ str(plot_times_final_f[y])) \
                #      + ' encountered an error. Could be that no values to plot so log scale broke.'\
                #      'Or it could be that the pathway to save the plot is broken.')
                pass

        except Exception as e:
            print(f"Error #2 in main plotting loop iteration {y}: {e}")
        
        finally:
            # CRITICAL: Always close figures, even if there's an error
            if fig is not None:
                plt.close(fig)
                del fig
            
            # Force garbage collection every few iterations
            if y % 10 == 0:
                gc.collect()
                
                
    # Final cleanup
    plt.close('all')
    gc.collect()