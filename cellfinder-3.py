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
import time

clr.AddReference(r'D:\JEAN\DMD\Interop.MMAppLib.dll')
import MMAppLib
mm=MMAppLib.UserCallClass()

def findcells(img,thresh):
    #img=(img/2^8).astype(np.uint8)
    plt.imshow(img)
    med=filters.gaussian(img,sigma=11)*65535
    binary = med > thresh
    plt.imshow(binary)
    #plt.title('after threshold')
    #print(np.max(binary))
    er=ndimage.binary_erosion(np.array(binary*255),iterations=2)
    dil=ndimage.binary_dilation(er,iterations=10)
    #plt.figure()
    plt.title('dilation')
    #print(np.max(dil))
    #plt.imshow(dil*65535)
    filled=ndimage.binary_fill_holes(dil).astype(int)
    label_img, cc_num = ndimage.label(filled)
    #CC = ndimage.find_objects(label_img)
    cc_areas = ndimage.sum(binary, label_img, range(cc_num+1))
    area_mask = (cc_areas < max(cc_areas))
    # label_img[area_mask[label_img]] = 0
    return cc_areas,label_img


def create_pos_file(pos_list,filename):
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

fact=0.214 #facteur de conversion des pixels vers les micrometres
thr=410
step=100
pos_cells=[]
x_init=mm.GetMMVariable('Device.Stage.XPosition',0)[2]
print(x_init)
y_init=mm.GetMMVariable('Device.Stage.YPosition',0)[2]
for i in range(-25, 25):
    mm.SetMMVariable('Device.Stage.XPosition',x_init+i*step)
    for j in range(-25,25):
        if i%2 ==0:
            y_to_go=y_init+j*step
        else:
            y_to_go=y_init-j*step
        mm.SetMMVariable('Device.Stage.YPosition',y_to_go)
# =============================================================================
#         mm.RunJournal('C:\MM\app\mmproc\journals\Start_autofocus.jnl')
#         time.sleep(1)
#         mm.RunJournal('C:\MM\app\mmproc\journals\Stop_autofocus.jnl')
# =============================================================================
        mm.RunJournal(r'C:\MM\app\mmproc\journals\s.JNL')
        img=Image.open(r'C:\TEMP\tmp.tif')
        #img.save('img'+str(i)+'.png')
        array=np.array(img)
        cc_areas,label_img=findcells(array,thr)
        max_area=max(cc_areas)
        print(max_area)
        #Image.fromarray(seg*65535).save('pos'+str(i)+'_'+str(j)+'.png')
        if max_area>4500:
            for k,area in enumerate(cc_areas):
                if area>4500:
                    y_all,x_all=np.where(label_img==k)
                    dx=np.mean(x_all)-512
                    dy=np.mean(y_all)-512
                    print("dx is "+str(dx))
                    z=mm.GetMMVariable('Device.Focus.CurPos',0)
                    pos_cells+=[(x_init+step*i+fact*dx,y_to_go+fact*dy,z[2])]
                    
                    #now go to the position, take an image, and save it
                    mm.SetMMVariable('Device.Stage.XPosition',int(x_init+step*i+fact*dx))
                    mm.SetMMVariable('Device.Stage.YPosition',int(y_to_go+fact*dy))
                    mm.RunJournal(r'C:\MM\app\mmproc\journals\s.JNL')
                    snap=Image.open(r'C:\TEMP\tmp.tif')
                    snap.save('img_'+str(len(pos_cells))+'.png')
        print(i,j)
        time.sleep(0.2)

print(pos_cells)

create_pos_file(pos_cells,'listpositions')

#%%
import os

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
    while j<len(sorted_pos) and abs(sorted_pos[j].x-sorted_pos[i].x)<100:
        if abs(sorted_pos[j].y-sorted_pos[i].y)<200:
            sorted_pos.remove(sorted_pos[j])
            #os.remove('img_'+str(count)+'.png')
        else:    
            j+=1
        #print(len(sorted_pos))


save_pos(sorted_pos)

create_pos_file([pos.coord for pos in sorted_pos],'sortedlistpositions')