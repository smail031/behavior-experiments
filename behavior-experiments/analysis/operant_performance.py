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
fig, axs = plt.subplots(nrows=2, ncols=2, figsize = (8, 6), constrained_layout = True)


mouse_list = np.array(['5305','5307','5308']) #for 4 tone (shifting) operant 
#mouse_list = np.array(['1','3','4315','4392','4357', '4514']) #for 2 tone operant 
training_days = np.empty(len(mouse_list), dtype=np.ndarray)

training_days[0] = np.array(['2021-03-16','2021-03-17','2021-03-18','2021-03-19','2021-03-20','2021-03-21','2021-03-23','2021-03-24','2021-03-25']) #for ms5305
training_days[1] = np.array(['2021-03-16','2021-03-17','2021-03-18','2021-03-19','2021-03-20','2021-03-21', '2021-03-23','2021-03-25']) #for ms5307
training_days[2] = np.array(['2021-03-15','2021-03-16','2021-03-17','2021-03-18','2021-03-20','2021-03-21', '2021-03-23','2021-03-24','2021-03-25']) #for ms 5308


#training_days[0] = np.array(['2020-10-17', '2020-10-18', '2020-10-19', '2020-10-23', '2020-10-25', '2020-10-26', '2020-10-27']) #for ms1
#training_days[1] = np.array(['2020-10-11', '2020-10-13', '2020-10-14', '2020-10-15', '2020-10-16', '2020-10-17', '2020-10-18', '2020-10-19', '2020-10-21', '2020-10-22', '2020-10-23', '2020-10-25', '2020-10-26', '2020-10-27', '2020-10-28', '2020-10-29', '2020-10-30']) #for ms3
#training_days[2] = np.array(['2019-09-13', '2019-09-16', '2019-09-17', '2019-09-18', '2019-09-19', '2019-09-20', '2019-09-23', '2019-09-24', '2019-09-25']) #for ms 4315
#training_days[3] = np.array(['2019-09-26', '2019-10-03', '2019-10-04', '2019-10-07', '2019-10-09', '2019-10-10', '2019-10-11', '2019-10-12', '2019-10-15', '2019-10-16', '2019-10-17', '2019-10-18', ]) #for ms4392
#training_days[4] = np.array(['2019-09-26', '2019-10-03', '2019-10-04', '2019-10-07', '2019-10-09', '2019-10-10', '2019-10-11', '2019-10-12', '2019-10-15', '2019-10-16']) #for ms 4357
#training_days[5] = np.array(['2020-01-17', '2020-01-19', '2020-01-20', '2020-01-27', '2020-01-28', '2020-01-29', '2020-01-30', '2020-02-03']) #for ms4514

correct_trials = np.empty(len(mouse_list), dtype=np.ndarray) #will store correct (1) and incorrect (0) trials
null_responses = np.empty(len(mouse_list), dtype=np.ndarray) #will store % null responses

bias = np.empty(len(mouse_list), dtype=np.ndarray) #will store L(0) and R(1) responses
response_time = np.empty(len(mouse_list), dtype=np.ndarray) #will store response times

for mouse in range(len(mouse_list)):

    correct_trials[mouse] = np.empty(len(training_days[mouse]))
    null_responses[mouse] = np.empty(len(training_days[mouse]))
    bias[mouse] = np.empty(len(training_days[mouse]))
    response_time[mouse] = np.empty(len(training_days[mouse]))


    for experiment in range(len(training_days[mouse])):

        mouse_number = mouse_list[mouse]
        date_experiment = training_days[mouse][experiment]
        block_number = '1'
        
        file = f'/Volumes/GoogleDrive/Shared drives/Beique Lab/Data/Raspberry PI Data/Sébastien/Dual_Lickport/Mice/{mouse_number}/{date_experiment}/ms{mouse_number}_{date_experiment}_block{block_number}.hdf5'

        f = h5py.File(file, 'r') #open HDF5 file

        total_trials = len(f['lick_l']['volt']) #get number of trials

        correct_trials[mouse][experiment] = 0

        null_responses[mouse][experiment] = 0
        
        bias[mouse][experiment] = 0
        
        reward_times = np.empty(total_trials)
        reward_times.fill(np.nan)

        for trial in range(total_trials):
            
            if 'N' in str(f['response'][trial]): #check for null responses
                null_responses[mouse][experiment] += 1
                
            if 'R' in str(f['response'][trial]): #check for null responses
                bias[mouse][experiment] += 1

            if np.isnan(f['rew_l']['t'][trial]) == False: #choose trials where reward time isn't NaN

                #correct_trials[mouse][experiment] += 1 #count this as a correct trial

                rew_time = f['rew_l']['t'][trial] #find time where reward was delivered
                sample_tone_end = f['sample_tone']['end'][trial] #Find sample tone end time
                reward_times[trial] = rew_time - sample_tone_end #Calculate difference

            elif np.isnan(f['rew_r']['t'][trial]) == False:

                #correct_trials[mouse][experiment] += 1 #count this as a correct trial

                rew_time = f['rew_r']['t'][trial] #find time where reward was delivered
                sample_tone_end = f['sample_tone']['end'][trial] #Find sample tone end time
                reward_times[trial] = rew_time - sample_tone_end

            if f['response'][trial] == f['sample_tone']['type'][trial]:
                #If response matches trial type, it's a correct response
                correct_trials[mouse][experiment] += 1 #count this as a correct response

        correct_trials[mouse][experiment] /= (total_trials)

        bias[mouse][experiment] /= (total_trials - null_responses[mouse][experiment])

        null_responses[mouse][experiment] /= total_trials                     

        response_time[mouse][experiment] = np.nanmean(reward_times)

    axs[0,0].plot(correct_trials[mouse]*100, label=mouse_list[mouse])
    axs[0,1].plot(null_responses[mouse]*100, label=mouse_list[mouse])
    axs[1,0].plot(bias[mouse]*100, label=mouse_list[mouse])
    axs[1,1].plot(response_time[mouse], label=mouse_list[mouse])


axs[0,0].set_ylabel('% Correct trials')
axs[0,0].set_xlabel('Training Day')
axs[0,0].set_ylim(0,100)
#axs[0].set_xlim(None, 15)
axs[0,0].spines['top'].set_visible(False)
axs[0,0].spines['right'].set_visible(False)
axs[0,0].legend()

axs[0,1].set_ylabel('% Null responses')
axs[0,1].set_xlabel('Training Day')
axs[0,1].set_ylim(0,100)
#axs[1].set_xlim(None, 15)
axs[0,1].spines['top'].set_visible(False)
axs[0,1].spines['right'].set_visible(False)
#axs[1].legend()

axs[1,0].set_ylabel('Response bias (%R responses)')
axs[1,0].set_xlabel('Training Day')
axs[1,0].set_ylim(0,100)
#axs[2].set_xlim(None, 15)
axs[1,0].spines['top'].set_visible(False)
axs[1,0].spines['right'].set_visible(False)
#axs[2].legend()

axs[1,1].set_ylabel('Response time (ms)')
axs[1,1].set_xlabel('Training Day')
axs[1,1].set_ylim(0,None)
#axs[3].set_xlim(None, 15)
axs[1,1].spines['top'].set_visible(False)
axs[1,1].spines['right'].set_visible(False)
#axs[3].legend()

plt.show()
