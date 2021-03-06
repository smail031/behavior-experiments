#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 16:57:22 2019

@author: sebastienmaille
"""
#In this protocol, a "go" cue is presented at the beginning of each trial,
#without a preceding sample cue. During the subsequent response period, the
#first lickport to report a lick will immediately deliver a reward.

import time
import RPi.GPIO as GPIO
import numpy as np
import os
import threading
import core
from picamera import PiCamera

#------------------------------------------------------------------------------
#Set experimental parameters:
#------------------------------------------------------------------------------

mouse_number = input('mouse number: ' ) #asks user for mouse number
block_number = input('block number: ' ) #asks user for block number (for file storage)
n_trials = int(input('How many trials?: ' )) #number of trials in this block

response_delay = 3000

go_tone_freq = 500 #frequency of go tone

#----------------------------
#Assign GPIO pins:
#----------------------------

servo_PWM = 17 #PWM pin for servo that adjusts lickport distance

L_enablePIN = 23 #enable pin for left stepper motor
L_directionPIN = 24 #direction pin for left stepper motor
L_stepPIN = 25 #step pin for left stepper motor
L_emptyPIN = 20 #empty switch pin for left stepper motor
L_lickometer = 12 #input pin for lickometer (black wire)

R_enablePIN = 10 #enable pin for right stepper motor
R_directionPIN = 9 #direction pin for right stepper motor
R_stepPIN = 11 #step pin for right stepper motor
R_emptyPIN = 21 #empty switch pin for right stepper motor
R_lickometer = 16 #input pin for lickometer (black wire)

#----------------------------
#Initialize class instances for experiment:
#----------------------------

#Turn off the GPIO warnings
GPIO.setwarnings(False)

#Set the mode of the pins (broadcom vs local)
GPIO.setmode(GPIO.BCM)

#set the enable pins for L and R stepper motors to 1 to prevent overheating
GPIO.setup(L_enablePIN, GPIO.OUT, initial = 1)
GPIO.setup(R_enablePIN, GPIO.OUT, initial = 1)

#create Stepper class instances for left and right reward delivery
water_L = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
water_R = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)

#create lickometer class instances for left and right lickometers
lick_port_L = core.lickometer(L_lickometer)
lick_port_R = core.lickometer(R_lickometer)

tone_go = core.tones(go_tone_freq, 0.75)

camera = PiCamera()

#----------------------------
#Initialize experiment
#----------------------------

camera.start_preview(rotation = 180, fullscreen = False, window = (0,-44,350,400))

#Set the time for the beginning of the block
trials = np.arange(n_trials)
data = core.data(n_trials, mouse_number, block_number)

#start L and R reward counters
total_reward_L = 0
total_reward_R = 0

for trial in trials:
    data._t_start_abs[trial] = time.time()*1000 #Set time at beginning of trial
    data.t_start[trial] = data._t_start_abs[trial] - data._t_start_abs[0]

    #create thread objects for left and right lickports
    thread_L = threading.Thread(target = lick_port_L.Lick, args = (1000, 4))
    thread_R = threading.Thread(target = lick_port_R.Lick, args = (1000, 4))

    thread_L.start() #Start threads for lick recording
    thread_R.start()

    time.sleep(0.5)

    data.t_tone[trial] = time.time()*1000 - data._t_start_abs[trial]
    tone_go.Play() #Play go tone

    length_L = len(lick_port_L._licks)
    length_R = len(lick_port_R._licks)
    response = False
    response_start = time.time()*1000

    while response == False:
        if sum(lick_port_R._licks[(length_R-1):]) > 0:
            response = 'R'
            data.t_rew_r[trial] = time.time()*1000 - data._t_start_abs[trial]
            data.v_rew_r[trial] = 5
            water_R.Reward() #Deliver L reward
            total_reward_R += 5

        elif sum(lick_port_L._licks[(length_L-1):]) > 0:
            response = 'L'
            data.t_rew_l[trial] = time.time()*1000 - data._t_start_abs[trial]
            data.v_rew_l[trial] = 5
            water_L.Reward() #Deliver L reward
            total_reward_L += 5

        elif time.time()*1000 - response_start > response_delay:
            response = 'N'
            time.sleep(2)


    data.t_end[trial] = time.time()*1000 - data._t_start_abs[0] #store end time

    #---------------
    #Post-trial data storage
    #---------------

    #Make sure the threads are finished
    thread_L.join()
    thread_R.join()

    #subtract lick timestamps from start of trial so that integers are not too
    #big for storage.
    lick_port_L._t_licks -= data._t_start_abs[trial]
    lick_port_R._t_licks -= data._t_start_abs[trial]

    #Store and process the data
    storage_list = [data.lick_l, data.lick_r]
    rawdata_list = [lick_port_L, lick_port_R]

    for ind, storage in enumerate(storage_list):
        storage[trial] = {}
        storage[trial]['t'] = rawdata_list[ind]._t_licks
        storage[trial]['volt'] = rawdata_list[ind]._licks

    ITI_ = 1.5
    time.sleep(ITI_)

camera.stop_preview()

data.Store() #store the data in a .hdf5 file
data.Rclone() #move the .hdf5 file to "temporary-data folder on Desktop and
                #then copy to the lab google drive.

#delete the .wav files created for the experiment
os.system(f'rm {go_tone_freq}Hz.wav')

print(f'Total L reward: {total_reward_L} uL')
print(f'Total R reward: {total_reward_R} uL')
