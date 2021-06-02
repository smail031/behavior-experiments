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
import getpass
import matplotlib.pyplot as plt
import h5py
from pygame import mixer


#------------------------------------------------------------------------------
#Define some classes!
#------------------------------------------------------------------------------

class tones():

    def __init__(self, frequency, tone_length, pulse_length):

        #Create a string that will be the name of the .wav file
        self.name = f'{frequency}Hz_{pulse_length}sec'
        self.freq = frequency
        self.tone_length = tone_length
        self.pulse_length = pulse_length
        self.pulse_number = tone_length/(2*pulse_length) # 2 because of the interpulse interval

        if self.tone_length == self.pulse_length: #determine if single or multi pulse tone
            self.multi_pulse = False
        else:
            self.multi_pulse = True

        if self.multi_pulse == False:
            #create a waveform called self.name from frequency and pulse_length
            os.system(f'sox -V0 -r 44100 -n -b 8 -c 2 {self.name}.wav synth {self.pulse_length} sin {self.freq} vol -20dB')

        elif self.multi_pulse == True:
            #create an empty wav file that will be the inter-pulse interval
            os.system(f'sox -V0 -r 44100 -n -b 8 -c 2 pulse.wav synth {self.pulse_length} sin {self.freq} vol -20dB') #tone
            os.system(f'sox -V0 -r 44100 -n -b 8 -c 2 interpulse.wav synth {self.pulse_length} sin {self.freq} vol -150dB') #silent interpulse interval

            #string with pulse/interpulse repeated for number of pulses
            concat_files = ' pulse.wav interpulse.wav' * int(self.pulse_number)

            os.system(f'sox{concat_files} {self.name}.wav')

            os.system(f'rm pulse.wav') #delete the pulse and interpulse, no longer useful.
            os.system(f'rm interpulse.wav')

        self.sound = mixer.Sound(f'{self.name}.wav')

    def Play(self):
 
        self.sound.play() #play the .wav file
        time.sleep(self.tone_length) #wait for it to end before continuing

    def Delete(self):
        # Delete the wav file
        os.system(f'rm {self.name}.wav')


class data():

    def __init__(self, protocol_description, n_trials, mouse_number, block_number, experimenter, mouse_weight):
        '''
        Creates an instance of the class Data which will store parameters for
        each trial, including lick data and trial type information.

        Parameters
        -------
        n_trials  : int
            Specifies the number of trials to initialize
        block_number : str
            Specifies the current trial block number for proper file storage

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

        self.mouse_number = mouse_number
        self.n_trials = n_trials
        self.block_number = block_number
        self.protocol_description = protocol_description
        self.experimenter = experimenter
        self.mouse_weight = mouse_weight

        self.exp_quality = '' #'y' if experiment was good, 'n' if there were problems.
        self.exp_msg = '' #if problems, user will explain. 

        self.t_experiment = time.strftime("%Y-%m-%d__%H:%M:%S",
                                     time.localtime(time.time()))
        self.date_experiment = time.strftime("%Y-%m-%d",
                                     time.localtime(time.time()))
        self.t_start = np.empty(self.n_trials) #start times of each trial
        self.t_end = np.empty(self.n_trials)

        self._t_start_abs = np.empty(self.n_trials) #Internal var. storing abs.
                            #start time in seconds for direct comparison with
                            #time.time()

        self.sample_tone = np.empty(self.n_trials, dtype = 'S1') #L or R, stores the trial types
        self.t_sample_tone = np.empty(self.n_trials) #stores the tone times relative to trial start.
        self.sample_tone_end = np.empty(self.n_trials)

        self.t_go_tone = np.empty(self.n_trials) #stores the times of go tones.
        self.go_tone_end = np.empty(self.n_trials)

        self.response = np.empty(self.n_trials, dtype = 'S1') #L, R, or N, stores
                                        #the animal's responses for each trial.

        self.lick_r = np.empty(self.n_trials, dtype = dict) #stores licks from R lickport
        self.lick_l = np.empty_like(self.lick_r) #stores licks from L lickport

        self.v_rew_l = np.empty(self.n_trials) #stores reward volumes from L lickport
        self.v_rew_l.fill(np.nan)
        self.t_rew_l = np.empty(self.n_trials) #stores reward times from L lickport
        self.t_rew_l.fill(np.nan) #fills t_rew_l with nan since not all trials will be rewarded.
        self.v_rew_r = np.empty(self.n_trials) #stores reward volumes from L lickport
        self.v_rew_r.fill(np.nan)
        self.t_rew_r = np.empty(self.n_trials) #stores reward times from L lickport
        self.t_rew_r.fill(np.nan) #fills t_rew_r with nan since not all trials will be rewarded.

        self.freq = np.empty(self.n_trials) #stores freq of presented tone in Hz
        self.multipulse = np.empty(self.n_trials) #stores whether presented tone is multipulse(1) or singlepulse(0)
        
        self.freq_rule = np.empty(self.n_trials) #stores whether freq(1) or pulse(0) rule for each trial
        self.left_port = np.empty(self.n_trials) #stores port assignment of tones
        #if freq rule, left_port=1 means highfreq on left port
        #if pulse rule, left_port=1 means multipulse on left port

        self.filename = 'ms' + str(self.mouse_number) + '_' + str(self.date_experiment) + '_' + 'block' + str(self.block_number) + '.hdf5'

    def Store(self):

        if os.path.exists(self.filename) and not force:
            raise IOError(f'File {self.filename} already exists.')

        with h5py.File(self.filename, 'w') as f:
            #Set attributes of the file
            f.attrs['animal'] = self.mouse_number
            f.attrs['time_experiment'] = self.t_experiment
            f.attrs['protocol_description'] = self.protocol_description
            f.attrs['experimenter'] = self.experimenter
            f.attrs['mouse_weight'] = self.mouse_weight
            f.attrs['experimental_quality'] = self.exp_quality
            f.attrs['experimental_message'] = self.exp_msg

            dtint = h5py.special_dtype(vlen = np.dtype('int32')) #Predefine variable-length
                                                            #dtype for storing t, volt
            dtfloat = h5py.special_dtype(vlen = np.dtype('float'))


            t_start = f.create_dataset('t_start', data = self.t_start)
            t_end = f.create_dataset('t_end', data = self.t_end)

            response = f.create_dataset('response', data = self.response, dtype = 'S1')

            #Create data groups for licks, tones and rewards.
            lick_l = f.create_group('lick_l')
            lick_r = f.create_group('lick_r')

            sample_tone = f.create_group('sample_tone')

            go_tone = f.create_group('go_tone')

            rew_l = f.create_group('rew_l')
            rew_r = f.create_group('rew_r')

            rule = f.create_group('rule') #stores rules and tone assignments

            #Preinitialize datasets for each sub-datatype within licks, tones
            #and rewards
            lick_l_t = lick_l.create_dataset('t', (self.n_trials,), dtype = dtfloat)
            lick_l_volt = lick_l.create_dataset('volt', (self.n_trials,), dtype = dtint)
            lick_r_t = lick_r.create_dataset('t', (self.n_trials,), dtype = dtfloat)
            lick_r_volt = lick_r.create_dataset('volt', (self.n_trials,), dtype = dtint)

            sample_tone_t = sample_tone.create_dataset('t', data = self.t_sample_tone, dtype = 'f8')
            sample_tone_type = sample_tone.create_dataset('type', data = self.sample_tone, dtype = 'S1')
            sample_tone_end = sample_tone.create_dataset('end', data = self.sample_tone_end, dtype = 'f8')
            sample_tone_freq = sample_tone.create_dataset('freq', data = self.freq, dtype=int)
            sample_tone_multipulse = sample_tone.create_dataset('multipulse', data = self.multipulse)

            go_tone_t = go_tone.create_dataset('t', data = self.t_go_tone)
            go_tone_end = go_tone.create_dataset('length', data = self.go_tone_end)

            rew_l_t = rew_l.create_dataset('t', data = self.t_rew_l)
            rew_l_v = rew_l.create_dataset('volume', data = self.v_rew_l)
            rew_r_t = rew_r.create_dataset('t', data = self.t_rew_r)
            rew_r_v = rew_r.create_dataset('volume', data = self.v_rew_r)

            freq_rule = rule.create_dataset('freq_rule', data = self.freq_rule)
            left_port = rule.create_dataset('left_port', data = self.left_port)

            for trial in range(self.n_trials):
                lick_l_t[trial] = self.lick_l[trial]['t']
                lick_l_volt[trial] = self.lick_l[trial]['volt']
                lick_r_t[trial] = self.lick_r[trial]['t']
                lick_r_volt[trial] = self.lick_r[trial]['volt']

            #Finally, store metadata for each dataset/groups
            lick_l.attrs['title'] = 'Lick signal acquired from the left \
                lickport; contains times (s) and voltages (arb. units)'
            lick_r.attrs['title'] = 'Lick signal acquired from the right \
                lickport; contains times (s) and voltages (arb. units)'
            sample_tone.attrs['title'] = 'Information about the delivered tones each \
                trial; contains times (s) and tone-type (a string denoting \
                whether the tone was large, small or nonexistent)'
            rew_l.attrs['title'] = 'Reward delivered to the left lickport; \
                contains time of reward (s) and its volume (uL)'
            rew_r.attrs['title'] = 'Reward delivered to the right lickport; \
                contains time of reward (s) and its volume (uL)'
            t_start.attrs['title'] = 'When the trial begins (s)'
            t_end.attrs['title'] = 'When the trial ends (s)'
            rule.attrs['title'] = 'Rule and port assignment. Freq_rule(1) -> freq rule; freq_rule(0) -> pulse rule. If freq rule, left_port(1) -> highfreq on left port; if pulse rule, left_port(1) -> multipulse on left port.'

    def Rclone(self):
        #find yesterday's data for this mouse
        yesterday_files = [fname for fname in os.listdir('/home/pi/Desktop/yesterday_data') if self.mouse_number in fname]

        for fname in yesterday_files: #move yesterday's files to temp data folder
            os.system(f'mv /home/pi/Desktop/yesterday_data/{fname} /home/pi/Desktop/temporary-data')

        #move current file to yesterday_data folder
        os.system(f'mv /home/pi/Desktop/behavior-experiments/behavior-experiments/{self.filename} /home/pi/Desktop/yesterday_data')
        #create folder on gdrive for today's data and copy file into that folder
        os.system(f'rclone mkdir gdrive:/Sebastien/Dual_Lickport/Mice/{self.mouse_number}')
        os.system(f'rclone mkdir gdrive:/Sebastien/Dual_Lickport/Mice/{self.mouse_number}/{self.date_experiment}')
        os.system(f'rclone copy /home/pi/Desktop/yesterday_data/{self.filename} gdrive:/Sebastien/Dual_Lickport/Mice/{self.mouse_number}/{self.date_experiment}')


class stepper():

    def __init__(self, enablePIN, directionPIN, stepPIN, emptyPIN):
        self.enablePIN = enablePIN
        self.directionPIN = directionPIN
        self.stepPIN = stepPIN
        self.emptyPIN = emptyPIN

        GPIO.setup(self.enablePIN, GPIO.OUT, initial=1)
        GPIO.setup(self.directionPIN, GPIO.OUT, initial=0)
        GPIO.setup(self.stepPIN, GPIO.OUT, initial=0)
        GPIO.setup(self.emptyPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def Motor(self, direction, steps):
        GPIO.output(self.enablePIN, 0) #enable the stepper motor
        GPIO.output(self.directionPIN, direction) #set direction

        for i in range(int(steps)): #move in "direction" for "steps"
            GPIO.output(self.stepPIN, 1)
            time.sleep(0.0001)
            GPIO.output(self.stepPIN, 0)
            time.sleep(0.0001)

        self.Disable() #disable stepper (to prevent overheating)

    def Reward(self,):
        steps = 400 #Calculate the number of steps needed to deliver
                                #volume. 400 steps gives 8.2uL
        if GPIO.input(self.emptyPIN):
            self.Motor(1, steps) #push syringe for "steps" until the empty pin
                                    #is activated.
        else:
            print('the syringe is empty')

    def Refill(self):

        while GPIO.input(self.emptyPIN): #Push syringe and check every 200
                                        #whether the empty pin is activated.
            self.Motor(1, 200)

        print('the syringe is empty')

        self.Motor(0, 96000) #Pull the syringe for 96000 steps, ~3mL.

    def Disable(self):

        GPIO.output(self.enablePIN, 1) #disable stepper (to prevent overheating)


class lickometer():

    def __init__(self, pin,):
        self._licks = []
        self._t_licks = []
        self.num_samples = 0
        self.pin = pin
        self.GPIO_setup()

    def GPIO_setup(self):
        #Set up the GPIO pin you will be using as input
        GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

    def Lick(self, sampling_rate, sampling_duration):
        #records the licks at a given sampling rate
        self._licks = []
        self._t_licks = []

        #calculate the number of samples needed
        self.num_samples = int(sampling_duration * sampling_rate)

        for i in range(self.num_samples):

            if GPIO.input(self.pin):
                #register lick
                self._licks.append(1)
                self._t_licks.append(time.time()*1000)

            else:
                #register no lick
                self._licks.append(0)
                self._t_licks.append(time.time()*1000)

            #wait for next sample and update step
            time.sleep(1/sampling_rate)

class servo():
    #Controls a servo that will adjust the lickport position relative to the
    #animal.

    def __init__(self, pin):
        self.pin = pin
        self.GPIO_setup()

    def GPIO_setup(self):
        #Set up the GPIO pin you will be using as input
        GPIO.setup(self.pin, GPIO.OUT)
        self.position = GPIO.PWM(self.pin, 50)  # GPIO 17 for PWM with 50Hz
        self.position.start(0)  # Initialization

    def Adjust(self, PWM):

        self.position.ChangeDutyCycle(PWM)

class ttl():
    def __init__(self, pin, pulse_length):
        self.pin = pin
        self.pulse_length = pulse_length
        self.GPIO_setup()

    def GPIO_setup(self):
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, False)

    def pulse(self):
        GPIO.output(self.pin, True)

        time.sleep(self.pulse_length)

        GPIO.output(self.pin, False)
