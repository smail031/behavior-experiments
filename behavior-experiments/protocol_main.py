#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 15:48:29 2019

@author: sebastienmaille
"""
import time
import RPi.GPIO as GPIO
import numpy as np
import os
import threading

#----------------------------
#Initialize class instances for experiment:
#----------------------------

#Turn off the GPIO warnings
GPIO.setwarnings(False)

#Set the mode of the pins (broadcom vs local)
GPIO.setmode(GPIO.BCM)

#Assign GPIOs
TTL = Stim("TTL",16,GPIO.OUT)

water_L = Stim("water_L",25,GPIO.OUT)
water_R = Stim("water_R",26,GPIO.OUT)

lick_port_L = Stim("lick_L",30,GPIO.IN)
lick_port_R = Stim("lick_R",31,GPIO.IN)

#create tones
tone_L = Tones(L_tone_freq, 1)
tone_R = Tones(R_tone_freq, 1)

tone_go = Tones(go_tone_freq, 0.75)

#----------------------------
#Initialize experiment
#----------------------------

#Set the time for the beginning of the block
trials = np.arange(n_trials)
data = Data(n_trials)

for trial in trials:
    data._t_start_abs[trial] = time.time() #Set time at beginning of trial
    data.t_start[trial] = data._t_start_abs[trial] - data._t_start_abs[0]

    #create thread objects for left and right lickports
    thread_L = threading.Thread(target = lick_port_L.lick, args = (1, 5))
    thread_R = threading.Thread(target = lick_port_R.lick, args = (1, 5))

    thread_L.start() #Start threads for lick recording
    thread_R.start()

    left_trial_ = np.random.rand() < 0.5 #decide if it will be a L or R trial

    if left_trial_ is True:
        data.tone[trial] = 'L' #Assign data type
        data.t_tone[trial] = time.time() - data._t_start_abs[trial]
        tone_L.play() #Play left tone

        time.sleep(delay_length) #Sleep for some delay

        tone_go.play() #Play go tone

        data.t_rew_l[trial] = time.time() - data._t_start_abs[trial]
        data.v_rew_l[trial] = 5
        water_L.reward(reward_size) #Deliver L reward

        data.t_end[trial] = time.time() - data._t_start_abs[0] #store end time

    else:
        data.tone[trial] = 'R' #Assign data type
        data.t_tone[trial] = time.time() - data._t_start_abs[trial]
        tone_R.play() #Play left tone

        time.sleep(delay_length) #Sleep for some delay

        tone_go.play() #Play go tone

        data.t_rew_r[trial] = time.time() - data._t_start_abs[trial]
        data.v_rew_r[trial] = 5
        water_R.reward(reward_size) #Deliver L reward

        data.t_end[trial] = time.time() - data._t_start_abs[0] #store end time

    #---------------
    #Post-trial data storage
    #---------------
    #Make sure the threads are finished
    thread_L.join()
    thread_R.join()

    #Store and process the data
    data_list = [data.lick_l, data.lick_r]
    lick_list = [lick_port_L, lick_port_R]

    for ind, obj in enumerate(data_list):
        obj[trial] = {}
        obj[trial]['t'] = lick_list[ind]._t_licks
        obj[trial]['volt'] = lick_list[ind]._licks

    #Pause for the ITI before next trial
    ITI_ = 1.5
#    while ITI_ > 10:
#        ITI_ = np.random.exponential(scale = 2)

    time.sleep(ITI_)


data.store() #store the data

#delete the .wav files created for the experiment
os.system(f'rm {L_tone_freq}Hz.wav')
os.system(f'rm {R_tone_freq}Hz.wav')
os.system(f'rm {go_tone_freq}Hz.wav')

#Clean up the GPIOs
#GPIO.cleanup()