#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 12 17:57:40 2025

@author: jamesklinman
"""

import netCDF4 as nc

flights = {
    "667": {"year": "1995", "path": "../../yr1995/f667/667.nc"},
    "668": {"year": "1995", "path": "../../yr1995/f668/668.nc"},
    "670": {"year": "1995", "path": "../../yr1995/f670/670.nc"},
    "754": {"year": "2000", "path": "../../yr2000/f754/754.nc"},
    "756": {"year": "2000", "path": "../../yr2000/f756/756.nc"},
    "757": {"year": "2000", "path": "../../yr2000/f757/757.nc"},
    "759": {"year": "2000", "path": "../../yr2000/f759/759.nc"},
    "761": {"year": "2000", "path": "../../yr2000/f761/761.nc"},
    "781": {"year": "2002", "path": "../../yr2002/f781/781.nc"},
    "798": {"year": "2003", "path": "../../yr2003/f798/798.nc"},
    "803": {"year": "2003", "path": "../../yr2003/f803/803.nc"},
    "815": {"year": "2003", "path": "../../yr2003/f815/815.nc"},
    "819": {"year": "2003", "path": "../../yr2003/f819/819.nc"},
    "820": {"year": "2003", "path": "../../yr2003/f820/820.nc"}
}

for x in flights.values():
    #print(x['path'])
    print(x['path'])
    file = nc.Dataset(x['path'])
    print(file['Time'], '\n\n')