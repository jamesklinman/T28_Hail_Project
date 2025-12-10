#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  1 14:08:24 2025

@author: jamesklinman
"""

import math
test = [1,6,3,98,4,3,6,7]
ordered_test = []
counter = 1
check_count = 0
while len(test) != 0:
    if counter == len(test):
        ordered_test.append(test[check_count])
        test.pop(check_count)
        counter = 0
        check_count = 0
        if len(test) == 0:
            break
    
    if test[check_count] < test[counter]:
        counter += 1
    elif test[check_count] >= test[counter]:
        check_count = counter
        counter += 1
        
length = len(ordered_test)
med = length/2
if med%1 == 0:
    med = [math.floor(med-1), math.ceil(med)]
    median = (ordered_test[med[0]] + ordered_test[med[1]]) / 2
else:
    med = math.floor(med)
    median = ordered_test[med]