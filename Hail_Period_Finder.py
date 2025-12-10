#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 14:25:44 2024

@author: james.klinman
"""

import os
import sys
import pandas as pd
import numpy as np
#import Top_Hail_Methods as hail
import matplotlib.pyplot as plt
import math
import netCDF4
from datetime import date
import pickle
import json
import re
from statistics import mode
import scipy



path_to_flight =  '../../yr2000/f757/'
flight_num = '757'

counts_file = path_to_flight + 'disp' + flight_num + '.0'



def SDSMT_disp_txt_read(dispfile):  
    file_read = 0
    try:
        strToDelete = 'F l i g h t  ...  ........  Hail Info'
        endoffiletodelete = '-=-  Hail Dump Complete  -=-'
        fin = open(dispfile, "r")
        fout = open("Random/Spec_Corrected_File", "w+")
        for line in fin:
            line = re.sub(strToDelete, '' , line)
            line = re.sub(endoffiletodelete, '', line)
            fout.write(line)
        fin.close()
        fout.close()
        
        file_read = 1
    except:
        pass
    
    if file_read == 0:
        try:
            strToDelete = 'F l i g h t  ...  .........  Hail Info'
            endoffiletodelete = '-=-  Hail Dump Complete  -=-'
            fin = open(dispfile, "r")
            fout = open("Random/Spec_Corrected_File", "w+")
            for line in fin:
                line = re.sub(strToDelete, '' , line)
                line = re.sub(endoffiletodelete, '', line)
                fout.write(line)
            fin.close()
            fout.close()
            
        except:
            pass
            
  
    #first loop from https://pynative.com/python-count-number-of-lines-in-file/
    #gets length of file and get reads in just the spec data
    with open(r"Random/Spec_Corrected_File", 'r') as file:
        for count, line in enumerate(file):
            pass
        FileLen = count + 1
    Spacing = 55          #these skips are hardcoded in. They're specific to
    RowsToSkip = []       #this type of file so it shouldn't matter that they 
    RowsToSkip.append(57) #aren't dynamically found
    NewHeadSkip = 57
    while NewHeadSkip <= FileLen:
        NewHeadSkip += Spacing
        RowsToSkip.append((NewHeadSkip))
    SpecFile = "Random/Spec_Corrected_File"
    SpecData = pd.read_csv(SpecFile, sep=' * ', header=0, skiprows=RowsToSkip, engine='python')
    
    return SpecData




#reading in coutns file
counts_data = SDSMT_disp_txt_read(counts_file)


#creating search function to look for periods where there's hail
#-----------------
#list of channels headers
channels = [str(i) for i in range(1, 15)]

#rows with counts
rows_with_counts = counts_data[(counts_data[channels] > 0).any(axis=1)]

#Get the indices of those rows
indices = rows_with_counts.index.tolist()


#Searching for indices that are 10 long so that there are at least 10 seconds
#of continuous data

grouped_indices = []
temp_array = []
counter = 0
for x in indices:
    if counter == 0: #just initilizing here
        temp_array.append(x)
        counter += 1
    else:
        if x == (temp_array[-1] + 1):
            temp_array.append(x)
        else:
            grouped_indices.append(temp_array)
            temp_array = []
            temp_array.append(x)

    
