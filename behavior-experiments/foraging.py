#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 16:57:22 2019

@author: sebastienmaille
"""
protocol_description = '''In this protocol, a sample cue is immediately followed by a "go" cue. During
the response period, first lickport that registers a lick determines the animal's
response. Correct responses trigger reward delivery from the correct port, while
incorrect or null responses are unrewarded. Trial types (L/R) are determined
randomly prior to every trial.'''

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

response_delay = 2000 #length of time for animals to give response

go_tone_freq = 500 #frequency of go tone
go_tone_length = 0.1

reward_tone_freq = 4000
no_reward_tone_freq = 1000
reward_tone_length = 0.5

wrong_tone_freq = 12000

reward_size = 2.3 #size of water rewards in uL

block_length = 25 #number of trials with same L/R probability

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

#initialize the mixer (for tones) at the proper sampling rate.
mixer.init(frequency = 44100)

#create Stepper class instances for left and right reward delivery
water_L = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
water_R = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)

#create lickometer class instances for left and right lickometers
lick_port_L = core.lickometer(L_lickometer)
lick_port_R = core.lickometer(R_lickometer)

#create tones
tone_go = core.tones(go_tone_freq, go_tone_length)

tone_reward = core.tones(reward_tone_freq, reward_tone_length) #create a reward tone
tone_no_reward = core.tones(no_reward_tone_freq, reward_tone_length) #create a "no reward" tone

tone_wrong = core.tones(wrong_tone_freq, reward_tone_length)

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
rewarded_side = []
rewarded_trials = []

L_prob = 1
R_prob = 0

trial_counter  = 0

while trial_counter < n_trials:

    for trial in range(block_length):

        data._t_start_abs[trial] = time.time()*1000 #Set time at beginning of trial
        data.t_start[trial] = data._t_start_abs[trial] - data._t_start_abs[0]

        #create thread objects for left and right lickports
        thread_L = threading.Thread(target = lick_port_L.Lick, args = (1000, 5))
        thread_R = threading.Thread(target = lick_port_R.Lick, args = (1000, 5))


        thread_L.start() #Start threads for lick recording
        thread_R.start()

        time.sleep(0.5)

        data.t_go_tone[trial] = time.time()*1000 - data._t_start_abs[trial]
        tone_go.Play() #Play go tone
        data.go_tone_end[trial] = time.time()*1000 - data._t_start_abs[trial]

        response = 'N'
        length_L = len(lick_port_L._licks)
        length_R = len(lick_port_R._licks)
        response_window_end = time.time()*1000 + response_delay

        while time.time()*1000 < response_window_end:

            if sum(lick_port_L._licks[(length_L-1):]) > 0:
                if np.random.rand() < L_prob:
                    data.t_rew_l[trial] = time.time()*1000 - data._t_start_abs[trial]
                    water_L.Reward() #Deliver L reward
                    tone_reward.Play()
                    rewarded_trials.append(1)
                    rewarded_side.append('L')
                    data.v_rew_l[trial] = reward_size
                else:
                    tone_no_reward.Play()

                response = 'L'
                break

            elif sum(lick_port_R._licks[(length_R-1):]) > 0:
                if np.random.rand() < R_prob:
                    data.t_rew_r[trial] = time.time()*1000 - data._t_start_abs[trial]
                    water_R.Reward() #Deliver L reward
                    tone_reward.Play()
                    rewarded_trials.append(1)
                    rewarded_side.append('R')
                    data.v_rew_r[trial] = reward_size
                else:
                    tone_no_reward.Play()

                response = 'R'
                break

        if response == 'N':
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

        trial_counter += 1

        if len(rewarded_trials) > 8 and sum(rewarded_trials[-8:]) == 0:
            #if 8 unrewarded trials in a row, deliver rewards through both ports.
            for i in range(2):
                tone_reward.Play()
                water_L.Reward()
                supp_reward_L += reward_size
                rewarded_trials.append(1)
                time.sleep(1)
                tone_reward.Play()
                water_R.Reward()
                supp_reward_R += reward_size
                rewarded_trials.append(1)
                time.sleep(1)

        # if rewarded_side[-5:] == ['L', 'L', 'L', 'L', 'L']:
        #     #if 5 rewards from L port in a row, deliver rewards through R port.
        #     for i in range(4):
        #         tone_R.Play()
        #         water_R.Reward()
        #         supp_reward_R += reward_size
        #         time.sleep(1)
        #     rewarded_side.append('R')
        #
        # elif rewarded_side[-5:] == ['R', 'R', 'R', 'R', 'R']:
        #     #if 5 rewards from R port in a row, deliver rewards through L port
        #     for i in range(4):
        #         tone_L.Play()
        #         water_L.Reward()
        #         supp_reward_L += reward_size
        #         time.sleep(1)
        #     rewarded_side.append('L')

        ITI_ = 2
        time.sleep(ITI_)

    L_prob = 1-L_prob
    R_prob = 1-R_prob

for i in range(5): #Play an "alarm" at the end of the experiment.
    tone_go.Play()
    tone_go.Play()

camera.stop_preview()

print(f'Total L reward: {total_reward_L} + {supp_reward_L}uL')
print(f'Total R reward: {total_reward_R} + {supp_reward_R}uL')
print(f'Total reward: {total_reward_L+supp_reward_L+total_reward_R+supp_reward_R}uL')

data.Store() #store the data in a .hdf5 file
data.Rclone() #move the .hdf5 file to "temporary-data folder on Desktop and
                #then copy to the lab google drive.

#delete the .wav files created for the experiment
tone_go.Delete()
tone_reward.Delete()
tone_no_reward.Delete()
