# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 16:00:35 2024

@author: james.klinman

convert new psd table format to old format
"""

import numpy as np
import os
import sys
import pandas as pd

#file = sys.argv[0]
filepath = 'Uncertainty_Tables/Tables_for_ppt/PSD_Conc_HAIL_000700-001100.txt'

table_file = pd.read_csv(filepath, sep=' * ', engine='python')
table_df = pd.DataFrame(table_file)




