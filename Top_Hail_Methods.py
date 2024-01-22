# -*- coding: utf-8 -*-
"""
Created on Thu Jul 27 09:17:30 2023

@author: james.klinman

IMPORTANT NOTE. I HAVE NOT TESTED ALL OF THE FUNCTIONS IN HERE SINCE UPDATING. 
IF ONE DOES NOT WORK THAT IS BECAUSE IT IS MISSING PARAMETERS MOST LIKELY
-UPDATE1 TO BIG NOTE. ONLY THE TIME FUNCS HAVENT BEEN TESTED NOW. EXCEPT TIMECONVDEC. THAT ONE WORKS
-UPDATE2 I want to edit all the time loops to accept a list of times. Or have someway
         to identify that it's a list or just a single value. So that way it's
         more robust
-
"""

import math
import numpy as np
import math

def sep_HHMMSS(time):
    "Accepts a list of times in the format HHMMSS. Must be a list or int."
    if type(time) is list:
        timelist = []
        tempiter = 0
        for x in time:
            if len(str(x)) == 6: 
                HH = str(x)[0:2]
                MM = str(x)[2:4]
                SS = str(x)[4:6]
                templist = []
                templist.append(HH)
                templist.append(MM)
                templist.append(SS)
                timelist.append(templist)
                tempiter += 1 
            else:
                return print("Issue at index =", tempiter, \
                             "Format must be numbers representing HHMMSS. Can be int or str. Should be 6 digits/characters")
        return timelist
    elif type(int(time)) is int:
        if len(str(time)) == 6: 
            HH = str(time)[0:2]
            MM = str(time)[2:4]
            SS = str(time)[4:6]
            timelist = []
            timelist.append(HH)
            timelist.append(MM)
            timelist.append(SS)
            return timelist
        else:
            return print("format must be numbers representing HHMMSS. Can be int or str. Should be 6 digits/characters")
        
    else:
        return(print("Data type not recognized. PLease make sure you're using"\
                     " either a single interger, or a list of intergers or strings."))


def HHMMSS_2_Dec(HHMMSS, timeCorrect=None):
    "timecorrect is time zone is diference from gmt"
    #can simplify and just do as hr min sec. not start and end
    #Can also include the sep_HHMMSS in this func so we don't have to type indv things
    if timeCorrect == None: #need to set to a number or addition below won't work
        timeCorrect = 0
        
    if type(HHMMSS) is int or type(HHMMSS) is str:
        allTime = sep_HHMMSS(HHMMSS)
        HH = int(allTime[0])
        MM = int(allTime[1])
        SS = int(allTime[2])
        MinConv = MM/60
        SecConv = SS/3600
        TimeConv = float(HH + MinConv + SecConv + timeCorrect) #+timezone's are to correct to GMT which the data is stored as
        if TimeConv >= 24: #bc time doesn't go over 24hrs
            TimeConv = TimeConv - 24
        return(TimeConv)
    elif type(HHMMSS) is list:
        timelist = []
        for x in HHMMSS:
            allTime = sep_HHMMSS(x)
            HH = int(allTime[0])
            MM = int(allTime[1])
            SS = int(allTime[2])
            MinConv = MM/60
            SecConv = SS/3600
            TimeConv = float(HH + MinConv + SecConv + timeCorrect) #+timezone's are to correct to GMT which the data is stored as
            if TimeConv >= 24: #bc time doesn't go over 24hrs
                TimeConv = TimeConv - 24
            timelist.append(TimeConv)
        return timelist


def dec2HHMMSS(timeDec, timeCorrect=None):
    "timeCorrect has to be + or - depending on time zone"
    HH = int(timeDec//1)
    updateDec = timeDec - HH
    MM = int(updateDec * 60 // 1)
    SS = int((updateDec * 60 - MM) * 60)
    
    return str(HH + timeCorrect) + str(MM) + str(SS)
    
    
def HHMMSS_2_SS(timeList):
    #Assumes HHMMSS format. No Decimal. No colons. Should be str
    newTimeList = []
    for x in timeList:
        if x.isdigit() != True:
            print("Warning: " + x + "is not an int")
            #print(x + "is on line" + index(timeList[x])) #
            pass
        else:
            HH = (int(x[0:2]) * 3600)#get HH and converts to sec
            MM = (int(x[2:4]) * 60)
            SS = (int(x[4:6]))
            tempTotTime = HH + MM + SS
            newTimeList.append(tempTotTime)
    Time_in_seconds = newTimeList
    return(Time_in_seconds)

    
def timeZone_adjustSec(timeList, timeZone):
    #adjusts list of time in 
    #timezone should be in hrs
    timeZone2 = timeZone * 3600
    newTimeList = []
    for x in timeList:
        newTimeList.append(x + timeZone2)
    TimeZone_Converted = newTimeList
    return(TimeZone_Converted)


def seconds_HHMMSS(timeList, timeZone=None):
    #takes interger values, not strings. idk if floats work
    if timeZone == None:
        timeZone = 0
    newtimeList = []
    for x in timeList:
        HH = int(math.floor(x/3600) + timeZone)
        temp = (x + timeZone*3600)%3600
        MM = int(math.floor((temp/60)))
        SS = int(temp%60)
        if len(str(SS)) != 2:
            SS = "0" + str(SS)
        newtimeList.append(str(HH) + str(MM) + str(SS))
        
        #newtimeList.append(time.strftime("%H%M%S", time.gmtime(x)))
    timeSec_toHHMMSS = newtimeList
    return(timeSec_toHHMMSS)


def find_loc_in_array(dataset, valueToFind, startLoc=None):
    """
    airplane time needs to be in decimal format
    have to make sure airplane time and input time are same timezone
    this also assumes a 20 hertz measurement 
    """
    #Currently just tested for netcdf. Need to expand to include list functionality
    #and probably things like arrays and pd datasets
    #just does 2D arrays
    
    xvar = 0
    yvar = 0
        
    if startLoc == None:
        if type(dataset.shape) is tuple: #works for netcdf. idk about other tuples
            #sort through x, y=0, go back a few rows, then search through the data more accurately to get the correct time
            #so that it sorts through 3000-4000 data entries instead of up to 80000
            while round(float(dataset[xvar, 0]), 3) != round(valueToFind, 3):  
                if dataset[xvar, 0] == valueToFind:
                    break
                elif dataset[xvar, 0] != valueToFind:
                    xvar = xvar + 1
        
            xvarmin = xvar - 3 #random, just goes back a few rows to start the
                                # more thourough search
            #search through each indv location in array now that it's close to the
            #location it's looking for
            while round(float(dataset[xvarmin, yvar]), 5) != round(valueToFind, 5):
                if dataset[xvarmin, yvar] == valueToFind:
                    break
                elif yvar == 19:
                    yvar = 0
                    xvarmin = xvarmin + 1
                elif yvar < 19:
                    yvar = yvar + 1
                    
            xLoc = xvarmin
            yLoc = yvar
            return(xLoc, yLoc)
      
    elif startLoc != None:
        xvarmin = startLoc
        if type(dataset.shape) is tuple: #works for netcdf. idk about other tuples
            while round(float(dataset[xvarmin, yvar]), 5) != round(valueToFind, 5):
                if dataset[xvarmin, yvar] == valueToFind:
                    break
                elif yvar == 19:
                    yvar = 0
                    xvarmin = xvarmin + 1
                elif yvar < 19:
                    yvar = yvar + 1
                    
            xLoc = xvarmin
            yLoc = yvar
            return(xLoc, yLoc)
 

def find_loc_in_array_1D(dataset, valueToFind):
    "Does 1D arrays. Designed for spectrometer data which is in 5sec increments"
    xvar=0
    #sort through x, y=0, go back a few rows, then search through the data more accurately to get the correct time
    #so that it sorts through 3000-4000 data entries instead of up to 80000
    while float(dataset[xvar]) <= (float(valueToFind) + 10):  
        if float(dataset[xvar]) <= (float(valueToFind) + 10) and float(dataset[xvar]) >= (float(valueToFind) - 10):
            break
        else:
            xvar = xvar + 1

    xvarlist = [(xvar-2), (xvar-1), xvar, (xvar+1), (xvar+2)] #random, just goes back a few rows to start the
                        # more thourough search
    #search through each indv location in array now that it's close to the
    #location it's looking for
    minlist = []
    for x in xvarlist:
        minlist.append(abs(float(valueToFind) - float(dataset[x])))
    locinlist = np.argmin(minlist)
    xLoc = xvarlist[locinlist]
    return(xLoc)


def create_dataList(dataset, startxLoc, endxLoc,\
                    startyLoc=None, endyLoc=None):          
    if startyLoc != None or endyLoc != None:
        pass
    #have not written functionality to search through column syet
    
    datalist = []    
    for x in range(startxLoc, endxLoc): 
        datalist.append(float(dataset[x,0])) 
        #stores a data point for each sec of flight (1Hz instead of 20Hz)
        #this is for netcdf aircraft data
    return datalist


def get_rangeOfBounds(startxloc, endxloc, startyloc=None, endyloc=None):
    rangeboundx = endxloc - startxloc #don't need -1 bc already
    if startyloc != None and endyloc != None:
        rangeboundy = endyloc - startyloc #corrected to 0 index earlier
    else:
        rangeboundy = None
    
    return(rangeboundx, rangeboundy)
    
  
def getSweep(R, Hradar, aircraftAlt, radarlat, radarlon, radarAngles\
             , elevation, startxloc, endxloc, planelat, planelon):
    altlist = []
    #A loop to go through the large array and pull out time synchronized 
    #latitude data points from the time range we identified
    for x in range(startxloc, endxloc): 
        altlist.append(float(aircraftAlt[x,0])) #stores a data point for each sec of flight (1Hz instead of 20Hz)

    avgheight = sum(altlist) / len(altlist) - elevation
    
    planelatavg = sum(planelat) / len(planelat) #these are the avgs that could be wrong
    planelonavg = sum(planelon) / len(planelon)
    latdif = abs(abs(planelatavg) - abs(radarlat[0]))
    longdif = abs(abs(planelonavg) - abs(radarlon[0]))
    #haversine func to get dist between radar and airplane
    #i do not remember where i got it im sorry dave
    dist = 2 * 6378 * math.asin(math.sqrt(math.sin(latdif * math.pi / 180 / 2)**2 + math.cos(radarlat[0] * math.pi / 180) * math.cos(planelatavg * math.pi / 180) * math.sin(longdif * math.pi / 180 / 2)**2))

    minlist = []
    sweepheight = []
    for x in radarAngles:
        sweepheightsearch = math.sqrt(dist**2 + R**2 + 2 * dist * R * math.sin(x * math.pi / 180)) - R + Hradar 
        sweepheightsearch = sweepheightsearch * 1000 #to convert to meters
        minlist.append(abs(avgheight - sweepheightsearch))
        sweepheight.append(sweepheightsearch)
    sweepnumtouse = minlist.index(np.min(minlist))
    sweepnumtouse = sweepnumtouse

    anglee = float(radarAngles[sweepnumtouse])
    
    return(anglee, sweepnumtouse, avgheight, sweepheight)

def sizechange(numberlist, numberofcharacters):
    # takes a list and maybe can do arrays too of numbers and returns them
    #shortened to the specified number of characters
    #include decimal points as characters
    outlist = []
    for x in numberlist:
        outnum = str(x)
        if len(outnum) < numberofcharacters:
            outnum = outnum +'0'
        elif len(outnum) > numberofcharacters:
            outnum = ''
            for y in range(4):
                outnum = outnum + str(x)[y]
        outlist.append(float(outnum))
    return(outlist)

def forceHHMMSS(data):
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

def HHMMSS_resetHH(time):
    #this if statement adjusts the time so that it isn't over 24 hours
    if int(str(time)[0:2]) >= 24: 
        newhour = int(str(time)[0:2]) - 24
        newtime = str(newhour) + str(time)[2:6]
    elif int(str(time)[0:2]) <= 24:
        newtime=str(time)
    return newtime    

def HHMMSS_adjustHH(time, adjust_amount):
     #changes the HH value by the amount specified
     newhour = int(str(time)[0:2]) + adjust_amount
     newtime = str(newhour) + str(time)[2:6]
     return newtime
 
def month_maker(month):
    #turns month into str so that the 
    #string can be deleted in the disp files
    if month == '06':
        output = 'Jun'
    if month == '07':
        output = 'Jul'
    return(output)

def year_maker(year):
    #turns month into str so that the 
    #string can be deleted in the disp files
    if year == '1995':
        output = '95'
    if year == '2000':
        output = '0'
    return(output)