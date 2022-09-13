# -*- coding: utf-8 -*-
"""
Created on Fri May  6 10:49:55 2022

@author: Atchoum
"""

import streamlit as st 
import glob
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import os

# =============================================================================
# def get_pos():
# #get all sorted positions
#     pos=[]
#     with open('./sortedlistpositions.stg','r') as file:
#         lines=file.readlines()
#         for line in lines[4:]:
#             val=line.split(', ')
#             pos.append((float(val[1]),float(val[2]),float(val[3])))
#     return pos
# =============================================================================
class Pos:
    def __init__(self,x,y,z,id_nb):
        self.x=x
        self.y=y
        self.z=z
        self.id_nb=id_nb
        self.coord=(x,y,z)
        
def read_pos():
    listpos= []
    with open(r'C:\Users\Atchoum\OneDrive\Documents\Python\Cellfinder\list.txt','r') as file:
        lines=file.readlines()
        for line in lines:
            val=line.split(' ')
            listpos.append(Pos(val[0],val[1],val[2],val[3]))
    return listpos

def create_pos_file(pos_list,filename):
    with open('C:/Users/Atchoum/OneDrive/Documents/Python/Cellfinder/'+filename+'.stg','w') as output:
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

# =============================================================================
# img_names=glob.glob('*.png')
# 
# img_names.sort(key=lambda x:int(x.split('_')[-1].split('.')[0]))
# 
# =============================================================================
if not 'index' in st.session_state:
    st.session_state.index=0
if not 'selected_pos' in st.session_state:
    st.session_state.selected_pos=[]

#pos=get_pos()
pos=read_pos()

str(st.session_state.index+1)+ '/' +str(len(pos))

c1,c2,c3=st.columns(3)

if c1.button('Keep'):
    st.session_state.selected_pos.append(pos[st.session_state.index].coord)
    st.session_state.index+=1
    
if c1.button('Remove'):
    st.session_state.index+=1
    
if c2.button('Back'):
    st.session_state.index-=1
    
if c2.button('Create position file'):
    create_pos_file(st.session_state.selected_pos,'selected_listpositions')
    print('ok')

image = np.array(Image.open('img_'+str(int(pos[st.session_state.index].id_nb))+'.png'))
figure=plt.figure()
plt.imshow(image,cmap='Greys_r')
st.pyplot(figure, use_column_width=True)
pos[st.session_state.index].coord
st.session_state.selected_pos