#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 15:49:33 2019

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

if date_experiment == 'today':
    date_experiment = time.strftime("%Y-%m-%d", time.localtime(time.time()))

file = f'/Volumes/GoogleDrive/Shared drives/Beique Lab/Data/Raspberry PI Data/Sébastien/Dual_Lickport/Mice/{mouse_number}/{date_experiment}/{mouse_number}_{date_experiment}_block{block_number}.hdf5'

f = h5py.File(file, 'r')

num_trials = len(f['lick_l']['volt'])

plt.style.use('seaborn-pastel')

fig = plt.figure(figsize = (10, 6), constrained_layout = True)
gs = gridspec.GridSpec(nrows = 1, ncols = 2, width_ratios = [1, 1], figure = fig)


#################
lick_keys = ['lick_l', 'lick_r']
ax = []

#transform trial types from "L/R" to "0/1" to simplify plotting
trial_types = []
for trial in range(num_trials):
    if 'L' in str(f['sample_tone']['type'][trial]):
        trial_types.append(0)
    elif 'R' in str(f['sample_tone']['type'][trial]):
        trial_types.append(1)

for ind, key in enumerate(lick_keys):

    ax.append(fig.add_subplot(gs[0, ind]))
    _all_licks = []

    for trial in range(num_trials):

        _lick_v = f[key]['volt'][trial] #raw lick data
        _d_lick_v = np.diff(_lick_v) #1st derivative of raw lick data
        _licks = np.argwhere(_d_lick_v > 0).flatten() #find indices where the
                                    #derivative of raw lick data goes above 0
        _all_licks.append(_licks)

        if len(trial_types) != 0 and trial_types[trial] == ind:
            ax[ind].fill_between([0,5000], [trial-0.5, trial-0.5],
              [trial+0.5, trial+0.5],
              facecolor = '#e1e1e1') #will show trial types on plots.

        _tone_on = f['sample_tone']['t'][trial]
        ax[ind].fill_between([_tone_on, _tone_on + 750], [trial-0.5, trial-0.5],
          [trial+0.5, trial+0.5],
          facecolor = '#ffb0b0') #Will show on plot where tones were played.

    plt.eventplot(_all_licks, linelengths=0.5, colors = '#5d5d5d') #creates raster

    #set axis limits, labels and title.
    ax[ind].set_ylim([None,num_trials])
    ax[ind].set_xlim([0, None])
    ax[ind].set_xticks([0, 1000, 2000, 3000, 4000, 5000])
    ax[ind].set_xlabel('Time (ms)')
    ax[ind].set_ylabel('Trials')
    _title_str = key[-1].upper() + ' Licks'
    ax[ind].set_title(_title_str)

plt.show(block=True)
