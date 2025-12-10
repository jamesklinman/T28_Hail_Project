#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  NAME:
    PBP_Viewer.py
 
  PURPOSE:
    To view individual particle images along with the particles properties.
    Uses the netcdf output from SODA.

  SYNTAX:
    PBP_Viewer.py filename
  
  PARAMETERS:
    filename: name of netcdf file output by SODA

  OUTPUT:
    Interactive graphical user interface to browse particle images.

  MODULES:
    netCDF4, numpy, sys, tkinter, PIL

  EXAMPLES:
    PBP_Viewer.py 06222000_232921_HVPS1.pbp.nc

  MODIFICATIONS:
    James Klinman <james.klinman@und.edu> - 2024/07/26
      Written
    James Klinman <james.klinman@und.edu> - 2024/08/19
      Added math to resize particles if resolutions aren't 1 to 1
      Added particle sorter section
      Updated the filters to be more flexible and include the data created by 
         the particle sorter

  Copyright 2024, David Delene <delene@aero.und.edu>.

  This program is distributed under terms of the GNU General Public License.

  This file is part of Airborne Data Processing and Analysis (ADPAA).

  ADPAA is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  ADPAA is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with ADPAA.  If not, see <http://www.gnu.org/licenses/>.
"""

import netCDF4
import numpy as np
import tkinter as tk
from tkinter import *
from tkinter import ttk, font
from tkinter import Menu, filedialog
from PIL import ImageTk, Image, ImageDraw
#from PIL import ImageGrab
from PIL import Image as im
import sys
import math
import time


#set. for some reason it needs to be before the definitio rather than just before running th emain loop
time_convert = False
diam_convert = False
use_sorter = None
is_loading = False


#---------------------------------------------------------------------
#Getting nc pbp file that contains the pbp images
#and files. More concise than previous image method
#runfile('PBP_Viewer_20240930.py', '06222000_232921_HVPS1_win.pbp.nc')
#pbp_data = netCDF4.Dataset('06222000_232921_HVPS1_win.pbp.nc', mode="r+", format="NETCDF4")
#---------------------------------------------------------------------




pbp_file = sys.argv[1]
if len(sys.argv) == 3:
    use_sorter = sys.argv[2] #'y' means yes and 'n' means no

if use_sorter == 'y':
    pbp_data = netCDF4.Dataset(pbp_file, mode="r+") #should be r+ for sorter
elif use_sorter == 'n':
    pbp_data = netCDF4.Dataset(pbp_file, mode="r") 
elif use_sorter == None:
    pbp_data = netCDF4.Dataset(pbp_file, mode="r")
else:
    print('"' + use_sorter + '"' + 'is not a possible specification to determine'\
          'if you want to use the sorter or not. Please use "y" or "n" instead.')    
    
#reading in entire image strip now. Saves time down the road so it's not 
#constantly read in
#It's an image of every particle along the entire flight all in 1 2D array
entire_image_strip = pbp_data['image'][:]  
probe_xres = pbp_data.getncattr('RES')
probe_yres = pbp_data.getncattr('YRES')

index_start, index_end = 0, pbp_data['starty'][:].shape[0]

#all the particle properties that SODA reads out
options = ['time', 'probetime', 'buffertime', 'rawtime', 'reftime', 'inttime', 
           'diam', 'xsize', 'ysize', 'xextent', 'oned', 'twod', 'areasize',
           'arearatio', 'arearatiofilled', 'aspectratio', 'area', 'areafilled', 
           'perimeterarea', 'area75', 'xpos', 'ypos', 'allin', 'centerin', 
           'dofflag', 'edgetouch', 'sizecorrection', 'zd', 'missed', 'probetas',
           'aircrafttas', 'overloadflag', 'particlecounter', 'orientation', 
           'rejectionflag', 'numregions', 'starty', 'stopy', 'startx', 'stopx', 
           'image']



#------------------------------------------------
#initializing the gui and starting it up with the 
#first particle in the particle file
#------------------------------------------------



#A couple helpful sources were, https://www.youtube.com/watch?v=zg4c92pNFeo
# https://pythonexamples.org/python-tkinter-window-background-color/
#--------------------------------------------------------------------------
gui = Tk()
gui.title('PBP Image and Data Viewer')

#window placement from https://stackoverflow.com/questions/14910858/how-to-specify-where-a-tkinter-window-opens
#width and height of window
w = 850 #width for the Tk root (gui)
h = 640 #height for the Tk root (gui)

#get screen width and height
ws = gui.winfo_screenwidth()
hs = gui.winfo_screenheight()

#calculate x and y coordinates for the Tk root window                  _     _
#doesn't do anything yet. Will be use for screengrabs eventually maybe  \_0_/
x = (ws/2) - (w/2)
y = (hs/2) - (h/2)

# set the dimensions of the screen 
# and where it is placed
gui.geometry('%dx%d+%d+%d' % (w, h, x, y))

#gui.geometry("600x600") #sets window size
gui.configure(bg='gray')

#creating the canvas for the particle image
canvas_particle_image = tk.Canvas(gui, width=600, height=600)
canvas_particle_image.pack()
canvas_particle_image.place(x=10, y=30)

#initializing text boxes
option1_text = Label(gui, text='')
option1_text.place(x=667, y=290)
option2_text = Label(gui, text='')
option2_text.place(x=667, y=370)
option3_text = Label(gui, text='')
option3_text.place(x=667, y=450)



#--------------------------------------
#Creating all the functions for the gui
#--------------------------------------



def find_index_of_closest_value(array, valueToFind):
    #for searching through arrays to find a spot in the array closest to the
    #value that you want to find
    differences = np.abs(array - valueToFind)
    closest_index = differences.argmin()
    return closest_index


#image altering definitions
#------------------------------------------------------------------------------
def resize_im(image, xres, yres):
    #e.g. 3 pixel by 4 pixel particle becomes 225 by 300
    im_width = image.width
    im_height = image.height #* .8
    
    
    #print(im_width, im_height)
    #if xres and yres arent the same this adjusts image
    if xres > yres:
        im_height = im_height * xres/yres
    if yres > xres:
        im_height = im_height * yres/xres
    #print(im_width, im_height)
    
    scale_factor = min(600/im_width, 600/im_height)

    final_width = int(scale_factor * im_width)
    final_height = int(scale_factor * im_height)
    #print(final_width, final_height)
  
    im_resized = image.resize((final_width, final_height), resample=Image.NEAREST)
 
    #Flip the image vertically (not sure why but it matches the SODA buffers this way)
    im_resized = im_resized.transpose(Image.FLIP_TOP_BOTTOM)   
    
    
    return im_resized


def crop_particle_image(image_data, starty, stopy, startx, stopx):   
    #doesn't take startx or stopx since those aren't correct yet
    #crop the particle from the entire image strip
    
    #finding blocked diodes
    image_all = image_data
    num_diodes = image_all.shape[1]
    num_blocked_diodes = []
    location_blocked_diodes = []
    for row in range(starty, stopy+1):
        diode_count = 0
        diode_locs = []
        for col in range(num_diodes):
            if image_all[row][col] == 1:
                diode_count += 1
                diode_locs.append(col)
        num_blocked_diodes.append([diode_count])
        location_blocked_diodes.append(diode_locs)

    #normalizing diode number to 0-widthofparticle instead of 0-256 
    min_value = 99999 #unrealistic number of diodes for initilization
    for x in location_blocked_diodes:
        for y in x:
            if y < min_value:
                min_value = y

    for x in range(len(location_blocked_diodes)):
        for y in range(len(location_blocked_diodes[x])):
            location_blocked_diodes[x][y] = location_blocked_diodes[x][y] - min_value
            
    #reconstructing particle now
    max_value = 0 #unrealistic number of diodes
    for x in location_blocked_diodes:
        for y in x:
            if y > max_value:
                max_value = y

    final_image = []
    for row in location_blocked_diodes:
        row_image = []
        row_index = 0
        for col in range(max_value+1):
            if len(row) == 0:
                row_image.append(0)
                continue
            if col == row[row_index]:
                row_image.append(1)
                row_index += 1
            else:
                row_image.append(0)
            if row_index == len(row):
                row_index = 0
        final_image.append(row_image)

    #Pad the array with zeros
    pad_width = ((1, 1), (1, 1))  #Pad 1 row/column on each side
    final_image = np.pad(final_image, pad_width, mode='constant', constant_values=0)
    
    #print(final_image)

    return final_image

def BufferView():
    def x_boundaries(x, y, size, x_bound, y_bound):
        #size is the radius of the x or circle
        #xbound and ybound are the edges of the displayed buffer
        #they can't  be exceeded or else the x or circle wont draw
        left = x - size
        right = x + size
        top = y - size     
        bottom = y + size  
        
        left_bound = 0
        right_bound = x_bound
        top_bound = 0
        bottom_bound = y_bound
        
        if left < left_bound:
            left = 0
        if right > right_bound:
            right = right_bound
        if top < 0:
            top = 0
        if bottom > bottom_bound:
            bottom = bottom_bound
            
        return left, right, top, bottom


    probe_type = pbp_data.PROBETYPE #hvps other name. need to figure out how to pull name 

    #checking if image height or width need to be adjusted
    probe_xres = pbp_data.RES
    probe_yres = pbp_data.YRES

    probe_res_adjust = 1  
    if probe_xres != probe_yres: 
        probe_res_adjust = probe_xres / probe_yres
        if probe_res_adjust < 1:
            probe_res_adjust = 1 / probe_res_adjust

    #amount to scale the image by 
    buffer_width = pbp_data.DIODERANGE[1] - pbp_data.DIODERANGE[0]
   

    #scale factor based on 600x600 pixel display
    if buffer_width <= 75:
        res_increase = 8
        cropped_buffer_yradius = 37
    elif buffer_width <= 100:
        res_increase = 6
        cropped_buffer_yradius = 50
    elif buffer_width <= 150:
        res_increase = 4
        cropped_buffer_yradius = 75
    elif buffer_width <= 200:
        res_increase = 3
        cropped_buffer_yradius = 100
        
            
    #if the probe x and y res are different, then need to adjust the ydim to account for that
    #Not sure if this works in the event the xres is higher than the yres
    cropped_buffer_yradius = math.floor(cropped_buffer_yradius / probe_res_adjust)


    #retreiving position of main particle and calculating it's
    #position in the continuous image strip
    ypos_main = pbp_data['ypos'][index_tracker]
    buffer_start_main = pbp_data['starty'][index_tracker]
    buffer_end_main = pbp_data['stopy'][index_tracker]

    if probe_type == 'HAIL': #since hailspec doesn't have an accurate starty or stopy
        buffer_centerpoint_main = int(buffer_start_main + ypos_main) #+ 1 #+1 seems to be a good adjustment
        buffer_centerpoint_decimal = buffer_start_main + ypos_main - int(buffer_start_main + ypos_main)  #for adjusting pos to be more accurately centered on particles
        
        if buffer_centerpoint_main%2 != 0: 
            buffer_centerpoint_decimal += 0.5
            #print('needed to adjust')
            
        if buffer_centerpoint_main%2 == 0: 
            buffer_centerpoint_decimal -= 0.25

        buffer_centerpoint_main += 1

    else:
        buffer_centerpoint_main = int(buffer_start_main + int(buffer_end_main - buffer_start_main)/2) + 1 #+1 seems to be a good adjustment
        


    #cropping the 100000's strips long image to the ~75-300 surrounding strips
    buffer_shortened = []
    for y in range(buffer_centerpoint_main - cropped_buffer_yradius, 
                   buffer_centerpoint_main + cropped_buffer_yradius):
        row_image = list(pbp_data['image'][y][pbp_data.DIODERANGE[0]:pbp_data.DIODERANGE[1]].data)                                         #!!!FIXED THE DIODES THING. DO THIS
        buffer_shortened.append(row_image)



    #-1 switches 0s and 1s so that it turns to black particles and white background
    buffer_shortened = np.array(buffer_shortened) - 1
    
    #print(buffer_shortened[40:50])

    #Normalize the array to be within the range 0-255 for image creation
    #If buffer_shortened has values that are not within the 0-255 range, normalize:
    buffer_shortened = (buffer_shortened - np.min(buffer_shortened)) * (255 / np.ptp(buffer_shortened))
    buffer_shortened = buffer_shortened.astype(np.uint8)  #Convert to unsigned 8-bit integer type

    #Convert to a PIL image
    partim_arr = Image.fromarray(buffer_shortened)

    #Flip the image upside down (vertical flip)
    #The program does this to match the SODA buffers orientation
    partim_arr = partim_arr.transpose(Image.FLIP_TOP_BOTTOM)

    #increase image resolution (scaling by 4x, for example)
    width_scale, height_scale = 1, 1
    if probe_xres != probe_yres:
        if probe_xres < probe_yres:
            height_scale = int(probe_yres / probe_xres)
        elif probe_yres < probe_xres:
            width_scale = int(probe_xres / probe_yres)
    new_width, new_height = partim_arr.size[0] * res_increase * width_scale, \
                            partim_arr.size[1] * res_increase * height_scale                     
    partim_arr = partim_arr.resize((new_width, new_height), Image.NEAREST)  # Use NEAREST or BILINEAR for better quality

    #setting up ability to draw X's and circles 
    #creates a new layer with transparancy to draw that stuff on
    overlay = Image.new("RGBA", partim_arr.size, (0, 0, 0, 0))
    overlay_draw  = ImageDraw.Draw(overlay)


    #retrieving coordinates of the main particle
    #also getting the boundaries of the cropper buffer image
    xpos_main = pbp_data['xpos'][index_tracker] #+ 0.5) * res_increase # x-coordinate of particle
    ypos_main = pbp_data['ypos'][index_tracker] #- buffer_centerpoint_decimal) * res_increase  # y-coordinate of particle
    size_y_manual = buffer_shortened.shape[0] * res_increase * height_scale
    size_x_manual = buffer_shortened.shape[1] * res_increase * width_scale


    #adjusting xpos and ypos to be truly centered on the particle
    #and not slightly down and left or something else

    if probe_type == 'HAIL':
        if buffer_centerpoint_decimal == 1:
            buffer_centerpoint_decimal -= 1
            
        ypos_adjust = buffer_centerpoint_decimal
        
    else:
        ypos_adjust =  1

    xpos_adjust = 0.5
    xpos_main += xpos_adjust
    xpos_main = xpos_main * res_increase

    

    #copying the below above to draw circles around the surrounding 12 particles
    #so =/- 6 particles on either end. The purpose of this is the help identify 
    #indivudal particles when particles circle diameters are overlapping
    for z in range(index_tracker-6, index_tracker+6+1): #+1 includes final particle
        if z == index_tracker:
            continue
        #getting circle diameter
        diam_circle = pbp_data['diam'][z]
        diam_circle = diam_circle / 2 / pbp_data.RES
        if probe_type != 'HAIL':
            diam_circle = diam_circle * 1.25 #1.25 makes circle fit better
        if diam_circle < 1:
            diam_circle = 1 #a solution (but not perfect) for super small particles
        
        #getting circle coordinates
        xpos_extras = pbp_data['xpos'][z] 
        xpos_extras += xpos_adjust  
        #scaling to match the final resolution
        xpos_extras = xpos_extras * res_increase
        
        if probe_type == 'HAIL':
            ypos_extras = pbp_data['ypos'][z]
            #diferrence between main particle and surrounding particle
            ypos_dif = ypos_extras - ypos_main
        
            left3, right3, top3, bottom3 = x_boundaries(x=xpos_extras * width_scale, 
                                                        y=(cropped_buffer_yradius - ypos_dif + ypos_adjust) * res_increase * height_scale, 
                                                        size=diam_circle * res_increase, 
                                                        x_bound=size_x_manual, 
                                                        y_bound=size_y_manual)
            
        else:
            #using start and stop y locations since ypos doesn't
            #always seem to work well (at least when tested with HVPS1)
            buffer_start_extras = pbp_data['starty'][z]
            buffer_end_extras = pbp_data['stopy'][z]
            buffer_centerpoint_extras = buffer_start_extras + \
                                        (buffer_end_extras - \
                                        buffer_start_extras)/2 + 1.5
            
            #getting relative ypos to center particle. Using the starty in 
            #this case since the ypos is wonky for the hvps
            extraparticle_relative_ypos = cropped_buffer_yradius + \
                                          (buffer_centerpoint_main - \
                                          buffer_centerpoint_extras) 
            
               
            left3, right3, top3, bottom3 = x_boundaries(x=xpos_extras * width_scale, 
                                                        y=(extraparticle_relative_ypos + ypos_adjust) * res_increase * height_scale,
                                                        size=diam_circle * res_increase, 
                                                        x_bound=size_x_manual, 
                                                        y_bound=size_y_manual)

        overlay_draw.ellipse((left3, top3, right3, bottom3), fill=(150, 150, 150, 125), outline=(150, 150, 150, 125), width=4)

    ypos_adjust -= 0.4
    #getting the boundaries of the particle within the buffer image
    left, right, top, bottom = x_boundaries(x=xpos_main * width_scale, 
                                            y=(cropped_buffer_yradius + ypos_adjust) * res_increase * height_scale, 
                                            size=3 * res_increase * probe_res_adjust, 
                                            x_bound=size_x_manual, 
                                            y_bound=size_y_manual)

    #drawing an X through the main particle to help distinguish it from others
    overlay_draw .line([(left, top), (right, bottom)], fill=(100, 100, 100, 255), width=1)
    overlay_draw .line([(left, bottom), (right, top)], fill=(100, 100, 100, 255), width=1)


    #getting circle radius and drawing a circle around the particle
    diam_circle = pbp_data['diam'][index_tracker]
    diam_circle = diam_circle / 2 / pbp_data.RES
    if probe_type != 'HAIL':
        diam_circle = diam_circle * 1.1 #just makes the circle fit a little better

    left2, right2, top2, bottom2 = x_boundaries(x=xpos_main * width_scale, 
                                                y=(cropped_buffer_yradius + ypos_adjust) * res_increase * height_scale, 
                                                size=diam_circle * res_increase, 
                                                x_bound=size_x_manual, 
                                                y_bound=size_y_manual)

    overlay_draw.ellipse((left2, top2, right2, bottom2), outline=(100, 100, 100, 255), width=1)

    #combining circles and big X with the particle images
    partim_arr = Image.alpha_composite(partim_arr.convert("RGBA"), overlay)

    #showing the particle for now while testing
    #partim_arr.show()
    
    
    #do the below but with tas for the ratio
    #getting a ratio beween aircraft tas and probetas to know how to scale
    #the image. It will scale the whole image based on the particle in focues
    #rather than scaling each particle/buffer independently.
    #This is a source of visual error
    
    if probe_type == 'HAIL':
        #adjusting particle images based on the tas ratio fed into the probe vs
        #the real tas from the aircraft. 
        #Only do this for hail. It works for hail. Tried with HVPS, it breaks.
        #HVPS is always a ratio of ~2 so it just makes the image too big for
        #the window
        probe_tas = pbp_data['probetas'][index_tracker]
        aircraft_tas = pbp_data['aircrafttas'][index_tracker]
        
        tas_ratio = aircraft_tas / probe_tas
        
        new_width2, new_height2 = partim_arr.size[0],\
                                  int(partim_arr.size[1] * tas_ratio)                     
        partim_arr = partim_arr.resize((new_width2, new_height2), Image.NEAREST) 
    
    return partim_arr

#creating buttons to scroll and particle information stuff
#------------------------------------------------------------------------------
def exit_button():
    global pbp_data
    pbp_data.sync()
    #pbp_data.to_netcdf(filename)
    #print(f"Before closing - seperated shape: {pbp_data['seperated'].shape}")
    #print(f"Before closing - splatter shape: {pbp_data['splatter'].shape}")

    pbp_data.close()
    
    gui.destroy()


def forward():
    #forward button for moving to the next particle
    global index_tracker
    global pbp_data
    global rows
    global is_loading
    
    #print("buttonpressed")
    
    button_back.config(state=NORMAL)
    if index_tracker >= index_end-1: #is this the best way to read in shape?
        button_forward.config(state=DISABLED) 
        print('At final particle')
    else:
        #save data before adjusting the index tracker
        if not is_loading and category_is_true == True:
            save_category_data()
        
        #index_tracker += 1    
        #updating the display

        """try:
            #updating the display
            update_display(option1_select, option2_select, option3_select, 'f')
        except IndexError:
            # Suppress the index error message for when the particle
            #sorter is opened. The error message doesn't report on something
            #that is an issue. It's more of a percieved issue. Bsically it 
            #seems to make the pbp_data length ynamic and shrinks it to 0.
            #all the data is still there, and when you click forward it will show
            #up, but it still shows the message.
            update_display(option1_select, option2_select, option3_select, 'f')
            pass"""
        
        update_display(option1_select, option2_select, option3_select, 
                       'f')
        
        #print(pbp_data['good'][0:20], 'test5')
        
        if not is_loading and category_is_true == True:
            #save_category_data()
            for each_row in rows:
                category_entry = each_row['category_entry']
                category_name = str(category_entry.get())
                
                each_row['particle_added'] = pbp_data[category_name][index_tracker]
                each_row['status_label'].config(text=str(each_row['particle_added']))
    

def back():
    #backwards button for moving to the previous particle
    global index_tracker
    global pbp_data
    
    button_forward.config(state=NORMAL)
    if index_tracker <= index_start:
        button_back.config(state=DISABLED)    
        print('At first particle')
    else:
        #save data before adjusting the index tracker
        if category_is_true == True:
            save_category_data()
        
        #index_tracker -= 1    
    
        update_display(option1_select, option2_select, option3_select, 
                      'b')
        
        if category_is_true == True:
            #save_category_data()
            for each_row in rows:
                category_entry = each_row['category_entry']
                category_name = str(category_entry.get())
                
                each_row['particle_added'] = pbp_data[category_name][index_tracker]
                each_row['status_label'].config(text=str(each_row['particle_added']))
    

def update_display(option1, option2, option3, f_or_b):
    #when the forward or backward button are clicked, this function updates
    #the particle information displayed and then checks to see if the particle
    #meets the threshold/filter requirements and skips forward/back if it
    #doesn't. Then it updates the particle image.
    global pbp_data
    global entire_image_strip
    global index_tracker
    global probe_xres, probe_yres
    global filters_list

    # Set a maximum number of iterations to prevent infinite looping
    max_iterations = pbp_data['time'].shape[0]
    iterations = 0

    if len(filters_list) == 0:
        if f_or_b == 'f':
            index_tracker += 1
        elif f_or_b == 'b':
            index_tracker -= 1
    else:
        filter_search_loops(filters_list, f_or_b, 'click')
        pass
    
    #print(pbp_data['good'][0:20], 'test6, updatedisplay')
    
    if buffer_notindividual == False:
        #updating particle image
        starty_p = pbp_data['starty'][index_tracker].data
        stopy_p = pbp_data['stopy'][index_tracker].data
        startx_p = pbp_data['startx'][index_tracker].data
        stopx_p = pbp_data['stopx'][index_tracker].data
    
        particle_image = crop_particle_image(entire_image_strip, starty_p, stopy_p, startx_p, stopx_p)
        particle_image = np.where((particle_image==0)|(particle_image==1), particle_image^1, particle_image)
        particle_image = particle_image * 255 #np.array(particle_image) * 255
        particle_image = particle_image.astype(np.uint8) #for making image need this
        particle_image_png = im.fromarray(particle_image)
        particle_image_resized = resize_im(particle_image_png, probe_xres, probe_yres)    
    
        try:
            image_rgb = particle_image_resized.convert("RGB") #needed for ImageTk to work
            
            img_height = image_rgb.height
            img_width = image_rgb.width
            
            original_height = len(particle_image)
            original_width = len(particle_image[0])
            spacing_hor_lines = img_width / original_width #// original_width + 0
            spacing_vert_lines = img_height / original_height #// original_height + 0
            
            #print(img_height, img_width, original_height, original_width, spacing_hor_lines, spacing_vert_lines)
            
            if grid_draw == True:
                # Draw grid lines on the image
                draw = ImageDraw.Draw(image_rgb)
        
                # Draw vertical lines (grid columns)
                for x in range(1, original_width + 1):
                    draw.line(xy=[(x * spacing_hor_lines, 0), (x * spacing_hor_lines, img_height)], fill=(0, 0, 127), width=1)
            
                # Draw horizontal lines (grid rows)
                for y in range(1, original_height + 1):
                    draw.line(xy=[(0, y * spacing_vert_lines), (img_width, y * spacing_vert_lines)], fill=(0, 0, 127), width=1)
    
    
            
            display = ImageTk.PhotoImage(image_rgb) #reads in image
            label.config(image=display)
            label.image = display
    
            # Clear previous image
            canvas_particle_image.delete("all")
            
            # Display the image on the canvas
            canvas_particle_image.create_image(0, 0, anchor=NW, image=display)
        except FileNotFoundError:
            print("Error: Image file not found.")
        except Exception as e:
            print("An error occurred:", e)
            
    elif buffer_notindividual == True:
        try:
            hail_image = BufferView()  # Generate the hail-specific image

            # Display the hail image
            display = ImageTk.PhotoImage(hail_image)
            label.config(image=display)
            label.image = display

            # Clear previous image
            canvas_particle_image.delete("all")

            # Display the image on the canvas
            canvas_particle_image.create_image(0, 0, anchor=NW, image=display)
        except Exception as e:
            print("An error occurred in Bufferview function:", e)
    
    particle_index_show = tk.Label(gui, text='Index in array: ' + str(index_tracker))    
    particle_index_show.place(x=15, y=7)
    
    #updating particle information
    particle_information(option1, option2, option3)
    #print(index_tracker, '1')


def particle_information(option1, option2, option3):   
    #for retrieving and updating the particle information on display                               
    global option1_text
    global option2_text
    global option3_text
    global pbp_data
    global index_tracker
    
    option1_p_data = pbp_data[option1][index_tracker]
    option2_p_data = pbp_data[option2][index_tracker]
    option3_p_data = pbp_data[option3][index_tracker]
    
    options_data_list = [option1_p_data, option2_p_data, option3_p_data]
    options_list_conversion = [option1, option2, option3]
    
    #chekcing for conversion between units for time and diameter
    #looking thorugh the displayed particle attribute names to 
    #see if any time or diameter units need to be converted
    if time_convert == True: 
        for x in range(len(options_list_conversion)):
            if 'time' == options_list_conversion[x]:
                options_data_list[x] = seconds_HHMMSS(options_data_list[x])
    
    if diam_convert == True:
        for x in range(len(options_list_conversion)):
            if ('diam'     == options_list_conversion[x]) or \
               ('xsize'    == options_list_conversion[x]) or \
               ('ysize'    == options_list_conversion[x]) or \
               ('xextent'  == options_list_conversion[x]) or \
               ('areasize' == options_list_conversion[x]):
                   options_data_list[x] = units_convert(options_data_list[x])
    
    
    
    option1_text.config(text=(option1 + ': ' + str(options_data_list[0])))
    option2_text.config(text=(option2 + ': ' + str(options_data_list[1])))
    option3_text.config(text=(option3 + ': ' + str(options_data_list[2])))


def update_selection(*args):
    #updates particle information after selecting new particle variable to show
    global option1_select, option2_select, option3_select
    option1_select = combodrop1.get() 
    option2_select = combodrop2.get() 
    option3_select = combodrop3.get() 
        
    particle_information(option1_select, option2_select, option3_select)  
    

#menu for the whole viewer
#-------------------------
def openfilterbox():
    #object that is treated as a new window
    filterwindow = Toplevel(gui)
    filterwindow.title('Filters')
    
    filterwindow.geometry("250x220")
    #Label(filterwindow, text='new window for filters').pack()
    create_filter_box(filterwindow)
    

def openunitconversion():
    #object that is treated as a new window
    unitswindow = Toplevel(gui)
    unitswindow.title('Unit Conversion')
    
    unitswindow.geometry("250x220")
    #Label(filterwindow, text='new window for filters').pack()
    
    #Other buttons set up
    button_sec    = tk.Button(unitswindow, text="seconds",     command=units_sec) 
    button_hhmmss = tk.Button(unitswindow, text="hhmmss",      command=units_hhmmss) 
    button_um     = tk.Button(unitswindow, text="micrometers", command=units_um)
    button_mm     = tk.Button(unitswindow, text="millimeters", command=units_mm)
    button_cm     = tk.Button(unitswindow, text="centimeters", command=units_cm)
    button_nm     = tk.Button(unitswindow, text="nanometers",  command=units_nm)

    button_sec.place(x=10, y=10)
    button_hhmmss.place(x=70, y=10)
    button_um.place(x=10, y=50)
    button_mm.place(x=85, y=50)
    button_cm.place(x=10, y=75)
    button_nm.place(x=85, y=75)


def toggle_particleview():
    global buffer_notindividual
    buffer_notindividual = not buffer_notindividual
    forward()
    back()

def toggle_gridview():
    global grid_draw
    grid_draw = not grid_draw
    forward()
    back()
    
def toggle_arrowkeys():
    global arrow_key_bindings
    
    arrow_key_bindings = not arrow_key_bindings
    
    if arrow_key_bindings == True:
        print('Arrow key binding are enabled')
    if arrow_key_bindings == False:
        print('Arrow key bindings are disabled')

    
    #toggle key bindings
def on_arrow_press(event):
    if not arrow_key_bindings: #false means it won't activate on press
        return  # Ignore key presses if key bindings are not enabled

    key2 = event.keysym
    if key2 == "Left":
        back()
        return "break"  # Prevent the key press from being processed by the Entry widget
    elif key2 == "Right":
        forward()
        return "break"  # Prevent the key press from being processed by the Entry widget


#units conversion section
#all of this assumes base units of seconds 
#for time and um for diamter
#-----------------------------------------
def units_sec():
    global time_convert
    global time_units
    time_convert = False
    time_units = 'seconds'
    
def units_hhmmss():
    global time_convert
    global time_units
    time_convert = True
    time_units = 'hhmmss'
    
def units_um():
    global diam_convert
    global diam_units
    diam_convert = False
    diam_units = 'um'
    
def units_mm():
    global diam_convert
    global diam_units
    diam_convert = True
    diam_units = 'mm'
    
def units_cm():
    global diam_convert
    global diam_units
    diam_convert = True
    diam_units = 'cm'

def units_nm():
    global diam_convert
    global diam_units
    diam_convert = True    
    diam_units = 'nm'


def seconds_HHMMSS(time):
    #takes interger values, not strings. idk if floats work
    #floats do not work as it makes the seconds default to 0
    decimal = str(time).split('.')[1][:5] #gets the decimal out to 5 places and saves it
    time = int(time)
    HH = str(math.floor(time/3600))
    temp = time % 3600
    MM = str(math.floor((temp/60)))
    SS = str(temp%60)
    #print(HH, MM, SS)
    if len(HH) != 2:
        if len(HH) == 1:
            HH = str(0) + HH
        else:
            HH ='00'
    if len(MM) != 2:
        if len(MM) == 1:
            MM = str(0) + MM
        else:
            MM ='00'
    if len(SS) != 2:
        if len(SS) == 1:
            SS = str(0) + SS
        else:
            SS ='00'
    return str(HH+MM+SS+'.'+decimal)
    

def units_convert(diam):
    diam_converted = diam
    if diam_units == 'mm':
        diam_converted = float(diam) / 1000
    elif diam_units == 'cm':
        diam_converted = float(diam) / 10000
    elif diam_units == 'nm':
        diam_converted = float(diam) / 0.001

    return round(diam_converted, 3)    

    
#filter functions
#------------------------------------------------------------------------------
def threshold_checks_filter(particle_data, filter_range):
    #just checking to see if the particle data is within the 
    #range of the filter provided
    global index_tracker

    #print(filter_range, particle_data)
    if particle_data >= filter_range[0] and particle_data <= filter_range[1]:
        return True
    else:
        return False


def create_tooltip_filter(widget, text):
    tooltip = None

    def show_tooltip(event):
        nonlocal tooltip
        x = event.x_root
        y = event.y_root
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x + 10}+{y + 5}")
        
        label = tk.Label(tooltip, text=text, bg="lightyellow", padx=5, pady=5, wraplength=250)
        label.pack()

    def hide_tooltip(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)


def create_filter_box(gui):
    # Creating a square canvas for the filter box
    filter_box = tk.Canvas(gui, width=200, height=200)
    filter_box.place(x=20, y=20)
    
    global combodrop_filter, gt_entry, lt_entry
    combodrop_filter = ttk.Combobox(gui, values=options, width=15)
    combodrop_filter.place(x=60, y=60)
    
    filter_label = tk.Label(gui, text='Filter Selection')
    gt_label = tk.Label(gui, text='Minimum')
    lt_label = tk.Label(gui, text='Maximum')
    filter_label.place(x=75, y=30)
    gt_label.place(x=50, y=85)
    lt_label.place(x=130, y=85)
    
    
    gt_entry = tk.Entry(gui)
    lt_entry = tk.Entry(gui)
    gt_entry.place(x=45, y=110, width=70)
    lt_entry.place(x=128, y=110, width=70)
    
 
    #option_search = combodrop_filter.get()
    #minimum = gt_entry.get()
    #maximum = lt_entry.get()
    search_button = tk.Button(gui, text='Apply Filter', command=filter_search)#(option_search, minimum, maximum))
    search_button.place(x=40, y=135)
    
    #creating button to remove a filter
    remove_filter_button = tk.Button(gui, text='Remove Filter', command=remove_filter)
    remove_filter_button.place(x=115, y=135)
    
    # Create a tooltip label
    tooltip_label = tk.Label(gui, text="How to use", fg="black", cursor="hand2")
    tooltip_label.place(x=80, y=165)
    
    # Tooltip text to display
    tooltip_text = ("KEEP THIS WINDOW OPEN IF A FILTER IS APPLIED \n\n"
                    "If values are like 'time' or 'diameter'\n"
                    "then min and max are straightforward, e.g., 85710 and 85730 for time\n"
                    "If values are like rejectflag, where it's 0, 1, 2, 4, etc.,\n"
                    "then putting 0 for both max and min will search for particles with only 0\n"
                    "whereas if you put 0 and 4, it'll search for everything in between")
    
    # Attach the tooltip to the label
    create_tooltip_filter(tooltip_label, tooltip_text)


def remove_filter():
    global filters_list
    
    option = combodrop_filter.get()
    for x in range(len(filters_list)):
        if option in filters_list[x]:
            del(filters_list[x])
    print(filters_list)
    

def filter_search():#option, minimum, maximum):
    #print(option, 'dfasuhyasdfhsdfldahidflkj')
    global index_tracker
    global filters_list
    
    #getting filter min and max
    option = combodrop_filter.get()
    minimum = float(gt_entry.get() or 0)
    maximum = float(lt_entry.get() or 99999)
    
    counter = 0
    found_option = False
    for f in filters_list:
        #print(f, option)#, 'fdjhafjhfasjhsafdasfashk')
        if option in f:
           found_option = True
           #print('found opiotn')
           break 
        counter += 1
       
    if found_option == True:
        filters_list[counter][1] = [minimum, maximum]
    elif found_option == False:
        if option in options:
            filters_list.append([option, [minimum, maximum]])
        else:
            print('Not a valid variable. It probably doesnt exist. Is it a typo?')

    #can check max and min for it
    print(filters_list, 'filters list')
    filter_search_loops(filters_list, 'f', 'search') #defaults to forward
    
    forward()
    back()


def filter_search_loops(filters_list, f_or_b, search_or_click):
    global pbp_data
    global index_tracker

    search_variable = combodrop_filter.get()

    particle_check = [0] * len(filters_list)

    while 0 in particle_check:
        #moving through particles
        if f_or_b == 'f':
            index_tracker += 1
        elif f_or_b == 'b':
            index_tracker -= 1
            
        #edge cases
        if index_tracker == index_start or index_tracker == index_end:
            print('Reached start or end without finding a particle that matches the filters')
            #print(index_tracker)
            if index_tracker == index_start:
                button_back.config(state=DISABLED)    
                print('At first particle')
            if index_tracker == index_end: 
                button_forward.config(state=DISABLED) 
                print('At final particle')
            particle_check[:] = [1] * len(particle_check) #to terminate the while loop
            continue #to skip to end of while loop
        
        #checking if particle satisfies filters
        counter = 0
        particle_check = [0] * len(filters_list)
        #print(index_tracker, 'searching')    
        for f in filters_list:
            min_f = f[1][0]
            max_f = f[1][1]
            optn  = f[0]
            particle_data = float(pbp_data[optn][index_tracker])
            if particle_data >= min_f and particle_data <= max_f:
                particle_check[counter] = 1
            else:
                if optn == 'time':
                    if search_or_click == 'click' or (search_or_click == 'search' and search_variable != 'time'):
                        #if time filter is already set, 
                        #then don't go outside the time boundaries
                        #edge cases for time boundaries
                        if particle_data < min_f:
                            button_back.config(state=DISABLED)    
                            print('At minimum filter time boundary')
                        if particle_data > max_f:
                            button_forward.config(state=DISABLED)    
                            print('At maximum filter time boundary')
                        particle_check[:] = [1] * len(particle_check) #to terminate the while loop
                        return
                        
                    if search_or_click == 'search':
                        pass
            counter += 1
            
               
                

#particle sorter functions
#------------------------------------------------------------------------------
def create_sorter():
    #this is the function that opens the sorter box when the button is clicked
    #
    global add_row_button
    global category_is_true
    add_row_button = tk.Button(gui, text='add row', command=add_row)
    add_row_button.place(x=row_x, y=row_y)
    sorter_button.destroy()
    sorter_warning_message.destroy()

    # creating the menu trigger
    menu_trigger = tk.Label(canvas_sorter_box, text="Load or Save Categories", 
                            bg="lightgrey", fg="black", font=("Arial", 10, "bold"),
                            cursor="hand2", padx=7, pady=3)
    menu_trigger.pack()
    menu_trigger.place(x=0, y=0)
    menu_trigger.bind("<Button-1>", create_menu)  # Bind the click event to show the menu

    def on_enter(event):
        # Adding a hover effect
        event.widget.config(bg="darkgrey", fg="white")
    def on_leave(event):
        event.widget.config(bg="lightgrey", fg="black")

    menu_trigger.bind("<Enter>", on_enter)
    menu_trigger.bind("<Leave>", on_leave)
    
    # Create and place the "Click for warning" label
    warning_trigger = tk.Label(gui, text="Hover for warning", bg="lightgrey", \
                               fg="black", font=("Arial", 10, "bold"), cursor="hand2")
    warning_trigger.place(x=row_x+1, y=185)
    
    # Bind the hover events to the label
    warning_trigger.bind("<Enter>", show_warning)
    warning_trigger.bind("<Leave>", hide_warning)
     
    create_toggle_button()
    
    #for when going to next or previous particle. tells the program to collect 
    #the the new particle's category data 
    category_is_true = True


#setting up messages for the the particle sorter to hover over
def show_warning(event):
    # Create and display the tooltip
    global tooltip
    tooltip = tk.Toplevel(gui)
    tooltip.wm_overrideredirect(True)
    tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 5}")
    label = tk.Label(tooltip, text="Warning: If changing category names, do so "\
                                   "before adding/removing data \n Otherwise "\
                                   "the data won't be saved to the categories."\
                                   "\n TO SAVE THE CATEGORIES, CLICK ON THE MENU"\
                                   " DROPDOWN", bg="lightyellow", padx=5, pady=5)
    label.pack()


def hide_warning(event):
    # Destroy the tooltip
    global tooltip
    if tooltip is not None:
        tooltip.destroy()
        tooltip = None


def show_tooltip(event):
    # Create and display the tooltip
    global tooltip
    tooltip = tk.Toplevel(gui)
    tooltip.wm_overrideredirect(True)
    tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 5}")
    label = tk.Label(tooltip, text="Will disable the '12345' and 'qwert' keys for typing, they become shortcuts to add and remove particles for the categories.", bg="lightyellow", padx=5, pady=5, wraplength=250)
    label.pack()


def hide_tooltip(event):
    # Destroy the tooltip
    global tooltip
    if tooltip is not None:
        tooltip.destroy()
        tooltip = None


#menu bar
def create_menu(event):
    # Function to create a menu
    menu = tk.Menu(gui, tearoff=0)
    menu.add_command(label="Save Category Names", command=updateorcreate_pbp_categories)#save_category_names)
    menu.add_command(label="Load Category Names", command=load_categories)
    menu.add_separator()
    menu.post(event.x_root, event.y_root)  # Display the menu at the position of the event (mouse click)


#toggle key bindings
def on_key_press(event):
    if not key_bindings_enabled:
        return  # Ignore key presses if key bindings are not enabled

    key = event.keysym
    if key in ["1", "2", "3", "4", "5"]:
        index = int(key) - 1
        add_particle(rows[index])
        return "break"  # Prevent the key press from being processed by the Entry widget
    elif key in ["q", "w", "e", "r", "t"]:
        index = ["q", "w", "e", "r", "t"].index(key)
        remove_particle(rows[index])
        return "break"  # Prevent the key press from being processed by the Entry widget


def create_toggle_button():
    global toggle_button
    toggle_button = tk.Button(gui, text="Toggle Bindings", relief="raised", command=toggle_key_bindings)
    toggle_button.place(x=746, y=182) #!!!

    # Bind hover events to the toggle button
    toggle_button.bind("<Enter>", show_tooltip)
    toggle_button.bind("<Leave>", hide_tooltip)
    
    
#chagpt made this toggle button stuff
def toggle_key_bindings():
    global key_bindings_enabled
    if toggle_button.config('relief')[-1] == 'sunken':
        toggle_button.config(relief="raised")
        key_bindings_enabled = False
        # Re-enable all Entry widgets
        for row_data in rows:
            row_data["category_entry"].config(state="normal")
    else:
        toggle_button.config(relief="sunken")
        key_bindings_enabled = True  # Enable key bindings when button is "sunken"
        # Disable all Entry widgets
        for row_data in rows:
            row_data["category_entry"].config(state="disabled")


#button for adding rows and the boxes/buttons/etc 
#that are displayed when the button is pressed
def add_row():
    #creates a row and adds all the entries, buttons,
    #labels to be associated with that row
    global row_x, row_y
    global particle_sort_data

    #cat_data_temp = []
    #for each_row in rows:
    #    data_entry = each_row['particle_added']
    #    cat_data_temp.append(data_entry)

    row_data = {
        "category_entry": create_category(),
        "add_button": create_particle_addremove(row_x + 140, row_y, 'add', lambda: add_particle(row_data)),
        "remove_button": create_particle_addremove(row_x + 80, row_y, 'remove', lambda: remove_particle(row_data)),
        "status_label": create_andupdate_addremove_status(row_x + 195, row_y),
        "particle_added": 0  # Unique state for each row
    }


    rows.append(row_data)

    row_y += 25
    add_row_button.place(x=row_x, y=row_y)
    if row_y == 57 + 25 * 5:
        add_row_button.destroy()
    

def create_category():
    #spot to name the category
    global row_x, row_y, tooltip  # Ensure to use global for tooltip
    
    # Create the entry spot to label/categorize the row
    category_entry = tk.Entry(gui, width=12)
    category_entry.place(x=row_x, y=row_y)
    return category_entry


def create_particle_addremove(x, y, label, command):
    #makes the add and remove buttons for the row
    button = tk.Button(gui, text=label, command=command)
    button.place(x=x, y=y)
    return button


def create_andupdate_addremove_status(x, y):
    #shows the status of the particle for that category
    #so like, if it's a 0, 1, or 2
    status_label = tk.Label(gui, text='0')
    status_label.place(x=x, y=y)
    return status_label


def add_particle(row_data):
    #adding particle yes or no or NA to category
    if row_data["particle_added"] == 2:
        print('No further categorization options')
    else:
        row_data["particle_added"] += 1
    row_data["status_label"].config(text=str(row_data["particle_added"]))


def remove_particle(row_data):
    #removing particle yes or no to category
    if row_data['particle_added'] == 0:
        print('Particle is already uncategorized')
    else:
        row_data["particle_added"] -= 1
    row_data["status_label"].config(text=str(row_data["particle_added"]))



    
    






        
def save_category_data():
    global pbp_data
    #for saving the -1, 0, 1's for the particle in each category to the pbp file
    #0 is not categorized
    #1 is false categorized
    #2 is positive categorize
    for each_row in rows:
        data_entry = each_row['particle_added']
        category_entry = each_row['category_entry']
        #print(category_entry.get(), data_entry, 'saving data now')
        category_name = str(category_entry.get())
        
        #print('\n')
        #print(category_name, data_entry, 'cat name and data entry')
        #print('/n ', pbp_data[category_name][index_tracker], 'data in the bpb file')
        #print('\n')  
        pbp_data[category_name][index_tracker] = data_entry

        #print(data_entry, index_tracker, 'data entry and index tracker')







loaded_rows_counter = 0
def add_row_loading(cat_name, cat_counter):
    #creates a row and adds all the entries, buttons, labels to be associated with that row
    global row_x, row_y
    global loaded_rows_counter

    cat_data_init = []
    for each_cat in cat_name:
        data_entry = pbp_data[each_cat][index_tracker] #each_row['particle_added']
        cat_data_init.append(data_entry)
        
    #cat_value =  pbp_data[each_cat][index_tracker]

    row_data = {
        "category_entry": create_category(),
        "add_button": create_particle_addremove(row_x + 140, row_y, 'add', lambda: add_particle(row_data)),
        "remove_button": create_particle_addremove(row_x + 80, row_y, 'remove', lambda: remove_particle(row_data)),
        "status_label": create_andupdate_addremove_status(row_x + 195, row_y),
        "particle_added": pbp_data[cat_name[loaded_rows_counter]][index_tracker]#0#cat_data_init[cat_counter] #0  # Unique state for each row
        }
    print(cat_data_init, 'cat dat a init')

    rows.append(row_data)


    row_y += 25
    add_row_button.place(x=row_x, y=row_y)
    if row_y == 50 + 25 * 5:
        add_row_button.destroy()


# Define a counter for the number of updates
update_counter = 0
max_updates = 100  # Total updates to perform

def update_display_with_delay():
    global update_counter
    global index_tracker

    if update_counter < max_updates:
        # Update the display with the current particle information
        update_display(option1_select, option2_select, option3_select, 'f')

        # Increment the update counter
        update_counter += 1
        
        # Move to the next particle index (adjust as needed)
        # index_tracker += 1

        # Schedule the next update after 200 milliseconds
        gui.after(40, update_display_with_delay)
    else:
        # Reset the counter if needed or perform any final actions
        update_counter = 0
        index_tracker -= max_updates + 1  # Adjust the index back if necessary #the plus one is necessary it sends it back to index 0 which makes it works if it goes back to index 1 it does not work
        update_display(option1_select, option2_select, option3_select, 'f')
        print('Completed 100 updates. Data should be loaded in now')

def load_categories():
    global index_tracker
    global is_loading
    #global pbp_data
    
    #for some reason need to skip forward normally? idk not sure pls work

    #index_tracker = 0
    
    is_loading = True  # Set the flag to True to indicate loading

    #preserving_nc_file = pbp_data    

    start_data_index = 0
    file_shape = pbp_data['time'].shape[0]

    pbp_keys = list(pbp_data.variables.keys())
    pbp_cats_index = pbp_keys.index('image') + 1 #assumes image was selected in processing with soda
    
    category_names = pbp_keys[pbp_cats_index:]
    print(category_names, 'cat names', len(category_names))
    
    # Store where you're at in the data
    index_currently_at = index_tracker

    # Clear the current content of the entry boxes
    # Add rows if there are more categories than rows
    counter = 0
    while len(rows) < len(category_names):
        add_row_loading(category_names, counter)
        #add_row()
        counter += 1

    #print(pbp_data['good'][0:20], 'test1 works')

    # Fill the entry boxes with the category names
    for i, category_name in enumerate(category_names):
        if i < len(rows) and i < 6:
            each_row = rows[i]
            each_row['category_entry'].insert(2, category_name)
            print(each_row, 'each rowww')
        else:
            break  # Prevents trying to insert into a non-existing entry box
    
    #print(pbp_data['good'][0:20], 'test2 works')
    
    #print(pbp_data['good'][0:6])
    # Load all particles to ensure the file is fully initialized
        # Start updating the display 20 times
    update_display_with_delay()  # Start the update process  #FOR LOOPS FREEZE THE GUI WHICH BREAKS THE WHOLE THING IT TOOK WEEKS

    #print(pbp_data['good'][0:20], 'test3... works')
    # Resetting index tracker back
    index_tracker = index_currently_at
    print(index_currently_at, 'where it ended up going back to')
    update_display(option1_select, option2_select, option3_select, 'b')
    button_forward.config(state=NORMAL)
    
    is_loading = False  # Reset the flag after loading
    #print(pbp_data['good'][0:20], 'test4 works')



    
    #get file dimnsion first before all the stuff above
    #then after everything is loaded in, save the index that you're at, then
    #create a simplified forward function
    #that scrolls through all the particles up to the final index, 
    #then simply reset back to the index you were at and you should be good to
    #go hopefully
    
        
    

def updateorcreate_pbp_categories():
    #creating the categories in the pbp file based off of what's in the entry 
    #boxes. If categories are already made, then it just makes sure it doesn't
    #need to add more
       
    pbp_keys = pbp_data.variables.keys()
    for each_row in rows:
        category_entry = each_row['category_entry']
        print(category_entry.get())
        category_name = str(category_entry.get())
        
        #if the category name isn't in the pbp file yet, 
        #then add it an fill it with 0's
        
        if category_name not in pbp_data.variables.keys():
            pbp_data.createVariable(category_name, np.int8, ('Time'))
            pbp_data[category_name][:] = 0
    #print(pbp_data.variables.keys(), 'keysysys')
    #print(pbp_data['splatter'].shape, 'splatter shape') 
    #print(pbp_data['splatter'][0:100])         

    


    
    
    
#----------------------------------------------
#Initializing variables and starting up the gui
#----------------------------------------------



# Example usage
#create_filter_box(gui)

filters_list = []

grid_draw = True
buffer_notindividual = False

time_units = 'seconds'
diam_units = 'um'

    
#initialzing the pbp viewer with the first particle
#and preset particle data
#-------------------------------------------------
index_tracker = 0 #Image you want to start with
option1_select, option2_select, option3_select = 'time', 'diam', 'allin'

#getting first particle image
label= Label(gui)
update_display(option1_select, option2_select, option3_select, 
                   'f')  
 
#Setting up dropdown menus for particle information
combodrop1 = ttk.Combobox(gui, values=options, width=15)
combodrop1.set('time')
combodrop1.place(x=667, y=270)
combodrop1.bind("<<ComboboxSelected>>", update_selection)

combodrop2 = ttk.Combobox(gui, values=options, width=15)
combodrop2.set('diam')
combodrop2.place(x=667, y=350)
combodrop2.bind("<<ComboboxSelected>>", update_selection)

combodrop3 = ttk.Combobox(gui, values=options, width=15)
combodrop3.set('allin')
combodrop3.place(x=667, y=430)
combodrop3.bind("<<ComboboxSelected>>", update_selection)


#menu for the whole viewer
#-------------------------
#time_convert = False
#diam_convert = False



menubar = Menu(gui)
filemenu = Menu(menubar, tearoff=0)

filemenu.add_command(label='Filters', command=openfilterbox)
filemenu.add_command(label='Convert Units', command=openunitconversion)
filemenu.add_command(label='Toggle Particle View', command=toggle_particleview)
filemenu.add_command(label='Toggle Grid View', command=toggle_gridview)
filemenu.add_command(label='Toggle Arrow Keys', command=toggle_arrowkeys)

menubar.add_cascade(label="File/Commands", menu=filemenu)

gui.config(menu=menubar)





# Particle sorter section setup
canvas_sorter_box = tk.Canvas(gui, width=220, height=175, bg="white")
canvas_sorter_box.pack()
canvas_sorter_box.place(x=620, y=30)


row_x, row_y = 621, 57
rows = []

particle_sort_data = []


# Global variable to keep track of the warning label
warning_label = None
category_is_true = False
tooltip = None  # Global variable to track the tooltip

sorter_button = None
sorter_warning_message = None

if use_sorter == 'y':
    def show_sorter_warning():
        global sorter_warning_message, sorter_button  # Declare them as global
        sorter_warning_message = tk.Label(gui, text='I do not recommend using\n'\
                                                    'unless you have been\n'\
                                                    'instructed on how to use\n'\
                                                    'this function. It will mess\n'\
                                                    'up the added sorter data.\n'\
                                                    "You've been warned\n")
        sorter_warning_message.place(x=660, y=48)
    
        sorter_check.destroy()    
    
        sorter_button = tk.Button(gui, text='Continue', command=create_sorter)
        sorter_button.place(x=700, y=170)
    
    sorter_check = tk.Button(gui, text='Open Particle Sorter', command=show_sorter_warning)
    sorter_check.place(x=675, y=100)

         
elif use_sorter == 'n':
    sorter_button_no = tk.Label(gui, text='Disabled')
    sorter_button_no.place(x=700, y=100)
elif use_sorter == None:
    sorter_button_no = tk.Label(gui, text='Disabled')
    sorter_button_no.place(x=700, y=100)
else:
    print('error? not sure how.')  




# Initialize key bindings state
key_bindings_enabled = False
#toggle_button = tk.Button(gui, text="Toggle Bindings", relief="raised", command=toggle_key_bindings)
gui.bind("<KeyPress>", on_key_press)

arrow_key_bindings = False
gui.bind_all("<KeyPress>", on_arrow_press)





gui.protocol("WM_DELETE_WINDOW", exit_button)

#Other buttons set up
button_back = tk.Button(gui, text="<<", command=back) 
button_exit = tk.Button(gui, text="exit", command=exit_button) 
button_forward = tk.Button(gui, text=">>", command=forward)

button_back.place(x=667, y=550)
button_exit.place(x=710, y=550)
button_forward.place(x=754, y=550)

#Opening the gui
gui.mainloop()
