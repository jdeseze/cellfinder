# -*- coding: utf-8 -*-
"""
Created on Fri Feb 18 20:24:58 2022

@author: Atchoum
"""

#pip install pythonnet
import clr
import time
from scipy import ndimage
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from skimage import filters
import tkinter as tk
from tkinter import simpledialog
import pycromanager as pm
import cv2

# Create the main application window
root = tk.Tk()
root.attributes("-topmost", True)  # Set the window to be on top
root.withdraw()  # Hide the main window

class ImagingSoftware:
    def __init__(self,name='Micromanager'):
        if name=='Metamorph':
            self.is_metamorph=True
            clr.AddReference(r'D:\JEAN\DMD\Interop.MMAppLib.dll')
            import MMAppLib
            self.mm=MMAppLib.UserCallClass()
        else:
            self.is_metamorph=False
            
    def get_position(self):
        if self.is_metamorph:
           self.x=self.mm.GetMMVariable('Device.Stage.XPosition',0)[2]
           self.y=self.mm.GetMMVariable('Device.Stage.YPosition',0)[2]
           self.z=self.mm.GetMMVariable('Device.Focus.CurPos',0)
        else:
            core=pm.Core() 
            self.x=core.get_x_position()
            self.y=core.get_y_position()
            self.z=core.get_position()
            
    def set_xyposition(self,xycoord):
        if self.is_metamorph:
            self.mm.SetMMVariable('Device.Stage.XPosition',xycoord[0])
            self.mm.SetMMVariable('Device.Stage.YPosition',xycoord[1])
        else:
            core=pm.Core() 
            core.set_xy_position(xycoord[0],xycoord[1])
        self.x,self.y=xycoord
            
    def set_zposition(self,zcoord):
        if self.is_metamorph:
            self.mm.SetMMVariable('Device.Focus.CurPos',0)
        else:
            core=pm.Core()  
            core.set_position(zcoord)
        self.z=zcoord
        
    def acquire(self):
        if self.is_metamorph:
            self.mm.RunJournal('C:/MM/app/mmproc/journals/s.JNL')
            pixvals=np.array(Image.open('C:/TEMP/tmp.tif'))
        else:
            core=pm.Core()
            core.snap_image()
            tagged_img=core.get_tagged_image()
            pixvals=np.reshape(tagged_img.pix,newshape=[tagged_img.tags['Height'], tagged_img.tags['Width']])

        self.disp_image=((pixvals - pixvals.min()) / (pixvals.max()-pixvals.min()))

class GetParams(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Threshold:").grid(row=0)
        tk.Label(master, text="Pixel_size (in µm):").grid(row=1)
        tk.Label(master, text="File name:").grid(row=2)
        self.use_metamorph_entry = tk.IntVar()
        tk.Checkbutton(master,text='Use Metamorph',variable=self.use_metamorph_entry).grid(row=3)
        
        self.threshold_entry = tk.Entry(master)
        self.pixel_entry = tk.Entry(master)
        self.filename_entry = tk.Entry(master)
        
        #Default values
        self.threshold_entry.insert(0, str(405))
        self.pixel_entry.insert(0, str(0.214))
        self.filename_entry.insert(0, str("listpositions"))
        

    def apply(self):
        try:
            self.threshold=int(self.threshold_entry.get())
            self.pixel_size = float(self.pixel_entry.get())
            self.filename=str(self.filename_entry.get())
            self.use_metamorph=bool(self.use_metamorph_entry.get())
            
        except ValueError:
            tk.messagebox.showerror("Error", "Invalid input. Please enter valid integer for threshold.")
            self.threshold_entry = None
            self.pixel_entry = None
            self.filename_entry=None

params = GetParams(root)
if params.use_metamorph:
    soft=ImagingSoftware('Metamroph')
else:
    soft=ImagingSoftware('Micromanager')
    

print(params.use_metamorph)

def findcells(img,thresh):
    ''' This function is designed to make a basic segmentation of big fluorescence objects within the image.
    it takes an 2D gray scale image as an input (img, as an np array) and a threshold thresh, give, in the interface. 
    It returns the list of areas of the found objects (cc_areas), and the labeled image'''
    med=filters.gaussian(img,sigma=11)*65535
    binary = med > thresh
    plt.imshow(binary)
    er=ndimage.binary_erosion(np.array(binary*255),iterations=2)
    dil=ndimage.binary_dilation(er,iterations=10)
    plt.title('dilation')
    filled=ndimage.binary_fill_holes(dil).astype(int)
    label_img, cc_num = ndimage.label(filled)
    cc_areas = ndimage.sum(binary, label_img, range(cc_num+1))
    return cc_areas,label_img


def create_pos_file(pos_list,filename):
    '''This function is creating a position file for Metamorph(.stg)in the directory of the script, with two parameters
    - a list of positions (triplets (x,y,z))
    - a filename'''
    with open('./'+filename+'.stg','w') as output:
        output.write('"Stage Memory List", Version 6.0'+' \n')
        output.write('0, 0, 0, 0, 0, 0, 0, "microns", "microns"'+' \n')
        output.write('0'+' \n')
        output.write(str(len(pos_list))+' \n')
        for i,pos in enumerate(pos_list):
            output.write(''.join(['"Position'+str(i)+'", ',
                             str(pos[0])+', ',
                             str(pos[1])+', ',
                             str(pos[2])+', 0, '+str(pos[2]),
                             ', FALSE, -9999, TRUE, TRUE, 0, -1, ""'+' \n']))

soft.acquire()
img_size=soft.disp_image.shape[0]
step=100
pos_cells=[]

#get initial position, which should be the center of the coverslip
soft.get_position()
x_init=soft.x
y_init=soft.y

#make a square around the position
for x in range(-2, 2):    
    for y in range(-2,2):
        if x%2 ==0:
            y_to_go=y_init+y*step
        else:
            y_to_go=y_init-y*step
        
        #set xy position
        soft.set_xyposition([x_init+x*step,y_to_go])
        
        #take an image
        soft.acquire()
        
        # find the cells
        array=soft.disp_image
        cc_areas,label_img=findcells(array,params.threshold)
        
        for k,area in enumerate(cc_areas):
            #criterium to remove too small areas
            if area>4500:
                y_all,x_all=np.where(label_img==k)
                dx=np.mean(x_all)-img_size/2
                dy=np.mean(y_all)-img_size/2
                print("dx is "+str(dx)+" and dy is"+str(dy))
                
                cell_xposition=int(x_init+x*step+params.pixel_size*dx)
                cell_yposition=int(y_to_go+params.pixel_size*dy)
                soft.get_position()
                z=soft.z
                
                pos_cells+=[(cell_xposition,cell_yposition,z)]
                
                #now go to the position of the center of the cell, take an image, and save it
                
                soft.set_xyposition([int(cell_xposition),int(cell_yposition)])
                
                soft.acquire()
                #Image.fromarray(soft.disp_image).save('img_'+str(len(pos_cells))+'.png')
                cv2.imwrite('img_'+str(len(pos_cells))+'.png',soft.disp_image*255)
        #to see how it goes, print the x,y evolution
        print(x,y)
        time.sleep(0.2)

print(pos_cells)

create_pos_file(pos_cells,'listpositions')

#%% sorting the positions, removing positions that are too near to each other. 
import os

min_dist=150

def save_pos(listpos):
    with open('./list.txt','w') as output:
        for pos in listpos:
            output.write(' '.join([str(pos.x),str(pos.y),str(pos.z),str(pos.id_nb),'\n']))

class Pos:
    def __init__(self,x,y,z,id_nb):
        self.x=x
        self.y=y
        self.z=z
        self.id_nb=id_nb
        self.coord=(x,y,z)
        
    
sorted_pos=[]
pos=[]
with open('./listpositions.stg','r') as file:
    lines=file.readlines()
    i=1
    for line in lines[4:]:
        val=line.split(', ')
        sorted_pos.append(Pos(float(val[1]),float(val[2]),float(val[3]),i))
        i+=1
        

sorted_pos.sort(key=lambda pos:pos.x)
for i in range(len(sorted_pos)):
    j=i+1
    while j<len(sorted_pos) and abs(sorted_pos[j].x-sorted_pos[i].x)<min_dist:
        if abs(sorted_pos[j].y-sorted_pos[i].y)<min_dist:
            sorted_pos.remove(sorted_pos[j])
            #os.remove('img_'+str(count)+'.png')
        else:    
            j+=1
        #print(len(sorted_pos))


save_pos(sorted_pos)

#creates the positions file  'sortedlistpositions.stg'
create_pos_file([pos.coord for pos in sorted_pos],'sortedlistpositions')