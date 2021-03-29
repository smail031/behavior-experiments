#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 23 11:47:22 2021

@author: sebastienmaille
"""
protocol_description = '''In this protocol, one of 4 sample cues is immediately followed by aresponse period. 
During this period, the first lickport that registers a lick determines the animal's response. Correct responses 
trigger reward delivery from the correct port with probability p_rew, while incorrect or null responses are 
unrewarded. if 18/20 trials are correct, a set shift is triggered.'''

import time
import RPi.GPIO as GPIO
import numpy as np
import os
import threading
import core
import h5py
from picamera import PiCamera
from pygame import mixer

#------------------------------------------------------------------------------
#Set experimental parameters:
#------------------------------------------------------------------------------

mouse_number = input('mouse number: ' ) #asks user for mouse number
block_number = input('block number: ' ) #asks user for block number (for file storage)
n_trials = int(input('How many trials?: ' )) #number of trials in this block
ttl_experiment = input('Send trigger pulses to imaging laser? (y/n)')

yesterday = input('Use yesterdays rules? (y/n): ') #ask whether previous day's rule should be used

if yesterday == 'n': #if not, ask user to specify the rule to be used
    freq_rule = int(input('Frequency rule(1) or Pulse rule(0): '))
    left_port = int(input('Port assignment: L(1) or R(0): '))


delay_length = 0 #length of delay between sample tone and go cue, in sec
response_delay = 2000 #length of time for animals to give response


sample_tone_length = 2 #length of sample tone

low_freq = 1000 #frequency of sample tone in left lick trials
high_freq = 4000 #frequency of sample tone in right lick trials

single_pulse_length = sample_tone_length #single tone pulse lasts the entire timexs
multi_pulse_length = 0.05

wrong_tone_freq = 8000
wrong_tone_length = 1

reward_size = 8.2 #size of water rewards in uL

p_rew = 0.8 #probability of reward following correct choice

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

#create tone that is used as an error signal
tone_wrong = core.tones(wrong_tone_freq, wrong_tone_length, wrong_tone_length)

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
performance = 0 #will store the total number of correct responses (to print at each trial)
correct_side = [] #will store ports from which rewards were received (to track bias)
correct_trials = [] #will store recent correct/incorrect trials (for supp rew and set shift)


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

#------ Iterate through trials -------

for trial in trials:
    data._t_start_abs[trial] = time.time()*1000 #Set time at beginning of trial
    data.t_start[trial] = data._t_start_abs[trial] - data._t_start_abs[0]

    #create thread objects for left and right lickports
    thread_L = threading.Thread(target = lick_port_L.Lick, args = (1000, 8))
    thread_R = threading.Thread(target = lick_port_R.Lick, args = (1000, 8))

    left_trial_ = np.random.rand() < 0.5 # 50% chance of L trial, otherwise R trial
    
    if ttl_experiment == 'y':
        TTL_trigger.pulse() # Trigger the start of a scan

    thread_L.start() #Start threads for lick recording
    thread_R.start()

    time.sleep(2)
    #Left trial:---------------------------------------------------------------
    if left_trial_ is True:

        if np.random.rand() < 0.5: #Choose which L tone will be played
            tone = L_tone_a
        else:
            tone = L_tone_b
        
        if ttl_experiment == 'y':
            TTL_marker.pulse() # Set a marker to align scans to trial start

        data.sample_tone[trial] = 'L' #Assign data type
        data.t_sample_tone[trial] = time.time()*1000 - data._t_start_abs[trial]
        tone.Play() #Play left tone
        data.sample_tone_end[trial] = time.time()*1000 - data._t_start_abs[trial]

        response = 'N'
        length_L = len(lick_port_L._licks)
        length_R = len(lick_port_R._licks)
        resp_window_end = time.time()*1000 + response_delay

        while time.time() * 1000 < resp_window_end:

            if sum(lick_port_L._licks[(length_L-1):]) > 0: #If first lick is L (correct)
                
                if np.random.rand() < p_rew: #stochastic rew delivery for correct lick

                    data.t_rew_l[trial] = time.time()*1000 - data._t_start_abs[trial]
                    water_L.Reward() #Deliver L reward
                    data.v_rew_l[trial] = reward_size
                    total_reward_L += reward_size

                else: #stochastic rew omission for correct lick
                    tone_wrong.Play()

                response = 'L' #record response
                performance += 1
                correct_trials.append(1)
                correct_side.append('L')
                    
                break

            elif sum(lick_port_R._licks[(length_R-1):]) > 0: #If first lick is R (incorrect)
                
                if np.random.rand() < p_rew: #stochastic rew omission for incorrect lick

                    tone_wrong.Play()

                else: #stochastic rew delivery for incorrect lick
                    
                    data.t_rew_r[trial] = time.time()*1000 - data._t_start_abs[trial]
                    water_R.Reward() #Deliver R reward
                    data.v_rew_r[trial] = reward_size
                    total_reward_R += reward_size

                response = 'R' #record response
                correct_trials.append(0)
                    
                break

        if response == 'N':
            tone_wrong.Play()
            correct_trials.append(0)

        data.response[trial] = response
        data.t_end[trial] = time.time()*1000 - data._t_start_abs[0] #store end time

    #Right trial:--------------------------------------------------------------
    else:

        if np.random.rand() < 0.5: #Choose which R tone will be played
            tone = R_tone_a
        else:
            tone = R_tone_b
        
        if ttl_experiment == 'y':
            TTL_marker.pulse() # Set a marker to align scans to trial start

        data.sample_tone[trial] = 'R' #Assign data type
        data.t_sample_tone[trial] = time.time()*1000 - data._t_start_abs[trial]
        tone.Play() #Play left tone
        data.sample_tone_end[trial] = time.time()*1000 - data._t_start_abs[trial]

        time.sleep(delay_length) #Sleep for delay_length

        response = 'N' #preset response to 'N'
        length_L = len(lick_port_L._licks)
        length_R = len(lick_port_R._licks)
        resp_window_end = time.time()*1000 + response_delay

        while time.time() * 1000 < resp_window_end:

                
            if sum(lick_port_R._licks[(length_R-1):]) > 0: #If first lick is R (correct)
                    
                if np.random.rand() < p_rew: #stochastic reward delivery

                    data.t_rew_r[trial] = time.time()*1000 - data._t_start_abs[trial]
                    water_R.Reward() #Deliver R reward
                    data.v_rew_r[trial] = reward_size
                    total_reward_R += reward_size

                else: #stochastic reward omission

                    tone_wrong.Play()

                response = 'R' #record response
                performance += 1
                correct_side.append('R')
                correct_trials.append(1)
                    
                break

            elif sum(lick_port_L._licks[(length_L-1):]) > 0: #If first lick is L (incorrect)

                if np.random.rand() < p_rew: #stochastic reward omission

                    tone_wrong.Play()

                else: #stochastic rew delivery for incorrect choice

                    data.t_rew_l[trial] = time.time()*1000 - data._t_start_abs[trial]
                    water_L.Reward() #Deliver R reward
                    data.v_rew_l[trial] = reward_size
                    total_reward_L += reward_size

                response = 'L'
                correct_trials.append(0)
                    
                break

        if response == 'N':
            tone_wrong.Play()
            correct_trials.append(0)

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
        
    data.freq[trial] = tone.freq #store tone frequency
    data.multipulse[trial] = tone.multi_pulse #store whether multipulse(1) or single pulse(0)

    data.freq_rule[trial] = freq_rule #store whether freq(1) or pulse(0) rule is in effect
    data.left_port[trial] = left_port #store port assighment of tones
    #if freq rule, left_port=1 means highfreq on left port
    #if pulse rule, left_port=1 means multipulse on left port

    print(f'Performance: {performance}/{trial+1}') #print performance/total trials to console

    if len(correct_trials) > 8 and sum(correct_trials[-8:]) == 0:
        #if 8 unrewarded trials in a row, deliver rewards through both ports.
        L_tone_a.Play()
        water_L.Reward()
        supp_reward_L += reward_size
        time.sleep(1)
        R_tone_a.Play()
        water_R.Reward()
        supp_reward_R += reward_size
        time.sleep(1)
        correct_trials = []

    if correct_side[-5:] == ['L', 'L', 'L', 'L', 'L']:
        #if 5 rewards from L port in a row, deliver rewards through R port.
        for i in range(2):

            if np.random.rand() < 0.5:        
                R_tone_a.Play()
            else:
                R_tone_b.Play()
                
            water_R.Reward()
            supp_reward_R += reward_size
            time.sleep(1)
        correct_side.append('R') #Added so the supp rewards aren't triggered next trial

    elif correct_side[-5:] == ['R', 'R', 'R', 'R', 'R']:
        #if 5 rewards from R port in a row, deliver rewards through L port
        for i in range(2):
            
            if np.random.rand() < 0.5:        
                L_tone_a.Play()
            else:
                L_tone_b.Play()
                
            water_L.Reward()
            supp_reward_L += reward_size
            time.sleep(1)
        correct_side.append('L') #Added so the supp rewards aren't triggered next trial

    if sum(correct_trials[-20:]) >= 18: #if 18 or more correct responses over last 20 trials
           
        correct_trials = [] #reset rewarded_trials
           
        freq_rule = not freq_rule #reverse task set (rule)
        left_port = np.random.randint(0,2) #randomly assign port (0/1)
        
        print('-------------------RULE SWITCH-------------------')
        print(f'freq_rule = {freq_rule}. left_port = {left_port}')

        #-------- Re-assign tones ----------
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

    ITI_ = 0
    while ITI_ > 12 or ITI_ < 8:
        ITI_ = np.random.exponential(scale = 10) #randomly select a new inter-trial interval

    time.sleep(ITI_) #wait for the length of the inter-trial interval

for i in range(2):
    L_tone_a.Play()
    R_tone_a.Play()

camera.stop_preview()

print(f'Total L reward: {total_reward_L} uL + {supp_reward_L}')
print(f'Total R reward: {total_reward_R} uL + {supp_reward_R}')
print(f'Total reward: {total_reward_L+supp_reward_L+total_reward_R+supp_reward_R}uL')
data.Store() #store the data in a .hdf5 file
data.Rclone() #move the .hdf5 file to "temporary-data folder on Desktop and
                #then copy to the lab google drive.

#delete the .wav files created for the experiment
lowfreq_singlepulse.Delete()
lowfreq_multipulse.Delete()
highfreq_singlepulse.Delete()
highfreq_multipulse.Delete()
tone_wrong.Delete()
