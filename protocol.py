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
#import _pickle as pickle
import matplotlib.pyplot as plt
import h5py

#------------------------------------------------------------------------------
#Set experimental parameters:
#------------------------------------------------------------------------------

mouse_number = input('mouse number: ' ) #asks user for mouse number

num_trial = 2 #number of trials in this block
delay_length = 1 #length of delay between sample tone and go cue, in sec

L_tone_freq = 1000 #frequency of sample tone in left lick trials
R_tone_freq = 4000 #frequency of sample tone in right lick trials
go_tone_freq = 500 #frequency of go tone

reward_size = 0.01 #size of water reward, in mL


#------------------------------------------------------------------------------
#Define some classes!
#------------------------------------------------------------------------------

class Stim(object):

    def __init__(self,name,pin,io):
        self.name = name
        self.pin = pin
        self.io = io
        self.GPIOsetup()
        self._licks = []
        self._t_licks = []
        self.lickstep = 0
        self.num_samples = 0

    def __str__(self):
        return'The {} {} associated to pin {}'.format(self.io,self.name,self.pin)

    def GPIOsetup (self):
        #Set up the GPIO pins you will be using as inputs or outputs
        GPIO.setup(self.pin, self.io)

    def reward(self, size, rate = 1 ):

        #size            - Size of reward in ml
        #rate            - Rate of flow in ml/sec

        #Calculate the reward_delay (duration of reward delivery) based on the given parameters
        reward_delay = 1/rate * size

        #Turn on the water dispenser
        GPIO.output(self.pin, True)

        #You'll have to account for the time it
        #takes for the water to get to the mouthpiece
        #Control the size of the reward
        time.sleep(reward_delay)

        #Turn off the water dispenser
        GPIO.output(self.pin, False)

    def lick(self, sampling_rate, sampling_duration):
        #records the licks at a given sampling rate
        self._licks = []
        self._t_licks = []

        #calculate the number of samples needed
        self.num_samples = int(sampling_duration * sampling_rate)

        for i in range(self.num_samples):

            if GPIO.input(self.pin):
                #register lick
                self._licks.append(1)
                self._t_licks.append(time.time())

            else:
                #register no lick
                self._licks.append(0)
                self._t_licks.append(time.time())

            #wait for next sample and update step
            time.sleep(1/sampling_rate)

class Tones():

    def __init__(self, frequency, tone_length):


        #Create a string that will be the name of the .wav file
        self.name = str(frequency) + 'Hz'
        self.freq = frequency

        #create a waveform called self.name from frequency and tone_length
        os.system(f'sox -V 0 -r 44100 -n -b 8 -c 2 {self.name}.wav synth {tone_length} sin {frequency} vol -10dB')

    def play(self):
        #send the wav file to the sound card
        os.system(f'play -V 0 {self.name}.wav')

class Data():

    def __init__(self, n_trials):
        '''
        Creates an instance of the class Data which will store parameters for
        each trial, including lick data and trial type information.

        Parameters
        -------
        n_trials  : int
            Specifies the number of trials to initialize


        Info
        --------
        self.t_experiment : str
            Stores the datetime where the behavior session starts

        self.t_start : np.ndarray
            Stores time of start for each trial

        self.tone : str
            Stores whether tone corresponded to 'l' or 'r'
        self.t_tone : np.ndarray
            Stores time of tone onset

        self.lick_r : dict
            A list of dictionaries where .lick_r[trial]['t'] stores the times
            of each measurement, and .lick_r[trial]['volt'] stores the voltage
            value of the measurement.
        self.v_rew_r : np.ndarray
            Stores reward volume
        self.t_rew_r : np.ndarray
            Stores time of reward onset

        '''

        self.t_experiment = time.strftime("%Y.%b.%d__%H:%M:%S",
                                     time.localtime(time.time()))
        self.t_start = np.empty(n_trials) #start times of each trial
        self.t_end = np.empty(n_trials)

        self._t_start_abs = np.empty(n_trials) #Internal var. storing abs.
                            #start time in seconds for direct comparison with
                            #time.time()

        self.tone = np.empty(n_trials, dtype = str) #L or R
        self.t_tone = np.empty(n_trials)

        self.lick_r = np.empty(n_trials, dtype = dict) #stores licks from R lickport
        self.lick_l = np.empty_like(self.lick_r) #stores licks from L lickport


        self.v_rew_l = np.empty(n_trials) #stores reward volumes from L lickport
        self.t_rew_l = np.empty(n_trials) #stores reward times from L lickport
        self.v_rew_r = np.empty(n_trials) #stores reward volumes from L lickport
        self.t_rew_r = np.empty(n_trials) #stores reward times from L lickport

    def _pkl_store(self, filename = None):
        if filename is None:
            filename = str(mouse_number) + str(self.t_experiment) + '.pkl'

        with open(filename, 'wb') as f:
            pickle.dump(self, f)

    def store(self, filename = None):
        if filename is None:
            filename = str(mouse_number) + str(self.t_experiment) + '.hdf5'

        with h5py.File(filename, 'w') as f:
            #Set attributes of the file
            f.attrs['animal'] = mouse_number
            f.attrs['time_experiment'] = self.t_experiment
            f.attrs['user'] = os.getlogin()

            dt = h5py.vlen_dtype(np.dtype('int32')) #Predefine variable-length
                                                #dtype for storing t, volt

            t_start = f.create_dataset('t_start', data = self.t_start)
            t_end = f.create_dataset('t_end', data = self.t_end)

            #Create data groups for licks, tones and rewards.
            lick_l = f.create_group('lick_l')
            lick_r = f.create_group('lick_r')

            tone = f.create_group('tone')

            rew_l = f.create_group('rew_l')
            rew_r = f.create_group('rew_r')

            #Preinitialize datasets for each sub-datatype within licks, tones
            #and rewards
            lick_l_t = lick_l.create_dataset('t', (n_trials,), dtype = dt)
            lick_l_volt = lick_l.create_dataset('volt', (n_trials,), dtype = dt)
            lick_r_t = lick_r.create_dataset('t', (n_trials,), dtype = dt)
            lick_r_volt = lick_r.create_dataset('volt', (n_trials,), dtype = dt)

            tone_t = tone.create_dataset('t', data = self.t_tone, dtype = 'f16')
            tone_type = tone.create_dataset('type', data = self.tone)

            rew_l_t = rew_l.create_dataset('t', data = self.t_rew_l)
            rew_l_v = rew_l.create_dataset('vol', data = self.v_rew_l)
            rew_r_t = rew_r.create_dataset('t', data = self.t_rew_r)
            rew_r_v = rew_r.create_dataset('vol', data = self.v_rew_r)

            for trial in range(n_trials):
                lick_l_t[trial] = self.lick_l[trial]['t']
                lick_l_volt[trial] = self.lick_l[trial]['volt']
                lick_r_t[trial] = self.lick_r[trial]['t']
                lick_r_t[trial] = self.lick_r[trial]['volt']

            #Finally, store metadata for each dataset/groups
            lick_l.attrs['title'] = 'Lick signal acquired from the left \
                lickport; contains times (s) and voltages (arb. units)'
            lick_r.attrs['title'] = 'Lick signal acquired from the right \
                lickport; contains times (s) and voltages (arb. units)'
            tone.attrs['title'] = 'Information about the delivered tones each \
                trial; contains times (s) and tone-type (a string denoting \
                whether the tone was large, small or nonexistent)
            rew_l.attrs['title'] = 'Reward delivered to the left lickport; \
                contains time of reward (s) and its volume (uL)
            rew_r.attrs['title'] = 'Reward delivered to the right lickport; \
                contains time of reward (s) and its volume (uL)
            t_start.attrs['title'] = 'When the trial begins (s)'
            t_ends.attrs['title'] = 'When the trial ends (s)'

    def plot(self, trial):
        '''
        parameters
        --------
        trial : int
            The trial to plot

        '''
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(self.lick_r[trial]['t'], self.lick_r[trial]['volt'], 'r')
        ax.plot(self.lick_l[trial]['t'], self.lick_l[trial]['volt'], 'g')

        ax.plot([self.t_tone, self.t_tone], [0, 5], 'k', linewidth = 2)

        ax.plot([self.t_rew_l, self.t_rew_l], [0, 5], 'b', linewidth = 2)
        ax.plot([self.t_rew_r, self.t_rew_r], [0, 5], 'b', linewidth = 2)

        plt.savefig('data_plt.pdf')


#******************************************************************************


#---------------
#Set experimental parameters:
#---------------

mouse_number = input('mouse number: ' ) #asks user for mouse number

num_trial = 2 #number of trials in this block
delay_length = 1 #length of delay between sample tone and go cue, in sec

L_tone_freq = 1000 #frequency of sample tone in left lick trials
R_tone_freq = 4000 #frequency of sample tone in right lick trials
go_tone_freq = 500 #frequency of go tone

reward_size = 0.01 #size of water reward, in mL

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
trials = np.arange(num_trial)
data = Data(num_trial)

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
