#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 11:26:28 2025

@author: james.klinman

purpose is to plot periods with times that are interesting, and to cut out the
rest of a plot
that way we can quickly look at the reflectivity plot to get 
general information about a flight
"""


"""
sketching out what i want to do

read in year
read in types of data to plot
keep it to two for now
save year
do for all years
merge all years together
"""


import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import glob

#define the min reflectivity to include
min_ref  = 30
min_plot = 29#29
max_plot = 80

dbz_bin_amount = 5


#which version of data to plot
version_plot = '20251006'
probe_plot   = ['HAIL-2D', 'HAIL-1D']
redo_case = False #i believe this is just to mask out certain bins

#hvps case against 670
#version_plot = '20250702_HVPS'
#probe_plot   = ['HVPS1', 'HAIL-1D']
#redo_case = True


#calling in whole path to all filenames that contain the relevant data
flight_list = glob.glob('../../yr*/f*/Code_Files_and_Outputs/Sensor_Information/'
                        'Count_Conc_Ref_Data/' + version_plot +
                        '/*/*/*_PBP_Processed_*.nc')

#get the flight numbers which gives us info on the year
#get the flight years as well from the directory structure
flight_nums_2 = []
flight_years  = []
for f in range(len(flight_list)):
    f_num   = flight_list[f].find('/f')
    f_numss = flight_list[f][f_num+2:f_num+5]
    
    f_year  = flight_list[f].find('Ref_Data/')
    f_year2 = flight_list[f][f_year+18:f_year+22]
    
    flight_nums_2.append(f_numss)
    flight_years.append(f_year2)
    
#remove duplicates
flight_nums_3 = sorted(list(set(flight_nums_2)))
flight_years2 = sorted(list(set(flight_years)))



#get all available flight dates
flight_dates_names = glob.glob('../../yr*/f*/Code_Files_and_Outputs/Sensor_Information/'
                         'Count_Conc_Ref_Data/' + version_plot + '/*')
flight_dates = []
for f in range(len(flight_dates_names)):
    f_days = flight_dates_names[f][-8:]
    flight_dates.append(f_days)

#remove duplicates
flight_dates = sorted(list(set(flight_dates)))


#organize flight lists for consistency in case glob doesn't organize ight in HVPS case
#had chatgpt make this solution. need to write thesessis
def organize_flight_files(flight_list):
    """
    Organizes flight files so that for each flight, the HVPS1 (or 2D) file 
    comes first, followed by the corresponding HAIL-1D file.

    Assumes each flight has one HAIL-1D file and one HVPS-type file.
    """
    hail_files = []
    hvps_files = []

    for f in flight_list:
        if 'HVPS1' in f:
            hvps_files.append(f)
        elif 'HVPS2D' in f or '2D' in f:  # adjust this condition as needed
            hvps_files.append(f)
        elif 'HAIL-1D' in f:
            hail_files.append(f)

    # Sort both lists to ensure matching order
    hvps_files.sort()
    hail_files.sort()

    # Interleave HVPS/2D and HAIL-1D
    organized = [val for pair in zip(hvps_files, hail_files) for val in pair]

    return organized


flight_list = organize_flight_files(flight_list)









#-----------------------------------------------------------------------------
#Data quality assuring 
#------------------------------------------------------------------------------


#it should read in the file, pull in the reflectivies
#then do the isinf and nan thing and then make a mask for everything that is nan and 2d1d<35
#and then read out that quality controlled data
#THE REASON IT'S 1D AND 2D OR TWO PROBES TOGETHER IS THAT THE REFLECTIVITY
#THRESHOLD IS IMPLEMENTED IN THERE AS THE COMPARISON.
def data_quality_assurance(file_list):

    #will read in the file, replace and inf with nan, and then mask out all
    #the cases where either the 1d or 2d have a nan reflectivity, it will 
    #also mask out cases where reflectivity is <35 for the 1D and 2D to normalize
    #the data to work primarily with potential to certain hail cases.
    
    global min_ref
    
    #looping through to store reflectivities
    data_list = []
    #f is file
    for f in range(len(file_list)):
        data = nc.Dataset(file_list[f])
        data_list.append(data)
        print(data.Probe)
     
        
    #hvps and hailspec comparisons are pointless unless constrained to same bins
    #do the reflectivity recompute here

    if redo_case == True:
        def compute_dbz(D_bs, N_d, dielectric):
            """Helper function for reflectivity calculation"""
            #from claude
            power_sum = np.nansum(D_bs**6 * N_d)
            return -np.inf if power_sum == 0 else 10 * np.log10(dielectric * power_sum)
        
        hvps_case_ref_list = []
        
        
        ice_water_dielectric = (0.197) / (0.93)
        for x in range(len(file_list)):
            
            #make mask for specific bins
            if data_list[x].Probe == 'HVPS1':
                mask = np.array([False, False, False, False, False, False,
                        True, True, True, True, True, True, True, False,
                        False, False, False, False, False, False])
                #mask = np.array([False, False, False, False, False, False,
                #        True, True, True, True, True, True, True, True,
                #        True, True, False, False, False, False])

            elif data_list[x].Probe == 'HAIL-1D' or data_list[x].Probe == 'HAIL-2D':
                #mask = np.array([True, True, True, True, True, True, True,
                #                  False, False, False, False, False, False, False])
                
                #all bins mask, just messing with dieletric constant
                mask = np.array([True, True, True, True, True, True, True,
                                  True, True, True, True, True, True, True])
                
                #up to 2cm mask
                #mask = np.array([True, True, True, True, True, True, True,
                #                  True, True, True, False, False, False, False])
                
                #make the 1d 2d match mask
                #mask = np.array([False, True, True, True, True, False, False,
                #                  False, False, False, False, False, False, False])
            
            #comment out if you wanbt to use the bin mask. this is just all true
            #if np.any(mask):
            #    mask[:] = True
            #print(mask)
            
            D_bs = (data_list[x]['bin_startpoints'][:][mask].astype('f8') + \
                    (data_list[x]['bin_size'][:][mask].astype('f8')/2))\
                    / 1000 #into mm, the size of the particle in mm
            
            bin_conversion = (data_list[x]['bin_size'][:][mask]/1e6)
            
            temp_ref = []
            if data_list[x].Probe == 'HAIL-1D':
                psdname = 'psd_1D'
            elif data_list[x].Probe == 'HAIL-2D':
                psdname = 'psd_2d_xsize'
            for t in range(len(data_list[x][psdname])):
                #print(data_list[x]['conc'][t][mask])

                #main reflectivity
                N_d_2 = data_list[x][psdname][t][mask] * bin_conversion
                dbz = compute_dbz(D_bs, N_d_2, ice_water_dielectric)
                #print(dbz)
                temp_ref.append(dbz)
            
            hvps_case_ref_list.append(temp_ref)
    
    
    #okay that made really intersting plots so repeating process for the hailspec
    
    
    
    #read in ref's    
    #and uncertainties wihch are different for 1D vs 2D
    #self note. 2d is type 1 since it's read in first
    #so the below assumes constant 2D first and 1D second
    
    ref_type1 = data_list[0]['Z_e_2D_xsize'][:]
    ref_type2 = data_list[1]['Z_e_1D'][:]
    
    #creating zeros array since not all the ref options exist anymore but
    #i dont want to go through and change hundreds of lines of code
    #throughout the whole file
    zeros_array = np.zeros(ref_type1.shape)
    
    #this is not propogated through so the uncertainties are not valiid 
    #if using hvps data
    if redo_case == True:
        pass
        
        #!!!!!!!!!!!!!! COMMENTED OUT FOR PLAYING WITH HAILSPEC BUT IS IMPORNAT FOR HVPS
        #ref_type1 = np.array(hvps_case_ref_list[0])
        #ref_type2 = np.array(hvps_case_ref_list[1])
    
    #biggest uncertainties
    ref_type1_u = data_list[0]['Z_e_2D_mean_upper_uncertainty'][:]
    ref_type1_l = data_list[0]['Z_e_2D_mean_lower_uncertainty'][:]
    
    ref_type2_u = zeros_array#data_list[1]['ref_biggest_upper_uncert'][:]
    ref_type2_l = zeros_array#data_list[1]['ref_biggest_lower_uncert'][:]
    
    #specific uncertainties
    ref_type1_spatial_u = zeros_array#data_list[0]['ref_spatial_upper_uncert'][:]
    ref_type1_spatial_l = zeros_array#data_list[0]['ref_spatial_lower_uncert'][:]
    ref_type1_poisson_u = data_list[0]['Z_e_2D_xsize_upper_uncertainty'][:]
    ref_type1_poisson_l = data_list[0]['Z_e_2D_xsize_lower_uncertainty'][:]
    ref_type1_sizing_u  = zeros_array#data_list[0]['ref_sizing_upper_uncert'][:]
    ref_type1_sizing_l  = zeros_array#data_list[0]['ref_sizing_lower_uncert'][:]
    
    ref_type2_spatial_u = zeros_array#data_list[1]['ref_spatial_upper_uncert'][:]
    ref_type2_spatial_l = zeros_array#data_list[1]['ref_spatial_lower_uncert'][:]
    ref_type2_poisson_u = data_list[1]['Z_e_1D_upper_uncertainty'][:]
    ref_type2_poisson_l = data_list[1]['Z_e_1D_lower_uncertainty'][:]
    ref_type2_sizing_u  = zeros_array#data_list[1]['ref_sizing_upper_uncert'][:]
    ref_type2_sizing_l  = zeros_array#data_list[1]['ref_sizing_lower_uncert'][:]
    
    #turning -inf's to nan
    ref_type1[np.isinf(ref_type1)] = np.nan
    ref_type2[np.isinf(ref_type2)] = np.nan
    
    #creating and applying a mask to get rid of any cases where either the 
    #1d or 2d data has a nan value. Also masks out cases where ref
    #is less than 35 for the 1d to normalize for hail cases and cases
    #with more particles.
    nanmask = ~np.isnan(ref_type2) & ~np.isnan(ref_type1) \
            & ~(ref_type1 < min_ref) & ~(ref_type2 < min_ref)
    ref_type2_nonan = ref_type2[nanmask]
    ref_type1_nonan = ref_type1[nanmask]    
    
    #mask all the  uncertainty using the mask from the main data
    ref_type1_u_nonan = ref_type1_u[nanmask]
    ref_type1_l_nonan = ref_type1_l[nanmask]
    ref_type2_u_nonan = ref_type2_u[nanmask]
    ref_type2_l_nonan = ref_type2_l[nanmask]
    
    ref_type1_spatial_u_nonan = ref_type1_spatial_u[nanmask]
    ref_type1_spatial_l_nonan = ref_type1_spatial_l[nanmask]
    ref_type1_poisson_u_nonan = ref_type1_poisson_u[nanmask]
    ref_type1_poisson_l_nonan = ref_type1_poisson_l[nanmask]
    ref_type1_sizing_u_nonan  = ref_type1_sizing_u[nanmask]
    ref_type1_sizing_l_nonan  = ref_type1_sizing_l[nanmask]
    
    ref_type2_spatial_u_nonan = ref_type2_spatial_u[nanmask]
    ref_type2_spatial_l_nonan = ref_type2_spatial_l[nanmask]
    ref_type2_poisson_u_nonan = ref_type2_poisson_u[nanmask]
    ref_type2_poisson_l_nonan = ref_type2_poisson_l[nanmask]
    ref_type2_sizing_u_nonan  = ref_type2_sizing_u[nanmask]
    ref_type2_sizing_l_nonan  = ref_type2_sizing_l[nanmask]
    
    
    #lower uncertainty is sometimes zero which becomes negative inf somewhere
    ref_type1_l_nonan[ref_type1_l_nonan == -np.inf] = 0
    ref_type2_l_nonan[ref_type2_l_nonan == -np.inf] = 0
    ref_type1_spatial_l_nonan[ref_type1_spatial_l_nonan == -np.inf] = 0
    ref_type2_spatial_l_nonan[ref_type2_spatial_l_nonan == -np.inf] = 0
    ref_type1_poisson_l_nonan[ref_type1_poisson_l_nonan == -np.inf] = 0
    ref_type2_poisson_l_nonan[ref_type2_poisson_l_nonan == -np.inf] = 0
    ref_type1_sizing_l_nonan[ref_type1_sizing_l_nonan == -np.inf] = 0
    ref_type2_sizing_l_nonan[ref_type2_sizing_l_nonan == -np.inf] = 0
    
    
    #sometimes reflectivity is negative i guess. 
    #setting to 0 for plotting purposes
    ref_type1_l_nonan[ref_type1_l_nonan < 0] = 0
    ref_type2_l_nonan[ref_type2_l_nonan < 0] = 0
    ref_type1_spatial_l_nonan[ref_type1_spatial_l_nonan < 0] = 0
    ref_type2_spatial_l_nonan[ref_type2_spatial_l_nonan < 0] = 0
    ref_type1_poisson_l_nonan[ref_type1_poisson_l_nonan < 0] = 0
    ref_type2_poisson_l_nonan[ref_type2_poisson_l_nonan < 0] = 0
    ref_type1_sizing_l_nonan[ref_type1_sizing_l_nonan < 0] = 0
    ref_type2_sizing_l_nonan[ref_type2_sizing_l_nonan < 0] = 0

    
    
    #self note, the 1d is being read out first since that positioning 
    #matches the rest of the code which i don't feel like changing.
    #so its a switchup here
    ref_list = [ref_type2_nonan, ref_type1_nonan]
    ref_upper_list = [ref_type2_u_nonan, ref_type1_u_nonan]
    ref_lower_list = [ref_type2_l_nonan, ref_type1_l_nonan]
    ref_upper_spatial_list = [ref_type2_spatial_u_nonan, ref_type1_spatial_u_nonan]
    ref_lower_spatial_list = [ref_type2_spatial_l_nonan, ref_type1_spatial_l_nonan]    
    ref_upper_poisson_list = [ref_type2_poisson_u_nonan, ref_type1_poisson_u_nonan]
    ref_lower_poisson_list = [ref_type2_poisson_l_nonan, ref_type1_poisson_l_nonan]    
    ref_upper_sizing_list = [ref_type2_sizing_u_nonan, ref_type1_sizing_u_nonan]
    ref_lower_sizing_list = [ref_type2_sizing_l_nonan, ref_type1_sizing_l_nonan]
    
    
    
    return ref_list, ref_lower_list, ref_upper_list, \
       ref_lower_spatial_list, ref_upper_spatial_list, \
       ref_lower_poisson_list, ref_upper_poisson_list, \
       ref_lower_sizing_list, ref_upper_sizing_list


each_flight_ref = []
each_flight_lower_ref = []
each_flight_upper_ref = []
each_flight_lower_spatial_ref = []
each_flight_upper_spatial_ref = []
each_flight_lower_poisson_ref = []
each_flight_upper_poisson_ref = []
each_flight_lower_sizing_ref = []
each_flight_upper_sizing_ref = []
for f in range(len(flight_nums_3)): #each flight
    probe_files = []
    for p in range(len(flight_list)): #all probes for all flights
        if flight_nums_3[f] in flight_list[p] and probe_plot[0] in flight_list[p]:
            probe_files.append(flight_list[p])
        if flight_nums_3[f] in flight_list[p] and probe_plot[1] in flight_list[p]:
            probe_files.append(flight_list[p])
    #print(probe_files)
    
    reflectivities_temp = data_quality_assurance(probe_files) 
    
    each_flight_ref.append(reflectivities_temp[0])
    each_flight_lower_ref.append(reflectivities_temp[1])
    each_flight_upper_ref.append(reflectivities_temp[2])
    each_flight_lower_spatial_ref.append(reflectivities_temp[3])
    each_flight_upper_spatial_ref.append(reflectivities_temp[4])
    each_flight_lower_poisson_ref.append(reflectivities_temp[5])
    each_flight_upper_poisson_ref.append(reflectivities_temp[6])
    each_flight_lower_sizing_ref.append(reflectivities_temp[7])
    each_flight_upper_sizing_ref.append(reflectivities_temp[8])
    


#FLATTEN THE REFS HERE
reflectivities = each_flight_ref

#------------------------------------------------------------------------------
#Group each field campaign together
#------------------------------------------------------------------------------

#each_flight_ref[3][1][0:5]   [x][y][z] x is flight y is probe z is time

#binning by each field campaign
#prepare lists for 1D data binning
campaigns_ref_1D = []
campaigns_ref_u_1D = []
campaigns_ref_l_1D = []
campaigns_ref_u_spatial_1D = []
campaigns_ref_l_spatial_1D = []
campaigns_ref_u_poisson_1D = []
campaigns_ref_l_poisson_1D = []
campaigns_ref_u_sizing_1D = []
campaigns_ref_l_sizing_1D = []

for x in range(len(flight_years2)):
    temp_year_ref = []
    temp_year_ref_u = []
    temp_year_ref_l = []
    temp_year_ref_u_spatial = []
    temp_year_ref_l_spatial = []
    temp_year_ref_u_poisson = []
    temp_year_ref_l_poisson = []
    temp_year_ref_u_sizing = []
    temp_year_ref_l_sizing = []
    for y in range(0, len(flight_years), 2):
        if flight_years[y] == flight_years2[x]:
            y = int(y / 2) #two probes means year is registered twice. /2 handles that
            temp_year_ref.append(each_flight_ref[y][0])
            temp_year_ref_u.append(each_flight_upper_ref[y][0])
            temp_year_ref_l.append(each_flight_lower_ref[y][0])
            
            temp_year_ref_u_spatial.append(each_flight_upper_spatial_ref[y][0])
            temp_year_ref_l_spatial.append(each_flight_lower_spatial_ref[y][0])
            
            temp_year_ref_u_poisson.append(each_flight_upper_poisson_ref[y][0])
            temp_year_ref_l_poisson.append(each_flight_lower_poisson_ref[y][0])
            
            temp_year_ref_u_sizing.append(each_flight_upper_sizing_ref[y][0])
            temp_year_ref_l_sizing.append(each_flight_lower_sizing_ref[y][0])
            
    campaigns_ref_1D.append(temp_year_ref)
    campaigns_ref_u_1D.append(temp_year_ref_u)
    campaigns_ref_l_1D.append(temp_year_ref_l)
    
    campaigns_ref_u_spatial_1D.append(temp_year_ref_u_spatial)
    campaigns_ref_l_spatial_1D.append(temp_year_ref_l_spatial)
    
    campaigns_ref_u_poisson_1D.append(temp_year_ref_u_poisson)
    campaigns_ref_l_poisson_1D.append(temp_year_ref_l_poisson)
    
    campaigns_ref_u_sizing_1D.append(temp_year_ref_u_sizing)
    campaigns_ref_l_sizing_1D.append(temp_year_ref_l_sizing)


#prepare lists for 2D data binning
campaigns_ref_2D = []
campaigns_ref_u_2D = []
campaigns_ref_l_2D = []
campaigns_ref_u_spatial_2D = []
campaigns_ref_l_spatial_2D = []
campaigns_ref_u_poisson_2D = []
campaigns_ref_l_poisson_2D = []
campaigns_ref_u_sizing_2D = []
campaigns_ref_l_sizing_2D = []

for x in range(len(flight_years2)):
    temp_year_ref = []
    temp_year_ref_u = []
    temp_year_ref_l = []
    temp_year_ref_u_spatial = []
    temp_year_ref_l_spatial = []
    temp_year_ref_u_poisson = []
    temp_year_ref_l_poisson = []
    temp_year_ref_u_sizing = []
    temp_year_ref_l_sizing = []
    for y in range(0, len(flight_years), 2): # years counted twice, probes are seperated so need to count half
        if flight_years[y] == flight_years2[x]:
            y = int(y / 2) #two probes means year is registered twice. /2 handles that
            temp_year_ref.append(each_flight_ref[y][1])
            temp_year_ref_u.append(each_flight_upper_ref[y][1])
            temp_year_ref_l.append(each_flight_lower_ref[y][1])
            
            temp_year_ref_u_spatial.append(each_flight_upper_spatial_ref[y][1])
            temp_year_ref_l_spatial.append(each_flight_lower_spatial_ref[y][1])
            
            temp_year_ref_u_poisson.append(each_flight_upper_poisson_ref[y][1])
            temp_year_ref_l_poisson.append(each_flight_lower_poisson_ref[y][1])
            
            temp_year_ref_u_sizing.append(each_flight_upper_sizing_ref[y][1])
            temp_year_ref_l_sizing.append(each_flight_lower_sizing_ref[y][1])
            
    campaigns_ref_2D.append(temp_year_ref)
    campaigns_ref_u_2D.append(temp_year_ref_u)
    campaigns_ref_l_2D.append(temp_year_ref_l)
    
    campaigns_ref_u_spatial_2D.append(temp_year_ref_u_spatial)
    campaigns_ref_l_spatial_2D.append(temp_year_ref_l_spatial)
    
    campaigns_ref_u_poisson_2D.append(temp_year_ref_u_poisson)
    campaigns_ref_l_poisson_2D.append(temp_year_ref_l_poisson)
    
    campaigns_ref_u_sizing_2D.append(temp_year_ref_u_sizing)
    campaigns_ref_l_sizing_2D.append(temp_year_ref_l_sizing)





#------------------------------------------------------------------------------
#Fitting data for the probe comparison plots
#------------------------------------------------------------------------------



#get r2 values
def compute_R2(observed, pred):    
    ybar = np.mean(observed)
    #total and residual square of sums
    rss = np.sum((observed - pred)**2)
    tss = np.sum((observed - ybar)**2)
    #print(rss, tss)
    #coefficient of determination
    r2 = 1 - rss/tss
    return r2

def compute_pred(xvals, slope, yint):
    pred_vals = []
    for x in xvals:
        pred = yint + slope*x
        pred_vals.append(pred)
    return pred_vals



#setting up xaxis for fits
xaxis = np.linspace(0, max_plot, 8) #x values for best fit

#do the polyfit for each individual flight
#f stands for flight
slopes = []
yints  = []
r2_flight = []
for f in range(len(reflectivities)):
    print(len(reflectivities[f][0]))
    if len(reflectivities[f][0]) == 0:
        #need to check if not reflectivities met the 35 min threshold. If so
        #have to skip or np polyfit get mad
        slopes.append(1)
        yints.append(0)
        r2_flight.append(0)
    else:
        refs = reflectivities[f]
        slope, yint = np.polyfit(refs[0], refs[1], deg=1) #hard coded to 1 degree
        slopes.append(slope)
        yints.append(yint)
        
        pred_yvals_ea = compute_pred(refs[0], slope, yint)
        ea_flight_r2 = compute_R2(refs[1], pred_yvals_ea)
        r2_flight.append(ea_flight_r2)
        
"""
#i think the below is a duplicate for some reason
for f in range(len(reflectivities)):
    print(len(reflectivities[f][0]))
    if len(reflectivities[f][0]) == 0:
        #need to check if not reflectivities met the 35 min threshold. If so
        #have to skip or np polyfit get mad
        slopes.append(1)
        yints.append(0)
    else:
        refs = reflectivities[f]
        slope, yint = np.polyfit(refs[0], refs[1], deg=1) #hard coded to 1 degree
        slopes.append(slope)
        yints.append(yint)
"""
    

#do polyfit for field campaign
slopes_campaign = []
yints_campaign  = []
yaxis_campaign  = []
r2_campaign     = []
for x in range(len(flight_years2)):
    temp_refs_1d = []
    temp_refs_2d = []
    for y in range(0, len(flight_years), 2):
        #print(y)
        #print(flight_years[y], flight_years2[x])
        if flight_years[y] == flight_years2[x]:
            #print(flight_years2[x])
            y=int(y/2)
            temp_refs_1d.append(reflectivities[y][0])
            temp_refs_2d.append(reflectivities[y][1])
            #print(flight_years[y], flight_years2[x], 'hi')
    campaign_1d_refs_flat = np.concatenate(temp_refs_1d)
    campaign_2d_refs_flat = np.concatenate(temp_refs_2d)
    
    #campaign refs yaxis
    try:
        slope_campaign, yint_campaign = np.polyfit(campaign_1d_refs_flat, campaign_2d_refs_flat, deg=1)
        campaign_yaxis = slope_campaign * xaxis + yint_campaign
        pred_yvals_yr = compute_pred(campaign_1d_refs_flat, slope_campaign, yint_campaign)
        ea_yr_r2 = compute_R2(campaign_2d_refs_flat, pred_yvals_yr)
        r2_campaign.append(ea_yr_r2)
    except:
        print('No data or invalid data when fitting')
        #means that there were 
        slope_campaign, yint_campaign = (1, 0)
        campaign_yaxis = slope_campaign * xaxis + yint_campaign
        r2_campaign = 0
        
    slopes_campaign.append(slope_campaign)
    yints_campaign.append(yint_campaign)
    yaxis_campaign.append(campaign_yaxis)
    
#do polyfit for all the flights combined
#ignore error message it spits out. it still works. not sure why it gives
#error message but my best guess is that it doesn't like that its lists not 
#arrays but also this might not apply idk even know rn
#r stands for reflectivities
all_1d_refs = [r[0] for r in reflectivities]
all_2d_refs = [r[1] for r in reflectivities]

#now stacking the 1d and 2d reflectivities together
#ACTUALLY IM NOT SURE THAT THIS IS NECESSARY BUT IM KEEPING IT BC I WANT TO
all_1d_refs_flat = np.concatenate(all_1d_refs)
all_2d_refs_flat = np.concatenate(all_2d_refs)


#setting up x and y axis data now for the fits
yaxis = []
#f stands for flight
for f in range(len(slopes)):#range(len(all_1d_refs)):
    y_values = slopes[f] * xaxis + yints[f]
    yaxis.append(y_values)

#all refs yaxis
try:
    slope_all, yint_all = np.polyfit(all_1d_refs_flat, all_2d_refs_flat, deg=1)
    all_yaxis = slope_all * xaxis + yint_all
except:
    print('No data or invalid data when fitting')
    #means that there were 
    slope_all, yint_all = (1, 0)
    all_yaxis = slope_all * xaxis + yint_all
    



pred_yvals_all = compute_pred(all_1d_refs_flat, slope_all, yint_all)
r2_all_flights = compute_R2(all_2d_refs_flat, pred_yvals_all)

#------------------------------------------
#SPECIFYING DATA FORMATS EVEN IF REPETITIVE 
#BECUASE THIS IS GETTING REALLY CONFUSING
#THESE ARE ESSENTIALLY RENAMES/COPIES
#------------------------------------------

#Will be labeled as entire, campaign, and indvflight
#Additionally 1D and 2D
#mid, upp == upper, low == lower
#aft == along flight track, siz == sizing, poi == poisson, big == biggest


#Entire dataset
#First flatten everything
def flatten(data, probe):
    return [r2 for r in data for r2 in r[probe]]
    
entire_1D_ref_mid     = flatten(each_flight_ref, 0)
entire_1D_ref_upp_big = flatten(each_flight_upper_ref, 0)
entire_1D_ref_low_big = flatten(each_flight_lower_ref, 0)
entire_1D_ref_upp_poi = flatten(each_flight_upper_poisson_ref, 0)
entire_1D_ref_low_poi = flatten(each_flight_lower_poisson_ref, 0)
entire_1D_ref_upp_siz = flatten(each_flight_upper_sizing_ref, 0)
entire_1D_ref_low_siz = flatten(each_flight_lower_sizing_ref, 0)
entire_1D_ref_upp_aft = flatten(each_flight_upper_spatial_ref, 0)
entire_1D_ref_low_aft = flatten(each_flight_lower_spatial_ref, 0)

entire_2D_ref_mid     = flatten(each_flight_ref, 1)
entire_2D_ref_upp_big = flatten(each_flight_upper_ref, 1)
entire_2D_ref_low_big = flatten(each_flight_lower_ref, 1)
entire_2D_ref_upp_poi = flatten(each_flight_upper_poisson_ref, 1)
entire_2D_ref_low_poi = flatten(each_flight_lower_poisson_ref, 1)
entire_2D_ref_upp_siz = flatten(each_flight_upper_sizing_ref, 1)
entire_2D_ref_low_siz = flatten(each_flight_lower_sizing_ref, 1)
entire_2D_ref_upp_aft = flatten(each_flight_upper_spatial_ref, 1)
entire_2D_ref_low_aft = flatten(each_flight_lower_spatial_ref, 1)



#organize so it can loop through by probe
entire_xx_ref_mid     = [entire_1D_ref_mid, entire_2D_ref_mid]
entire_xx_ref_upp_big = [entire_1D_ref_upp_big, entire_2D_ref_upp_big]
entire_xx_ref_low_big = [entire_1D_ref_low_big, entire_2D_ref_low_big]
entire_xx_ref_upp_poi = [entire_1D_ref_upp_poi, entire_2D_ref_upp_poi]
entire_xx_ref_low_poi = [entire_1D_ref_low_poi, entire_2D_ref_low_poi]
entire_xx_ref_upp_siz = [entire_1D_ref_upp_siz, entire_2D_ref_upp_siz]
entire_xx_ref_low_siz = [entire_1D_ref_low_siz, entire_2D_ref_low_siz]
entire_xx_ref_upp_aft = [entire_1D_ref_upp_aft, entire_2D_ref_upp_aft]
entire_xx_ref_low_aft = [entire_1D_ref_low_aft, entire_2D_ref_low_aft]



#Campaign ref's
#they are stored in lists
#campaigns are technically years btw so the 2003 two campaigns are grouped together
#structure is [year][flight][data]
def flatten2(data):
    return [[r2 for flight in year for r2 in flight] for year in data]

#data now stored as [year][data]
campaign_1D_ref_mid     = flatten2(campaigns_ref_1D)
campaign_1D_ref_upp_big = flatten2(campaigns_ref_u_1D)
campaign_1D_ref_low_big = flatten2(campaigns_ref_l_1D)
campaign_1D_ref_upp_poi = flatten2(campaigns_ref_u_poisson_1D)
campaign_1D_ref_low_poi = flatten2(campaigns_ref_l_poisson_1D)
campaign_1D_ref_upp_siz = flatten2(campaigns_ref_u_sizing_1D)
campaign_1D_ref_low_siz = flatten2(campaigns_ref_l_sizing_1D)
campaign_1D_ref_upp_aft = flatten2(campaigns_ref_u_spatial_1D)
campaign_1D_ref_low_aft = flatten2(campaigns_ref_l_spatial_1D)

campaign_2D_ref_mid     = flatten2(campaigns_ref_2D)
campaign_2D_ref_upp_big = flatten2(campaigns_ref_u_2D)
campaign_2D_ref_low_big = flatten2(campaigns_ref_l_2D)
campaign_2D_ref_upp_poi = flatten2(campaigns_ref_u_poisson_2D)
campaign_2D_ref_low_poi = flatten2(campaigns_ref_l_poisson_2D)
campaign_2D_ref_upp_siz = flatten2(campaigns_ref_u_sizing_2D)
campaign_2D_ref_low_siz = flatten2(campaigns_ref_l_sizing_2D)
campaign_2D_ref_upp_aft = flatten2(campaigns_ref_u_spatial_2D)
campaign_2D_ref_low_aft = flatten2(campaigns_ref_l_spatial_2D)



#organize so it can loop through by probe
campaign_xx_ref_mid     = [campaign_1D_ref_mid, campaign_2D_ref_mid]
campaign_xx_ref_upp_big = [campaign_1D_ref_upp_big, campaign_2D_ref_upp_big]
campaign_xx_ref_low_big = [campaign_1D_ref_low_big, campaign_2D_ref_low_big]
campaign_xx_ref_upp_poi = [campaign_1D_ref_upp_poi, campaign_2D_ref_upp_poi]
campaign_xx_ref_low_poi = [campaign_1D_ref_low_poi, campaign_2D_ref_low_poi]
campaign_xx_ref_upp_siz = [campaign_1D_ref_upp_siz, campaign_2D_ref_upp_siz]
campaign_xx_ref_low_siz = [campaign_1D_ref_low_siz, campaign_2D_ref_low_siz]
campaign_xx_ref_upp_aft = [campaign_1D_ref_upp_aft, campaign_2D_ref_upp_aft]
campaign_xx_ref_low_aft = [campaign_1D_ref_low_aft, campaign_2D_ref_low_aft]




#Now each flight
#saved as x, y, z where x==flight, y==probe type, z==data points
#I'm not going to uncompress atm

flight_xx_ref_mid     = each_flight_ref
flight_xx_ref_upp_big = each_flight_upper_ref
flight_xx_ref_low_big = each_flight_lower_ref
flight_xx_ref_upp_poi = each_flight_upper_poisson_ref
flight_xx_ref_low_poi = each_flight_lower_poisson_ref
flight_xx_ref_upp_siz = each_flight_upper_sizing_ref
flight_xx_ref_low_siz = each_flight_lower_sizing_ref
flight_xx_ref_upp_aft = each_flight_upper_spatial_ref
flight_xx_ref_low_aft = each_flight_lower_spatial_ref





    
    
#------------------------------------------------------------------------------
#Initial plots of the data. 
#Creating probe comparison plots for each flight and all flights
#This has already been set up so it doesn't use the new data names 
#and since it works as is im not updating them
#------------------------------------------------------------------------------

#plotting the individual flights and their reflectivity data
#setting up some global variables
axlims = (min_plot, max_plot)

#Individual flight plot creation
#f stands for flight
for f in range(len(all_1d_refs)):
    fig, ax = plt.subplots(figsize=[13.0, 10.0])
    ax.scatter(all_1d_refs[f], all_2d_refs[f], label='Reflectivity')
    #ax.errorbar(x=all_1d_refs[f], y=all_2d_refs[f],
                #yerr=(all_2d_refs[f] - each_flight_lower_ref[f][1], 
                #      each_flight_upper_ref[f][1] - all_2d_refs[f]),
                #xerr=(all_1d_refs[f] - each_flight_lower_ref[f][0], 
                #      each_flight_upper_ref[f][0] - all_1d_refs[f]),
                #ls='none', capsize=4, elinewidth=1, fmt='none')
    
    ax.plot([0, max_plot], [0, max_plot], color='black', label='1:1 Line')
    ax.plot(xaxis, yaxis[f], color='black', \
            label=f'Best Fit: yint = {np.round(yints[f], 2)}\n              slope = {np.round(slopes[f], 2)}\n              $R^2$ = {round(r2_flight[f], 2)}', \
            linestyle=':')
    ax.set_xlim(axlims)
    ax.set_ylim(axlims)
    ax.set_xlabel('1D Estimated Reflectivity (dBZ)', fontsize=25)
    ax.set_ylabel('1D Estimated Reflectivity (dBZ)', fontsize=25)
    ax.set_title(f"Hail Spectrometer 1D vs 2D Estimated Reflectivity For Flight {flight_nums_3[f]}", fontsize=25, pad=20)  
    
    ax.tick_params(axis='both', labelsize=25)
    
    ax.grid(alpha=.4)
    ax.legend(fontsize=25, loc='upper left')
    
    #plt.show()
    plt.savefig(f"Quantitative_Folder/Flight_{flight_nums_3[f]}_{flight_dates[f]}")


#campaign plots
#all plotted same color bc too laxy to do separate flights rn
#c stands for flight
for c in range(len(campaigns_ref_1D)):
    fig, ax = plt.subplots(figsize=[13.0, 10.0])
    
    campaign_1d_all = np.concatenate(campaigns_ref_1D[c])
    campaign_2d_all = np.concatenate(campaigns_ref_2D[c])
    
    ax.scatter(campaign_1d_all, campaign_2d_all, label='Reflectivity')

    
    ax.plot([0, max_plot], [0, max_plot], color='black', label='1:1 Line')
    ax.plot(xaxis, yaxis_campaign[c], color='black', \
            label=f'Best Fit: yint = {np.round(yints_campaign[c], 2)}\n              slope = {np.round(slopes_campaign[c], 2)}\n              $R^2$ = {round(r2_campaign[c], 2)}', \
            linestyle=':')
    ax.set_xlim(axlims)
    ax.set_ylim(axlims)
    ax.set_xlabel('HS 1D Reflectivity (dBZ)', fontsize=25)
    ax.set_ylabel('HS 2D Reflectivity (dBZ)', fontsize=25)
    ax.set_title(f"HS 1D vs 2D Reflectivity For Year {flight_years2[c]}", fontsize=25, pad=20)  
    
    ax.tick_params(axis='both', labelsize=25)
    
    ax.grid(alpha=.4)
    ax.legend(fontsize=25, loc='upper left')
    
    #plt.show()
    plt.savefig(f"Quantitative_Folder/Campaign_{flight_years2[c]}")




#All flight plot creation
#setting up colors for all the different flights
#https://matplotlib.org/stable/gallery/color/individual_colors_from_cmap.html
#color set up magically worked by copy and pasting from matplotlib docs lmao
#cmap = matplotlib.colormaps['spring']
cmap = matplotlib.colormaps['magma']
colors = cmap(np.linspace(0, 1, len(all_1d_refs)))
   
#creating color map based on year/field campaign
cmap = matplotlib.colormaps['magma']
colors = cmap(np.linspace(0, .8, len(flight_years2)))

colors_project = []
for x in range(len(flight_years2)):
    for y in range(0, len(flight_years), 2):
        if flight_years[y] == flight_years2[x]:
            colors_project.append(colors[x])
        
#creating symbol map based on year/field campaign
markers_to_use = ['o', '^', 's', 'X', '*']
markers_project = []
for x in range(len(flight_years2)):
    for y in range(0, len(flight_years), 2):
        if flight_years[y] == flight_years2[x]:
            markers_project.append(markers_to_use[x])

#label by year rather than flight
group_years = flight_years[::2]
labeled_years = set()

#color schematic potentially
cbf_colors= ["#000000", "#800000", "#3366CC", "#66CC99"]
colors_project = []
for x in range(len(flight_years2)):
    for y in range(0, len(flight_years), 2):
        if flight_years[y] == flight_years2[x]:
            colors_project.append(cbf_colors[x])

fig_all, ax_all = plt.subplots(figsize=[13.0, 10.0])
#ax_all.set_title(f"All Reflectivity")
"""for f in range(len(all_1d_refs)):
    #only once per year from chagpt
    year = group_years[f]

    if year not in labeled_years:
        label = f"Reflectivity, Year 1995"#{year}"
        labeled_years.add(year)
    else:
        label = None  # No label for legend

    
    #attemptong to plot the erorororororororororor
    ax_all.errorbar(x=all_1d_refs[f], y=all_2d_refs[f],
                yerr=(np.abs(all_2d_refs[f] - each_flight_lower_ref[f][1]), 
                      np.abs(each_flight_upper_ref[f][1] - all_2d_refs[f])),
                xerr=(np.abs(all_1d_refs[f] - each_flight_lower_ref[f][0]), 
                      np.abs(each_flight_upper_ref[f][0] - all_1d_refs[f])),
                ls='none', capsize=2, elinewidth=0.2, fmt='none')
    """

ax_all.plot([0, max_plot], [0, max_plot], color='black', label='1:1 Line')
ax_all.plot(xaxis, all_yaxis, \
            label=f'Best Fit: yint = {np.round(yint_all, 2)}\n              slope = {np.round(slope_all, 2)}\n              $R^2$ = {round(r2_all_flights, 2)}',#$R^2$ = {r2_all_flights:.2e}',#'$R^2$ = {round(r2_all_flights, 2)}', \
            color='black', linestyle=':')


for f in range(len(all_1d_refs)):
    #only once per year from chagpt
    year = group_years[f]

    if str(year)+' Reflectivity' not in labeled_years:
        label = str(year)+' Reflectivity'#f"Reflectivity, Year 1995"#{year}"
        labeled_years.add(str(year) + ' Reflectivity')
    else:
        label = None  # No label for legend
    
    ax_all.scatter(all_1d_refs[f], all_2d_refs[f], \
                   label=label, 
                   color=colors_project[f], marker=markers_project[f])
    






ax_all.set_xlim(axlims)
ax_all.set_ylim(axlims)
#ax_all.set_xlabel('1D Estimated Reflectivity (dBZ)', fontsize=25)
#ax_all.set_ylabel('HVPS1 Estimated Reflectivity (dBZ)', fontsize=25)
#ax_all.set_title(f"HS 1D vs HVPS1 Estimated Reflectivity For All Flights", fontsize=25, pad=20)     
#Hail Spectrometer 1D vs 2D
ax_all.set_xlabel('HS 1D Reflectivity (dBZ)', fontsize=25)
ax_all.set_ylabel('HS 2D Reflectivity (dBZ)', fontsize=25)
ax_all.set_title(f"HS 1D vs HS 2D Reflectivity For All Flights", fontsize=25, pad=20)     


ax_all.tick_params(axis='both', labelsize=25)
 
ax_all.grid(alpha=.4)
ax_all.legend(fontsize=20, loc='upper left')

plt.show()
plt.savefig(f"Quantitative_Folder/Flight_All_temp")




#------------------------------------------------------------------------------   
#the xaxis error plots
#Not binned by 5dbz
#------------------------------------------------------------------------------   
"""
for f in range(len(all_1d_refs)):
    fig, ax = plt.subplots(figsize=[13.0, 10.0])
    ax.scatter(all_1d_refs[f], np.zeros(len(all_1d_refs[f])), label='Reflectivity')
    ax.errorbar(y=np.zeros(len(all_1d_refs[f])), x=all_1d_refs[f],
                yerr=(all_1d_refs[f] - each_flight_lower_ref[f][0], 
                      each_flight_upper_ref[f][0] - all_1d_refs[f]),
                ls='none', capsize=4, elinewidth=1, fmt='none')
    
    #ax.plot([0, 70], [0, 70], color='black', label='Slope 1 Line')
    #ax.plot(xaxis, yaxis[f], color='black', label='Best Fit', linestyle=':')
    ax.set_ylim([-20, 20])
    ax.set_xlim([min_plot, max_plot])
    ax.set_xlabel('Estimated dBZ 1D_Uncertainty', fontsize=25)
    ax.set_ylabel('Estimated dBZ 1D', fontsize=25)
    ax.set_title(f"Flight {flight_nums_3[f]}, {flight_dates[f]}", fontsize=25)  
    
    ax.tick_params(axis='both', labelsize=25)
    
    ax.grid(alpha=.4)
    ax.legend(fontsize=25, loc='upper left')
    
    #plt.show()
    plt.savefig(f"Quantitative_Folder/xaxis1d_Flight_{flight_nums_3[f]}_{flight_dates[f]}")

#INBETWEEN COMMENT - the 0 is 1d the 1 is 2d
    
for f in range(len(all_2d_refs)):
    fig, ax = plt.subplots(figsize=[13.0, 10.0])
    ax.scatter(all_2d_refs[f], np.zeros(len(all_2d_refs[f])), label='Reflectivity')
    ax.errorbar(y=np.zeros(len(all_2d_refs[f])), x=all_2d_refs[f],
                yerr=(all_2d_refs[f] - each_flight_lower_ref[f][1], 
                      each_flight_upper_ref[f][1] - all_2d_refs[f]),
                ls='none', capsize=4, elinewidth=1, fmt='none')
    
    #ax.plot([0, 70], [0, 70], color='black', label='Slope 1 Line')
    #ax.plot(xaxis, yaxis[f], color='black', label='Best Fit', linestyle=':')
    ax.set_ylim([-20, 20])
    ax.set_xlim([min_plot, max_plot])
    ax.set_xlabel('Estimated dBZ 2D_Uncertainty', fontsize=25)
    ax.set_ylabel('Estimated dBZ 2D', fontsize=25)
    ax.set_title(f"Flight {flight_nums_3[f]}, {flight_dates[f]}", fontsize=25)  
    
    ax.tick_params(axis='both', labelsize=25)
    
    ax.grid(alpha=.4)
    ax.legend(fontsize=25, loc='upper left')
    
    #plt.show()
    plt.savefig(f"Quantitative_Folder/xaxis2d_Flight_{flight_nums_3[f]}_{flight_dates[f]}")
    
    
#field campaign xaxis plots
for c in range(len(flight_years2)):
    fig, ax = plt.subplots(figsize=[13.0, 10.0])
    
    #flatten for now
    flat_2D_ref = np.concatenate(campaigns_ref_2D[c])
    flat_2D_ref_upper = np.concatenate(campaigns_ref_u_2D[c])
    flat_2D_ref_lower = np.concatenate(campaigns_ref_l_2D[c])
    
    ax.scatter(flat_2D_ref, np.zeros(len(flat_2D_ref)), label='Reflectivity')
    ax.errorbar(y=np.zeros(len(flat_2D_ref)), x=flat_2D_ref,
                yerr=(flat_2D_ref - flat_2D_ref_lower, 
                      flat_2D_ref_upper - flat_2D_ref),
                ls='none', capsize=4, elinewidth=1, fmt='none')
    
    #ax.plot([0, 70], [0, 70], color='black', label='Slope 1 Line')
    #ax.plot(xaxis, yaxis[f], color='black', label='Best Fit', linestyle=':')
    ax.set_ylim([-20, 20])
    ax.set_xlim([min_plot, max_plot])
    ax.set_xlabel('Estimated dBZ 2D_Uncertainty', fontsize=25)
    ax.set_ylabel('Estimated dBZ 2D', fontsize=25)
    ax.set_title(f"Campaign_{flight_years2[c]}", fontsize=25)  
    
    ax.tick_params(axis='both', labelsize=25)
    
    ax.grid(alpha=.4)
    ax.legend(fontsize=25, loc='upper left')
    
    #plt.show()
    plt.savefig(f"Quantitative_Folder/xaxis2d_Campaign_{flight_years2[c]}")


def plot_campaign_uncert(data, upper_uncert, lower_uncert, type_probe,
                         year, uncert_type):
    fig, ax = plt.subplots(figsize=[13.0, 10.0])
    
    flat_ref   = np.concatenate(data)
    flat_ref_u = np.concatenate(upper_uncert)
    flat_ref_l = np.concatenate(lower_uncert)
    
    #sometimes the upp/lower uncertainty is the same as the main uncertainty
    #but subtracting the two introduces floating point issues where it might
    #lead to a tiiiiinnnnyyyy negative number like -0.00000001 but matplotlib
    #can't plot that, so this brief check is here to prevent that
    #~ is so that it replaces the small negative values  not the opposite case
    upper_error = flat_ref_u - flat_ref
    lower_error = flat_ref - flat_ref_l
    #if upper_error < 0 and upper_error > -1:
    upper_error = np.where(~((upper_error < 0) & (upper_error > -1)),
                           upper_error, 0)
    #if lower_error < 0 and lower_error > -1:
    lower_error = np.where(~((lower_error < 0) & (lower_error > -1)),
                           lower_error, 0)
    #print('upper', upper_error, '\n\n', 'lower', lower_error)
    yaxis = np.zeros(len(flat_ref))
    
    ax.scatter(flat_ref, yaxis, label='Reflectivity')
    
    ax.errorbar(y=yaxis, x=flat_ref,
                yerr=(lower_error, 
                      upper_error),
                ls='none', capsize=4, elinewidth=1, fmt='none')
    
    ax.set_ylim([-20, 20])
    ax.set_xlim([min_plot, max_plot])
    ax.set_xlabel(f'Estimated dBZ {type_probe}', fontsize=25)
    ax.set_ylabel(f'Estimated dBZ {type_probe} {uncert_type} Uncertainty', fontsize=25)
    ax.set_title(f"Campaign_{year}_{type_probe}_{uncert_type}", fontsize=25)  
    ax.tick_params(axis='both', labelsize=25)
    ax.grid(alpha=.4)
    ax.legend(fontsize=25, loc='upper left')
    
    #plt.show()
    plt.savefig(f"Quantitative_Folder/{type_probe}_{uncert_type}_Campaign_{year}")

#plot 2D
for c in range(len(flight_years2)): #c for campaign
    #biggest uncertainty    
    plot_campaign_uncert(campaigns_ref_2D[c], campaigns_ref_u_2D[c], 
                         campaigns_ref_l_2D[c], '2D', flight_years2[c],
                         'biggest')
    
    #poisson uncertainty    
    plot_campaign_uncert(campaigns_ref_2D[c], campaigns_ref_u_poisson_2D[c], 
                         campaigns_ref_l_poisson_2D[c], '2D', flight_years2[c],
                         'poisson')
    #sizing uncertainty    
    plot_campaign_uncert(campaigns_ref_2D[c], campaigns_ref_u_sizing_2D[c], 
                         campaigns_ref_l_sizing_2D[c], '2D', flight_years2[c],
                         'sizing')
    
    #spatial uncertainty    
    plot_campaign_uncert(campaigns_ref_2D[c], campaigns_ref_u_spatial_2D[c], 
                         campaigns_ref_l_spatial_2D[c], '2D', flight_years2[c],
                         'spatial')
    



#all together xaxis plots
"""    

#--------------------------------------------
#Binning together by flight now
#Then binning together by increments of 5 dbz
#--------------------------------------------


    
    
#creating 5dbz masks onto those field campiagns and the individual flights
def bin_by_dbz(data, upper_uncert, lower_uncert, bin_increment):
    global min_ref
    global max_plot
    
    #force data to be numpy arrays
    data = np.array(data)
    upper_uncert = np.array(upper_uncert)
    lower_uncert = np.array(lower_uncert)
    
    #go through and make list for each increment of data
    binned_data_mid = []
    binned_data_upp = []
    binned_data_low = []
    for x in range(min_ref, max_plot, bin_increment):
        lower = x
        upper = x + bin_increment
        ref_mask = ((data >= lower) & (data < upper))
        
        temp_mid = data[ref_mask]
        temp_upp = upper_uncert[ref_mask]
        temp_low = lower_uncert[ref_mask]
        
        binned_data_mid.append(temp_mid)
        binned_data_upp.append(temp_upp)
        binned_data_low.append(temp_low)
    
    return binned_data_mid, binned_data_upp, binned_data_low
    
campaign_2D_binned_mid, campaign_2D_binned_upp, campaign_2D_binned_low = \
                          bin_by_dbz(campaigns_ref_2D[0][0], 
                                    campaigns_ref_u_spatial_2D[0][0], 
                                    campaigns_ref_l_spatial_2D[0][0], 
                                    dbz_bin_amount)     
    
   
  
    
    
#making loop to bin year data
#structure is p, y, data where p==probe, y==year, data==ref data
"""
campaign_xx_ref_mid_binned = []
campaign_xx_ref_upp_big_binned = []
campaign_xx_ref_low_big_binned = []
campaign_xx_ref_upp_poi_binned = []
campaign_xx_ref_low_poi_binned = []
campaign_xx_ref_upp_siz_binned = []
campaign_xx_ref_low_siz_binned = []
campaign_xx_ref_upp_aft_binned = []
campaign_xx_ref_low_aft_binned = []

for p in range(2): #hardcoding in that it's two probes
    temp_ref_mid_binned = []
    temp_ref_upp_big_binned = []
    temp_ref_low_big_binned = []
    temp_ref_upp_poi_binned = []
    temp_ref_low_poi_binned = []
    temp_ref_upp_siz_binned = []
    temp_ref_low_siz_binned = []
    temp_ref_upp_aft_binned = []
    temp_ref_low_aft_binned = []
    for y in range(len(campaign_2D_ref_mid)): #for each year
        binned_mid, binned_upp_big, binned_low_big = bin_by_dbz(\
                            campaign_xx_ref_mid[p][y],
                            campaign_xx_ref_upp_big[p][y],
                            campaign_xx_ref_low_big[p][y], 
                            dbz_bin_amount)
            
        binned_mid, binned_upp_poi, binned_low_poi = bin_by_dbz(\
                            campaign_xx_ref_mid[p][y],
                            campaign_xx_ref_upp_poi[p][y],
                            campaign_xx_ref_low_poi[p][y], 
                            dbz_bin_amount)
            
        binned_mid, binned_upp_siz, binned_low_siz = bin_by_dbz(\
                            campaign_xx_ref_mid[p][y],
                            campaign_xx_ref_upp_siz[p][y],
                            campaign_xx_ref_low_siz[p][y], 
                            dbz_bin_amount)
            
        binned_mid, binned_upp_aft, binned_low_aft = bin_by_dbz(\
                            campaign_xx_ref_mid[p][y],
                            campaign_xx_ref_upp_aft[p][y],
                            campaign_xx_ref_low_aft[p][y], 
                            dbz_bin_amount)
        
        # Append all binned values for this year
        temp_ref_mid_binned.append(binned_mid)
        temp_ref_upp_big_binned.append(binned_upp_big)
        temp_ref_low_big_binned.append(binned_low_big)
        temp_ref_upp_poi_binned.append(binned_upp_poi)
        temp_ref_low_poi_binned.append(binned_low_poi)
        temp_ref_upp_siz_binned.append(binned_upp_siz)
        temp_ref_low_siz_binned.append(binned_low_siz)
        temp_ref_upp_aft_binned.append(binned_upp_aft)
        temp_ref_low_aft_binned.append(binned_low_aft)
    
    # Append per-probe bins
    campaign_xx_ref_mid_binned.append(temp_ref_mid_binned)
    campaign_xx_ref_upp_big_binned.append(temp_ref_upp_big_binned)
    campaign_xx_ref_low_big_binned.append(temp_ref_low_big_binned)
    campaign_xx_ref_upp_poi_binned.append(temp_ref_upp_poi_binned)
    campaign_xx_ref_low_poi_binned.append(temp_ref_low_poi_binned)
    campaign_xx_ref_upp_siz_binned.append(temp_ref_upp_siz_binned)
    campaign_xx_ref_low_siz_binned.append(temp_ref_low_siz_binned)
    campaign_xx_ref_upp_aft_binned.append(temp_ref_upp_aft_binned)
    campaign_xx_ref_low_aft_binned.append(temp_ref_low_aft_binned)
"""            
def bin_all_refs_by_dbz(ref_mid, ref_upp_big, ref_low_big,
                        ref_upp_poi, ref_low_poi,
                        ref_upp_siz, ref_low_siz,
                        ref_upp_aft, ref_low_aft,
                        dbz_bin_amount):
    """
    Bin all reference datasets by dbz for 1D and 2D probes.

    Parameters:
        ref_mid, ref_upp_*, ref_low_*: list of [1D, 2D] datasets (each a list per year)
        dbz_bin_amount: int or float, bin width for dbz

    Returns:
        A tuple of 9 lists, each [1D, 2D], of per-year binned results
    """
    # Output containers
    ref_mid_binned     = []
    ref_upp_big_binned = []
    ref_low_big_binned = []
    ref_upp_poi_binned = []
    ref_low_poi_binned = []
    ref_upp_siz_binned = []
    ref_low_siz_binned = []
    ref_upp_aft_binned = []
    ref_low_aft_binned = []

    for p in range(2):  # 0 = 1D, 1 = 2D
        temp_ref_mid_binned     = []
        temp_ref_upp_big_binned = []
        temp_ref_low_big_binned = []
        temp_ref_upp_poi_binned = []
        temp_ref_low_poi_binned = []
        temp_ref_upp_siz_binned = []
        temp_ref_low_siz_binned = []
        temp_ref_upp_aft_binned = []
        temp_ref_low_aft_binned = []

        for y in range(len(ref_mid[p])):  # Loop over years
            binned_mid, binned_upp_big, binned_low_big = bin_by_dbz(
                ref_mid[p][y], ref_upp_big[p][y], ref_low_big[p][y], dbz_bin_amount)

            _, binned_upp_poi, binned_low_poi = bin_by_dbz(
                ref_mid[p][y], ref_upp_poi[p][y], ref_low_poi[p][y], dbz_bin_amount)

            _, binned_upp_siz, binned_low_siz = bin_by_dbz(
                ref_mid[p][y], ref_upp_siz[p][y], ref_low_siz[p][y], dbz_bin_amount)

            _, binned_upp_aft, binned_low_aft = bin_by_dbz(
                ref_mid[p][y], ref_upp_aft[p][y], ref_low_aft[p][y], dbz_bin_amount)

            temp_ref_mid_binned.append(binned_mid)
            temp_ref_upp_big_binned.append(binned_upp_big)
            temp_ref_low_big_binned.append(binned_low_big)
            temp_ref_upp_poi_binned.append(binned_upp_poi)
            temp_ref_low_poi_binned.append(binned_low_poi)
            temp_ref_upp_siz_binned.append(binned_upp_siz)
            temp_ref_low_siz_binned.append(binned_low_siz)
            temp_ref_upp_aft_binned.append(binned_upp_aft)
            temp_ref_low_aft_binned.append(binned_low_aft)

        # Append per-probe (1D or 2D) results
        ref_mid_binned.append(temp_ref_mid_binned)
        ref_upp_big_binned.append(temp_ref_upp_big_binned)
        ref_low_big_binned.append(temp_ref_low_big_binned)
        ref_upp_poi_binned.append(temp_ref_upp_poi_binned)
        ref_low_poi_binned.append(temp_ref_low_poi_binned)
        ref_upp_siz_binned.append(temp_ref_upp_siz_binned)
        ref_low_siz_binned.append(temp_ref_low_siz_binned)
        ref_upp_aft_binned.append(temp_ref_upp_aft_binned)
        ref_low_aft_binned.append(temp_ref_low_aft_binned)

    return (ref_mid_binned, ref_upp_big_binned, ref_low_big_binned,
            ref_upp_poi_binned, ref_low_poi_binned,
            ref_upp_siz_binned, ref_low_siz_binned,
            ref_upp_aft_binned, ref_low_aft_binned)

campaign_xx_ref_mid_binned, campaign_xx_ref_upp_big_binned,\
    campaign_xx_ref_low_big_binned, campaign_xx_ref_upp_poi_binned, \
    campaign_xx_ref_low_poi_binned, campaign_xx_ref_upp_siz_binned, \
    campaign_xx_ref_low_siz_binned, campaign_xx_ref_upp_aft_binned,  \
    campaign_xx_ref_low_aft_binned = bin_all_refs_by_dbz(
     campaign_xx_ref_mid, campaign_xx_ref_upp_big, campaign_xx_ref_low_big,
     campaign_xx_ref_upp_poi, campaign_xx_ref_low_poi,
     campaign_xx_ref_upp_siz, campaign_xx_ref_low_siz,
     campaign_xx_ref_upp_aft, campaign_xx_ref_low_aft,
     dbz_bin_amount)
  



def bin_all_refs_by_dbz_entire(ref_mid, ref_upp_big, ref_low_big,
                               ref_upp_poi, ref_low_poi,
                               ref_upp_siz, ref_low_siz,
                               ref_upp_aft, ref_low_aft,
                               dbz_bin_amount,
                               ref_diffs):
    """
    Bin all reference datasets by dbz for 1D and 2D probes for entire flight (no yearly split).
    Assumes ref_* are lists with 2 elements: [1D_array, 2D_array]
    """

    ref_mid_binned     = []
    ref_upp_big_binned = []
    ref_low_big_binned = []
    ref_upp_poi_binned = []
    ref_low_poi_binned = []
    ref_upp_siz_binned = []
    ref_low_siz_binned = []
    ref_upp_aft_binned = []
    ref_low_aft_binned = []

    for p in range(2):  # 0=1D, 1=2D
        binned_mid, binned_upp_big, binned_low_big = bin_by_dbz(
            ref_mid[p], ref_upp_big[p], ref_low_big[p], dbz_bin_amount)

        _, binned_upp_poi, binned_low_poi = bin_by_dbz(
            ref_mid[p], ref_upp_poi[p], ref_low_poi[p], dbz_bin_amount)

        _, binned_upp_siz, binned_low_siz = bin_by_dbz(
            ref_mid[p], ref_upp_siz[p], ref_low_siz[p], dbz_bin_amount)

        _, binned_upp_aft, binned_low_aft = bin_by_dbz(
            ref_mid[p], ref_upp_aft[p], ref_low_aft[p], dbz_bin_amount)

        ref_mid_binned.append(binned_mid)
        ref_upp_big_binned.append(binned_upp_big)
        ref_low_big_binned.append(binned_low_big)
        ref_upp_poi_binned.append(binned_upp_poi)
        ref_low_poi_binned.append(binned_low_poi)
        ref_upp_siz_binned.append(binned_upp_siz)
        ref_low_siz_binned.append(binned_low_siz)
        ref_upp_aft_binned.append(binned_upp_aft)
        ref_low_aft_binned.append(binned_low_aft)

    #ref_diffs_binned = []
    _, binned_diffs_upp, binned_diffs_low = \
                bin_by_dbz(ref_mid[0], ref_diffs, ref_diffs, dbz_bin_amount)
    
    #test = entire_xx_ref_diffs
    for x in range(len(binned_diffs_upp)):
        binned_diffs_upp[x] = np.where(binned_diffs_upp[x] >= 0, binned_diffs_upp[x], np.nan)
        binned_diffs_low[x] = np.where(binned_diffs_low[x] < 0, binned_diffs_low[x], np.nan)

    return (ref_mid_binned, ref_upp_big_binned, ref_low_big_binned,
            ref_upp_poi_binned, ref_low_poi_binned,
            ref_upp_siz_binned, ref_low_siz_binned,
            ref_upp_aft_binned, ref_low_aft_binned,
            binned_diffs_upp, binned_diffs_low)

         
entire_xx_ref_diffs = []
for x in range(len(all_1d_refs)):
    diffs_t = all_1d_refs[x] - all_2d_refs[x]
    for v in diffs_t:
        entire_xx_ref_diffs.append(v)
    

      
entire_xx_ref_mid_binned, entire_xx_ref_upp_big_binned, \
entire_xx_ref_low_big_binned, entire_xx_ref_upp_poi_binned, \
entire_xx_ref_low_poi_binned, entire_xx_ref_upp_siz_binned, \
entire_xx_ref_low_siz_binned, entire_xx_ref_upp_aft_binned, \
entire_xx_ref_low_aft_binned, \
entire_xx_ref_diffs_upp, entire_xx_ref_diffs_low = bin_all_refs_by_dbz_entire(
    entire_xx_ref_mid, entire_xx_ref_upp_big, entire_xx_ref_low_big,
    entire_xx_ref_upp_poi, entire_xx_ref_low_poi,
    entire_xx_ref_upp_siz, entire_xx_ref_low_siz,
    entire_xx_ref_upp_aft, entire_xx_ref_low_aft,
    dbz_bin_amount,
    entire_xx_ref_diffs)
        
    

#making loop to bin flight data
pass
    
    

#bin the all flights everything entire data

    
    
    
    
locations   = np.arange(min_ref+dbz_bin_amount/2, max_plot, dbz_bin_amount)  
plot_xticks = np.arange(min_ref, max_plot+dbz_bin_amount, dbz_bin_amount) 


    
#plot_centered_uncertainty_boxplot(
#    campaign_2D_binned_mid,
#    campaign_2D_binned_upp,
#    campaign_2D_binned_low,
#    locations,
#    'test')    
    
    
 


#[uncertainty_group][midupper/lower][probe][year][10ish data bins]
campaign_groups = [
                   [campaign_xx_ref_mid_binned, campaign_xx_ref_upp_big_binned, campaign_xx_ref_low_big_binned],
                   [campaign_xx_ref_mid_binned, campaign_xx_ref_upp_poi_binned, campaign_xx_ref_low_poi_binned],
                   [campaign_xx_ref_mid_binned, campaign_xx_ref_upp_siz_binned, campaign_xx_ref_low_siz_binned],
                   [campaign_xx_ref_mid_binned, campaign_xx_ref_upp_aft_binned, campaign_xx_ref_low_aft_binned]                   
                  ]


uncert_types_list = ['Biggest', 'Poisson', 'Sizing', 'Along-Flight Track']
probe_types = ['1D', '2D']


entire_groups = [
                 [entire_xx_ref_mid_binned, entire_xx_ref_upp_big_binned, entire_xx_ref_low_big_binned],
                 [entire_xx_ref_mid_binned, entire_xx_ref_upp_poi_binned, entire_xx_ref_low_poi_binned],
                 [entire_xx_ref_mid_binned, entire_xx_ref_upp_siz_binned, entire_xx_ref_low_siz_binned],
                 [entire_xx_ref_mid_binned, entire_xx_ref_upp_aft_binned, entire_xx_ref_low_aft_binned]
                ]
                           

entire_diff_groups = [entire_xx_ref_mid_binned, entire_xx_ref_diffs_upp, entire_xx_ref_diffs_low] 
    

    
    
    
#Making new plotting scheme since uncertainty is kinda eh now and can be represented
#differently. should do observed ref comparison after this.

#so, making x-axis 5dbz bins and y axis is how many were in that bin
#does that mean I do the uncertainty on the x-axis? oh wait i can do a dual y axis im genius


#First, retrieve total number of intervals with a reflectivity in a bin
num_ea_bin = []
for p in range(len(entire_xx_ref_mid_binned)):
    probe_total = []
    for x in range(len(entire_xx_ref_mid_binned[p])):
        total = len(entire_xx_ref_mid_binned[p][x])
        probe_total.append(total)
    num_ea_bin.append(probe_total)



#Now generate boxplot data for each bin for each probe
#-----------------------------------------------------------
#medians ----------------------
lower_medians = []
upper_medians = []
lower_medians_diff = []
upper_medians_diff = []
for p in range(len(entire_xx_ref_mid_binned)):
    low_bin_medians = []
    upp_bin_medians = []
    
    low_bin_medians_diff = []
    upp_bin_medians_diff = []
    for x in range(len(entire_xx_ref_mid_binned[p])):
        low_bin_median = np.median(entire_xx_ref_low_poi_binned[p][x])
        low_bin_medians.append(low_bin_median)
        
        upp_bin_median = np.median(entire_xx_ref_upp_poi_binned[p][x])
        upp_bin_medians.append(upp_bin_median)
        
        
        
        low_bin_median_diff = entire_xx_ref_mid_binned[p][x] - entire_xx_ref_low_poi_binned[p][x]
        low_bin_median_diff_single = np.median(low_bin_median_diff)
        low_bin_medians_diff.append(low_bin_median_diff_single)
        
        upp_bin_median_diff = entire_xx_ref_upp_poi_binned[p][x] - entire_xx_ref_mid_binned[p][x]
        upp_bin_median_diff_single = np.median(upp_bin_median_diff)
        upp_bin_medians_diff.append(upp_bin_median_diff_single)
    
    lower_medians.append(low_bin_medians)
    upper_medians.append(upp_bin_medians)
    
    lower_medians_diff.append(low_bin_medians_diff)
    upper_medians_diff.append(upp_bin_medians_diff)

#percetiles
lower_percentile = []
upper_percentile = []
lower_percentile_diff = []
upper_percentile_diff = []

upper_refdiff_percentile = []
lower_refdiff_percentile = []
for p in range(len(entire_xx_ref_mid_binned)):
    low_bin_percentile = []
    upp_bin_percentile = []
    
    low_bin_percentile_diff = []
    upp_bin_percentile_diff = []
    
    low_refdiff_bin_percentile = []
    upp_refdiff_bin_percentile = []
    for x in range(len(entire_xx_ref_mid_binned[p])):
        low_percentile = np.percentile(entire_xx_ref_low_poi_binned[p][x], q=10) if\
                         len(entire_xx_ref_low_poi_binned[p][x]) > 0 else np.nan
        low_bin_percentile.append(low_percentile)
        
        upp_percentile = np.percentile(entire_xx_ref_upp_poi_binned[p][x], q=90) if\
                         len(entire_xx_ref_low_poi_binned[p][x]) > 0 else np.nan
        upp_bin_percentile.append(upp_percentile)

    
        low_bin_diff = entire_xx_ref_mid_binned[p][x] - entire_xx_ref_low_poi_binned[p][x]
        low_percentile_diff = np.percentile(low_bin_diff, q=90) if\
                         len(entire_xx_ref_low_poi_binned[p][x]) > 0 else np.nan
        low_bin_percentile_diff.append(low_percentile_diff)
        
        upp_bin_diff = entire_xx_ref_upp_poi_binned[p][x] - entire_xx_ref_mid_binned[p][x]
        upp_percentile_diff = np.percentile(upp_bin_diff, q=90) if\
                         len(entire_xx_ref_upp_poi_binned[p][x]) > 0 else np.nan
        upp_bin_percentile_diff.append(upp_percentile_diff)

    
        low_refdiff_percentile = np.nanpercentile(entire_xx_ref_diffs_low[x], q=10) if\
                         len(entire_xx_ref_diffs_low[x]) > 0 else np.nan
        low_refdiff_bin_percentile.append(low_refdiff_percentile)
        
        upp_refdiff_percentile = np.nanpercentile(entire_xx_ref_diffs_upp[x], q=90) if\
                         len(entire_xx_ref_diffs_upp[x]) > 0 else np.nan
        upp_refdiff_bin_percentile.append(upp_refdiff_percentile)

    lower_percentile.append(low_bin_percentile)
    upper_percentile.append(upp_bin_percentile)
    
    lower_percentile_diff.append(low_bin_percentile_diff)
    upper_percentile_diff.append(upp_bin_percentile_diff)
    
    
#now to plot?
locations   = np.arange(min_ref+dbz_bin_amount/2, max_plot, dbz_bin_amount)  
plot_xticks = np.arange(min_ref, max_plot+dbz_bin_amount, dbz_bin_amount) 

    
def plot_probes_poisson_uncert(entire_groups, locations, uncert_types_list, 
                               probe_types, medians, quartiles, frequency,
                               box_width=1.25, line_width=2, fontsize=20):
    #chatgpt was very heavily used to make this boxplot def. 
    #data was checked though and output was checked so it should
    #all be good to go

    markers = ['o', '*']

    n_groups = 2#len(entire_groups)  # how many groups to plot side by side
    shift_amount = box_width * 1.5  # horizontal distance between box groups

    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(8, 10), dpi=150, sharex=True)

    #fig, ax = plt.subplots(figsize=(6,6), dpi=150)
    #ax2 = ax.twinx()
    # To collect legend handles
    legend_handles = []
    legend_handles2 = []

    for p in range(len(probe_types)):
        
        data_to_plot = []
        positions = []


        #legend_handles.append(probe_types[p])
        # Center the groups around original location, so they don't shift all to one side
        # e.g. for 4 groups: shifts = [-1.5*shift, -0.5*shift, 0.5*shift, 1.5*shift]
        shifts = np.linspace(-shift_amount*(n_groups-1)/2, shift_amount*(n_groups-1)/2, n_groups)


        for i in range(len(medians[0][p])):
    
            if len(medians[0][p]) == 0:
                q1 = 0
                whisker_low = 0
            else:
                #q1 = -np.percentile(low_diffs, 25) #chatgpt baaad
                q1 = -medians[0][p][i]#-np.median(low_diffs)
                whisker_low = -quartiles[0][p][i]#-np.percentile(low_diffs, 90, method='nearest')#-np.max(low_diffs)
                #print(whisker_low, q1)

            if len(medians[1][p]) == 0:
                q3 = 0
                whisker_high = 0
            else:
                #q3 = np.percentile(upp_diffs, 75) #chatgpt baaad
                q3 = medians[1][p][i]#np.median(upp_diffs)
                whisker_high = quartiles[1][p][i]#np.percentile(upp_diffs, 90, method='nearest')#np.max(upp_diffs)
            #print(low_diffs, 'hiiii', q1, np.percentile(low_diffs, 10, method='nearest'))    
            

            box = {
                'med': 0,
                'q1': q1,
                'q3': q3,
                'whislo': whisker_low,
                'whishi': whisker_high,
                'fliers': [],
                'label': f"{p:.1f}"
                }
            data_to_plot.append(box)
            positions.append(locations[i] + shifts[p])  # apply horizontal shift

        #print(data_to_plot)
        #print(positions)
        bxp = ax.bxp(data_to_plot, positions=positions, showfliers=False,
                     widths=box_width,
                     boxprops=dict(linewidth=line_width),
                     whiskerprops=dict(linewidth=line_width),
                     capprops=dict(linewidth=line_width),
                     medianprops=dict(linewidth=line_width),
                     patch_artist=True)
        
        #cbf_colors = [
        #    "#000000",  # Black - darkest
        #    "#D73027",  # Red - fairly dark and vivid
        #    "#4575B4",  # Blue - medium brightness
        #    "#91CF60",  # Green - lightest/bright
        #        ]
        
        cbf_colors = [
            "#000000",  # Black
            "#404040",  # Dark Grey
            "#808080",  # Medium Grey
            "#BFBFBF",  # Light Grey
            "#DCDCDC"   # Very Light Grey
                     ]
        

        cbf_colors= ["#000000", "#800000", "#3366CC", "#66CC99"]
        
        # Inside your plotting loop:
        color = cbf_colors[p+1]# cbf_colors[g_idx % len(cbf_colors)]
        for patch in bxp['boxes']:
            patch.set_facecolor(color)

        legend_handles.append(bxp["boxes"][0])
        
        
        #plot frequency
        scatter_colors = ['#B33333', '#6699E6']
        lazy_positions = [32.5, 37.5, 42.5, 47.5, 52.5, 57.5, 62.5, 67.5, 72.5, 77.5]
        ax2.scatter(lazy_positions, frequency[p], color=color, 
                    label=probe_types[p], marker=markers[p],
                    s=100, edgecolor='black')
        legend_handles2.append([])
        


    ax.axhline(0, color='black', linestyle='--', linewidth=2)
    #ax.set_xlabel('Reflectivity per 5 dBZ Group', fontsize=fontsize)
    ax.set_ylabel('Reflectivity Uncertainty (dBZ)', fontsize=fontsize)
    ax.set_title('HS Reflectivity Uncertainty and Frequency', fontsize=fontsize)#(f'Probe Type: Hail Spectrometer {probe_types[p]} - Uncertainty Types Comparison', fontsize=fontsize+2)

    #its a bit confusing having the x-axis be normal but the bars
    #plotted spaced out. idk it would just be more visually intuitive
    #to make the xaxis groups so i had chatgpt figure this out
    #its a bit confusing having the x-axis be normal but the bars
    #plotted spaced out. idk it would just be more visually intuitive
    #to make the xaxis groups so i had chatgpt figure this out
    # Set tick locations and labels for binned axis
    #bin_edges = np.arange(30, 75, 5)
    #bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    #bin_labels = [f"{a}-{b}" for a, b in zip(bin_edges[:-1], bin_edges[1:])]
    
    #ax.set_xticks(bin_centers)
    #ax.set_xticklabels(bin_labels, rotation=45)


    ax.set_xticks(plot_xticks)
    ax.set_xticklabels([str(x) for x in plot_xticks])
    #Add padding around the min and max xticks:
    padding = (plot_xticks[-1] - plot_xticks[0]) * 0.05  # 5% of the total range
    xmin = plot_xticks[0] - padding
    xmax = plot_xticks[-1] + padding
    ax.set_xlim(xmin, xmax)
    
    ax.set_yticks(np.arange(-30, 5.1, 5))#(np.arange(-50, 40+10, 10))
    ax.set_ylim(-27.2, 5.2)

    ax.grid(True)
    ax.legend(legend_handles, probe_types, 
              loc='lower left', fontsize=fontsize)


    #setting up axis 2
    ax2.set_xlabel('Reflectivity per 5 dBZ Group', fontsize=fontsize)
    ax2.set_ylabel('Frequency', fontsize=fontsize)
    #matching 0 location. just did relative so sthat zeros line up
    ax2.set_ylim(0, 165)#(-262.89, 180) 
    ax2.set_yticks([0, 50, 100, 150], )
    ax2.grid()
    #ax2.legend(loc='upper right', fontsize=fontsize)

    ax.tick_params('both', labelsize=fontsize-2)    
    ax2.tick_params('both', labelsize=fontsize-2)    

    # first legend handles (probe types)
    handles1, labels1 = ax.get_legend_handles_labels()
    
    # second legend handles (ax2 frequency, etc.)
    handles2, labels2 = ax2.get_legend_handles_labels()
    
    # combine them
    handles = handles1 + handles2
    labels = labels1 + labels2
    
    # make one legend
    #ax.legend(handles, labels, loc='lower left', fontsize=fontsize)
    ax2.legend(handles, labels, loc='upper right', fontsize=fontsize)


    plt.tight_layout()
    plt.show()

#len(entire_groups[1][0][0][3]) #poisson, into, probe, into the ref stuff

plot_probes_poisson_uncert(entire_groups[1][0], locations, 
                                 uncert_types_list, probe_types,
                                 [lower_medians_diff, upper_medians_diff], 
                                 [lower_percentile_diff, upper_percentile_diff],
                                 num_ea_bin)  
    
























#plotting for specific time period
Ref_Data_1D = nc.Dataset(flight_list[11])
Ref_Data_2D = nc.Dataset(flight_list[10])




"""
#quick variables for calculating water or air content
LWC     = np.array([1.44, 0.66, 0.81, 0.87, 1.67, 1.13, 0.58, 0.46,
                    0.28, 0.11, 0.83, 0.94])

UPDRAFT = np.array([7.83, 6.24, 6.84, 7.74, 2.45, 19.82, 7.25, -1.51,
                    -2.15, -8.66, 7.34, 9.92])

TEMP    = np.array([-4.62, -4.21, -4.12, -4.43, -4.94, -5.19, -5.90, -7.53,
                    -8.86, -8.14, -7.76, -5.89])

ice_water_dielectric = 0.197

#compute adjustment for dielectric constant
lwc_adjust     = 1 / (1/LWC)             #more lwc increases constant. centered on 1 as no adjustment so it's auto adjust if that makes sense either *1.5 or .5 ya know
updraft_adjust = 1 - ((UPDRAFT-7)/100 + 1)        #more updraft increases effect of lwc. becomes an add on. not sure how big to make the add on
temp_adjust    = -(((TEMP+4)**2)**.5 / 10 - .4)                   #colder temps reduce impact of lwc

final_adjust   = lwc_adjust - updraft_adjust + temp_adjust

ice_water_dielectric_2 = ice_water_dielectric * final_adjust

#chatgpt suggestion. elts see if it works
# Tunable params
ref_lwc = 1.0         # reference LWC (g/m^3)
max_lwc_scale = 3.0   # cap LWC ratio (avoids huge multipliers)
alpha = 0.5           # amplitude of dielectric change (±50% possible)
u0 = 7.0              # updraft center (m/s)
u_scale = 3.0         # logistic scale (m/s)
temp_warm = -3.0      # temperature (C) above which liquid coating likely
temp_cold = -15.0     # temperature (C) below which liquid coating unlikely

# Maps
f_lwc = np.clip(LWC / ref_lwc, 0.0, max_lwc_scale)
updraft_effect = 1.0 / (1.0 + np.exp(-(UPDRAFT - u0) / u_scale))   # 0..1 logistic
temp_effect = np.clip((TEMP - temp_cold) / (temp_warm - temp_cold), 0.0, 1.0)  # 0..1 linear

# Combined multiplicative factor
final_adjust = 1.0 + alpha * (f_lwc / max_lwc_scale) * updraft_effect * temp_effect
final_adjust = np.clip(final_adjust, 0.5, 1.5)  # safe bounds

# Apply to base dielectric (example base value)
ice_water_dielectric_3 = ice_water_dielectric * final_adjust
"""
"""
ref_lwc = .2         # reference LWC (g/m^3)
max_lwc_scale = 4.0   # cap LWC ratio (avoids huge multipliers)
alpha = .5           # amplitude of dielectric change (±50% possible)
u0 = 7.0              # updraft center (m/s)
u_scale = 15.0         # logistic scale (m/s)
temp_warm = -2.      # temperature (C) above which liquid coating likely
temp_cold = -15.     # temperature (C) below which liquid coating unlikely

gamma_lwc  = 5
gamma_up   = 5
gamma_temp = 5

# Maps
f_lwc = np.clip(LWC / ref_lwc, 0.0, max_lwc_scale)
updraft_effect = 1.0 / (1.0 + np.exp(-(UPDRAFT - u0) / u_scale))   # 0..1 logistic
temp_effect = (TEMP - temp_cold) / (temp_warm - temp_cold)

# Combined multiplicative factor
final_adjust = .994 \
               + alpha * (f_lwc / max_lwc_scale)**gamma_lwc \
               * (updraft_effect**gamma_up) \
               * (temp_effect**gamma_temp)
final_adjust = np.clip(final_adjust, 0.1, 4)  # safe bounds
final_adjust = np.clip(1.0 + 100 * (final_adjust - 1.0), 0.1, 4)
print(final_adjust)
"""


temp_concs = Ref_Data_2D['psd_2d_mean'][193:205]
def compute_z(D_bs, N_d):
    indv_ref = D_bs**6 * N_d
    summed_ref = np.nansum(indv_ref, axis=1)
    #power_sum = np.nansum(D_bs**6 * N_d, axis=1)
    #return -np.inf if power_sum == 0 else power_sum
    return indv_ref, summed_ref#power_sum

bin_mids_ref = (Ref_Data_2D['bin_startpoints'][:] + Ref_Data_2D['bin_size'][:]/2) /1000
temp_concs2 = temp_concs * (Ref_Data_2D['bin_size'][:]/1e6)
"""
10*np.log10(ice_water_dielectric_3 * compute_z(bin_mids_ref, temp_concs2)[1])
"""

#start and end index
#s = 193
#e = 205

ref_mean = [Ref_Data_2D['Z_e_2D_mean'][193:205], Ref_Data_2D['Z_e_2D_mean_upper_uncertainty'][193:205], 
            Ref_Data_2D['Z_e_2D_mean_lower_uncertainty'][193:205]]

ref_circle = [Ref_Data_2D['Z_e_2D_circle'][193:205], Ref_Data_2D['Z_e_2D_circle_upper_uncertainty'][193:205], 
              Ref_Data_2D['Z_e_2D_circle_lower_uncertainty'][193:205]]
ref_xsize = [Ref_Data_2D['Z_e_2D_xsize'][193:205], Ref_Data_2D['Z_e_2D_xsize_upper_uncertainty'][193:205], 
             Ref_Data_2D['Z_e_2D_xsize_lower_uncertainty'][193:205]]
ref_xextent = [Ref_Data_2D['Z_e_2D_xextent'][193:205], Ref_Data_2D['Z_e_2D_xextent_upper_uncertainty'][193:205], 
               Ref_Data_2D['Z_e_2D_xextent_lower_uncertainty'][193:205]] 
ref_ysize = [Ref_Data_2D['Z_e_2D_ysize'][193:205], Ref_Data_2D['Z_e_2D_ysize_upper_uncertainty'][193:205], 
             Ref_Data_2D['Z_e_2D_ysize_lower_uncertainty'][193:205]]
ref_areasize = [Ref_Data_2D['Z_e_2D_areasize'][193:205], Ref_Data_2D['Z_e_2D_areasize_upper_uncertainty'][193:205], 
                Ref_Data_2D['Z_e_2D_areasize_lower_uncertainty'][193:205]]

ref_1D = [Ref_Data_1D['Z_e_1D'][193:205], Ref_Data_1D['Z_e_1D_upper_uncertainty'][193:205], 
          Ref_Data_1D['Z_e_1D_lower_uncertainty'][193:205]]

ref_observed = [45.53, 50.56, 59.79, 62.72, 60.28, 56.30, 50.95, 51.13, 47.35, 44.66, 44.83, 42.88]
ref_observed = [ref_observed, ref_observed, ref_observed]

times = []
for t in Ref_Data_2D['time_start'][193:205]:
    HH = t[0:2]
    MM = t[2:4]
    SS = t[4:6]
    
    out = f'{MM}:{SS}'
    times.append(out)

refs_plot = [ref_observed, ref_1D, ref_mean, ref_circle, ref_xsize, ref_xextent, ref_ysize, ref_areasize]
#labels = ['Radar', 'HS-1D', 'HS-2D Mean', 'HS-2D Circle', 'HS-2D Xsize', 'HS-2D Xextent', 'HS-2D Ysize', 'HS-2D Areasize']
labels = ['Radar', 'HS-1D', 'HS-2D-M', 'HS-2D-C', 'HS-2D-XS', 'HS-2D-XE', 'HS-2D-Y', 'HS-2D-A']



#TOGGLE
plot_05 = True

if plot_05 == True:
    ref_05 = nc.Dataset('../../yr2000/f757/Code_Files_and_Outputs/Sensor_Information/Count_Conc_Ref_Data/20251208/20000622/242100_242300/757_PBP_Processed_HAIL-2D.nc')
    
    ref_05_mean = [ref_05['Z_e_2D_mean'][0:12], ref_05['Z_e_2D_mean_upper_uncertainty'][0:12], 
                ref_05['Z_e_2D_mean_lower_uncertainty'][0:12]]

    ref_05_circle = [ref_05['Z_e_2D_circle'][0:12], ref_05['Z_e_2D_circle_upper_uncertainty'][0:12], 
                  ref_05['Z_e_2D_circle_lower_uncertainty'][0:12]]
    ref_05_xsize = [ref_05['Z_e_2D_xsize'][0:12], ref_05['Z_e_2D_xsize_upper_uncertainty'][0:12], 
                 ref_05['Z_e_2D_xsize_lower_uncertainty'][0:12]]
    ref_05_xextent = [ref_05['Z_e_2D_xextent'][0:12], ref_05['Z_e_2D_xextent_upper_uncertainty'][0:12], 
                   ref_05['Z_e_2D_xextent_lower_uncertainty'][0:12]] 
    ref_05_ysize = [ref_05['Z_e_2D_ysize'][0:12], ref_05['Z_e_2D_ysize_upper_uncertainty'][0:12], 
                 ref_05['Z_e_2D_ysize_lower_uncertainty'][0:12]]
    ref_05_areasize = [ref_05['Z_e_2D_areasize'][0:12], ref_05['Z_e_2D_areasize_upper_uncertainty'][0:12], 
                    ref_05['Z_e_2D_areasize_lower_uncertainty'][0:12]]

    refs_05_plot = [ref_observed, ref_1D, ref_05_mean, ref_05_circle, ref_05_xsize, ref_05_xextent, ref_05_ysize, ref_05_areasize]

fig, ax = plt.subplots(figsize=(12,6))

colors_refs = [
    "#000000",  # black        - observed
    "#E41A1C",  # red          - 1D
    "#377EB8",  # blue         - mean
    "#4DAF4A",  # green        - circle
    "#984EA3",  # purple       - xsize
    "#FF7F00",  # orange       - xextent
    "#A65628",  # brown        - ysize
    "#F781BF",  # pink         - areasize
]

markers_refs = [
    "o",   # circle
    "s",   # square
    "^",   # triangle up
    "v",   # triangle down
    "D",   # diamond
    "P",   # plus (filled)
    "X",   # x (filled)
    "*",   # star
]




locations = np.arange(0, 12, 1)
fontsize = 25
pointsize = 170

fig, ax = plt.subplots(nrows=5, figsize=(12,15))
fig.suptitle('Observed vs Calculated Reflectivity', fontsize=fontsize)
for r in range(1, 6):# range(len(refs_plot)):
    
    #fig, ax = plt.subplots(figsize=(12,2.5))
    
    if r == 0:
        continue
    print(r)
    #plot obvs data for comparison
    ax[r-1].scatter(locations, refs_plot[0][0], c=colors_refs[0], 
               marker=markers_refs[0], label=labels[0], s=pointsize)
    
    #plot airplane data
    ax[r-1].scatter(locations, refs_plot[r][0], c=colors_refs[r], 
               marker=markers_refs[r], label=labels[r]+',\n0.3', s=pointsize)
    
    ax[r-1].errorbar(locations, refs_plot[r][0], 
                yerr=[np.array(refs_plot[r][0]) - np.array(refs_plot[r][2]), 
                      np.array(refs_plot[r][1]) - np.array(refs_plot[r][0])],
                c=colors_refs[r], 
                marker=markers_refs[r],
                fmt=' ', capsize=6, elinewidth=3, capthick=3)
    
    #plot airplane 0.5 area ratio data
    if plot_05 == True:
        if r == 1:
            pass
        else:
            
            ax[r-1].scatter(locations+.1, refs_05_plot[r][0], edgecolor=colors_refs[r], 
                       marker='o', label=labels[r]+',\n0.5', s=pointsize,
                       facecolor='none', linewidth=2)
        
            ax[r-1].errorbar(locations+.1, refs_05_plot[r][0], 
                        yerr=[np.array(refs_05_plot[r][0]) - np.array(refs_05_plot[r][2]), 
                              np.array(refs_05_plot[r][1]) - np.array(refs_05_plot[r][0])],
                        c=colors_refs[r], 
                        marker='none',
                        fmt=' ', capsize=6, elinewidth=3, capthick=3)
    
    
    #locations += .1

    ax[r-1].set_xticks(np.arange(0, 12, 1))#, label=times, rotation=45)    
    ax[r-1].tick_params(axis='x', which='major', labelbottom=False)
    
    ax[r-1].set_yticks(np.arange(30, 81, 20))
    ax[r-1].set_yticks(np.arange(40, 91, 20), minor=True) 
    ax[r-1].set_xlim(-0.5, 11.5)
    ax[r-1].set_ylim(26, 80)
    ax[r-1].tick_params(axis='both', which='major', labelsize=fontsize-3)
    
    ax[r-1].grid(True, which='major', linestyle='-', alpha=1)
    ax[r-1].grid(True, which='minor', linestyle='-', alpha=0.75)
    ax[r-1].legend(loc='upper right', bbox_to_anchor=(1.32, 1),
                   fontsize=fontsize-5)

        
ax[r-1].tick_params(axis='x', which='major', labelbottom=True)
ax[r-1].set_xticks(np.arange(0, 12, 1), labels=times, rotation=45)

fig.supylabel('Reflectivity (dBZ)', fontsize=fontsize)
fig.supxlabel('Time Interval Start (MM:SS)', fontsize=fontsize)

plt.tight_layout()
plt.show()





fig, ax = plt.subplots(nrows=5, figsize=(12,15))
fig.suptitle('Observed vs Calculated Reflectivity', fontsize=fontsize)
for r in range(3, 8):# range(len(refs_plot)):
    
    #fig, ax = plt.subplots(figsize=(12,2.5))
    
    if r == 0:
        continue
    
    #plot obvs data for comparison
    ax[r-3].scatter(locations, refs_plot[0][0], c=colors_refs[0], 
               marker=markers_refs[0], label=labels[0], s=pointsize)
    
    #plot airplane data
    ax[r-3].scatter(locations, refs_plot[r][0], c=colors_refs[r], 
               marker=markers_refs[r], label=labels[r]+',\n0.3', s=pointsize)
    
    ax[r-3].errorbar(locations, refs_plot[r][0], 
                yerr=[np.array(refs_plot[r][0]) - np.array(refs_plot[r][2]), 
                      np.array(refs_plot[r][1]) - np.array(refs_plot[r][0])],
                c=colors_refs[r], 
                marker=markers_refs[r],
                fmt=' ', capsize=6, elinewidth=3, capthick=3)
    
    #plot airplane 0.5 area ratio data
    if plot_05 == True:
        ax[r-3].scatter(locations+.1, refs_05_plot[r][0], edgecolor=colors_refs[r], 
                   marker='o', label=labels[r]+',\n0.5', s=pointsize,
                   facecolor='none', linewidth=2)
    
        ax[r-3].errorbar(locations+.1, refs_05_plot[r][0], 
                    yerr=[np.array(refs_05_plot[r][0]) - np.array(refs_05_plot[r][2]), 
                          np.array(refs_05_plot[r][1]) - np.array(refs_05_plot[r][0])],
                    c=colors_refs[r], 
                    marker='none',
                    fmt=' ', capsize=6, elinewidth=3, capthick=3)
    #locations += .1

    ax[r-3].set_xticks(np.arange(0, 12, 1))#, label=times, rotation=45)    
    ax[r-3].tick_params(axis='x', which='major', labelbottom=False)
    
    ax[r-3].set_yticks(np.arange(30, 81, 20))
    ax[r-3].set_yticks(np.arange(40, 91, 20), minor=True) 
    ax[r-3].set_xlim(-0.5, 11.5)
    ax[r-3].set_ylim(26, 80)
    ax[r-3].tick_params(axis='both', which='major', labelsize=fontsize-3)
    
    ax[r-3].grid(True, which='major', linestyle='-', alpha=1)
    ax[r-3].grid(True, which='minor', linestyle='-', alpha=0.75)
    ax[r-3].legend(loc='upper right', bbox_to_anchor=(1.32, 1),
                   fontsize=fontsize-5)

        
ax[r-3].tick_params(axis='x', which='major', labelbottom=True)
ax[r-3].set_xticks(np.arange(0, 12, 1), labels=times, rotation=45)

fig.supylabel('Reflectivity (dBZ)', fontsize=fontsize)
fig.supxlabel('Time Interval Start (MM:SS)', fontsize=fontsize)

plt.tight_layout()
plt.show()






#doing everything above but for a second time period for a different flight
#because ughhhhhhh i wish i had made better code but i understand why i didn't
#make it a thing ofr everything



#plotting for specific time period
#f670 now
Ref_Data_1D = nc.Dataset(flight_list[5])
Ref_Data_2D = nc.Dataset(flight_list[4])



temp_concs = Ref_Data_2D['psd_2d_mean'][6:15]


bin_mids_ref = (Ref_Data_2D['bin_startpoints'][:] + Ref_Data_2D['bin_size'][:]/2) /1000
temp_concs2 = temp_concs * (Ref_Data_2D['bin_size'][:]/1e6)
"""
10*np.log10(ice_water_dielectric_3 * compute_z(bin_mids_ref, temp_concs2)[1])
"""

#start and end index
#s = 193
#e = 205

ref_mean = [Ref_Data_2D['Z_e_2D_mean'][8:15], Ref_Data_2D['Z_e_2D_mean_upper_uncertainty'][8:15], 
            Ref_Data_2D['Z_e_2D_mean_lower_uncertainty'][8:15]]

ref_circle = [Ref_Data_2D['Z_e_2D_circle'][8:15], Ref_Data_2D['Z_e_2D_circle_upper_uncertainty'][8:15], 
              Ref_Data_2D['Z_e_2D_circle_lower_uncertainty'][8:15]]
ref_xsize = [Ref_Data_2D['Z_e_2D_xsize'][8:15], Ref_Data_2D['Z_e_2D_xsize_upper_uncertainty'][8:15], 
             Ref_Data_2D['Z_e_2D_xsize_lower_uncertainty'][8:15]]
ref_xextent = [Ref_Data_2D['Z_e_2D_xextent'][8:15], Ref_Data_2D['Z_e_2D_xextent_upper_uncertainty'][8:15], 
               Ref_Data_2D['Z_e_2D_xextent_lower_uncertainty'][8:15]] 
ref_ysize = [Ref_Data_2D['Z_e_2D_ysize'][8:15], Ref_Data_2D['Z_e_2D_ysize_upper_uncertainty'][8:15], 
             Ref_Data_2D['Z_e_2D_ysize_lower_uncertainty'][8:15]]
ref_areasize = [Ref_Data_2D['Z_e_2D_areasize'][8:15], Ref_Data_2D['Z_e_2D_areasize_upper_uncertainty'][8:15], 
                Ref_Data_2D['Z_e_2D_areasize_lower_uncertainty'][8:15]]

ref_1D = [Ref_Data_1D['Z_e_1D'][8:15], Ref_Data_1D['Z_e_1D_upper_uncertainty'][8:15], 
          Ref_Data_1D['Z_e_1D_lower_uncertainty'][8:15]]

ref_observed = [44.7, 53.0, 50.2, 47.1, 44.5, 39.3, 36.0]
ref_observed = [ref_observed, ref_observed, ref_observed]

times = []
for t in Ref_Data_2D['time_start'][8:15]:
    HH = t[0:2]
    MM = t[2:4]
    SS = t[4:6]
    
    out = f'{MM}:{SS}'
    times.append(out)

refs_plot = [ref_observed, ref_1D, ref_mean, ref_circle, ref_xsize, ref_xextent, ref_ysize, ref_areasize]
#labels = ['Radar', 'HS-1D', 'HS-2D Mean', 'HS-2D Circle', 'HS-2D Xsize', 'HS-2D Xextent', 'HS-2D Ysize', 'HS-2D Areasize']
labels = ['Radar', 'HS-1D', 'HS-2D-M', 'HS-2D-C', 'HS-2D-XS', 'HS-2D-XE', 'HS-2D-Y', 'HS-2D-A']



#TOGGLE
plot_05 = True

if plot_05 == True:
    ref_05 = nc.Dataset('../../yr1995/f670/Code_Files_and_Outputs/Sensor_Information/Count_Conc_Ref_Data/20251210/19950627/152700_152830/670_PBP_Processed_HAIL-2D.nc')
    
    ref_05_mean = [ref_05['Z_e_2D_mean'][2:9], ref_05['Z_e_2D_mean_upper_uncertainty'][2:9], 
                ref_05['Z_e_2D_mean_lower_uncertainty'][2:9]]

    ref_05_circle = [ref_05['Z_e_2D_circle'][2:9], ref_05['Z_e_2D_circle_upper_uncertainty'][2:9], 
                  ref_05['Z_e_2D_circle_lower_uncertainty'][2:9]]
    ref_05_xsize = [ref_05['Z_e_2D_xsize'][2:9], ref_05['Z_e_2D_xsize_upper_uncertainty'][2:9], 
                 ref_05['Z_e_2D_xsize_lower_uncertainty'][2:9]]
    ref_05_xextent = [ref_05['Z_e_2D_xextent'][2:9], ref_05['Z_e_2D_xextent_upper_uncertainty'][2:9], 
                   ref_05['Z_e_2D_xextent_lower_uncertainty'][2:9]] 
    ref_05_ysize = [ref_05['Z_e_2D_ysize'][2:9], ref_05['Z_e_2D_ysize_upper_uncertainty'][2:9], 
                 ref_05['Z_e_2D_ysize_lower_uncertainty'][2:9]]
    ref_05_areasize = [ref_05['Z_e_2D_areasize'][2:9], ref_05['Z_e_2D_areasize_upper_uncertainty'][2:9], 
                    ref_05['Z_e_2D_areasize_lower_uncertainty'][2:9]]

    refs_05_plot = [ref_observed, ref_1D, ref_05_mean, ref_05_circle, ref_05_xsize, ref_05_xextent, ref_05_ysize, ref_05_areasize]

fig, ax = plt.subplots(figsize=(12,6))

colors_refs = [
    "#000000",  # black        - observed
    "#E41A1C",  # red          - 1D
    "#377EB8",  # blue         - mean
    "#4DAF4A",  # green        - circle
    "#984EA3",  # purple       - xsize
    "#FF7F00",  # orange       - xextent
    "#A65628",  # brown        - ysize
    "#F781BF",  # pink         - areasize
]

markers_refs = [
    "o",   # circle
    "s",   # square
    "^",   # triangle up
    "v",   # triangle down
    "D",   # diamond
    "P",   # plus (filled)
    "X",   # x (filled)
    "*",   # star
]




locations = np.arange(0, 7, 1)
fontsize = 25
pointsize = 170

fig, ax = plt.subplots(nrows=5, figsize=(12,15))
fig.suptitle('Observed vs Calculated Reflectivity', fontsize=fontsize)
for r in range(1, 6):# range(len(refs_plot)):
    
    #fig, ax = plt.subplots(figsize=(12,2.5))
    
    if r == 0:
        continue
    print(r)
    #plot obvs data for comparison
    ax[r-1].scatter(locations, refs_plot[0][0], c=colors_refs[0], 
               marker=markers_refs[0], label=labels[0], s=pointsize)
    
    #plot airplane data
    ax[r-1].scatter(locations, refs_plot[r][0], c=colors_refs[r], 
               marker=markers_refs[r], label=labels[r]+',\n0.3', s=pointsize)
    
    ax[r-1].errorbar(locations, refs_plot[r][0], 
                yerr=[np.array(refs_plot[r][0]) - np.array(refs_plot[r][2]), 
                      np.array(refs_plot[r][1]) - np.array(refs_plot[r][0])],
                c=colors_refs[r], 
                marker=markers_refs[r],
                fmt=' ', capsize=6, elinewidth=3, capthick=3)
    
    #plot airplane 0.5 area ratio data
    if plot_05 == True:
        if r == 1:
            pass
        else:
            
            ax[r-1].scatter(locations+.1, refs_05_plot[r][0], edgecolor=colors_refs[r], 
                       marker='o', label=labels[r]+',\n0.5', s=pointsize,
                       facecolor='none', linewidth=2)
        
            ax[r-1].errorbar(locations+.1, refs_05_plot[r][0], 
                        yerr=[np.array(refs_05_plot[r][0]) - np.array(refs_05_plot[r][2]), 
                              np.array(refs_05_plot[r][1]) - np.array(refs_05_plot[r][0])],
                        c=colors_refs[r], 
                        marker='none',
                        fmt=' ', capsize=6, elinewidth=3, capthick=3)
    
    
    #locations += .1

    ax[r-1].set_xticks(np.arange(0, 7, 1))#, label=times, rotation=45)    
    ax[r-1].tick_params(axis='x', which='major', labelbottom=False)
    
    ax[r-1].set_yticks(np.arange(30, 81, 20))
    ax[r-1].set_yticks(np.arange(40, 91, 20), minor=True) 
    ax[r-1].set_xlim(-0.5, 6.5)
    ax[r-1].set_ylim(26, 80)
    ax[r-1].tick_params(axis='both', which='major', labelsize=fontsize-3)
    
    ax[r-1].grid(True, which='major', linestyle='-', alpha=1)
    ax[r-1].grid(True, which='minor', linestyle='-', alpha=0.75)
    ax[r-1].legend(loc='upper right', bbox_to_anchor=(1.32, 1),
                   fontsize=fontsize-5)

        
ax[r-1].tick_params(axis='x', which='major', labelbottom=True)
ax[r-1].set_xticks(np.arange(0, 7, 1), labels=times, rotation=45)

fig.supylabel('Reflectivity (dBZ)', fontsize=fontsize)
fig.supxlabel('Time Interval Start (MM:SS)', fontsize=fontsize)

plt.tight_layout()
plt.show()





fig, ax = plt.subplots(nrows=5, figsize=(12,15))
fig.suptitle('Observed vs Calculated Reflectivity', fontsize=fontsize)
for r in range(3, 8):# range(len(refs_plot)):
    
    #fig, ax = plt.subplots(figsize=(12,2.5))
    
    if r == 0:
        continue
    
    #plot obvs data for comparison
    ax[r-3].scatter(locations, refs_plot[0][0], c=colors_refs[0], 
               marker=markers_refs[0], label=labels[0], s=pointsize)
    
    #plot airplane data
    ax[r-3].scatter(locations, refs_plot[r][0], c=colors_refs[r], 
               marker=markers_refs[r], label=labels[r]+',\n0.3', s=pointsize)
    
    ax[r-3].errorbar(locations, refs_plot[r][0], 
                yerr=[np.array(refs_plot[r][0]) - np.array(refs_plot[r][2]), 
                      np.array(refs_plot[r][1]) - np.array(refs_plot[r][0])],
                c=colors_refs[r], 
                marker=markers_refs[r],
                fmt=' ', capsize=6, elinewidth=3, capthick=3)
    
    #plot airplane 0.5 area ratio data
    if plot_05 == True:
        ax[r-3].scatter(locations+.1, refs_05_plot[r][0], edgecolor=colors_refs[r], 
                   marker='o', label=labels[r]+',\n0.5', s=pointsize,
                   facecolor='none', linewidth=2)
    
        ax[r-3].errorbar(locations+.1, refs_05_plot[r][0], 
                    yerr=[np.array(refs_05_plot[r][0]) - np.array(refs_05_plot[r][2]), 
                          np.array(refs_05_plot[r][1]) - np.array(refs_05_plot[r][0])],
                    c=colors_refs[r], 
                    marker='none',
                    fmt=' ', capsize=6, elinewidth=3, capthick=3)
    #locations += .1

    ax[r-3].set_xticks(np.arange(0, 7, 1))#, label=times, rotation=45)    
    ax[r-3].tick_params(axis='x', which='major', labelbottom=False)
    
    ax[r-3].set_yticks(np.arange(30, 81, 20))
    ax[r-3].set_yticks(np.arange(40, 91, 20), minor=True) 
    ax[r-3].set_xlim(-0.5, 6.5)
    ax[r-3].set_ylim(26, 80)
    ax[r-3].tick_params(axis='both', which='major', labelsize=fontsize-3)
    
    ax[r-3].grid(True, which='major', linestyle='-', alpha=1)
    ax[r-3].grid(True, which='minor', linestyle='-', alpha=0.75)
    ax[r-3].legend(loc='upper right', bbox_to_anchor=(1.32, 1),
                   fontsize=fontsize-5)

        
ax[r-3].tick_params(axis='x', which='major', labelbottom=True)
ax[r-3].set_xticks(np.arange(0, 7, 1), labels=times, rotation=45)

fig.supylabel('Reflectivity (dBZ)', fontsize=fontsize)
fig.supxlabel('Time Interval Start (MM:SS)', fontsize=fontsize)

plt.tight_layout()
plt.show()