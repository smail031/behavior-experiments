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
sides = ['l', 'r']
ax = []

#transform trial types from "L/R" to "0/1" to simplify plotting
trial_types = []
for trial in range(num_trials):
    if 'L' in str(f['sample_tone']['type'][trial]):
        trial_types.append(0)
    elif 'R' in str(f['sample_tone']['type'][trial]):
        trial_types.append(1)

for ind, key in enumerate(sides):

    ax.append(fig.add_subplot(gs[0, ind]))
    _all_licks = []

    for trial in range(num_trials):

        _lick_v = f[f'lick_{key}']['volt'][trial] #raw lick data
        _d_lick_v = np.diff(_lick_v) #1st derivative of raw lick data
        _licks = np.argwhere(_d_lick_v > 0).flatten() #find indices where the
                                    #derivative of raw lick data goes above 0
        _all_licks.append(_licks)

        if len(trial_types) != 0 and trial_types[trial] == ind:
            ax[ind].fill_between([0,5000], [trial-0.5, trial-0.5],
              [trial+0.5, trial+0.5],
              facecolor = '#cce6ff') #will show trial types on plots.

        sample_tone_on = f['sample_tone']['t'][trial]
        sample_tone_end = f['sample_tone']['end'][trial]
        go_tone_on = f['go_tone']['t'][trial]
        go_tone_end = f['go_tone']['length'][trial]
        ax[ind].fill_between([sample_tone_on, sample_tone_end], [trial-0.5, trial-0.5],
          [trial+0.5, trial+0.5],
          facecolor = '#dbdbdb', alpha = 0.6) #Will show on plot where tones were played.
        ax[ind].fill_between([go_tone_on, go_tone_end], [trial-0.5, trial-0.5],
          [trial+0.5, trial+0.5],
          facecolor = '#dbdbdb', alpha = 0.6) #Will show on plot where tones were played.
        plt.plot([sample_tone_on, sample_tone_on], [trial-0.5, trial+0.5,], '#808080', lw = 0.5)
        plt.plot([sample_tone_end, sample_tone_end], [trial-0.5, trial+0.5,], '#808080', lw = 0.5)
        plt.plot([go_tone_on, go_tone_on], [trial-0.5, trial+0.5,], '#808080', lw = 0.5)
        plt.plot([go_tone_end, go_tone_end], [trial-0.5, trial+0.5,], '#808080', lw = 0.5)


    plt.eventplot(_all_licks, linelengths=0.8, linewidths = 0.8, colors = 'black') #creates raster
    reward_times = np.expand_dims(f[f'rew_{key}']['t'], 1)
    plt.eventplot(reward_times, linelengths=1, colors = '#00c907')

    #set axis limits, labels and title.
    ax[ind].set_ylim([0,num_trials])
    ax[ind].set_xlim([0, 4000])
    ax[ind].set_xticks([0, 1000, 2000, 3000, 4000])
    ax[ind].set_xlabel('Time (ms)')
    ax[ind].set_ylabel('Trials')
    ax[ind].spines['top'].set_visible(False)
    ax[ind].spines['right'].set_visible(False)
    _title_str = key[-1].upper() + ' Licks'
    ax[ind].set_title(_title_str, y = 1.01)

    ax[ind].text((sample_tone_on + sample_tone_end)/2,num_trials, 'sample', horizontalalignment = 'center')
    ax[ind].text((go_tone_on + go_tone_end)/2, num_trials, 'go', horizontalalignment = 'center')


plt.show(block=True)
