# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 13:46:42 2024

@author: james.klinman

command to run

what it does


notes to self
maybe add one where you can change a variable into another?

also need to add a specification that if doing the radar variable one, to do
in groupings of 2
"""

import json
import os
import ast

flight_num = str(input("What flight number do you want to manage? "))
flight_num = flight_num.replace(' ', '')

filename = flight_num + "_paramInfo.txt"

#Creating paramInfo file if it doesn't exist
#Initializing dictionaries too
if not os.path.exists("Param_Info/" + filename):
    variables_list = ['Time_Start', 'Time_End', 'Points_of_Interest', 
                      'Radar_Variable', 'Timezone', 'Timezone_true',
                      'PSD_Time_Res', 'Variables_Plot']
    data = {}
    for variable in variables_list:
        data[variable] = []
    data['Timezone'] = [0] #hardcoded in. don't worry about it   
    
    with open("Param_Info/" + filename, 'w') as file:
        json.dump(data, file, indent=2)

    print(filename + "_paramInfo was created")
else:
    print('File_Runner_Info exists')

#Loading in file data
with open('Param_Info/' + filename, 'r') as file:
    file_content = file.read()
    
#Showing file data
data = json.loads(file_content)
print(data)
print('')

changes_ask = input("Would you like to make changes (y/n)?   ")

if changes_ask == 'y' or changes_ask == 'Y':
    dictkeys = list(data.keys())
    
    print("\n\nWhat would you like to change?")
    print('NOTE: Ignore "Timezone" it should be 0.')
    print("The options are, ")
    for key in dictkeys:
        print('  ' + key)
    update_data = input("For example, to do both, type 'Time_Start, Time_End' without the ''\n")
    update_data = update_data.replace(" ", "")
    update_data = update_data.split(',')
    
    print("\n\nIf you're curious how to format the inputs, then look at "
          "another parameter file for reference.\n"
          "As a note though, Variables_Plot should be done as \n"
          "['var1', 'var2'], ['var3', 'var1'], ['var4', 'var5'] or as ['var1'], ['var2'] with the ' ' or quotes "
          "\n\n")
    
    #varp is a check for variables plot
    varp = False
    for item in update_data:
        try:
            print('')
            print('The data for ' + item + ' is, ')
            print(data[item])
            print('')
            
            if item == 'Variables_Plot':
                varp = True

            choice = input("Would you like to add (a), remove (r), or completely redo the data (c)?   ")
            if choice == 'a' or choice == 'A':
                inputs = input("What inputs do you want to add? Use commas to" 
                               " seperate multiple inputs: ")
                if varp is True:
                    inputs = ast.literal_eval(inputs)
                    for user_input in inputs:
                        data[item].append(user_input)
                else:
                    inputs = inputs.replace(' ', '')
                    inputs = inputs.split(',')
                    for user_input in inputs:
                        data[item].append(user_input)
            
            if choice == 'r' or choice == 'R':
                inputs = input("What inputs do you want to remove? Use commas to" 
                               " seperate multiple inputs: ")
                if varp is True:
                    inputs = ast.literal_eval(inputs)
                    for user_input in inputs:
                        data[item].remove(user_input)
                else:
                    inputs = inputs.replace(' ', '')
                    inputs = inputs.split(',')
                    for user_input in inputs:
                        data[item].remove(user_input)
                
            if choice == 'c' or choice == 'C':
                inputs = input("Type inputs here. Use commas to seperate multiple inputs: ")
                if varp is True:
                    inputs = ast.literal_eval(inputs)
                    data[item] = inputs
                else:
                    inputs = inputs.replace(' ', '')
                    inputs = inputs.split(',')
                    data[item] = inputs
        except:
            print('\n\nAn error occured for ' + str(item) + '. Could it be a typo?')
        
    with open("Param_Info/" + filename, 'w') as file:
        json.dump(data, file, indent=2)
    