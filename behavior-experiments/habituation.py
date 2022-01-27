#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 16:21:22 2022

@author: sebastienmaille
"""
protocol_name = 'habituation'
protocol_description = ('The goal of this protocol is to 1) habituate the mouse'
                        'to the behavior rig and all associated stimuli, and'
                        '2) to begin associating licks on lickports to water'
                        'delivery. On each trial, one of two lickports is armed'
                        'such that licking that port willr result in water'
                        'delivery. ITIs are short (~2 seconds)')
                        
import time
import RPi.GPIO as GPIO
import numpy as np
import os
import threading
import core
from picamera import PiCamera
from pygame import mixer

camera = PiCamera()
camera.start_preview(fullscreen = False, window = (0,-44,350,400))

#-------------------------------------------------------------------------------
# Set experimental parameters:
#-------------------------------------------------------------------------------

experimenter = input('Initials: ')
mouse_number = input('mouse number: ' )
mouse_weight = float(input('mouse weight(g): '))

block_number = input('block number: ' )
n_trials = int(input('How many trials?: ' ))
ttl_experiment = input('Send trigger pulses to imaging laser? (y/n): ')
syringe_check = input('Syringe check: ')

end_tone_freq = 1000 # Tone that will be played at the end of the experiment.
end_tone_length = 8

reward_size = 10 # Size of water rewards in uL
response_window = 5000 # Duration(ms) of response window each trial.

TTL_pulse_length = 0.01 # Length of TTL pulses, in seconds

#-------------------------------------------------------------------------------
#Assign GPIO pins:
#-------------------------------------------------------------------------------

L_enablePIN = 23 # Enable pin for left stepper motor.
L_directionPIN = 24 # Direction pin for left stepper motor.
L_stepPIN = 25 # Step pin for left stepper motor.
L_emptyPIN = 20 # Empty switch pin for left stepper motor.
L_lickometer = 12 # Input pin for lickometer (black wire).


R_enablePIN = 10 # Enable pin for right stepper motor.
R_directionPIN = 9 # Direction pin for right stepper motor.
R_stepPIN = 11 # Step pin for right stepper motor.
R_emptyPIN = 21 # Empty switch pin for right stepper motor.
R_lickometer = 16 # Input pin for lickometer (black wire).

TTL_trigger_PIN = 15 # TTL output to trigger to start/end of laser scans.
TTL_marker_PIN = 27 # TTL output for imaging markers.

#-------------------------------------------------------------------------------
# Initialize class instances for experiment:
#-------------------------------------------------------------------------------

# Turn off the GPIO warnings.
GPIO.setwarnings(False)

# Set the mode of the pins (broadcom vs local).
GPIO.setmode(GPIO.BCM)

# Set the enable pins for L and R stepper motors to 1 to prevent overheating.
GPIO.setup(L_enablePIN, GPIO.OUT, initial = 1)
GPIO.setup(R_enablePIN, GPIO.OUT, initial = 1)

# Initialize the mixer (for tones) at the proper sampling rate.
mixer.init(frequency = 44100)

# Create Stepper class instances for left and right reward delivery.
water_L = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
water_R = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)

# Create lickometer class instances for left and right lickometers.
lick_port_L = core.lickometer(L_lickometer)
lick_port_R = core.lickometer(R_lickometer)

# Generate a tone to mark end of the experiment.
tone_end = core.tones(end_tone_freq, end_tone_length)

if ttl_experiment == 'y':
    # Set up ttl class instances triggers and marker TTL output.
    TTL_trigger = core.ttl(TTL_trigger_PIN, TTL_pulse_length)
    TTL_marker = core.ttl(TTL_marker_PIN, TTL_pulse_length)

#-------------------------------------------------------------------------------
# Initialize experiment:
#-------------------------------------------------------------------------------

trials = np.arange(n_trials)
data = core.data(protocol_name, protocol_description, n_trials, mouse_number,
                 block_number, experimenter, mouse_weight)

total_reward_L = 0
total_reward_R = 0

#-------------------------------------------------------------------------------
# Iterate through trials:
#-------------------------------------------------------------------------------

for trial in trials:

    print(f'Trial {trial}, total reward: {total_reward_L+total_reward_R}')
    
    data._t_start_abs[trial] = time.time()*1000 #Set time at beginning of trial
    data.t_start[trial] = data._t_start_abs[trial] - data._t_start_abs[0]

    # Initialize thread objects for left and right lickports
    thread_L = threading.Thread(target = lick_port_L.Lick, args = (1000, 8))
    thread_R = threading.Thread(target = lick_port_R.Lick, args = (1000, 8))

    left_trial_ = np.random.rand() < 0.5 # 50% chance of L trial
    
    if ttl_experiment == 'y':
        TTL_trigger.pulse() # Trigger the start of a scan.

    thread_L.start() # Start threads for lick recording.
    thread_R.start()

    time.sleep(2)
    
    # Left trial:---------------------------------------------------------------
    if left_trial_:
        
        if ttl_experiment == 'y':
            TTL_marker.pulse() # Set a marker to align scans to trial start

        data.sample_tone[trial] = 'L' # No sample tone, just to record trialtype

        length_L = len(lick_port_L._licks)
        resp_window_end = time.time()*1000 + response_window

        while time.time()*1000 < resp_window_end:
            if sum(lick_port_L._licks[(length_L-1):]) > 0: # Check for any licks
                data.t_rew_l[trial] = time.time()*1000 - data._t_start_abs[trial]
                water_L.Reward() #Deliver L reward
                data.v_rew_l[trial] = reward_size
                total_reward_L += reward_size

        data.t_end[trial] = time.time()*1000 - data._t_start_abs[0]

    # Right trial:--------------------------------------------------------------
    else:
        
        if ttl_experiment == 'y':
            TTL_marker.pulse() # Set a marker to align scans to trial start

        data.sample_tone[trial] = 'R' # No sample tone, just to record trialtype
        length_R = len(lick_port_R._licks)
        resp_window_end = time.time()*1000 + response_window
        
        while time.time()*1000 < resp_window_end:
            if sum(lick_port_R._licks[(length_R-1):]) > 0: # Check for any licks
                data.t_rew_r[trial] = time.time()*1000 - data._t_start_abs[trial]
                water_R.Reward() #Deliver R reward
                data.v_rew_r[trial] = reward_size
                total_reward_R += reward_size

        data.t_end[trial] = time.time()*1000 - data._t_start_abs[0]

    #---------------------------------------------------------------------------
    # Post-trial data storage
    #---------------------------------------------------------------------------

    # Make sure the threads are finished
    thread_L.join()
    thread_R.join()

    if ttl_experiment == 'y':
        TTL_trigger.pulse() #trigger the end of the scan

    lick_port_L._t_licks -= data._t_start_abs[trial]
    lick_port_R._t_licks -= data._t_start_abs[trial]

    #Store and process the data
    storage_list = [data.lick_l, data.lick_r]
    rawdata_list = [lick_port_L, lick_port_R]

    for ind, storage in enumerate(storage_list):
        storage[trial] = {}
        storage[trial]['t'] = rawdata_list[ind]._t_licks
        storage[trial]['volt'] = rawdata_list[ind]._licks

    if sum(lick_port_L._licks) == 0:
        print('No Left licks detected')

    if sum(lick_port_R._licks) == 0:
        print('No Right licks detected')

    ITI_ = 0
    while ITI_ > 4 or ITI_ < 0:
        ITI_ = np.random.exponential(scale = 1) 

    time.sleep(ITI_) # Wait for the length of the inter-trial interval.

tone_end.Play() # Play tone to signal the end of the experiment.
camera.stop_preview()

print(f'Total L reward: {total_reward_L} uL')
print(f'Total R reward: {total_reward_R} uL')
data.total_reward = (total_reward_L + total_reward_R)
print(f'Total reward: {data.total_reward}uL')

data.exp_quality = input('Should this data be used? (y/n): ')
if data.exp_quality == 'n':
    # If there is a problem with the experiment, user can describe it in this
    # string that will be stored with the data.
    data.exp_msg = input('What went wrong?: ')

# Store the data in an HDF5 file and upload this file to a remote drive.
data.Store()
data.Rclone()

tone_end.Delete()
