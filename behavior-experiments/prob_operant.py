#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 11:47:22 2021
@author: sebastienmaille
"""
protocol_name = 'prob_operant'
protocol_description = ('In this protocol, one of 2 sample cues (differing based'
                        'on frequency) is immediately followed by a response '
                        'period. During this period, the first lickport that '
                        'registers a lick determines the animals response. '
                        'Correct responses trigger reward delivery from the '
                        'correct port with probability p_rew, while incorrect '
                        'or null responses are unrewarded. if 19/20 trials are '
                        'correct, the mouse is considered an "expert".')

import time
import RPi.GPIO as GPIO
import numpy as np
import os
import threading
import core
from picamera import PiCamera
from pygame import mixer


camera = PiCamera() #create camera object
camera.start_preview(fullscreen = False, window = (0,-44,350,400))

#------------------------------------------------------------------------------
# Set experimental parameters:
#------------------------------------------------------------------------------

experimenter = input('Initials: ')
mouse_number = input('mouse number: ' )
mouse_weight = float(input('mouse weight(g): '))


fetch = input('Fetch previous data? (y/n) ')
if fetch == 'y':
    [freq_rule, left_port, countdown, expert] = (
        core.get_previous_data(mouse_number, protocol_name))
else:
    print('Warning: no previous data imported. Ensure that rule is correct, and'
          'that the performance criterion was not met recently.')

block_number = input('block number: ')
n_trials = int(input('How many trials?: '))
ttl_experiment = input('Send trigger pulses to imaging laser? (y/n): ')
syringe_check = input('Syringe check: ')

yesterday = input('Use yesterdays rules? (y/n): ')
if yesterday == 'n':
    left_port = int(input('Port assignment: L(1) or R(0): '))
    countdown = np.nan

if input('Manually add expert value? (y/n): ') == 'y':
    expert = bool(input('Indicate whether expert(1) or not(0): '))
    
response_window = 2000 # Time window(ms) for animals to respond after cue.

sample_tone_length = 2 # Length of sample tone (s)
low_freq = 6000 # Frequency(Hz) of high frequency sample tone.
high_freq = 10000 # Frequency(Hz) of high frequency sample tone.

wrong_tone_freq = 14000
wrong_tone_length = 1
end_tone_freq = 4000 # Tone to signal the end of the experiment.
end_tone_length = 8

reward_size = 10 # Volume(uL) of water rewards.
p_rew = 0.9 # Probability of reward following correct choice
criterion = [19,20] # Mouse must get [0] of [1] correct to reach criterion.
countdown_start = 250

#------------------------------------------------------------------------------
#Assign GPIO pins:
#------------------------------------------------------------------------------

servo_PWM = 17 #PWM pin for servo that adjusts lickport distance

L_enablePIN = 23 #enable pin for left stepper motor
L_directionPIN = 24  # Direction pin for left stepper motor
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

#------------------------------------------------------------------------------
# Initialize class instances for experiment:

#------------------------------------------------------------------------------

# Turn off the GPIO warnings
GPIO.setwarnings(False)

# Set the mode of the pins (broadcom vs local)
GPIO.setmode(GPIO.BCM)

# Set the enable pins for L and R stepper motors to 1 to prevent overheating
GPIO.setup(L_enablePIN, GPIO.OUT, initial=1)
GPIO.setup(R_enablePIN, GPIO.OUT, initial=1)

# Initialize the mixer (for tones) at the proper sampling rate.
mixer.init(frequency=44100)

# Create Stepper class instances for left and right reward delivery
water_L = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
water_R = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)

# Create lickometer class instances for left and right lickometers
lick_port_L = core.lickometer(L_lickometer)
lick_port_R = core.lickometer(R_lickometer)

# Create instruction tones
lowfreq = core.PureTone(low_freq, sample_tone_length)
highfreq = core.PureTone(high_freq, sample_tone_length)

# Create tone that is used as an error signal
tone_wrong = core.PureTone(wrong_tone_freq, wrong_tone_length)
tone_end = core.PureTone(end_tone_freq, end_tone_length, vol=-25)

rule = core.Rule([highfreq,lowfreq], left_port, criterion,
                 countdown_start, expert, countdown)

if ttl_experiment == 'y':
    #set up ttl class instances triggers and marker TTL output
    TTL_trigger = core.ttl(TTL_trigger_PIN)
    TTL_marker = core.ttl(TTL_marker_PIN)

#-------------------------------------------------------------------------------
# Initialize experiment:
#-------------------------------------------------------------------------------

#Set the time for the beginning of the block
trials = np.arange(n_trials)
data = core.data(protocol_name, protocol_description, n_trials, mouse_number,
                 block_number, experimenter, mouse_weight)

total_reward_L = 0
supp_reward_L = 0
total_reward_R = 0
supp_reward_R = 0
performance = 0 # Total number of correct responses (to print at each trial)
correct_side = [] # Ports from which past rewards were received (to track bias)

#-------------------------------------------------------------------------------
# Iterate through trials:
#-------------------------------------------------------------------------------

for trial in trials:
    data._t_start_abs[trial] = time.time()*1000 #Set time at beginning of trial
    data.t_start[trial] = data._t_start_abs[trial] - data._t_start_abs[0]

    # Initialize thread objects for left and right lickport recording
    thread_L = threading.Thread(target = lick_port_L.Lick, args = (1000, 8))
    thread_R = threading.Thread(target = lick_port_R.Lick, args = (1000, 8))

    left_trial_ = np.random.rand() < 0.5 # 50% chance of L trial
    
    if ttl_experiment == 'y':
        TTL_trigger.pulse()

    # Start lick recording threads
    thread_L.start()
    thread_R.start()

    time.sleep(2)
    
    #Left trial:----------------------------------------------------------------
    if left_trial_:
        tone = rule.L_tone
        
        if ttl_experiment == 'y':
            TTL_marker.pulse()

        data.sample_tone[trial] = 'L'
        data.t_sample_tone[trial] = time.time()*1000 - data._t_start_abs[trial]
        tone.play()
        data.sample_tone_end[trial] = (time.time()*1000
                                       - data._t_start_abs[trial])

        response = 'N'
        length_L = len(lick_port_L._licks)
        length_R = len(lick_port_R._licks)
        resp_window_end = time.time()*1000 + response_window

        while time.time() * 1000 < resp_window_end:
            #If first lick is L (correct)
            if sum(lick_port_L._licks[(length_L-1):]) > 0: 
                # Reward delivery for correct lick
                if np.random.rand() < p_rew:
                    data.t_rew_l[trial] = (time.time()*1000
                                           - data._t_start_abs[trial])
                    water_L.Reward()
                    data.v_rew_l[trial] = reward_size
                    total_reward_L += reward_size

                # Stochastic reward omission for correct lick
                else: 
                    tone_wrong.play()

                response = 'L'
                performance += 1
                rule.correct_trials.append(1)
                correct_side.append('L')
                    
                break

            # If first lick is R (incorrect)
            elif sum(lick_port_R._licks[(length_R-1):]) > 0: 
                # Reward omission for incorrect lick
                if np.random.rand() < p_rew: 
                    tone_wrong.play()

                # Reward delivery for incorrect lick
                else: 
                    data.t_rew_r[trial] = (time.time()*1000
                                           - data._t_start_abs[trial])
                    water_R.Reward()
                    data.v_rew_r[trial] = reward_size
                    total_reward_R += reward_size

                response = 'R'
                rule.correct_trials.append(0)
                    
                break

        if response == 'N':
            tone_wrong.play()
            rule.correct_trials.append(0)

        data.response[trial] = response
        data.t_end[trial] = time.time()*1000 - data._t_start_abs[0]

    #Right trial:---------------------------------------------------------------
    else:
        tone = rule.R_tone
        
        if ttl_experiment == 'y':
            TTL_marker.pulse() # Set a marker to align scans to trial start

        data.sample_tone[trial] = 'R'
        data.t_sample_tone[trial] = time.time()*1000 - data._t_start_abs[trial]
        tone.play() #Play left tone
        data.sample_tone_end[trial] = (time.time()*1000
                                       - data._t_start_abs[trial])

        response = 'N'
        length_L = len(lick_port_L._licks)
        length_R = len(lick_port_R._licks)
        resp_window_end = time.time()*1000 + response_window

        while time.time() * 1000 < resp_window_end:
            #If first lick is R (correct)
            if sum(lick_port_R._licks[(length_R-1):]) > 0:
                # Stochastic reward delivery
                if np.random.rand() < p_rew: 
                    data.t_rew_r[trial] = (time.time()*1000
                                           - data._t_start_abs[trial])
                    water_R.Reward()
                    data.v_rew_r[trial] = reward_size
                    total_reward_R += reward_size

                # Stochastic reward omission
                else:
                    tone_wrong.play()

                response = 'R'
                performance += 1
                correct_side.append('R')
                rule.correct_trials.append(1)
                    
                break

            #If first lick is L (incorrect)
            elif sum(lick_port_L._licks[(length_L-1):]) > 0: 
                # Stochastic reward omission
                if np.random.rand() < p_rew: 
                    tone_wrong.play()

                # Stochastic rew delivery for incorrect choice
                else: 
                    data.t_rew_l[trial] = (time.time()*1000
                                           - data._t_start_abs[trial])
                    water_L.Reward()
                    data.v_rew_l[trial] = reward_size
                    total_reward_L += reward_size

                response = 'L'
                rule.correct_trials.append(0)
                    
                break

        if response == 'N':
            tone_wrong.play()
            rule.correct_trials.append(0)

        data.response[trial] = response
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

    # Store and process the data
    storage_list = [data.lick_l, data.lick_r]
    rawdata_list = [lick_port_L, lick_port_R]

    for ind, storage in enumerate(storage_list):
        storage[trial] = {}
        storage[trial]['t'] = rawdata_list[ind]._t_licks
        storage[trial]['volt'] = rawdata_list[ind]._licks
        
    data.freq[trial] = tone.freq #store tone frequency
    data.loc[trial] = tone.loc #store whether multipulse(1) or single pulse(0)
    data.left_port[trial] = rule.rule #store port assighment of tones
    data.countdown[trial] = rule.countdown
    data.expert[trial] = rule.expert
    data.rew_prob[trial] = p_rew
    #if freq rule, left_port=1 means highfreq on left port
    #if pulse rule, left_port=1 means multipulse on left port

    licks_detected = ''
    # Will indicate which ports recorded any licks in the entire trial.
    if sum(lick_port_L._licks) != 0:
        licks_detected += 'L'
    if sum(lick_port_R._licks) != 0:
        licks_detected += 'R'
        
    print(f'Tone:{tone.freq}, Resp:{response}, Licks:{licks_detected}, '
          f'Rew:{np.nansum([data.v_rew_l[trial],data.v_rew_r[trial]])}, '
          f'Corr:{rule.correct_trials[-1]}, Perf:{performance}/{(trial+1)}')

    #---------------------------------------------------------------------------
    # Deliver supplementary rewards:
    #---------------------------------------------------------------------------

    # If 8 unrewarded trials in a row, deliver rewards through both ports.
    if len(rule.correct_trials) > 8 and sum(rule.correct_trials[-8:]) == 0:
        rule.L_tone.play()
        water_L.Reward()
        supp_reward_L += reward_size
        time.sleep(1)
        rule.R_tone.play()
        water_R.Reward()
        supp_reward_R += reward_size
        time.sleep(1)
        rule.correct_trials = []

    # If 5 rewards from L port in a row, deliver rewards through R port.
    if correct_side[-5:] == ['L', 'L', 'L', 'L', 'L']:
        for i in range(2):
            if np.random.rand() < 0.5:        
                rule.R_tone.play()
            else:
                rule.R_tone.play()
                
            water_R.Reward()
            supp_reward_R += reward_size
            time.sleep(1)
        correct_side.append('R')

    # If 5 rewards from R port in a row, deliver rewards through L port
    elif correct_side[-5:] == ['R', 'R', 'R', 'R', 'R']:
        for i in range(2):
            if np.random.rand() < 0.5:        
                rule.L_tone.play()
            else:
                rule.L_tone.play()
                
            water_L.Reward()
            supp_reward_L += reward_size
            time.sleep(1)
        correct_side.append('L')

    if ((rule.expert == False) & rule.check_criterion()):
        print('-----Performance criterion has been met.-----')
        rule.expert = True

    ITI_ = 0
    while ITI_ > 30 or ITI_ < 10:
        ITI_ = np.random.exponential(scale = 20)

    time.sleep(ITI_)

tone_end.play()
camera.stop_preview()

print(f'Total L reward: {total_reward_L} uL + {supp_reward_L}')
print(f'Total R reward: {total_reward_R} uL + {supp_reward_R}')
data.total_reward = (total_reward_L + supp_reward_L
                     + total_reward_R + supp_reward_R)
print(f'Total reward: {data.total_reward}uL')

# Ask the user if there were any problems with the experiment. If so, prompt
# the user for an explanation that will be stored in the data file.
data.exp_quality = input('Should this data be used? (y/n): ') 
if data.exp_quality == 'n':
    data.exp_msg = input('What went wrong?: ')

# Store the data in an HDF5 file and upload this file to a remote drive.
data.Store()
data.Rclone()

#delete the .wav files created for the experiment
core.delete_tones()
