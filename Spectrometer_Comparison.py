                                                                            #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 11:54:20 2023

@author: james.klinman
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


#this is just bob. dont mind bob
player = 'bob'

filename = player+'.txt'

if os.path.exists(filename):
    append_write = 'a' # append if already exists
else:
    append_write = 'w' # make a new file if not

highscore = open(filename,append_write)
highscore.write("Username: " + player + '\n')
highscore.close()


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
plane_time_start = getattr(airplanedata, 'TimeInterval')[0:8]
for char in plane_time_start:
    if char == ':':
        plane_time_start = plane_time_start.replace(':', '')

#Now can finally call concentration file names
#---------------------------------------------
filenameHVPS = path_to_flight + '/SODA_Outputs/' + FlightDate_File + '_' +\
                FlightTimeStart + '_HVPS1.txt'

filenameSpec = path_to_flight + '/disp' + FlightNum + '.0'

#y means counts, n means conc from soda
#!!!note for future self. if filename ends in txt or 1Hz can then specify
#if you want to do adppa or soda
#then next step can be to see if 1Hz is conc or counts in name
#although i don't think there would be any reason to use concs since
#that should theoretically be the same as SODA output .txt
sodaconcversion = 'y'

filenameSpec2 = path_to_flight + '/SODA_Outputs/00_06_22_23_29_21.HAIL_V.counts.1Hz'   #counts

#filenameSpec2 = path_to_flight + '/SODA_Outputs/' + FlightDate_File + '_' +\
#                FlightTimeStart + '_HAIL.txt'    #concs


#spec 2 is treated as the soda calc conc but it should be switchable with 
# just spec if you wanted to flip the two for some reason
                

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

time_index_to_use = iterationTracker['Iteration'][0]# * \
    #iterationTracker['Skip_Num'][0]
time_index_to_use = 2                                         #  to only do first one

starttime = str(initParameters['Time_Start'][time_index_to_use])
endtime = str(initParameters['Time_End'][time_index_to_use])
timeZone = int(initParameters['Timezone_true'][0])

#Defining relevant information that is used in the math and
#binning that happens later on.
#---------------------------------------------------------

#final temporal resolution of particle size distribution
TimeResolution = int(initParameters['PSD_Time_Res'][0])

#SODA defaults to a rate of 5 seconds So this just hardcodes that in.
SodaPreChunk = 5
                
#Bin size is used in calculating concentration later on 
#It's the change in width for each channel
BinSize = np.array([.1, .1, .1, .1, .14, .16, .20, .26, .30, .31, .44, .60,\
                    .79, 1])
BinSize = BinSize / 100 #to correct for cm -> m


#These are the bin start/endpoints. Units are in cm.
xaxis = np.array([.02, .04, .06, .08, .1, .12, .14, .16, .18, .22, .26, .3, \
                  .35, .4, .5, .6, .7, .8, .94, 1.1, 1.3, 1.56, 1.86, 2.17, \
                  2.61, 3.21]) #hvps bins

xaxis2 = np.array([.4, .5, .6, .7, .8, .94, 1.1, 1.3, 1.56, 1.86, 2.17, 2.61,\
                   3.21, 4]) #channels for Hail spectrometer

xaxis4 = np.array([.45, .55, .65, .75, .87, 1.02, 1.2, 1.43, 1.71, 2.015, \
                   2.39, 2.91, 3.605, 4.5]) #hail bin midpoints

xaxis3 = np.array([.02, .04, .06, .08, .1, .12, .14, .16, .18, .22, .26, .3,\
                   .34, .38, .42, .46, .5, .6, .7, .8, .9, 1, 1.5, 2, 2.5])
#xaxis3 is the default soda bins

"""
#Sample area adjusted for all in
#100x10 cm minus the particle size
SAx = []
SAy = []
for x in xaxis4:
    SAx.append(100 - x)
    SAy.append(10 - x)

SA = []    
for x in range(len(SAx)):
    xlen = SAx[x] / 100
    ylen = SAy[x] / 100
    SA.append(xlen * ylen)
"""
SA = .1 #sample area for not all in
#stopped using all in in 1981 so it should just be .1 i think


#----------------------------------------------------------------------
#Next big chunk of code is reading in the counts and concentration files
#----------------------------------------------------------------------


#Preping HVPS data
#-----------------
HVPSData = pd.read_csv(filenameHVPS, sep=' * ', header=22, engine='python')
tempdf = pd.DataFrame(HVPSData)
tempdf = tempdf.drop(index=0)
HVPSData = pd.DataFrame.reset_index(tempdf)


#try and except because so far two variations f hail spectormeter data have
#been run through this program. The try works if the data file is from SODA,
#and the except works for the output generated by the South Dakota School of Mines
#---------------------------------------------------------------------------------
try:
    #easier to read spec data from SODA
    SpecData = pd.read_csv(filenameSpec, sep=' * ', header=22, engine='python')
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
    
    strdate = FlightDateSplit[1]
    strmonth = hail.month_maker(FlightDateSplit[0])
    stryear = hail.year_maker(FlightDateSplit[2])
    finalfmt = strdate + '-' + strmonth + '-' + stryear
    
    strToDelete = ['F l i g h t  ' + flight_num + '  ' + finalfmt + '  Hail Info']                         #needs updating!!!!!!!!
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
    SpecData = pd.read_csv(SpecFile, sep=' * ', header=0, skiprows=RowsToSkip, engine='python')
    #spec data is stored in local time not utc. need to add 6hrs
    
    #need this since the files are in their local timezones time instead of utc
    starttimeSpec = hail.HHMMSS_adjustHH(starttime, (-(timeZone)))
    endtimeSpec = hail.HHMMSS_adjustHH(endtime, (-(timeZone)))
    starttimeSpec = hail.forceHHMMSS(starttimeSpec)
    endtimeSpec = hail.forceHHMMSS(endtimeSpec)
    
    #determines which if statement to enter in a couple of the steps later on 
    new_spec_file_tracker = 'n'
    
try:
    #easier to read spec data from SODA
    if sodaconcversion == 'n':
        SpecData2 = pd.read_csv(filenameSpec2, sep=' * ', header=22, engine='python')   #for the conc version
    elif sodaconcversion == 'y':
        SpecData2 = pd.read_csv(filenameSpec2, sep=' * ', header=31, engine='python')    #for the counts version
    tempdf3 = pd.DataFrame(SpecData2)
    tempdf3 = tempdf3.drop(index=0)
    SpecData2 = pd.DataFrame.reset_index(tempdf3)
    #HVPSDataDF = pd.DataFrame(HVPSData) 
    #note for below, minimum time resolution can be 5
    
    #determines which if statement to enter in a couple of the steps later on
    new_spec_file_tracker2 = 'y'

except:
    #Preping Spectrometer data
    #got the below chunk of code from https://stackoverflow.com/questions/7356043/how-to-delete-specific-strings-from-a-file
    #it deletes all the new page headers that are attached to the rows of data
    #strToDelete = ['F l i g h t  668  22-Jun-95  Hail Info'] #header to delete for each page
    strToDelete = ['F l i g h t  ' + flight_num + '  ' + finalfmt + '  Hail Info']
    endoffiletodelete = '-=-'
    fin = open(filenameSpec2, "r")
    fout = open("Random/Spec_Corrected_File2", "w+")
    for line in fin:
        for word in strToDelete:
            line = line.replace(word, "")
        fout.write(line)
    fin.close()
    fout.close()
    
    #first loop from https://pynative.com/python-count-number-of-lines-in-file/
    #gets length of file and get reads in just the spec data
    with open(r"Random/Spec_Corrected_File2", 'r') as file:
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
    SpecFile2 = "Random/Spec_Corrected_File2"
    SpecData2 = pd.read_csv(SpecFile2, sep=' * ', header=0, skiprows=RowsToSkip, engine='python')
    #spec data is stored in local time not utc. need to add 6hrs
    
    #need this since the files are in their local timezones time instead of utc
    starttimeSpec2 = hail.HHMMSS_adjustHH(starttime, (-(timeZone)))
    endtimeSpec2 = hail.HHMMSS_adjustHH(endtime, (-(timeZone)))
    starttimeSpec2 = hail.forceHHMMSS(starttimeSpec2)
    endtimeSpec2 = hail.forceHHMMSS(endtimeSpec2)
    
    #determines which if statement to enter in a couple of the steps later on 
    new_spec_file_tracker2 = 'n'


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



#Making sure the starttime used by spec aligns with the start time from hvps
#---------------------------------------------------------------------------
hvps_time_start = HVPSData['Time'][HVPS_Indx_Start]
hvps_time_end = HVPSData['Time'][HVPS_Indx_End]
hvps_2_hhmmss_s = hail.seconds_HHMMSS([int(HVPSData['Time'][HVPS_Indx_Start])])[0]
hvps_2_hhmmss_e = hail.seconds_HHMMSS([int(HVPSData['Time'][HVPS_Indx_End])])[0]
if hvps_time_start != hvps_2_hhmmss_s:
    starttime_adjust = hvps_2_hhmmss_s
if hvps_time_end != hvps_2_hhmmss_e:
    endtime_adjust = hvps_2_hhmmss_e


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
            
if new_spec_file_tracker2 == 'y':
    SpecStartTimeIndx2 = hail.find_loc_in_array_1D(SpecData2['Time'], hail.HHMMSS_2_SS([starttime_adjust])[0])
    SpecEndTimeIndx2 = hail.find_loc_in_array_1D(SpecData2['Time'], hail.HHMMSS_2_SS([endtime_adjust])[0])

#if you're getting an error with the start and endtimeSpec, then copy the method
#from the starttime_adjust for the HVPS for the Spec here. Not tested since I
#haven't run f668 through this updated program yet
elif new_spec_file_tracker2 == 'n':
    #not tested for if the index is in line with one of the omitted rows
    SpecStartTimeIndx2 = None
    SpecEndTimeIndx2 = None
    tempiter = 0
    for x in SpecData2['Time']:
        if x == '-=-':  #this means you're at the end of the file
            break
        if str(int(float(x))) == str(starttime_adjust): #need starttimeSPec if its 1995, but adjust if it's 2000   .....
            SpecStartTimeIndx2 = tempiter
        if str(int(float(x))) == str(endtime_adjust):
            SpecEndTimeIndx2 = tempiter
            break
        else:
            tempiter +=1

#Getting the plane data index's now
#--------------------------------------
#starttimeTAS = hail.HHMMSS_resetHH(starttime)
#endtimeTAS = hail.HHMMSS_resetHH(endtime)

#starttimeTAS = hail.forceHHMMSS(starttimeTAS)
#endtimeTAS = hail.forceHHMMSS(endtimeTAS)

starttimeTAS = starttime_adjust
endtimeTAS = endtime_adjust

PlaneStartIndx = None
PlaneEndIndx = None
tempiter = 0
#TAS file is in HHMMSS and resets after 24hrs 
for x in TASfile['HHMMSS']:
    if int(x[0:2]) < 10: #checks for times less before 10utc bc tas is in 001320 whereas specdata is in 241320
        x = int(x) + 240000
    if str(x) == str(starttimeTAS):
        PlaneStartIndx = tempiter
    if str(x) == str(endtimeTAS):
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
        if spectime == int(TASfile['HHMMSS'][x]):
            PlaneSpeeds.append(TASfile['Calc_Airspeed'][x])
        else:
            pass

        
#-------------------------------------------------------
#Chunking the data together now and applying corrections
#-------------------------------------------------------

def soda_chunking22(conc_amount, chunk_size, soda_res, indx_start, indx_end,
                  soda_data):
    """
    Notes: conc amount is 14 or 25 i think.
    """      
    #creating the empty numpy arrays to store the data in
    array_len = math.ceil(
        (indx_end - indx_start) / (chunk_size / soda_res))
    hvps_chunks = np.zeros((array_len, conc_amount), dtype=float)

    chunk_tracker = 0
    second_tracker = 0
    for indexes in range(indx_start, indx_end): 
        #now we're into each row
        array_binnum = 0 #the array we're making starts with 0 but the channels start with 1
        for binnum in range(1, conc_amount):
            #now we're looping through each bin
            if binnum < 10:
                temp_binnum = 'Conc' + str(0)+str(0)+str(binnum)
            else:
                temp_binnum = 'Conc' + str(0)+str(binnum)
            hvps_chunks[chunk_tracker, array_binnum] = \
                hvps_chunks[chunk_tracker, array_binnum] + \
                    float(soda_data[str(temp_binnum)][indexes]) #float for conc, int for counts
            array_binnum += 1
        
        #since soda is prechunked to 5, this keeps track of the 5 second intervals
        second_tracker += soda_res   

        #once specified chunk of time is reached, specifies to start adding to
        #the next chunk
        if second_tracker == chunk_size: 
            second_tracker = 0
            chunk_tracker += 1

        if indexes == SpecEndTimeIndx:
            if second_tracker != 0:
                print('seconds in final bin are', second_tracker)

    return(hvps_chunks) #need to test on hvps data that isn't resetting
    
    
def sdsmt_chunking22(sdsmt_data, conc_amount, chunk_size, indx_start, indx_end,
                   bin_correction, surface_area, airspeed):
    
    #first need to create an array of array froms the sdsmt hail
    #counts file and then we can operate on those arrays
    array_len = math.ceil((indx_end - indx_start))
    spec1d_seconds = np.zeros((array_len, conc_amount), dtype=float)
    
    row_counter = 0
    for indexes in range(indx_start, indx_end):
        #now we're into each row
        array_binnum = 0 #the array we're making starts with 0 but the channels start with 1
        for binnum in range(1, conc_amount):
            #now we;re looping through each channel
            spec1d_seconds[row_counter, array_binnum] = \
                int(sdsmt_data[str(binnum)][indexes]) #hail counts should be int anyways
            array_binnum += 1
        row_counter += 1
    
    #now to apply math/corrections to the data to get it in
    #units of #/m^4
    print(spec1d_seconds.shape, len(airspeed))
    spec1d_seconds = spec1d_seconds / bin_correction / SA
    for second in range(spec1d_seconds.shape[0]):
        spec1d_seconds[second] = spec1d_seconds[second] / airspeed[second]
    
    
    #Now to chunk all of those rows together into the specified chunk size
    array_len = math.ceil((indx_end - indx_start) / chunk_size)
    spec1d_chunks = np.empty((array_len, conc_amount), dtype=float)
   
    low_indx = 0
    high_indx = chunk_size
    for chunk in range(array_len):
        spec1d_chunks[chunk] = np.sum(spec1d_seconds[low_indx:high_indx], axis=0)
        low_indx += chunk_size
        high_indx += chunk_size
        
        if high_indx > indx_end:
            print('Final chunk has less than ' +str(chunk_size)+ ' seconds')
            
    return(spec1d_chunks) 

def adpaa_chunking22(adpaa_data, conc_amount, chunk_size, indx_start, indx_end,
                   bin_correction, surface_area, airspeed, soda_res):
    #first need to create an array of array froms the sdsmt hail
    #counts file and then we can operate on those arrays
    array_len = math.ceil((indx_end - indx_start))
    spec2d_seconds = np.zeros((array_len, conc_amount), dtype=float)
    
    ch = 'HAILV_CH'
    row_counter = 0
    for indexes in range(indx_start, indx_end):
        #now we're into each row
        array_binnum = 0 #the array we're making starts with 0 but the channels start with 1
        for binnum in range(1, conc_amount):
            #now we;re looping through each channel
            spec2d_seconds[row_counter, array_binnum] = \
                int(adpaa_data[ch + str(binnum)][indexes]) #hail counts should be int anyways
            array_binnum += 1
        row_counter += 1
    
    #since temporal resolution is 5sec out of soda, need to average speed
    #over those 5 seconds
    airspeed_chunks = np.zeros(math.ceil(len(airspeed)/soda_res))
    chunk_tracker = 0
    second_tracker = 0
    for speed in airspeed:
        airspeed_chunks[chunk_tracker] = airspeed_chunks[chunk_tracker] + \
                                         speed
        second_tracker += 1
        if second_tracker == 5:
            second_tracker = 0
            chunk_tracker += 1
    airspeed_chunks = airspeed_chunks / soda_res
        
    if second_tracker != 0:
        print('Final time interval only has ' + str(second_tracker) + ' seconds of airplane data')
            
    #now to apply math/corrections to the data to get it in
    #units of #/m^4
    spec2d_seconds = spec2d_seconds / bin_correction / SA
    
    for interval in range(spec2d_seconds.shape[0]):
        spec2d_seconds[interval] = spec2d_seconds[interval] / airspeed_chunks[interval]
        
    #Now to chunk all of those rows together into the specified chunk size
    array_len = math.ceil((indx_end - indx_start) / (chunk_size / soda_res))
    spec2d_chunks = np.empty((array_len, conc_amount), dtype=float)
    
    low_indx = 0
    high_indx = chunk_size
    for chunk in range(array_len):
        spec2d_chunks[chunk] = np.sum(spec2d_seconds[low_indx:high_indx], axis=0)
        low_indx += int(chunk_size/soda_res)
        high_indx += int(chunk_size/soda_res)
        
        if high_indx > indx_end:
            print('Final chunk has less than ' +str(chunk_size)+ 'seconds')
            
    return(spec2d_chunks) 



"""
testsodaspecfile = path_to_flight + '/SODA_Outputs/06222000_232921_HAIL.txt'
specsodaData = pd.read_csv(testsodaspecfile, sep=' * ', header=22)
tempdftest = pd.DataFrame(specsodaData)
tempdftest = tempdftest.drop(index=0)
specsodaData = pd.DataFrame.reset_index(tempdftest)
"""

HVPS_binned = soda_chunking22(conc_amount=25, chunk_size=TimeResolution, 
                            soda_res=SodaPreChunk, 
                            indx_start=HVPS_Indx_Start, 
                            indx_end=HVPS_Indx_End,
                            soda_data=HVPSData) #i think it works. need good hvps data to test

SDSMT_Spec_binned = sdsmt_chunking22(sdsmt_data=SpecData, conc_amount=14,
                                   chunk_size=TimeResolution, 
                                   indx_start=SpecStartTimeIndx, 
                                   indx_end=SpecEndTimeIndx,
                                   bin_correction=BinSize, surface_area=SA, 
                                   airspeed=PlaneSpeeds)

if sodaconcversion == 'n':
    SODA_Spec_binned = soda_chunking22(conc_amount=14, chunk_size=TimeResolution, 
                                soda_res=SodaPreChunk, 
                                indx_start=SpecStartTimeIndx2, 
                                indx_end=SpecEndTimeIndx2,
                                soda_data=SpecData2) #update back to SpecData2 and the y/n is how you switch between them
elif sodaconcversion =='y':
    SODA_Spec_binned = adpaa_chunking22(adpaa_data=SpecData2, conc_amount=14,
                                       chunk_size=TimeResolution, 
                                       indx_start=SpecStartTimeIndx2, 
                                       indx_end=SpecEndTimeIndx2,
                                       bin_correction=BinSize, surface_area=SA, 
                                       airspeed=PlaneSpeeds, soda_res=SodaPreChunk)

"""
SODA_Spec_binned = adpaa_chunking22(sdsmt_data=SpecData2, conc_amount=14,
                                   chunk_size=TimeResolution, 
                                   indx_start=SpecStartTimeIndx2, 
                                   indx_end=SpecEndTimeIndx2,
                                   bin_correction=BinSize, surface_area=SA, 
                                   airspeed=PlaneSpeeds, soda_res=SodaPreChunk)
"""
#heres the frame where a point was missing
#SODA_Spec_binned[0][34], '\n', specsodaData['Conc014'][592], specsodaData['Conc014'][593], specsodaData['Conc014'][592]+specsodaData['Conc014'][593]

#----------------------------------------
#Plotting the data and making data tables
#----------------------------------------


FlightNum = str(getattr(airplanedata, 'FlightNumber'))
FlightDate = str(getattr(airplanedata, 'FlightDate'))
FlightDate = FlightDate.split('/')
FlightDate = FlightDate[2]+''+FlightDate[0]+''+FlightDate[1]

current_date = date.today()
file_created_date = current_date.strftime("%Y%m%d")



main_pathway_plot = path_to_folder + 'PSD_Plots/'
main_pathway_table = path_to_folder + 'PSD_Tables/'

main_pathway_plot2 = main_pathway_plot + 'Spectrometer_Comparison/'
if os.path.exists(main_pathway_plot2) is False:   
    os.mkdir(main_pathway_plot2)

main_pathway_plot3 = main_pathway_plot2 + file_created_date
if os.path.exists(main_pathway_plot3) is False:   
    os.mkdir(main_pathway_plot3)

main_pathway_plot4 = main_pathway_plot3 + '/' +str(FlightDate) + '/'
if os.path.exists(main_pathway_plot4) is False:   
    os.mkdir(main_pathway_plot4)

main_pathway_plot5 = main_pathway_plot4 + str(starttime) + '_' + str(endtime) +'/'
if os.path.exists(main_pathway_plot5) is False:   
    os.mkdir(main_pathway_plot5)
    
main_pathway_table2 = main_pathway_table + 'Spectrometer_Comparison/'
if os.path.exists(main_pathway_table2) is False:   
    os.mkdir(main_pathway_table2)

main_pathway_table3 = main_pathway_table2 + file_created_date
if os.path.exists(main_pathway_table3) is False:   
    os.mkdir(main_pathway_table3)

main_pathway_table4 = main_pathway_table3 + '/' + str(FlightDate) + '/'
if os.path.exists(main_pathway_table4) is False:   
    os.mkdir(main_pathway_table4)

main_pathway_table5 = main_pathway_table4 + str(starttime) + '_' + str(endtime) +'/'
if os.path.exists(main_pathway_table5) is False:   
    os.mkdir(main_pathway_table5)

pathname_plots = main_pathway_plot5
pathname_tables = main_pathway_table5


tempTime = HVPS_Indx_Start
for x in range(HVPS_binned.shape[0]): #len(SpecPlotLists)
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
    plt.title("Hail Spectrometer 1D and 2D Comparison,\n" + timeRange, fontsize=50)
    tableNameSpec = pathname_tables + "Spec_Conc_per_Bin_" \
                     + HVPSTimeConv[tempTime]+'-'+ \
                      str(tempRange) +'.txt'
    
    filein = open(tableNameSpec, "w+")
    filein.write('{z:<7}{q:<18}{a:<18}'.format\
                   (z='Bin', q='Bin_Size_Min(cm)', a='Spec_Conc(#/m^4)'))
    filein.write('\n\n')
    if new_spec_file_tracker == 'y': 
        for y in range(xaxis4.shape[0]):
            filein.write('{z:<7}{q:<18}{a:<18}'.format(z=int(y +1), q=float(xaxis4[y]), a=SDSMT_Spec_binned[x][y]))
            filein.write('\n')
    elif new_spec_file_tracker == 'n':
        for y in range(xaxis4.shape[0]):
            filein.write('{z:<7}{q:<18}{a:<18}'.format(z=int(y +1), q=float(xaxis4[y]), a=SDSMT_Spec_binned[x][y]))
            filein.write('\n')
    filein.close()
    
    
    
    tableNameSpec2 = pathname_tables + "Spec_Conc_per_Bin2_" \
                     + HVPSTimeConv[tempTime]+'-'+ \
                      str(tempRange) +'.txt'
    filein = open(tableNameSpec2, "w+")
    filein.write('{z:<7}{q:<18}{a:<18}'.format\
                   (z='Bin', q='Bin_Size_Min(cm)', a='Spec_Conc(#/m^4)'))
    filein.write('\n\n')
    if new_spec_file_tracker2 == 'y': 
        if sodaconcversion == 'n':
            for y in range(xaxis4.shape[0] - 1):
                filein.write('{z:<7}{q:<18}{a:<18}'.format(z=int(y +1), q=float(xaxis4[y]), a=SODA_Spec_binned[x][y]))
                filein.write('\n')   
        elif sodaconcversion =='y':
            for y in range(xaxis4.shape[0] - 1):
                filein.write('{z:<7}{q:<18}{a:<18}'.format(z=int(y +1), q=float(xaxis4[y]), a=SODA_Spec_binned[x][y]))
                filein.write('\n')
    elif new_spec_file_tracker2 == 'n':
        for y in range(xaxis4.shape[0]):
            filein.write('{z:<7}{q:<18}{a:<18}'.format(z=int(y +1), q=float(xaxis4[y]), a=SODA_Spec_binned[x][y]))
            filein.write('\n')
    filein.close()
    
    
    
        
    #old bit ignore not updated dont want to test commenting it out
    tableNameHvps = pathname_tables + "Hvps_Conc_per_Bin_" \
                     + HVPSTimeConv[tempTime]+'-'+ \
                      str(tempRange) +'.txt'
    filein = open(tableNameHvps, "w+")
    filein.write('{z:<7}{q:<18}{b:<18}'.format\
                   (z='Bin', q='Bin_Size_Min(cm)', b='Hvps_Conc(#/m^4)'))
    filein.write('\n\n')
    for y in range(xaxis3.shape[0]):
        #print(x, y)
        filein.write('{z:<7}{q:<18}{b:<18}'.format(z=int(y +1), q=float(xaxis3[y]), b=HVPS_binned[x][y]))
        filein.write('\n')
    filein.close()
    
    plt.yscale("log")
    plotbins_sdsmt = np.isfinite(np.log(SDSMT_Spec_binned[x]), where=True)
    plotbins_soda = np.isfinite(np.log(SODA_Spec_binned[x]), where=True)
    if new_spec_file_tracker2 == 'y': 
        if sodaconcversion == 'n':
            plt.scatter(xaxis4[plotbins_soda], SODA_Spec_binned[x][plotbins_soda], label='SODA', s=500)
        elif sodaconcversion == 'y':
            plt.scatter(xaxis4[plotbins_soda], SODA_Spec_binned[x][plotbins_soda], label='SODA', s=500)
    elif new_spec_file_tracker2 == 'n':
        plt.scatter(xaxis4[plotbins_soda], SODA_Spec_binned[x][plotbins_soda], label='SODA', s=500)
    
    try:
        if new_spec_file_tracker == 'y': 
            plt.scatter(xaxis4[plotbins_sdsmt], SDSMT_Spec_binned[x][plotbins_sdsmt], label='SDSMT/UND', s=500)
        elif new_spec_file_tracker == 'n':
            plt.scatter(xaxis4[plotbins_sdsmt], SDSMT_Spec_binned[x][plotbins_sdsmt], label='SDSMT/UND', s=500)
                    
    except UserWarning:
        print("Time Range " + str(timeRange) + " had no spectrometer data")

        

    """    
    testidx2 = np.isfinite(np.log(HvpsPlotListsArray[x]), where=True)
    try:
        plt.scatter(xaxis3[testidx2], HvpsPlotListsArray[x][testidx2], label='HVPS', s=500)

    except UserWarning:
        print("Time Range " + str(timeRange) + " had no HVPS data")
    """    

    plt.ylim(bottom=0)
    plt.xticks(fontsize=50) 
    plt.yticks(fontsize=50)       
    plt.xlabel("Bin Size (cm)", fontsize=50)
    plt.ylabel("Conc (#/m^4)", fontsize=50)
    plt.legend(fontsize=50)
    #plt.plot = np.polyfit(xaxis2, np.log(SpecPlotLists[x]), 1)
    #HVPSFit = np.polyfit(xaxis, np.log(HvpsPlotLists[x]), 1)
    #plt.show()
    fig.savefig(pathname_plots \
                    + '/' + HVPSTimeConv[tempTime]+'-'+ \
                      str(tempRange) + '.png')#, bbox_inches = 'tight')
    fig.clf()
    
    tempTime += int(1 * TimeResolution / SodaPreChunk)

#maybe save into a folder with the data dn the title of the program, then the time resolution
#then all the plots in there
#PSD_plots/Program/Date/TIme Res/all the plots woooo





#final_indx != None so make a note on the final one

#Closing the files
#-----------------
airplanedata.close()





#olllllllllllllllllllllllllllllllddddddddddddddddddddddddddddd
"""
def soda_chunking(conc_amount, chunk_size, soda_res, indx_start, indx_end,
                  soda_data):
    
    #Notes: conc amount is 14 or 25 i think.
        
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
            #temp_chunk = np.sum(temp_chunk, axis=0)
            #binned_data = np.append(binned_data, np.array([temp_chunk]), axis=0)
            #temp_chunk = np.empty((0, conc_amount), float)
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
    data_corrected = (data_corrected / bin_correction) / SA
      
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
    return(binned_data, final_bin)

def adpaa_chunking(sdsmt_data, conc_amount, chunk_size, indx_start, indx_end,
                   bin_correction, surface_area, airspeed, soda_res):
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
            columnname = 'HAILV_CH' + str(column)
            each_value = float(sdsmt_data[columnname][row])
            bin_corrected = np.append(bin_corrected, each_value)
        data_corrected = np.append(data_corrected, np.array([bin_corrected]),
                                   axis=0)   
    
    #particle counts / (airspeed * bin size * surface area)  = # / m^4
    #applying binsize and surface area correction
    data_corrected = (data_corrected / bin_correction) / SA
    
    #applying airspeed correction
    #need to chunk the airspeeds for the correction here so that they 
    #are averaged over the soda chunk size time interval since it's
    #counts per 5 seconds or 10 or whatver now.
    chunked_airspeeds_list = []
    soda_res_placeholder = 0
    for chunk in range(math.ceil(len(airspeed) / soda_res)):
        chunked_airspeed = 0
        chunk_updated = chunk * soda_res
        end_checker = 0
        for sec in range(soda_res):
            try:
                chunked_airspeed += airspeed[chunk_updated]
                chunk_updated += 1
            except:
                print("Final airspeed time interval less than 5 seconds")
                end_checker += 1
        if end_checker != 0:
            soda_res_placeholder = soda_res
            soda_res = soda_res - end_checker
        chunked_airspeed = chunked_airspeed / soda_res
        chunked_airspeeds_list.append(chunked_airspeed)
        if end_checker != 0:
            soda_res = soda_res_placeholder
        end_checker = 0
    for second in range(data_corrected.shape[0]):
        data_corrected[second] = data_corrected[second] / chunked_airspeeds_list[second]
    
    
    


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
        elif int(row) == int((chunk_size /soda_res * time_counter)+ indx_start - 1): 
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
    return(binned_data, final_bin)




#works. not tested for full set of hvps data that doesn't cut off though
#not tested for numbers at each step to check for accuracy yet either
HVPS_binned = soda_chunking(conc_amount=25, chunk_size=TimeResolution, 
                            soda_res=SodaPreChunk, 
                            indx_start=HVPS_Indx_Start, 
                            indx_end=HVPS_Indx_End,
                            soda_data=HVPSData) #fix this next

SDSMT_Spec_binned = sdsmt_chunking(sdsmt_data=SpecData, conc_amount=14,
                                   chunk_size=TimeResolution, 
                                   indx_start=SpecStartTimeIndx, 
                                   indx_end=SpecEndTimeIndx,
                                   bin_correction=BinSize, surface_area=SA, 
                                   airspeed=PlaneSpeeds)
if sodaconcversion == 'n':
    SODA_Spec_binned = soda_chunking(conc_amount=14, chunk_size=TimeResolution, 
                                soda_res=SodaPreChunk, 
                                indx_start=SpecStartTimeIndx2, 
                                indx_end=SpecEndTimeIndx2,
                                soda_data=SpecData2)
elif sodaconcversion =='y':
    SODA_Spec_binned = adpaa_chunking(sdsmt_data=SpecData2, conc_amount=14,
                                       chunk_size=TimeResolution, 
                                       indx_start=SpecStartTimeIndx2, 
                                       indx_end=SpecEndTimeIndx2,
                                       bin_correction=BinSize, surface_area=SA, 
                                       airspeed=PlaneSpeeds, soda_res=SodaPreChunk)
"""

