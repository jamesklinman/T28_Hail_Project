# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 11:54:20 2023

@author: james.klinman

old file naming conventions for soda file is not up to date yet. soda doesn't
always start at the same time as the flight actually starts so need a way to 
work around that maybe it's possible to just use the date and * everything after

DOES NOT WORK FOR 5 SECOND PERIODS. do 10 second or above
Also exclude edge cases so like the first period and the last period for
now because I they haven't been properly coded to either fill out the total
specified chunking amount or just be excluded from the plotting
"""
import os
import sys
import pandas as pd
import numpy as np
import Top_Hail_Methods as hail
import matplotlib.pyplot as plt
import math
import netCDF4
from datetime import date
import pickle
import json


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


#Calling in plane data files
#---------------------------
TASfilename = 'Sensor_Information/HHMMSS_True_Calc_Airspeed_'\
               + flight_num + '.txt'
planefile = 'Flight_Files/' + flight_num + '.nc'

#true airspeed for each second
#and airplane data for naming the tables and plots
#-------------------------------------------------
TASfile = pd.read_csv(TASfilename, sep=' * ')
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
#plane_time_start = getattr(airplanedata, 'TimeInterval')[0:8]
#for char in plane_time_start:
#    if char == ':':
#        plane_time_start = plane_time_start.replace(':', '')

#Now can finally call concentration file names
#---------------------------------------------
"""
old file naming not made for soda output names though so not general use
filenameHVPS = 'Particle_Concs/' + FlightDate_File + '_' + plane_time_start +\
               '_HVPS1.txt'
#filenameSpec = 'Particle_Concs/disp' + flight_num + '.0'
filenameSpec = 'Particle_Concs/SODAfiles/' + FlightDate_File + '_' + plane_time_start + '_HAIL_AllIn_Xacross_3dof.txt'
"""

#filenameHVPS = 'Particle_Concs/SODA_Files/06221995_231519_HVPS1.txt' 
filenameHVPS = 'Particle_Concs/SODA_Files/' + FlightDate_File + '_' +\
                FlightTimeStart + '_HVPS1.txt'

#uncomment the file you want to run
filenameSpec = 'Particle_Concs/DISP' + FlightNum + '.0'
#filenameSpec = 'Particle_Concs/SODA_Files/' + FlightDate_File + '_' +\
#                FlightTimeStart + '_HAIL.txt'
#filenameSpec = "Particle_Concs/SODA_Files/06222000_232921_HAIL.txt"

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
print(indexs)

time_index_to_use = iterationTracker['Iteration'][0] #* \
    #iterationTracker['Skip_Num'][0]
#time_index_to_use = 0

starttime = str(initParameters['Time_Start'][time_index_to_use])
endtime = str(initParameters['Time_End'][time_index_to_use])
timeZone = int(initParameters['Timezone_true'][0])


#Tells the program what the chunks/number
#of seconds to bin the data together is
#minimum of either 1s or what SODA was set to
#--------------------------------------------
TimeResolution = int(initParameters['PSD_Time_Res'][0])


#SODA defaults to a rate of 5 seconds (read as 5s chunks which is
#related to the time resolution). So this just hardcodes that in.
#----------------------------------------------------------------
SodaPreChunk = 5
                
#If the spectrometer data is read in from the 1D hail counts file generated
#by SDSMT, it requires the below corrections.
#BinSize is the change in width for each channel
#SA is surface area the probe covered.
#--------------------------------------------------------------------------
BinSize = np.array([.1, .1, .1, .1, .14, .16, .20, .26, .30, .31, .44, .60,\
                    .79, 1])
BinSize = BinSize / 100 #to correct for cm -> m
#SA = .1 #in m^-2
#not all in sample area


#These are the channels/bins, whatever you want to call them. Units are in cm
#xaxis 2 is the channels for the 1D SDSMT hail counts. It is also used for 
#SODA if SODA bins were set to match the SDSMT ones
#xaxis3 are the default SODA bins and are typically used for the HVPS data
#-----------------------------------------------------------------------------
xaxis = np.array([.02, .04, .06, .08, .1, .12, .14, .16, .18, .22, .26, .3, \
                  .35, .4, .5, .6, .7, .8, .94, 1.1, 1.3, 1.56, 1.86, 2.17, \
                  2.61, 3.21])

    #size of minimum particle
xaxis2 = np.array([.4, .5, .6, .7, .8, .94, 1.1, 1.3, 1.56, 1.86, 2.17, 2.61,\
                   3.21, 4])

xaxis3 = np.array([.02, .04, .06, .08, .1, .12, .14, .16, .18, .22, .26, .3,\
                   .34, .38, .42, .46, .5, .6, .7, .8, .9, 1, 1.5, 2, 2.5])

#Sample area adjusted for all in
#100x10 cm minus the particle size
#---------------------------------
SAx = []
SAy = []
for x in xaxis2:
    SAx.append(100)
    SAy.append(10 - x)

SA = []    
for x in range(len(SAx)):
    xlen = SAx[x] / 100
    ylen = SAy[x] / 100
    SA.append(xlen * ylen)


#Preping HVPS data
#-----------------
HVPSData = pd.read_csv(filenameHVPS, sep=' * ', header=22)
tempdf = pd.DataFrame(HVPSData)
tempdf = tempdf.drop(index=0)
HVPSData = pd.DataFrame.reset_index(tempdf)


#try and except because so far two variations f hail spectormeter data have
#been run through this program. The try works if the data file is from SODA,
#and the except works for the output generated by the South Dakota School of Mines
#---------------------------------------------------------------------------------
try:
    #easier to read spec data from SODA
    SpecData = pd.read_csv(filenameSpec, sep=' * ', header=22)
    tempdf2 = pd.DataFrame(SpecData)
    tempdf2 = tempdf2.drop(index=0)
    SpecData = pd.DataFrame.reset_index(tempdf2)
    
    #determines which if statement to enter in a couple of the steps later on
    new_spec_file_tracker = 'y'

except:
    #Preping Spectrometer data
    #got the below chunk of code from 
    #https://stackoverflow.com/questions/7356043/how-to-delete-specific-strings-from-a-file
    #it deletes all the new page headers that are attached to the rows of data
    #strToDelete = ['F l i g h t  668  22-Jun-95  Hail Info'] #header to delete for each page
    strToDelete = ['F l i g h t  '+flight_num+'  22-Jun-0  Hail Info']                         #needs updating!!!!!!!!
    endoffiletodelete = '-=-'
    fin = open(filenameSpec, "r")
    fout = open("Random/Spec_Corrected_File", "w+")
    for line in fin:
        for word in strToDelete:
            line = line.replace(word, "")
        fout.write(line)
    fin.close()
    fout.close()
    
    #first loop from https://pynative.com/python-count-number-of-lines-in-file/
    #gets length of file and get reads in just the spec data
    with open(r"Random/Spec_Corrected_File", 'r') as file:
        for count, line in enumerate(file):
            pass
        FileLen = count + 1
    Spacing = 55 #spacing between rows to skip                                           #indpt var!!!!!
    RowsToSkip = []
    RowsToSkip.append(57)
    NewHeadSkip = 57
    while NewHeadSkip <= FileLen:
        NewHeadSkip += Spacing
        RowsToSkip.append((NewHeadSkip))
    SpecFile = "Random/Spec_Corrected_File"
    SpecData = pd.read_csv(SpecFile, sep=' * ', header=0, skiprows=RowsToSkip)
    #spec data is stored in local time not utc. need to add 6hrs
    
    #need this since the files are in their local timezones time instead of utc
    starttimeSpec = hail.HHMMSS_adjustHH(starttime, (-(timeZone)))
    endtimeSpec = hail.HHMMSS_adjustHH(endtime, (-(timeZone)))
    starttimeSpec = hail.forceHHMMSS(starttimeSpec)
    endtimeSpec = hail.forceHHMMSS(endtimeSpec)
    
    #determines which if statement to enter in a couple of the steps later on 
    new_spec_file_tracker = 'n'


#----------------------------------
#Now that the data is read in
#Moving on to working with the data
#----------------------------------
  
  
#converting HVPS data to HHMMSS format so it matches spectrometer format
#HVPS data from SODA is typically in UTC, which is why the timezone isn't
#included in the function
#------------------------------------------------------------------------
templist = []
for x in HVPSData['Time']:
    templist.append(int(x))
HVPSTimeConv = hail.seconds_HHMMSS(templist)

#!NOTE
#this assumes no flights started after 2:59 UTC because of the > 3
#the adjustment is just making sure that the time didn't go back to 0 hours
#after 24hrs since the HVPS and spec data need it to be in the 24+ hr format
#----------------------------------------------
if int(airplanedata['TIME_HOURS_20Hz'][0][0]) > 3:
    if starttime[0:2] == '00':
        adjustHH = 24
    elif int(starttime[0:2]) <= 3:
        adjustHH = 24
    else:
        adjustHH = 0

starttime_adjust = hail.HHMMSS_adjustHH(starttime, adjustHH)
endtime_adjust = hail.HHMMSS_adjustHH(endtime, adjustHH)
starttime_adjust = hail.forceHHMMSS(starttime_adjust)
endtime_adjust = hail.forceHHMMSS(endtime_adjust)

#Getting the start and end index for the HVPS data
#-------------------------------------------------
HVPS_Indx_Start = hail.find_loc_in_array_1D(HVPSData['Time'],
                                            hail.HHMMSS_2_SS([starttime_adjust])[0])
HVPS_Indx_End = hail.find_loc_in_array_1D(HVPSData['Time'], 
                                          hail.HHMMSS_2_SS([endtime_adjust])[0])


#Using the 'y' 'n' from reading in the files, get the index's for the 
#spectrometer data using the starttime adjust 
#---------------------------------------------------------------------
if new_spec_file_tracker == 'y':
    SpecStartTimeIndx = hail.find_loc_in_array_1D(SpecData['Time'], 
                                                  hail.HHMMSS_2_SS([starttime_adjust])[0])
    SpecEndTimeIndx = hail.find_loc_in_array_1D(SpecData['Time'], 
                                                hail.HHMMSS_2_SS([endtime_adjust])[0])

#side note!
#if you're getting an error with the start and endtimeSpec, then copy the method
#from the starttime_adjust for the HVPS for the Spec here. Not tested since I
#haven't run f668 through this updated program yet
elif new_spec_file_tracker == 'n':
    #not tested for if the index is in line with one of the omitted rows
    SpecStartTimeIndx = None
    SpecEndTimeIndx = None
    tempiter = 0
    for x in SpecData['Time']:
        if x == '-=-': #this means you're at the end of the file
            break
        if str(int(float(x))) == str(starttime_adjust): #need starttimeSPec if its 1995, but adjust if it's 2000   .....
            SpecStartTimeIndx = tempiter
        if str(int(float(x))) == str(endtime_adjust):
            SpecEndTimeIndx = tempiter
            break
        else:
            tempiter +=1
            

#Getting the plane data index's now
#--------------------------------------
starttimeTAS = hail.HHMMSS_resetHH(starttime)
endtimeTAS = hail.HHMMSS_resetHH(endtime)

starttimeTAS = hail.forceHHMMSS(starttimeTAS)
endtimeTAS = hail.forceHHMMSS(endtimeTAS)

PlaneStartIndx = None
PlaneEndIndx = None
tempiter = 0
#TAS file is in HHMMSS and resets after 24hrs 
for x in TASfile['HHMMSS']:
    if int(x) == int(starttimeTAS):
        PlaneStartIndx = tempiter
    if int(x) == int(endtimeTAS):
        PlaneEndIndx = tempiter
        break
    else:
        tempiter +=1 
        
#Loops through and records all the speeds based on the
#airplane index's. But, if one of the times is off a little
#because of the way the data was read in then it checks for that
#and hopefully applies a correction. not sure though tbh 
#---------------------------------------------------------------
PlaneSpeeds = []
for x in range(PlaneStartIndx, PlaneEndIndx + 1):
    for y in range(SpecStartTimeIndx, SpecEndTimeIndx + 1):
        spectime = int(SpecData['Time'][y])
        if int(SpecData['Time'][y]) >= 240000:
            spectime = int(SpecData['Time'][y]) - 240000
            #print('hi')
        if spectime == int(TASfile['HHMMSS'][x]):
            PlaneSpeeds.append(TASfile['Calc_Airspeed'][x])
        else:
            pass

        
#-------------------------------------------------------
#Chunking the data together now and applying corrections
#-------------------------------------------------------


def soda_chunking(conc_amount, chunk_size, soda_res, indx_start, indx_end,
                  soda_data):
    """
    Notes: conc amount is 14 or 25 i think.
    """
    
    #calculating how many chunks of time there are in the specified time period
    temporal_resolution = math.ceil(
        (indx_end + 1 - indx_start) / (chunk_size / soda_res))
    
    #Makes the empty lists to store the data in
    binned_data = []
    for size in range(temporal_resolution):
        binned_data.append([])
    #binned_data = np.empty((0, conc_amount), float)    
    
    #Binning the data together
    extra_counter = 0 #counts rows for if final bin isn't the full time range
    tempiter = 0 #tracks which empty bin to add data to
    time_counter = 1 #helps calculate which bin start the binning at
    final_bin = None
    for row in range(indx_start, indx_end + 1): #to include final index
        extra_counter += 1
        #if the column index is equal to the end index for the bin
        
        #temp_chunk = np.append(temp_chunk, np.array([soda_data[row]]), axis=0)
        if int(row) == int(indx_start):
            if chunk_size != soda_res:
                pass
                print('hiiiii')
            else:
                #look below for comments
                low_indx = int(row - chunk_size)
                high_indx = int(row)
                for conc in range(1, conc_amount + 1):
                    if conc < 10:
                        temp_conc = 'Conc' + str(0)+str(0)+str(conc)
                    else:
                        temp_conc = 'Conc' + str(0)+str(conc)
                    binned_data[tempiter].append(np.sum(
                        soda_data[str(temp_conc)][int(low_indx):int(high_indx)]))
                tempiter += 1
                extra_counter = 0 #resetting variable
                time_counter += 1
                print('doubletrouble')
        elif int(row) == int((chunk_size / soda_res * time_counter)+ indx_start - 1): 
            low_indx = int(row - chunk_size)
            high_indx = int(row)
            for conc in range(1, conc_amount + 1):
                if conc < 10:
                    temp_conc = 'Conc' + str(0)+str(0)+str(conc)
                else:
                    temp_conc = 'Conc' + str(0)+str(conc)
                binned_data[tempiter].append(np.sum(
                    soda_data[str(temp_conc)][int(low_indx):int(high_indx)]))
            tempiter += 1
            extra_counter = 0 #resetting variable
            time_counter += 1
        elif int(row) == int(indx_end):
            #should enter into this loop if the there aren't enough rows to
            #make a full bin and bin together the remaining data and add a note
            #for potential error
            low_indx = int(row - extra_counter)
            high_indx = int(row)
            for conc in range(1, conc_amount + 1):
                #conc_count += 1
                if conc < 10:
                    temp_conc = 'Conc' + str(0)+str(0)+str(conc)
                else:
                    temp_conc = 'Conc' + str(0)+str(conc)
                binned_data[tempiter].append(np.sum(
                    soda_data[str(temp_conc)][int(low_indx):int(high_indx)]))
            final_bin = high_indx - low_indx
            #final bin is how many n sec bits inside the final chunk there are
            #if there weren't enough to do a full n (chunksize) seconds

    return(np.array([binned_data]), final_bin)
            

def sdsmt_chunking(sdsmt_data, conc_amount, chunk_size, indx_start, indx_end,
                   bin_correction, surface_area, airspeed):
    #look at bottom of file for some shorter examples to see what's
    #going on more clearly.
    
    #initiallizing numpy array
    #row_range = indx_end - indx_start
    data_corrected = np.empty((0, conc_amount), float)                            #might need to replace onc amount with row
    #data_corrected = data_corrected.reshape(row_range, 0)
    
    #applying bin size corrections
    #np does #of columns, #of rows  (2, 3) is 2 column 3 row
    for row in range(indx_start, indx_end + 1): #including final index
        bin_corrected = np.array([])
        for column in range(1, conc_amount + 1):#+1 to include the final conc
            each_value = float(sdsmt_data[str(column)][row])
            bin_corrected = np.append(bin_corrected, each_value)
        data_corrected = np.append(data_corrected, np.array([bin_corrected]),
                                   axis=0)   
    
    #particle counts / (airspeed * bin size * surface area)  = # / m^4
    #applying binsize and surface area correction
    data_corrected = data_corrected / bin_correction / SA
      
    #applying airspeed correction
    for second in range(data_corrected.shape[0]):
        data_corrected[second] = data_corrected[second] / airspeed[second]
    

    #Initializing arrays to store the binned data    
    #Makes the empty lists to store the data in
    binned_data = np.empty((0, conc_amount), float)
        
    #Binning the data together
    extra_counter = 0 #counts rows for if final bin isn't the full time range
    time_counter = 1 #helps calculate which bin start the binning at
    temp_chunk = np.empty((0, conc_amount), float)
    final_bin = None
    for row in range(indx_start, indx_end + 1):#to include final index
        extra_counter += 1
        #adding rows to temp chunk until the end of the chunk size is met
        row_temp = row - indx_start
        temp_chunk = np.append(temp_chunk, np.array([data_corrected[row_temp]]), axis=0)
        #if the column index is equal to the end index for the bin
        
        if int(row) == int(indx_start):
            pass
        elif int(row) == int((chunk_size * time_counter)+ indx_start - 1): 
            temp_chunk = np.sum(temp_chunk, axis=0)
            binned_data = np.append(binned_data, np.array([temp_chunk]), axis=0)
            extra_counter = 0 #resetting variable
            time_counter += 1
            temp_chunk = np.empty((0, conc_amount), float)
        elif int(row) == int(indx_end):                                               
            #should enter into this loop if the there aren't enough rows to
            #make a full bin and bin together the remaining data and add a note
            #for potential error
            low_indx = int(row - extra_counter)
            high_indx = int(row) 
            temp_chunk = np.sum(temp_chunk, axis=0)
            binned_data = np.append(binned_data, np.array([temp_chunk]), axis=0)
            final_bin = high_indx - low_indx
            #final bin is how many n sec bits inside the final chunk there are
            #if there weren't enough to do a full n (chunksize) seconds
            
    #binned_data = binned_data / bin_correction / SA
    
    return(binned_data, final_bin)


#works. not tested for full set of hvps data that doesn't cut off though
#not tested for numbers at each step to check for accuracy yet either
HVPS_binned = soda_chunking(conc_amount=25, chunk_size=TimeResolution, 
                            soda_res=SodaPreChunk, 
                            indx_start=HVPS_Indx_Start, 
                            indx_end=HVPS_Indx_End,
                            soda_data=HVPSData)
if new_spec_file_tracker == 'y':
    #SODA version
    Spec_binned = soda_chunking(conc_amount=14, chunk_size=TimeResolution, 
                                soda_res=SodaPreChunk, 
                                indx_start=SpecStartTimeIndx, 
                                indx_end=SpecEndTimeIndx,
                                soda_data=SpecData)
elif new_spec_file_tracker == 'n':
    #SDSMT version
    Spec_binned = sdsmt_chunking(sdsmt_data=SpecData, conc_amount=14,
                                       chunk_size=TimeResolution, 
                                       indx_start=SpecStartTimeIndx, 
                                       indx_end=SpecEndTimeIndx,
                                       bin_correction=BinSize, surface_area=SA, 
                                       airspeed=PlaneSpeeds)


#----------------------------------------
#Plotting the data and making data tables
#----------------------------------------


FlightNum = str(getattr(airplanedata, 'FlightNumber'))
FlightDate = str(getattr(airplanedata, 'FlightDate'))
FlightDate = FlightDate.split('/')
FlightDate = FlightDate[2]+''+FlightDate[0]+''+FlightDate[1]

current_date = date.today()
file_created_date = current_date.strftime("%Y%m%d")


if os.path.exists('./PSD_Plots/HVPS_Spectrometer_Comparison/') is False:   
    os.mkdir('./PSD_Plots/HVPS_Spectrometer_Comparison/')
if os.path.exists('./PSD_Plots/HVPS_Spectrometer_Comparison/' + file_created_date) is False:   
    os.mkdir('./PSD_Plots/HVPS_Spectrometer_Comparison/' + file_created_date)
if os.path.exists('./PSD_Plots/HVPS_Spectrometer_Comparison/' + file_created_date
                   + '/' + str(FlightDate) + '/') is False:   
    os.mkdir('./PSD_Plots/HVPS_Spectrometer_Comparison/' + file_created_date
              + '/' + str(FlightDate) + '/')
if os.path.exists('./PSD_Plots/HVPS_Spectrometer_Comparison/' + file_created_date
                   + '/' + str(FlightDate) + '/'
                   + str(starttime) + '_' + str(endtime) +'/') is False:   
    os.mkdir('./PSD_Plots/HVPS_Spectrometer_Comparison/' + file_created_date
              + '/' + str(FlightDate) + '/' + str(starttime) + '_' + str(endtime) +'/')
    

if os.path.exists('./PSD_Tables/HVPS_Spectrometer_Comparison/') is False:   
    os.mkdir('./PSD_Tables/HVPS_Spectrometer_Comparison/')
if os.path.exists('./PSD_Tables/HVPS_Spectrometer_Comparison/' + file_created_date) is False:   
    os.mkdir('./PSD_Tables/HVPS_Spectrometer_Comparison/' + file_created_date)
if os.path.exists('./PSD_Tables/HVPS_Spectrometer_Comparison/' + file_created_date
                   + '/' + str(FlightDate) + '/') is False:   
    os.mkdir('./PSD_Tables/HVPS_Spectrometer_Comparison/' + file_created_date
              + '/' + str(FlightDate) + '/')
if os.path.exists('./PSD_Tables/HVPS_Spectrometer_Comparison/' + file_created_date
                   + '/' + str(FlightDate) + '/'
                   + str(starttime) + '_' + str(endtime) +'/') is False:   
    os.mkdir('./PSD_Tables/HVPS_Spectrometer_Comparison/' + file_created_date
              + '/' + str(FlightDate) + '/' + str(starttime) + '_' + str(endtime) +'/')



pathname_plots = ('./PSD_Plots/HVPS_Spectrometer_Comparison/' + str(file_created_date)
            + '/'  + str(FlightDate) + '/' + str(starttime) + '_' + str(endtime) +'/')
pathname_tables = ('./PSD_Tables/HVPS_Spectrometer_Comparison/' + str(file_created_date)
            + '/'  + str(FlightDate) + '/' + str(starttime) + '_' + str(endtime) +'/')

tempTime = HVPS_Indx_Start
for x in range(HVPS_binned[0][0].shape[0]): #len(SpecPlotLists)
    fig = plt.figure(figsize = [23.0,20.0]) #in x in
    # Plot title     need to include date
    #print(x, "x")
    tempRange = int(HVPSTimeConv[tempTime]) + TimeResolution
    timeRange = str(HVPSTimeConv[tempTime][0:2] +':'+
                    HVPSTimeConv[tempTime][2:4] +':'+
                    HVPSTimeConv[tempTime][4:6]) + "-" + str(
                        str(tempRange)[0:2] +':'+
                        str(tempRange)[2:4] +':'+
                        str(tempRange)[4:6])
    plt.title("HVPS and Hail Spectrometer Comparison,\n" + timeRange, fontsize=50)
    print('Hi')
    
    tableNameSpec = pathname_tables + "/Spec_Conc_per_Bin_" + str(FlightDate)\
                    + '_' + HVPSTimeConv[tempTime]+'-'+ \
                      str(tempRange) +'.txt'
    filein = open(tableNameSpec, "w+")
    filein.write('{z:<7}{q:<18}{a:<18}'.format\
                   (z='Bin', q='Bin_Size_Min(cm)', a='Spec_Conc(#/m^4)'))
    filein.write('\n\n')
    if new_spec_file_tracker == 'y': 
        for y in range(xaxis2.shape[0]):
            filein.write('{z:<7}{q:<18}{a:<18}'.format(z=int(y +1), q=float(xaxis2[y]), a=Spec_binned[0][0][x][y]))
            filein.write('\n')
    elif new_spec_file_tracker == 'n':
        for y in range(xaxis2.shape[0]):
            filein.write('{z:<7}{q:<18}{a:<18}'.format(z=int(y +1), q=float(xaxis2[y]), a=Spec_binned[0][x][y]))
            filein.write('\n')
    filein.close()
    

        
    
    tableNameHvps = pathname_tables + "/Hvps_Conc_per_Bin_" + str(FlightDate) \
                    + '_' + HVPSTimeConv[tempTime]+'-'+ \
                      str(tempRange) +'.txt'
    filein = open(tableNameHvps, "w+")
    filein.write('{z:<7}{q:<18}{b:<18}'.format\
                   (z='Bin', q='Bin_Size_Min(cm)', b='Hvps_Conc(#/m^4)'))
    filein.write('\n\n')
    for y in range(xaxis3.shape[0]):
        #print(x, y)
        filein.write('{z:<7}{q:<18}{b:<18}'.format(z=int(y +1), q=float(xaxis3[y]), b=HVPS_binned[0][0][x][y]))
        filein.write('\n')
    filein.close()
    
    
    
    plt.yscale("log")
    
    testidx2 = np.isfinite(np.log(HVPS_binned[0][0][x]), where=True)
    
    plt.scatter(xaxis3[testidx2], HVPS_binned[0][0][x][testidx2], label='HVPS', s=500)
    
    if new_spec_file_tracker == 'y': 
        testidx = np.isfinite(np.log(Spec_binned[0][0][x]), where=True)
        plt.scatter(xaxis2[testidx], Spec_binned[0][0][x][testidx], label='Spec - SODA', s=500)
    elif new_spec_file_tracker == 'n':    
        testidx = np.isfinite(np.log(Spec_binned[0][x]), where=True)
        plt.scatter(xaxis2[testidx], Spec_binned[0][x][testidx], label='Spec - SDSMT/UND', s=500)



    plt.ylim(bottom=0)
    plt.xticks(fontsize=50) 
    plt.yticks(fontsize=50)       
    plt.xlabel("Bin Size (cm)", fontsize=50)
    plt.ylabel("Conc (#/m^4)", fontsize=50)
    plt.legend(fontsize=50)

    plt.show()
    
    if new_spec_file_tracker == 'y':
        title_clarify  = '2D'
    elif new_spec_file_tracker == 'n': 
        title_clarify  = '1D'
        
    fig.savefig(pathname_plots \
                    + title_clarify + '_' + HVPSTimeConv[tempTime]+'-'+ \
                      str(tempRange) + '.png')#, bbox_inches = 'tight')
    fig.clf()
    
    tempTime += int(1 * TimeResolution / SodaPreChunk)



#final_indx != None so make a note on the final one

#Closing the files
#-----------------
airplanedata.close()
