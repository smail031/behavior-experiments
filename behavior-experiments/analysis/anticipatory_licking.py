"""
Created on Fri Jul 19 15:49:33 2019

@author: sebastienmaille
"""

import h5py
import numpy as np
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

lickrates = []
for trial in range(num_trials):

    trial_type = str(f['sample_tone']['type'][trial]) #trial type (b'L' or b'R')
    trial_type = trial_type.replace('b', '')
    trial_type = trial_type.replace("'", '')
    _lick_v = f[f'lick_{trial_type.lower()}']['volt'][trial] #raw lick data
    _d_lick_v = np.diff(_lick_v) #1st derivative of raw lick data
    _licks = np.argwhere(_d_lick_v > 0).flatten() #find indices where the
                                #derivative of raw lick data goes above 0
    _lick_timestamps = []
    if len(_licks) != 0:
        for i in range(len(_licks)):
            _lick_timestamps.append(f[f'lick_{trial_type.lower()}']['t'][trial][_licks[i]])

    sample_tone_on = f['sample_tone']['t'][trial] #find start and end times of sample tones
    sample_tone_end = f['sample_tone']['end'][trial]
    sample_tone_length = sample_tone_end - sample_tone_on # gets exact length of sample tone


    anticipatory_licks = np.argwhere(np.logical_and(_lick_timestamps > sample_tone_on, _lick_timestamps < sample_tone_end))
    lick_count = anticipatory_licks.size
    # anticipatory_licks = np.count_nonzero(sample_tone_on < _lick_timestamps < sample_tone_end)
    lick_rate = (lick_count/sample_tone_length)*1000

    lickrates.append(lick_rate)

trials_with_lick = np.count_nonzero(lickrates)
print(f'average anticipatory lick rate: {np.mean(lickrates)}')
print(f'trials with any anticipatory licks: {trials_with_lick}/{num_trials} ({(trials_with_lick/num_trials)*100}%)')
