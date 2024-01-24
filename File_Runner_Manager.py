#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 13:46:42 2024

@author: james.klinman

command to run

what it does
"""

import json
import os

#Creating File_Runner_Info if it doesn't exist
#Initializing dictionaries too
if not os.path.exists("Param_Info/File_Runner_Info.txt"):
    flight_nums = []
    programs_to_run = []
    with open("Param_Info/File_Runner_Info.txt", 'w') as file:
        data = {'flight_num': flight_nums,
                'programs_to_run': programs_to_run}
        json.dump(data, file, indent=2)
    print("File_Runner_Info was created")
else:
    print('File_Runner_Info exists')

#Loading in file data
with open('Param_Info/File_Runner_Info.txt', 'r') as file:
    file_content = file.read()

print('here')
    
#Showing file data
data = json.loads(file_content)
print(data)
print('')

changes_ask = input("Would you like to make changes (y/n)?   ")

if changes_ask == 'y' or changes_ask == 'Y':
    print("\n\nWhat would you like to change?")
    print("The options are, \n flight_num (f) \n programs_to_run (p)")
    update_data = input("For example, to do both, type 'f, p' without the ''\n")
    update_data = update_data.replace(" ", "")
    update_data = update_data.split(',')
    
    if 'f' in update_data:
        flight_nums = input("What flight numbers would you like to include?\n"
                            "Include any that are currently in the list.\n\n"
                            "Example: 123,234,987\n\n")
        flight_nums = flight_nums.replace(' ', '')
        flight_nums = flight_nums.split(',')
        data['flight_num'] = flight_nums

            
    if 'p' in update_data:
        programs = input("\nWhat programs would you like to run?\n"
                            "Include any that are currently in the list.\n\n"
                            "Example (be sure to copy file name exactly): " 
                            "Flight_Index_Finder.py, Aircraft_Plotting.py\n\n")
        programs = programs.replace(' ', '')
        programs = programs.split(',')
        data['programs_to_run'] = programs
    
    with open("Param_Info/File_Runner_Info.txt", 'w') as file:
        json.dump(data, file, indent=2)
        