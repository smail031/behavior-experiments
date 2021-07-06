#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 14 15:14:33 2021

@author: sebastienmaille
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os
import time

mouse_number = input('Mouse: ')
date_experiment = input('Date of experiment (yyyy-mm-dd or today): ')
block_number = input('Block number: ')
x_limit = 5000

if date_experiment == 'today':
    date_experiment = time.strftime("%Y-%m-%d", time.localtime(time.time()))

file = f'/Volumes/GoogleDrive/Shared drives/Beique Lab/Data/Raspberry PI Data/Sébastien/Dual_Lickport/Mice/{mouse_number}/{date_experiment}/ms{mouse_number}_{date_experiment}_block{block_number}.hdf5'

f = h5py.File(file, 'r') #open HDF5 file



plt.style.use('seaborn-pastel')
fig, ax = plt.subplots(figsize = (8, 6), constrained_layout = True)
#gs = gridspec.GridSpec(nrows = 1, ncols = 2, width_ratios = [1, 1], figure = fig)


#################

num_trials = len(f['lick_l']['volt']) #get number of trials

L_licks = np.zeros(num_trials, dtype=np.ndarray) #Will store left licks
R_licks = np.zeros(num_trials, dtype=np.ndarray) #Will store right licks

plt.eventplot(np.expand_dims(f['rew_l']['t'], 1), lw=2.5, linelengths=0.8, color='black') #create raster of L reward times
plt.eventplot(np.expand_dims(f['rew_r']['t'], 1),lw=2.5,  linelengths=0.8, color='black') #create raster of R reward times

for trial in range(num_trials):

    L_lick_v = f['lick_l']['volt'][trial] #raw voltage traces from left lickport
    R_lick_v = f['lick_r']['volt'][trial] #raw voltage traces from right lickport

    L_lick_d = np.diff(L_lick_v) #1st derivative of L lickport voltage
    R_lick_d = np.diff(R_lick_v) #1st derivative of R lickport voltage

    L_licks[trial] = np.argwhere(L_lick_d > 0).flatten() #licks occur where lick_d is above 0
    R_licks[trial] = np.argwhere(R_lick_d > 0).flatten()
    
    ax.eventplot(L_licks[trial], lineoffsets=trial, linelengths=0.8, linewidths=0.9, color='blue') #create raster plot of L licks
    ax.eventplot(R_licks[trial], lineoffsets=trial, linelengths=0.8, linewidths=0.9, color='red') #create raster plot of R licks

    sample_tone_on = f['sample_tone']['t'][trial] #Find sample tone start time
    sample_tone_end = f['sample_tone']['end'][trial] #Find sample tone end time

    if 'L' in str(f['sample_tone']['type'][trial]): #if L trial

        ax.fill_between([sample_tone_on, sample_tone_end], [trial-0.5, trial-0.5], [trial+0.5, trial+0.5], edgecolor='black',lw=0.5, facecolor='blue', alpha=0.3) #Show where the tone was played

    elif 'R' in str(f['sample_tone']['type'][trial]): #if R trial
                              
        ax.fill_between([sample_tone_on, sample_tone_end], [trial-0.5, trial-0.5], [trial+0.5, trial+0.5], edgecolor='black',lw=0.5, facecolor='red', alpha=0.3)



ax.set_ylim(-0.5,None)
ax.set_xlim(0,None)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_ylabel('Trials')
ax.set_xlabel('Time (ms)')

ax.set_yticks(np.arange(0, ax.get_ylim()[1], 5))

plt.show()
