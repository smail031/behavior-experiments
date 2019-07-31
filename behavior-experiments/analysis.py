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

filename = input('Filename: ')
#trial = input('Trial: ')
num_trials = 10

f = h5py.File(filename, 'r')

plt.style.use('fivethirtyeight')

fig = plt.figure(figsize = (10, 6), constrained_layout = True)
gs = gridspec.GridSpec(nrows = 1, ncols = 2, width_ratios = [1, 1], figure = fig)


###################
lick_keys = ['lick_l', 'lick_r']
ax = []

for ind, key in enumerate(lick_keys):

    ax.append(fig.add_subplot(gs[0, ind]))
    for trial in range(num_trials):
        
        _lick_v = f[key]['volt'] [int(trial)-1]
        _d_lick_v = np.diff(_lick_v)
        _licks = np.argwhere(_d_lick_v > 0).flatten()
        _values = np.full(len(_licks), trial)
        
        _tone_on = f['tone']['t'][trial]
        ax[ind].fill_between([_tone_on, _tone_on + 1000], [trial-0.5, trial-0.5], 
          [trial+0.5, trial+0.5],
          facecolor = '#ff0000', alpha = 0.2)
        ax[ind].scatter(_licks, _values, marker = '|', color = '#5d5d5d', s = 60)

        
    
    ax[ind].set_ylim([0,num_trials])
    ax[ind].set_xlim([0, None])
    ax[ind].set_xticks([0, 1000, 2000, 3000, 4000, 5000])
    ax[ind].set_xlabel('Time (ms)')
    ax[ind].set_ylabel('Trials')

    
    _title_str = key[-1].upper() + ' Licks'
    ax[ind].set_title(_title_str)

#fig.savefig('test.pdf')
