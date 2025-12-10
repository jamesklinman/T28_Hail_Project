#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar  9 19:16:10 2024

@author: james.klinman

some goals
  -aspect ratio per size bin
  -std devation for whole
     - not sure if std dev or poisson for larger ones
  -can characterize size bin ranges as rain, graoupel , wet and dry hail
  -want a mean axis ratio and distribution for it
  
  
the program does not like it if it can't find any data just a heads up  
"""

import json
import netCDF4
import numpy as np
import pandas as pd
import pickle
import math
import scipy.stats as stats
import matplotlib.pyplot as plt

#Getting stuff like flight data and number

#getting flight num
#------------------
flight_programs_file = 'Param_Info/File_Runner_Info.txt'
#flight_programs_info = pd.read_csv(flight_programs_file, sep=' * ', engine='python')
with open(flight_programs_file, 'r') as file:
    flight_programs_info = file.read()  
flight_programs_info = json.loads(flight_programs_info)
flight_num = str(flight_programs_info['flight_num'][0])

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

#TASfilename = '20240517/HHMMSS_True_Calc_Airspeed_757.txt'
#planefile = '20240517/757.nc'

#TASfile = pd.read_csv(TASfilename, sep=' * ', dtype={'HHMMSS': str}, engine='python')
airplanedata = netCDF4.Dataset(planefile)

#Getting the flight data and other data for file naming and plot title making.
#Needed up here since SODA file names require date
#-----------------------------------------------------------------------------
#FlightNum = str(getattr(airplanedata, 'FlightNumber'))

FlightDate = str(getattr(airplanedata, 'FlightDate'))
FlightDateSplit = FlightDate.split('/')
FlightDate = FlightDateSplit[2]+''+FlightDateSplit[0]+''+FlightDateSplit[1]
FlightDate_File = FlightDateSplit[0]+''+FlightDateSplit[1]+''+FlightDateSplit[2]

FlightTime = str(getattr(airplanedata, 'TimeInterval'))
FlightTimeStart = str(FlightTime)[0:8]
FlightTimeStart = FlightTimeStart.split(':')
FlightTimeStart = FlightTimeStart[0] + FlightTimeStart[1] + FlightTimeStart[2]

#duplicate method not used anywhere else i think 

#plane_time_start = getattr(airplanedata, 'TimeInterval')[0:8]
#for char in plane_time_start:
#    if char == ':':
#        plane_time_start = plane_time_start.replace(':', '')

#Calling start and end time before reading in the 
#rest of the files since they're time dependent
#------------------------------------------------
#initParameters = pd.read_csv(paramInfo, sep=' * ', engine='python')
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


#starttime = '234846'
#endtime = '235316'
#starttime = '235316'
#endtime = '235546'
#starttime = '235636'
#endtime = '240006'
#starttime = '240101'
#endtime = '240401'
#starttime = '240501'
#endtime = '241201'
#starttime = '241301'
#endtime = '242301'
#starttime = '242931'
#endtime = '243931'

starttime = '241831'
endtime = '241901'

#sizebin defining. need to make better
#sizebins = [[200,10000], [200,1000], [1000,10000]]
#sizebins = [[4000, 6500],[15000, 50000]]
sizebins = [[200,800], [800,4000], [5000,10000], [5000,38000], [200,38000]]




#accesing soda sav file
#There's a lot of data and information that can be accessed and is commented out
#The stuff for asepect ratios is uncommented
#-------------------------------------------------------------------------------
nc_pbp_file = path_to_flight + '/SODA_Outputs/Setting_Testing/pbp/06222000_232921_HAIL.pbp.nc'
nc_pbp_file = 'test_soda_temp/06222000_232921_HAIL.pbp.nc'

nc_pbp_file2 = 'test_soda_temp/06222000_232921_HVPS1.pbp.nc' 

#file_list = [nc_pbp_file2, nc_pbp_file]
file_list = [nc_pbp_file2]

pbp_data = []
for x in range(len(file_list)):
    pbp_data.append(netCDF4.Dataset(file_list[x]))
    print(file_list[x])

#nc_pbp = netCDF4.Dataset(nc_pbp_file)
#nc_pbp['time'] #everything is pbp so it should all be the same index
#print('pbp keys, ')
#print(nc_pbp.variables.keys())
#print('pbp other,')
#print(nc_pbp.ncattrs(), '\n ncattrs', nc_pbp.getncattr('STARTTIME'))


#Definitions for the script
#-------------------------

def find_index_of_closest_value(array, valueToFind):
    differences = np.abs(array - valueToFind)
    closest_index = differences.argmin()
    return closest_index

def HHMMSS_2_SS(time):
    #Assumes HHMMSS format. No Decimal. No colons. Should be str
    #assumes time is a string of a value
    
    HH = (int(time[0:2]) * 3600)#get HH and converts to sec
    MM = (int(time[2:4]) * 60)
    SS = (int(time[4:6]))
    time_sec = HH + MM + SS

    return(time_sec)

def past_midnight_check(time):
    #not sophisticated. just says if close enough to midnight, then
    #add 24 hours to match the seconds past midnight that aaron does
    #in SODA
    
    #time should be a string, int, or float. In hhmmss format. needs to be
    #HHMMSS or HHMMSS.decimals. Needs all 6 digits
    
    if time is int or time is float:
        time = str(time)
        
    if float(time[0:2]) >= 0 and float(time[0:2]) <= 4:
        adjust_hours = float(time[0:2]) + 24
        time = str(int(adjust_hours)) + time[2:]
        
    return time

def seconds_HHMMSS(time):
    #takes interger values, not strings. idk if floats work
    #floats do not work as it makes the seconds default to 0
    time = int(time)
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
    return str(HH+MM+SS)

def std_dev(data, mean):
    #data should be an array
    top = sum((data-mean)**2)
    bottom = data.shape[0]
    result = np.sqrt(top/bottom)
    
    return result
    
def gaussian(standard_dev, mean, x_var):
    left = 1 / np.sqrt(2 * np.pi * standard_dev**2)
    top1 = (x_var - mean)**2
    bot1 = 2 * standard_dev**2
    right = np.exp((top1 / bot1)*-1)
    result = left * right
    
    return result


def plot_std_dev2(avg_value, standard_dev, x_axis, ax):
    ax.plot(x_axis, prob_distr_func[x][s])
    
    one_sd = standard_dev * avg_value
    two_sd = standard_dev * 2 * avg_value
    three_sd = standard_dev * 3 * avg_value
    four_sd = standard_dev * 4 * avg_value
    
    ax.fill_between(
        x = x_axis, 
        y1 = stats.norm.pdf(x_axis, avg_value, standard_dev), 
        where = (avg_value-one_sd < x_axis)&(x_axis < avg_value+one_sd),
        color = "b",
        alpha = 0.2)
    
    ax.fill_between(
        x = x_axis, 
        y1 = stats.norm.pdf(x_axis, avg_value, standard_dev), 
        where = (avg_value-two_sd < x_axis)&(x_axis < avg_value+two_sd),
        color = "b",
        alpha = 0.2)
    
    ax.fill_between(
        x = x_axis, 
        y1 = stats.norm.pdf(x_axis, avg_value, standard_dev), 
        where = (avg_value-three_sd < x_axis)&(x_axis < avg_value+three_sd),
        color = "b",
        alpha = 0.2)
    
    ax.fill_between(
        x = x_axis, 
        y1 = stats.norm.pdf(x_axis, avg_value, standard_dev), 
        where = (avg_value-four_sd < x_axis)&(x_axis < avg_value+four_sd),
        color = "b",
        alpha = 0.2)


def sorting_particles_1probe(sizebins):
    #worked for previous versions of this code but haven't tested it for this
    #version yet
    
    global TimeResolution
    global starttime_s
    global endtime_s
    global times
    global rejectflags
    global aspectratios
    global xsizes
    
    
    #sorting by accepted/rejected and diameter size
    time_accepted_particles     = []
    asprtio_accepted_particles  = []
    time_rejected_particles     = []
    time_interval_start         = []
    
    temp_time_a_storage =    []
    temp_asprtio_a_storage = []
    temp_time_r_storage =    []
    
    #making bins for spots for each size range specified
    for x in range(len(sizebins)):
        temp_time_a_storage.append([])
        temp_asprtio_a_storage.append([])
        temp_time_r_storage.append([])
    
    timelower = starttime_s
    timeupper = starttime_s + TimeResolution
    timefinish = endtime_s
    counter = 0
    for particle_time in time_part:
        if particle_time >= timeupper:
            if len(temp_time_a_storage) == 0 & len(temp_asprtio_a_storage) == 0\
               & len(temp_asprtio_a_storage) == 0:
                timelower += TimeResolution
                timeupper += TimeResolution
                continue
            
            else:
                time_interval_start.append(timelower)
                if len(temp_time_a_storage) == 0:
                    time_accepted_particles.append([-99999])
                else:
                    time_accepted_particles.append(temp_time_a_storage)
                if len(temp_asprtio_a_storage) == 0:
                    asprtio_accepted_particles.append([-99999])
                else:
                    asprtio_accepted_particles.append(temp_asprtio_a_storage)
                if len(temp_time_r_storage) == 0:
                    time_rejected_particles.append([-99999])
                else:
                    time_rejected_particles.append(temp_time_r_storage)
       
                temp_time_a_storage =    []
                temp_asprtio_a_storage = []
                temp_time_r_storage =    [] #!!!!!!!!!!!!!!!!!!!!!!!!!
                
                #making bins for spots for each size range specified
                for x in range(len(sizebins)):
                    temp_time_a_storage.append([])
                    temp_asprtio_a_storage.append([])
                    temp_time_r_storage.append([])
                
                timelower += TimeResolution
                timeupper += TimeResolution
    
            
        if particle_time < timeupper and particle_time >= timelower:
            flag = rejectflags[counter]
            if flag == 0:
                particle_size = xsize_pbp[counter]
                temp_counter = 0
                for size in sizebins:
                    if particle_size >= size[0] and particle_size <= size[1]:
                        temp_asprtio_a_storage[temp_counter].append(aspectratios[counter])
                        temp_time_a_storage[temp_counter].append(time_part[counter])
                    temp_counter += 1
            else:
                particle_size = xsize_pbp[counter]
                temp_counter = 0
                for size in sizebins:
                    if particle_size >= size[0] and particle_size <= size[1]:
                        temp_time_r_storage[temp_counter].append(time_part[counter])
                    temp_counter += 1
    
        counter += 1

    #append final chunk/batch of data. since the check comes first, the final
    #bit doesn't get read out
    time_accepted_particles.append(temp_time_a_storage)
    asprtio_accepted_particles.append(temp_asprtio_a_storage)
    time_rejected_particles.append(temp_time_r_storage)
    time_interval_start.append(timelower)
    
    
    return time_accepted_particles, asprtio_accepted_particles, \
           time_rejected_particles, time_interval_start

    
def sorting_particles(sizebins):
    #Combines data from 1 or multiple probes to improve statistics where
    #there is overlap
    #to process one probe at a time. Simply use only one probe pbp.nc file
    
    global TimeResolution
    global starttime_s
    global endtime_s
    global times
    global rejectflags
    global aspectratios
    global xsizes

    #creating structure to organize and store all the data
    time_accepted_particles     = []
    asprtio_accepted_particles  = []
    time_rejected_particles     = [] #for ratio of accepted/rejected particles
    time_interval_start         = []
    
    num_intervals = math.ceil((endtime_s - starttime_s) / TimeResolution)
    for x in range(num_intervals):
        temp_tima = []
        temp_aspr = []
        temp_timr = []
        #temp_intv = []
        for y in range(len(sizebins)):
            temp_tima.append([])
            temp_aspr.append([])
            temp_timr.append([])
            #temp_intv.append([])
        
        time_accepted_particles.append(temp_tima)
        asprtio_accepted_particles.append(temp_aspr)
        time_rejected_particles.append(temp_timr)
        #time_interval_start.append(temp_intv)
    
    
    #now add data to final structure
    timelower = starttime_s
    timeupper = starttime_s + TimeResolution
    timefinish = endtime_s
    for probe in range(len(file_list)):
        time_tracker = 0
        timelower = starttime_s
        timeupper = starttime_s + TimeResolution
        timefinish = endtime_s
        print(file_list[probe], 'probe')
        print(time_tracker, 'time_tracker pre')
        for counter in range(len(times[probe])):
            
            particle_time = times[probe][counter]
            particle_size = xsizes[probe][counter]
            particle_aspr = aspectratios[probe][counter]
            particle_flag  = rejectflags[probe][counter] 
            
            if particle_time >= timeupper:
                #adding error codes for if no particles met the criteria
                #rather than it just being an empty array
                """for s in range(len(sizebins)):
                    if len(time_accepted_particles[time_tracker][s]) == 0:
                        time_accepted_particles[time_tracker][s].append(-99999)
                    if len(asprtio_accepted_particles[time_tracker][s]) == 0:
                        asprtio_accepted_particles[time_tracker][s].append(-99999)
                    if len(time_rejected_particles[time_tracker][s]) == 0:
                        time_rejected_particles[time_tracker][s].append(-99999)"""
                
                #moving onto next time interval now
                time_interval_start.append(timelower)
                time_tracker += 1 #onto next time interval
                print(time_tracker, 'time_tracker')
                timelower += TimeResolution
                timeupper += TimeResolution     

            
            if particle_time < timeupper and particle_time >= timelower: #checking for time domain
                if particle_flag == 0 or particle_flag == 4:
                    for s in range(len(sizebins)):
                        if particle_size >= sizebins[s][0] and particle_size <= sizebins[s][1]:
                            time_accepted_particles[time_tracker][s].append(particle_time)
                            asprtio_accepted_particles[time_tracker][s].append(particle_aspr)
                else:
                    for s in range(len(sizebins)):
                        if particle_size >= sizebins[s][0] and particle_size <= sizebins[s][1]:
                            time_rejected_particles[time_tracker][s].append(particle_time)

    #doing the timeupper check one final tiem since it doens't get activated since 
    #endloc data shoudn't stretch past it
    """for s in range(len(sizebins)):
        if len(time_accepted_particles[time_tracker][s]) == 0:
            time_accepted_particles[time_tracker][s].append(-99999)
        if len(asprtio_accepted_particles[time_tracker][s]) == 0:
            asprtio_accepted_particles[time_tracker][s].append(-99999)
        if len(time_rejected_particles[time_tracker][s]) == 0:
            time_rejected_particles[time_tracker][s].append(-99999)"""
    
    #getting the final particle and time interval since it won't enter the final check
    time_interval_start.append(timelower)
    time_tracker += 1 #onto next time interval
    timelower += TimeResolution
    timeupper += TimeResolution 
    if particle_time < timeupper and particle_time >= timelower: #checking for time domain
        if particle_flag == 0 or particle_flag == 4:
            for s in range(len(sizebins)):
                if particle_size >= sizebins[s][0] and particle_size <= sizebins[s][1]:
                    time_accepted_particles[time_tracker][s].append(particle_time)
                    asprtio_accepted_particles[time_tracker][s].append(particle_aspr)
        else:
            for s in range(len(sizebins)):
                if particle_size >= sizebins[s][0] and particle_size <= sizebins[s][1]:
                    time_rejected_particles[time_tracker][s].append(particle_time)
    
    return time_accepted_particles, asprtio_accepted_particles, \
           time_rejected_particles, time_interval_start
            

#getting the start and end location in the arrays
#------------------------------------------------
starttime = past_midnight_check(starttime)
endtime = past_midnight_check(endtime)

starttime_s = HHMMSS_2_SS(str(starttime))
endtime_s = HHMMSS_2_SS(str(endtime))

startlocs = []
endlocs = []
for x in range(len(file_list)):
    startloc = find_index_of_closest_value(pbp_data[x]['time'][:], starttime_s)
    endloc = find_index_of_closest_value(pbp_data[x]['time'][:], endtime_s)
    startlocs.append(startloc)
    endlocs.append(endloc)

#getting specific pbp data for the defined start and end indices
#-------------------------------------------------------------
aspectratios = []
times = []
rejectflags = []
xsizes = []
for x in range(len(file_list)):
    aspr = pbp_data[x]['aspectratio'][startlocs[x]:endlocs[x]]
    time = pbp_data[x]['time'][startlocs[x]:endlocs[x]]
    rf = pbp_data[x]['rejectionflag'][startlocs[x]:endlocs[x]]
    xs = pbp_data[x]['xsize'][startlocs[x]:endlocs[x]]
    ys = pbp_data[x]['ysize'][startlocs[x]:endlocs[x]]
    
    aspr = np.minimum(xs, ys) / np.maximum(xs, ys)
    
    aspectratios.append(aspr)
    times.append(time)
    rejectflags.append(rf)
    xsizes.append(xs)



#Sorting particles by aspect ratio, accepted/rejected, getting time interval
#starts, and also sorting by diameter of particle based on xsize
#Xsize since it's consistent with processing for PSDs for T28_CHILL project
#---------------------------------------------------------------------------
all_size_bins = sorting_particles(sizebins)


#now to get avg for each
averages = []
for time_period in all_size_bins[1]: #1 is the aspect ratio
    temp_averages = []
    for size in time_period:
        average_for_range = np.mean(size)
        temp_averages.append(np.round(average_for_range, 3))
    averages.append(temp_averages)


#now getting accepted/rejected ratio
accepted_rejected_ratio = []
total_particles_size_ranges = []
for time_period in range(len(all_size_bins[0])):
    temp_ratio = []
    temp_total = []
    for size in range(len(all_size_bins[0][time_period])):
        if len(all_size_bins[0][time_period][size]) == 0 or\
           len(all_size_bins[2][time_period][size]) == 0:
               temp_ratio.append(-99999)
               temp_total.append(len(all_size_bins[0][time_period][size]) +\
                                 len(all_size_bins[2][time_period][size]))
        else:
            a_num = len(all_size_bins[0][time_period][size])
            r_num = len(all_size_bins[2][time_period][size])
            
            total_interval = a_num + r_num
            a_ratio = round(a_num / total_interval, 3)
            temp_ratio.append(a_ratio)
            temp_total.append(total_interval)
    accepted_rejected_ratio.append(temp_ratio)
    total_particles_size_ranges.append(temp_total)


#counting num of particles per aspect ratio to
#plot a discrete amount on top of the gaussian
size_aspr_bins = 10
aspect_ratio_discrete_all = []
for t in range(len(all_size_bins[1])):
    time_bins_temp = []
    for s in range(len(all_size_bins[1][t])):
        size_bins = []
        for x in range(size_aspr_bins):
            size_bins.append([])
        #aspr_disc = all_size_bins[1][t][s]
        for p in all_size_bins[1][t][s]:
            for i in range(size_aspr_bins):
                #print(i/size_aspr_bins, (i+1)/size_aspr_bins, p)
                if p >= (i / size_aspr_bins) and p < ((i + 1) / size_aspr_bins):
                    size_bins[i].append(p)
                    break  # Break once the correct bin is found
        time_bins_temp.append(size_bins)
    aspect_ratio_discrete_all.append(time_bins_temp)

aspect_ratio_discrete = []
for t in aspect_ratio_discrete_all:
    temp_s_for_t = []
    for s in t: 
        temp_ar_for_s = []
        for ar in s:
            temp_ar_for_s.append(len(ar))
        temp_s_for_t.append(temp_ar_for_s)
    aspect_ratio_discrete.append(temp_s_for_t)
#making midpoints to plot the data
aspr_midpoints = []
for x in range(size_aspr_bins):
    midpoint_adjust = ((x+1) - x) / 2   / size_aspr_bins
    bin_midpoint = x / 10 + midpoint_adjust
    aspr_midpoints.append(round(bin_midpoint, 3)) # assumes it's not more precise than 3 decimal places

    
#getting std dev
std_dev_size_ranges = []
for t in range(len(all_size_bins[1])):
    temp_sd = []
    for s in range(len(all_size_bins[1][t])):
        if len(all_size_bins[0][t][s]) == 0:
            result_s = -99999
        else:
            result_s = std_dev(data=np.array(all_size_bins[1][t][s]),
                             mean=averages[t][s])
        temp_sd.append(result_s)
    std_dev_size_ranges.append(temp_sd)


#creating a HHMMSS timelist for the output file as well
time_start_HHMMSS_all = []
for time in all_size_bins[3]:
    converted_time = seconds_HHMMSS(int(time))
    time_start_HHMMSS_all.append(converted_time)
time_start_HHMMSS = []
for time in time_start_HHMMSS_all:
    if time in time_start_HHMMSS:
        pass
    else:
        time_start_HHMMSS.append(time)



#the pdf function automatically takes the -99999 and says yeah that aint
#possible and makes the result a nan yay!
x_axis = np.linspace(0, 1, 100)
prob_distr_func = []
for x in range(len(std_dev_size_ranges)):
    temp_pdf = []
    for s in range(len(std_dev_size_ranges[x])):
        pdf_func = stats.norm.pdf(x_axis, averages[x][s], std_dev_size_ranges[x][s])
        temp_pdf.append(pdf_func)
    prob_distr_func.append(temp_pdf)


# Plotting
for x in range(len(time_start_HHMMSS)):
    print(x)
    fig, axes = plt.subplots(len(sizebins), 1, figsize=(8, 4*len(sizebins)))  # Create a figure with 3 subplots vertically
    fig.suptitle(f'Time Period {time_start_HHMMSS[x]}')

    if len(sizebins) == 1:
        axes = [axes]  # Make axes a list if it contains only one subplot

    for s in range(len(sizebins)):  # Assuming each time period has exactly 3 PDFs
        plot_std_dev2(avg_value=averages[x][s], 
                     standard_dev=std_dev_size_ranges[x][s], 
                     x_axis=x_axis,
                     ax=axes[s])
        axes[s].set_title(f'PDF {sizebins[s]} um')
        axes[s].set_xlabel('Aspect Ratio')
        axes[s].set_ylabel('Probability Density')
        
        # Create a secondary y-axis
        ax2 = axes[s].twinx()
        # Plot vertical lines on the secondary y-axis
        ax2.vlines(x=aspr_midpoints, ymin=0, ymax=aspect_ratio_discrete[x][s], color='k', label='Counts per aspect ratio')
        
        #for midpoint, count in zip(aspr_midpoints, aspect_ratio_discrete[x][s]):
        #    ax2.vlines(x=midpoint, ymin=0, ymax=count, color='r', alpha=0.7, label='Aspect Ratio Discrete' if midpoint == aspr_midpoints[0] else "")

        ax2.set_ylabel('Aspect Ratio Discrete')
        ax2.set_ylim(0, max(max(aspect_ratio_discrete[x][s]), 1))

    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust layout to make room for the main title
    #plt.show()
    
    plt.savefig('Aspr/Plots/' + f'Time Period {time_start_HHMMSS[x]}' + '.png')
    
    

#Creating the output file
#-----------------------
TestFile = open('Aspr/Tables/' + str(starttime) + '_20000622_AspectRatios.txt', "w+")

#Writing the header
header = '{a:<10}{b:<10}'.format(a='Time_(s)', b='HHMMSS')
counter = 1
for size in range(len(averages[0])): #dyanmically making headers based on number of size bins
    header += '{c:<13}{d:<9}{e:<13}'.format(c='Range'+str(counter)+'_Avg', 
                                                                    d='Stddev', 
                                                                    e='%_Accepted') 
    counter += 1
TestFile.write(header + '\n\n')

for x in range(len(averages)):    
    line = '{a:<10}{b:<10}'.format(a=all_size_bins[3][x], b=time_start_HHMMSS[x]) 
    for s in range(len(averages[x])):      
        if np.isnan(averages[x][s]) is True:
            avgs = 'nan'
        else:
            avgs = str(round(averages[x][s], 3))
        if std_dev_size_ranges[x][s] == -99999:
            stddevs = str(-99999)
        else:
            stddevs = str(round(std_dev_size_ranges[x][s], 3))
        if np.isnan(accepted_rejected_ratio[x][s]) is True:
            arratio = 'nan'
        else:
            arratio = str(round(accepted_rejected_ratio[x][s], 3))
        
        #print(avgs, type(avgs), stddevs, type(stddevs), arratio, type(arratio))
        
        line += '{c:^13}{d:<9}{e:<13}'.format(c=avgs,
                                              d=stddevs,
                                              e=arratio)
        
    TestFile.write(line + '\n')    

TestFile.close()
