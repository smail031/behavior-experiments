#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 16:57:22 2019

@author: sebastienmaille
"""
protocol_description = '''In this protocol, a sample cue is immediately followed by aresponse period. During this period, the first lickport that registers a lick determines the animal's
response. Correct responses trigger reward delivery from the correct port, while
incorrect or null responses are unrewarded. Trial types (L/R) alternate every
3 trials or randomly, depending on user input.'''

import time
import RPi.GPIO as GPIO
import numpy as np
import os
import threading
import core
from picamera import PiCamera
from pygame import mixer

#------------------------------------------------------------------------------
#Set experimental parameters:
#------------------------------------------------------------------------------

mouse_number = input('mouse number: ' ) #asks user for mouse number
block_number = input('block number: ' ) #asks user for block number (for file storage)
n_trials = int(input('How many trials?: ' )) #number of trials in this block
trial_alternation = input('Alternate trials randomly(r) or every 3 trials(t)?: ')#
ttl_experiment = input('Send trigger pulses to imaging laser? (y/n)')

delay_length = 0 #length of delay between sample tone and go cue, in sec
response_delay = 2000 #length of time for animals to give response

L_tone_freq = 1000 #frequency of sample tone in left lick trials
R_tone_freq = 4000 #frequency of sample tone in right lick trials
sample_tone_length = 2 #length of sample tone

wrong_tone_freq = 8000
wrong_tone_length = 1

reward_size = 10 #size of water rewards in uL

TTL_pulse_length = 0.01 #length of TTL pulses, in seconds

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

TTL_trigger_PIN = 100 # output for TTL pulse triggers to start/end laser scans
TTL_marker_PIN = 100 # output for TTL pulse markers

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

#initialize the mixer (for tones) at the proper sampling rate.
mixer.init(frequency = 44100)

#create Stepper class instances for left and right reward delivery
water_L = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
water_R = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)

#create lickometer class instances for left and right lickometers
lick_port_L = core.lickometer(L_lickometer)
lick_port_R = core.lickometer(R_lickometer)

#create tones
tone_L = core.tones(L_tone_freq, sample_tone_length)
tone_R = core.tones(R_tone_freq, sample_tone_length)

# tone_go = core.tones(go_tone_freq, go_tone_length)
tone_wrong = core.tones(wrong_tone_freq, wrong_tone_length)

if ttl_experiment == 'y':
    #set up ttl class instances triggers and marker TTL output
    TTL_trigger = core.ttl(TTL_trigger_PIN, TTL_pulse_length)
    TTL_marker = core.ttl(TTL_marker_PIN, TTL_pulse_length)

camera = PiCamera() #create camera object

#----------------------------
#Initialize experiment
#----------------------------

camera.start_preview(rotation = 180, fullscreen = False, window = (0,-44,350,400))

#Set the time for the beginning of the block
trials = np.arange(n_trials)
data = core.data(protocol_description, n_trials, mouse_number, block_number)

total_reward_L = 0
supp_reward_L = 0
total_reward_R = 0
supp_reward_R = 0
performance = 0 #will store the total number of correct responses.
rewarded_side = []
rewarded_trials = []

left_trial_ = True

for trial in trials:
    data._t_start_abs[trial] = time.time()*1000 #Set time at beginning of trial
    data.t_start[trial] = data._t_start_abs[trial] - data._t_start_abs[0]

    #create thread objects for left and right lickports
    thread_L = threading.Thread(target = lick_port_L.Lick, args = (1000, 7))
    thread_R = threading.Thread(target = lick_port_R.Lick, args = (1000, 7))

    if trial_alternation == 't':
        if float(trial/3).is_integer():
            left_trial_ = not left_trial_
    else:
        left_trial_ = np.random.rand() < 0.5

    if ttl_experiment == 'y':
        TTL_trigger.pulse() # Trigger the start of a scan

    thread_L.start() #Start threads for lick recording
    thread_R.start()

    time.sleep(1)
    #Left trial:---------------------------------------------------------------
    if left_trial_ is True:

        if ttl_experiment == 'y':
            TTL_marker.pulse() # Set a marker to align scans to trial start

        data.sample_tone[trial] = 'L' #Assign data type
        data.t_sample_tone[trial] = time.time()*1000 - data._t_start_abs[trial]
        tone_L.Play() #Play left tone
        data.sample_tone_end[trial] = time.time()*1000 - data._t_start_abs[trial]

        response = 'N'
        length_L = len(lick_port_L._licks)
        length_R = len(lick_port_R._licks)
        resp_window_end = time.time()*1000 + response_delay

        while time.time() * 1000 < resp_window_end:

            if sum(lick_port_L._licks[(length_L-1):]) > 0:
                response = 'L'
                data.t_rew_l[trial] = time.time()*1000 - data._t_start_abs[trial]
                data.v_rew_l[trial] = reward_size
                water_L.Reward() #Deliver L reward
                total_reward_L += reward_size
                performance += 1
                rewarded_side.append('L')
                rewarded_trials.append(1)
                break

            elif sum(lick_port_R._licks[(length_R-1):]) > 0:
                response = 'R'
                break

        if response == 'N' or response == 'R':
            tone_wrong.Play()
            rewarded_trials.append(0)

        data.response[trial] = response
        data.t_end[trial] = time.time()*1000 - data._t_start_abs[0] #store end time

    #Right trial:--------------------------------------------------------------
    else:

        if ttl_experiment == 'y':
            TTL_marker.pulse() # Set a marker to align scans to trial start

        data.sample_tone[trial] = 'R' #Assign data type
        data.t_sample_tone[trial] = time.time()*1000 - data._t_start_abs[trial]
        tone_R.Play() #Play left tone
        data.sample_tone_end[trial] = time.time()*1000 - data._t_start_abs[trial]

        time.sleep(delay_length) #Sleep for delay_length

        response = 'N' #preset response to 'N'
        length_L = len(lick_port_L._licks)
        length_R = len(lick_port_R._licks)
        resp_window_end = time.time()*1000 + response_delay

        while time.time() * 1000 < resp_window_end:

            if sum(lick_port_R._licks[(length_R-1):]) > 0:
                response = 'R'
                data.t_rew_r[trial] = time.time()*1000 - data._t_start_abs[trial]
                data.v_rew_r[trial] = reward_size
                water_R.Reward() #Deliver R reward
                total_reward_R += reward_size
                performance += 1
                rewarded_side.append('R')
                rewarded_trials.append(1)
                break

            elif sum(lick_port_L._licks[(length_L-1):]) > 0:
                response = 'L'
                break

        if response == 'N' or response == 'L':
            tone_wrong.Play()
            rewarded_trials.append(0)

        data.response[trial] = response
        data.t_end[trial] = time.time()*1000 - data._t_start_abs[0] #store end time

    #---------------
    #Post-trial data storage
    #---------------

    #Make sure the threads are finished
    thread_L.join()
    thread_R.join()

    if ttl_experiment == 'y':
        TTL_trigger.pulse() #trigger the end of the scan

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

    print(f'Performance: {performance}/{trial+1}')

    if len(rewarded_trials) > 8 and sum(rewarded_trials[-8:]) == 0:
        #if 8 unrewarded trials in a row, deliver rewards through both ports.
        tone_L.Play()
        water_L.Reward()
        supp_reward_L += reward_size
        rewarded_trials.append(1)
        time.sleep(1)
        tone_R.Play()
        water_R.Reward()
        supp_reward_R += reward_size
        rewarded_trials.append(1)
        time.sleep(1)

    if rewarded_side[-5:] == ['L', 'L', 'L', 'L', 'L']:
        #if 5 rewards from L port in a row, deliver rewards through R port.
        for i in range(2):
            tone_R.Play()
            water_R.Reward()
            supp_reward_R += reward_size
            time.sleep(1)
        rewarded_side.append('R')

    elif rewarded_side[-5:] == ['R', 'R', 'R', 'R', 'R']:
        #if 5 rewards from R port in a row, deliver rewards through L port
        for i in range(2):
            tone_L.Play()
            water_L.Reward()
            supp_reward_L += reward_size
            time.sleep(1)
        rewarded_side.append('L')

    ITI_ = 0
    while ITI_ > 12 or ITI_ < 8:
        ITI_ = np.random.exponential(scale = 10) #randomly select a new inter-trial interval

    time.sleep(ITI_) #wait for the length of the inter-trial interval

for i in range(2):
    tone_L.Play()
    tone_R.Play()

camera.stop_preview()

print(f'Total L reward: {total_reward_L} uL + {supp_reward_L}')
print(f'Total R reward: {total_reward_R} uL + {supp_reward_R}')
print(f'Total reward: {total_reward_L+supp_reward_L+total_reward_R+supp_reward_R}uL')
data.Store() #store the data in a .hdf5 file
data.Rclone() #move the .hdf5 file to "temporary-data folder on Desktop and
                #then copy to the lab google drive.

#delete the .wav files created for the experiment
tone_L.Delete()
tone_R.Delete()
tone_wrong.Delete()
