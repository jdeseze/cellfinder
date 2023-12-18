# -*- coding: utf-8 -*-
"""
Created on Fri Feb 18 20:24:58 2022

@author: Atchoum
"""

#pip install pythonnet
#import clr
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

class Pos:
    def __init__(self,x,y,z,id_nb):
        self.x=x
        self.y=y
        self.z=z
        self.id_nb=id_nb
        self.coord=(x,y,z)

class ImagingSoftware:
    def __init__(self,name='Micromanager'):
        if name=='Metamorph':
            self.is_metamorph=True
            #clr.AddReference(r'D:\JEAN\DMD\Interop.MMAppLib.dll')
            #import MMAppLib
            #self.mm=MMAppLib.UserCallClass()
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
   
    def create_pos_file(self,pos_list,filename):
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

def check_corners(soft,dist):#get initial position, which should be the center of the coverslip
    soft.get_position()
    x_init=soft.x
    y_init=soft.y
    if messagebox.askokcancel("Check", "Did you put the stage at the center of the coverslip?"):
        soft.set_xyposition([int(-dist*step),int(dist*step)])
        soft.set_xyposition([int(-dist*step),int(-dist*step)])
        soft.set_xyposition([int(dist*step),int(-dist*step)])
        soft.set_xyposition([int(dist*step),int(dist*step)])

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


# Create the main application window
root = tk.Tk()
root.title('Cell finder')
root.attributes("-topmost", True)  # Set the window to be on top
root.withdraw()  # Hide the main window

class GetParams(simpledialog.Dialog):
    def __init__(self, parent, title="Dialog Title"):
        self.title_name = title
        super().__init__(parent)

    def body(self, master):
        tk.Label(master, text="Threshold:").grid(row=0)
        tk.Label(master, text="Pixel_size (in µm):").grid(row=1)
        tk.Label(master, text="File name:").grid(row=3)
        tk.Label(master, text="Magnification:").grid(row=2)

        self.use_metamorph_entry = tk.IntVar()
        tk.Checkbutton(master, text='Use Metamorph', variable=self.use_metamorph_entry).grid(row=4, columnspan=2)

        self.threshold_entry = tk.Entry(master)
        self.pixel_entry = tk.Entry(master)
        self.filename_entry = tk.Entry(master)
        self.magnification_entry = tk.Entry(master)

        # Default values
        self.threshold_entry.insert(0, str(405))
        self.pixel_entry.insert(0, str(0.214))
        self.filename_entry.insert(0, str("listpositions"))
        self.magnification_entry.insert(0, str("60"))

        # Call grid method for entry widgets
        self.threshold_entry.grid(row=0, column=1)
        self.pixel_entry.grid(row=1, column=1)
        self.filename_entry.grid(row=3, column=1)
        self.magnification_entry.grid(row=2, column=1)

        # Check corners button TO BE CHANGED
        tk.Button(master, text="Check corners", command=command=lambda: check_corners(dist,soft)).grid(row=5, columnspan=2)

    def apply(self):
        try:
            self.threshold = int(self.threshold_entry.get())
            self.pixel_size = float(self.pixel_entry.get())
            self.filename = str(self.filename_entry.get())
            self.magnification = int(self.magnification_entry.get())
            self.use_metamorph = bool(self.use_metamorph_entry.get())
        except ValueError:
            tk.messagebox.showerror("Error", "Invalid input. Please enter valid values.")
            self.threshold = None
            self.pixel_size = None
            self.filename = None
            self.magnification = None
            self.use_metamorph = None

if params.use_metamorph:
    soft=ImagingSoftware('Metamorph')
else:
    soft=ImagingSoftware('Micromanager')
params = GetParams(root)

    
print(params.use_metamorph)

soft.acquire()
img_size=soft.disp_image.shape[0]
step=int(0.8*params.pixel_size*img_size/params.magnification)
print(step)
pos_cells=[]

#get initial position, which should be the center of the coverslip
soft.get_position()
x_init=soft.x
y_init=soft.y

#make a square around the position
for x in range(-1, 2):    
    for y in range(-1,2):
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

soft.create_pos_file(pos_cells,'listpositions')

#%% sorting the positions, removing positions that are too near to each other. 
import os

min_dist=1.5*step
    
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

#creates the positions file  'sortedlistpositions.stg'
soft.create_pos_file([pos.coord for pos in sorted_pos],'sortedlistpositions')

#%%
from PIL import ImageTk
from tkinter import messagebox
import tkinter as tk


class CellChooser:
    def __init__(self, root, pos_list):
        self.root = root
        self.root.title("Tkinter App")
        self.pos_list = pos_list
        self.index = 0
        self.selected_pos = []
        self.photo_image = None  # Reference to PhotoImage object

        self.label = tk.Label(root, text=f"{self.index + 1}/{len(self.pos_list)}")
        self.label.pack()

        self.canvas = tk.Canvas(root)
        self.canvas.pack()

        self.update_display()

        self.button_keep = tk.Button(root, text="Keep", command=self.keep_position)
        self.button_remove = tk.Button(root, text="Remove", command=self.remove_position)
        self.button_back = tk.Button(root, text="Back", command=self.back_position)
        self.button_create_file = tk.Button(root, text="Create position file", command=self.create_position_file)

        self.button_keep.pack(side=tk.LEFT)
        self.button_remove.pack(side=tk.LEFT)
        self.button_back.pack(side=tk.LEFT)
        self.button_create_file.pack(side=tk.LEFT)
        
    def initialize_window(self):
        self.root.deiconify()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind('<KeyPress-Return>', lambda event: self.keep_position())
        self.root.bind('<KeyPress-x>', lambda event: self.remove_position())
        self.root.bind('<Left>', lambda event: self.back_position())
        self.root.mainloop()
        self.root.mainloop()
    
    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()    
    
    def update_display(self):
        if self.index>-1 and self.index<len(self.pos_list):
            image_path = './img_' + str(int(self.pos_list[self.index].id_nb)) + '.png'
            image = Image.open(image_path)
            self.photo_image = ImageTk.PhotoImage(image)
            self.canvas.config(width=image.width, height=image.height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
            self.label.config(text=f"{self.index + 1}/{len(self.pos_list)}")
        else:
            messagebox.showinfo("Info", "you reached last position")

    def keep_position(self):
        self.selected_pos.append(self.pos_list[self.index].coord)
        self.index += 1
        print(self.index)
        self.update_display()

    def remove_position(self):
        self.index += 1
        print(self.index)
        self.update_display()

    def back_position(self):
        if self.index > 0:
            self.index -= 1
            self.update_display()
        else:
            messagebox.showinfo("Info", "Already at the first position")

    def create_position_file(self):
        # Assuming 'create_pos_file' is defined somewhere
        soft.create_pos_file(self.selected_pos, 'selected_listpositions')
        messagebox.showinfo("Info", "Position file created successfully!")

# Example usage
#root = tk.Tk()  # Main Tkinter instance
cell_chooser = CellChooser(root, sorted_pos)
cell_chooser.initialize_window()
