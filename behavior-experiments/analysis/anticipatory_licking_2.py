#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 14 15:14:33 2021

@author: sebastienmaille
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
import os
import time


plt.rcParams['pdf.fonttype'] = 42
fig, axs = plt.subplots(nrows=1, ncols=2, figsize = (8, 6), constrained_layout = True)

#mouse_list = np.array(['5300','5305','5307','5308'])
mouse_list = np.array(['5300']) #ms 5300 with reverse rule

training_days = np.empty(len(mouse_list), dtype=np.ndarray)

training_days[0] = np.array(['2021-03-16', '2021-03-17', '2021-03-18', '2021-03-19']) #for ms5300 reverse (pulse) rule
#training_days[0] = np.array(['2021-03-02', '2021-03-03', '2021-03-04', '2021-03-05', '2021-03-08', '2021-03-09']) #for ms5300
#training_days[1] = np.array(['2021-03-02', '2021-03-03', '2021-03-04', '2021-03-05', '2021-03-08', '2021-03-09', '2021-03-10', '2021-03-11', '2021-03-15']) for ms5305
#training_days[2] = np.array(['2021-03-02', '2021-03-03', '2021-03-04', '2021-03-05', '2021-03-08', '2021-03-09', '2021-03-10', '2021-03-11', '2021-03-15']) for ms5307
#training_days[3] = np.array(['2021-03-02', '2021-03-03', '2021-03-04', '2021-03-05', '2021-03-08', '2021-03-09', '2021-03-10', '2021-03-11']) for ms 5308

lick_rates = np.empty(len(mouse_list), dtype=np.ndarray) #will store a_lick rates for each mouse and each experiment
incorr_lick_rates = np.empty(len(mouse_list), dtype=np.ndarray) #will store lick rates on the incorrect port
diff_lick_rates = np.empty(len(mouse_list), dtype=np.ndarray)# will store difference in rate between correct vs incorrect ports

lick_trials = np.empty(len(mouse_list), dtype=np.ndarray) #will store proportion of a_lick trials for each mouse and each experiment
incorr_lick_trials = np.empty(len(mouse_list), dtype=np.ndarray) #will store trials with incorrect a_licks.
diff_lick_trials = np.empty(len(mouse_list), dtype=np.ndarray)

for mouse in range(len(mouse_list)):

    lick_rates[mouse] = np.empty(len(training_days[mouse]))
    incorr_lick_rates[mouse] = np.empty(len(training_days[mouse]))
    diff_lick_rates[mouse] = np.empty(len(training_days[mouse]))
    
    lick_trials[mouse] = np.empty(len(training_days[mouse]))
    incorr_lick_trials[mouse] = np.empty(len(training_days[mouse]))
    diff_lick_trials[mouse] = np.empty(len(training_days[mouse]))

    for experiment in range(len(training_days[mouse])):

        mouse_number = mouse_list[mouse]
        date_experiment = training_days[mouse][experiment]
        block_number = '1'
        
        file = f'/Volumes/GoogleDrive/Shared drives/Beique Lab/Data/Raspberry PI Data/Sébastien/Dual_Lickport/Mice/{mouse_number}/{date_experiment}/ms{mouse_number}_{date_experiment}_block{block_number}.hdf5'

        f = h5py.File(file, 'r') #open HDF5 file

        #################

        num_trials = len(f['lick_l']['volt']) #get number of trials

        a_licking = np.zeros(num_trials) #will store whether there was anticipatory licking
        a_licking.fill(np.nan)
        incorr_a_licking = np.zeros(num_trials)
        incorr_a_licking.fill(np.nan)   
        
        a_licking_rate = np.zeros(num_trials) #will store a lick rate for each trial
        a_licking_rate.fill(np.nan)
        incorr_a_licking_rate = np.zeros(num_trials) #ant lick rates for incorrect port

        for trial in range(num_trials):

            if 'L' in str(f['sample_tone']['type'][trial]): #if L trial
        
                lick_v = f['lick_l']['volt'][trial] #raw voltage traces from left (correct) port
                incorr_lick_v = f['lick_r']['volt'][trial] #voltage traces from right (incorrect) port
        
                rew_time = f['rew_l']['t'][trial] #get L reward delivery time

            elif 'R' in str(f['sample_tone']['type'][trial]): #if R trial
        
                lick_v = f['lick_r']['volt'][trial] #raw voltage traces from right (correct) port
                incorr_lick_v = f['lick_l']['volt'][trial] #raw voltage traces from left (incorrect) port
        
                rew_time = f['rew_r']['t'][trial] #get R reward delivery time
        
            lick_d = np.diff(lick_v) #1st derivative of correct lickport voltage
            incorr_lick_d = np.diff(incorr_lick_v) #derivative of incorrect lickport
            
            licks = np.argwhere(lick_d > 0).flatten() #Get correct lick timestamps
            incorr_licks = np.argwhere(incorr_lick_d > 0).flatten() #Get incorrect lick timestamps

            sample_tone_end = f['sample_tone']['end'][trial] #Find sample tone end time

            delay = rew_time - sample_tone_end #delay between tone end and rew delivery

            if delay > 250: #only interested in delays greater than 250ms

                a_licks = licks[(licks > sample_tone_end) & (licks < rew_time)]
                incorr_a_licks = incorr_licks[(incorr_licks>sample_tone_end)&(incorr_licks<rew_time)]
                
                a_licking_rate[trial] = len(a_licks) / (delay/1000) #lick rate in Hz
                incorr_a_licking_rate[trial] = len(incorr_a_licks) / (delay/1000)


                if len(a_licks) > 0: #Store whether there were any licks at all
                    a_licking[trial] = True

                elif len(a_licks) == 0: #False if there were no licks
                    a_licking[trial] = False

                if len(incorr_a_licks) > 0: #Store whether there were any incorrect licks
                    incorr_a_licking[trial] = True

                elif len(incorr_a_licks) == 0: #False if there were no licks
                    incorr_a_licking[trial] = False

            lick_rates[mouse][experiment] = np.nanmean(a_licking_rate)
            incorr_lick_rates[mouse][experiment] = np.nanmean(incorr_a_licking_rate)
            diff_lick_rates[mouse][experiment] = lick_rates[mouse][experiment] - incorr_lick_rates[mouse][experiment]
            
            lick_trials[mouse][experiment] = (int(np.nansum(a_licking))/num_trials) * 100
            incorr_lick_trials[mouse][experiment] = (int(np.nansum(incorr_a_licking))/num_trials) * 100
            diff_lick_trials[mouse][experiment] = lick_trials[mouse][experiment] - incorr_lick_trials[mouse][experiment]

    axs[0].plot(lick_trials[mouse], color='steelblue', alpha=0.5, lw=2, label = mouse_list[mouse])
    axs[0].plot(incorr_lick_trials[mouse], color='orange', alpha=0.5, lw=2, label = mouse_list[mouse])
    axs[0].plot(diff_lick_trials[mouse], color='red', alpha=0.5, lw=2, label = mouse_list[mouse])
    
    
    axs[1].plot(lick_rates[mouse], color='steelblue', alpha=0.5, lw=2,  label = mouse_list[mouse])
    axs[1].plot(incorr_lick_rates[mouse], color='orange', alpha=0.5, lw=2,  label = mouse_list[mouse])
    axs[1].plot(diff_lick_rates[mouse], color='red', alpha=0.5, lw=2, label = mouse_list[mouse])

#axs[0].plot(np.mean(lick_trials, axis=0), color='steelblue')
#axs[0].plot(np.mean(incorr_lick_trials, axis=0), color='orange')

#axs[1].plot(np.mean(lick_rates, axis=0), color='steelblue')
#axs[1].plot(np.mean(incorr_lick_rates, axis=0), color='orange')
    

axs[0].set_ylabel('% Trials with anticipatory licking')
axs[0].set_xlabel('Training Day')
axs[0].set_ylim(0,None)
axs[0].spines['top'].set_visible(False)
axs[0].spines['right'].set_visible(False)
#axs[0].legend()

axs[1].set_ylabel('Mean anticipatory lick rate (Hz)')
axs[1].set_xlabel('Training Day')
axs[1].set_ylim(0,None)
axs[1].spines['top'].set_visible(False)
axs[1].spines['right'].set_visible(False)
#axs[1].legend()







#ax.set_ylim(-0.5,20.5)
# #ax.set_xlim(0,None)
# ax.spines['top'].set_visible(False)
# ax.spines['right'].set_visible(False)
# ax.set_ylabel('Trials')
# ax.set_xlabel('Time (ms)')

# ax.set_yticks(np.arange(0, ax.get_ylim()[1], 5))

plt.show()
