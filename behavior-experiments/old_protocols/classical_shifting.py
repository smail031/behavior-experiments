#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 16:57:22 2019

@author: sebastienmaille
"""
protocol_description = '''In this protocol, a sample cue is immediately followed by a "go", which itself
is followed by reward delivery from the corresponding port. A delay can be
introduced between sample and go cues by changing the "delay_length"" variable.'''

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

experimenter = input('Initials: ') #gets experimenter initials
mouse_number = input('mouse number: ' ) #asks user for mouse number
mouse_weight = float(input('mouse weight(g): '))
block_number = input('block number: ' ) #asks user for block number (for file storage)
n_trials = int(input('How many trials?: ' )) #number of trials in this block
ttl_experiment = input('Send trigger pulses to imaging laser? (y/n)')

yesterday = input('Use yesterdays rules? (y/n): ') #ask whether previous day's rule should be used

if yesterday == 'n': #if not, ask user to specify the rule to be used
    freq_rule = int(input('Frequency rule(1) or Pulse rule(0): '))
    left_port = int(input('Port assignment: L(1) or R(0): '))

delay_length = 0 #length of delay between sample tone and go cue, in sec

sample_tone_length = 2 #length of sample tone

low_freq = 1000 #frequency of lower freq sample tone 
high_freq = 4000 #frequency of lower freq sample tone

single_pulse_length = sample_tone_length
multi_pulse_length = 0.1

reward_size = 8.2 #size of water rewards in uL

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

TTL_trigger_PIN = 15 # output for TTL pulse triggers to start/end laser scans
TTL_marker_PIN = 27 # output for TTL pulse markers

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

#create instruction tones
lowfreq_singlepulse = core.tones(low_freq, sample_tone_length, single_pulse_length) #1000Hz single pulse
lowfreq_multipulse = core.tones(low_freq, sample_tone_length, multi_pulse_length) #1000Hz multi pulse
highfreq_singlepulse = core.tones(high_freq, sample_tone_length, single_pulse_length) #4000Hz single pulse
highfreq_multipulse = core.tones(high_freq, sample_tone_length, multi_pulse_length) #4000Hz multi pulse

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
data = core.data(protocol_description, n_trials, mouse_number, block_number, experimenter, mouse_weight)

total_reward_L = 0
total_reward_R = 0

#------ Assign tones according to rules -------

if yesterday == 'y':  
    #get data from yesterday's experiment
    yesterday_directory = '/home/pi/Desktop/yesterday_data'
    yesterday_file = [fname for fname in os.listdir(yesterday_directory) if mouse_number in fname][0] #get yesterday's file for this mouse, should only be one.

    yesterday_file = yesterday_directory + '/' + yesterday_file

    f = h5py.File(yesterday_file, 'r') #open HDF5 file
    
    freq_rule = f['rule']['freq_rule'][-1] #get value of freq_rule of last trial yesterday
    left_port = f['rule']['left_port'][-1] #get value of left_port of last trial yesterday
            
if freq_rule == 1: #Tone freq is relevant dimension (pulsing is irrelevant)

    if left_port == 1: #highfreq tones are on L port (lowfreq -> R port)

        L_tone_a = highfreq_singlepulse
        L_tone_b = highfreq_multipulse
        R_tone_a = lowfreq_singlepulse
        R_tone_b = lowfreq_multipulse

    elif left_port ==0: #highfreq is on R port (lowfreq -> L port)

        L_tone_a = lowfreq_singlepulse
        L_tone_b = lowfreq_multipulse
        R_tone_a = highfreq_singlepulse
        R_tone_b = highfreq_multipulse

elif freq_rule == 0: #Tone pulsing is relevant dimension (freq is irrelevant)
  
    if left_port == 1: #multipulse tones are on L port (singlepulse -> R port)

        L_tone_a = highfreq_multipulse
        L_tone_b = lowfreq_multipulse
        R_tone_a = highfreq_singlepulse
        R_tone_b = lowfreq_singlepulse

    elif left_port ==0: #multipulse is on R port (singlepulse -> L port)

        L_tone_a = highfreq_singlepulse
        L_tone_b = lowfreq_singlepulse
        R_tone_a = highfreq_multipulse
        R_tone_b = lowfreq_multipulse

for trial in trials:

    print(f'Trial {trial}, total reward: {total_reward_L+total_reward_R}')
    
    data._t_start_abs[trial] = time.time()*1000 #Set time at beginning of trial
    data.t_start[trial] = data._t_start_abs[trial] - data._t_start_abs[0]

    #create thread objects for left and right lickports
    thread_L = threading.Thread(target = lick_port_L.Lick, args = (1000, 5))
    thread_R = threading.Thread(target = lick_port_R.Lick, args = (1000, 5))

    left_trial_ = np.random.rand() < 0.5 # 50% chance of L trial, otherwise R trial 

    trace_period = 3
    while trace_period > 2:
        trace_period = np.random.exponential(scale=2)

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
        if np.random.rand() > 0.5:
            L_tone_a.Play()
        else:
            L_tone_b.Play()
        data.sample_tone_end[trial] = time.time()*1000 - data._t_start_abs[trial]

        time.sleep(trace_period)
        
        data.t_rew_l[trial] = time.time()*1000 - data._t_start_abs[trial]
        water_L.Reward() #Deliver L reward
        data.v_rew_l[trial] = reward_size
        total_reward_L += reward_size

        data.t_end[trial] = time.time()*1000 - data._t_start_abs[0] #store end time


    #Right trial:--------------------------------------------------------------
    else:

        if ttl_experiment == 'y':
            TTL_marker.pulse() # Set a marker to align scans to trial start
        
        data.sample_tone[trial] = 'R' #Assign data type

        data.t_sample_tone[trial] = time.time()*1000 - data._t_start_abs[trial]
        if np.random.rand() > 0.5:
            R_tone_a.Play()
        else:
            R_tone_b.Play()
        data.sample_tone_end[trial] = time.time()*1000 - data._t_start_abs[trial]

        time.sleep(trace_period)
        
        data.t_rew_r[trial] = time.time()*1000 - data._t_start_abs[trial]
        water_R.Reward() #Deliver R reward
        data.v_rew_r[trial] = reward_size
        total_reward_R += reward_size

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

    ITI_ = 0
    while ITI_ > 12 or ITI_ < 8:
        ITI_ = np.random.exponential(scale = 10)

    time.sleep(ITI_)

for i in range(2):
    tone_L_A.Play()
    tone_R_A.Play()


camera.stop_preview()

print(f'Total L reward: {total_reward_L}uL')
print(f'Total R reward: {total_reward_R}uL')
print(f'Total reward: {total_reward_L+total_reward_R}uL')

data.Store() #store the data in a .hdf5 file
data.Rclone() #move the .hdf5 file to "temporary-data folder on Desktop and
                #then copy to the lab google drive.

#delete the .wav files created for the experiment
lowfreq_singlepulse.Delete()
lowfreq_multipulse.Delete()
highfreq_singlepulse.Delete()
highfreq_multipulse.Delete()
