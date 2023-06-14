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
import h5py
from pygame import mixer
import rclone
# ------------------------------------------------------------------------------
# Define some classes
# ------------------------------------------------------------------------------


class Tone:
    '''
    A parent class to handle auditory tones to be used during the task.

    Attributes:
    -----------
    self.name: str
        The filename of the corresponding wav file (e.g. '1000Hz.wav').

    self.tone_length: float
        The total duration (in seconds) of the tone.

    self.sound: object
        A pygame.mixer object corresponding to the tone.
    '''
    def generate_tone(self):
        '''
        Use the sox library to generate a wav file corresponding to this tone.
        '''
        raise NotImplementedError

    def play(self):
        '''Play the sound over the speakers.'''
        self.sound.play()
        time.sleep(self.tone_length)

    def delete(self):
        ''' Delete the file from the local directory.'''
        os.system(f'rm {self.name}')


class PureTone(Tone):
    '''
    A tone with a single frequency, playing continuously from both channels for
    a given amount of time.
    '''
    def __init__(self, frequency: int, tone_length: float, vol=-20):
        self.freq = frequency
        self.tone_length = tone_length
        self.loc = 'B'
        self.vol = vol
        self.name = f'{self.freq}Hz.wav'
        self.generate_tone()
        self.sound = mixer.Sound(self.name)

    def generate_tone(self):
        os.system(f'sox -V0 -r 44100 -n -b 8 -c 1 {self.name} '
                  f'synth {self.tone_length} sin {self.freq} vol {self.vol}dB')


class LocalizedTone(Tone):
    '''
    A tone with a single frequency, playing continuously from a single channel
    (left or right) for a given amount of time.
    '''
    def __init__(self, frequency, tone_length, loc, vol=-20):
        self.freq = frequency
        self.tone_length = tone_length
        self.loc = loc
        self.vol = vol
        self.name = f'{self.freq}Hz_{self.loc}.wav'
        self.generate_tone()
        self.sound = mixer.Sound(self.name)

    def generate_tone(self):
        # Generate audible and silent channels
        os.system(f'sox -V0 -r 44100 -n -b 8 -c 1 audible.wav '
                  f'synth {self.tone_length} sin {self.freq} vol {self.vol}dB')
        os.system('sox -V0 -r 44100 -n -b 8 -c 1 silent.wav synth 2 sin '
                  '4000 vol -200dB')

        if self.loc == 'L':
            # Merge with audible in L channel and silent in R channel.
            os.system(f'sox -M audible.wav silent.wav {self.name}')

        elif self.loc == 'R':
            # Merge with silent in L channel and audible in R channel.
            os.system(f'sox -M silent.wav audible.wav {self.name}')

        os.system('rm silent.wav')
        os.system('rm audible.wav')


class PulsingTone(Tone):
    '''
    A tone of a given frequency pulsing on and off at a given frequency.
    (tone_length%(stim_length*2)) should be equal to 0.
    '''
    def __init__(self, frequency, tone_length, stim_length, vol=-20):
        self.freq = frequency
        self.tone_length = tone_length
        self.stim_length = stim_length
        self.vol = vol
        self.name = f'{self.freq}Hz_pulsing.wav'

    def generate_tone(self):
        pulse_number = self.tone_length/(2*self.stim_length)
        # Multiplying pulse length by 2 because of the inter-pulse interval
        # Generate wav files for pulse and silent inter-pulse interval
        os.system(f'sox -V0 -r 44100 -n -b 8 -c 1 pulse.wav synth '
                  f'{self.stim_length} sin {self.freq} vol -20dB')
        os.system('sox -V0 -r 44100 -n -b 8 -c 1 interpulse.wav synth '
                  '{self.stim_length} sin {self.freq} vol -150dB')
        # Generate a string with sequence of pulses to be to the tone
        concat_files = ' pulse.wav interpulse.wav' * int(self.stim_number)
        # Concatenate the pulse and IPI into a single file and delete originals
        os.system(f'sox{concat_files} {self.name}.wav')
        os.system('rm pulse.wav')
        os.system('rm interpulse.wav')

class PureTone2(Tone):
    '''
    A tone with a single frequency, playing continuously from both channels for
    a given amount of time.
    '''
    def __init__(self, n_trials, frequency: int, tone_length: float, vol=-20):
        self.n_trials = n_trials
        self.freq = frequency
        self.tone_length = tone_length
        self.loc = 'B'
        self.vol = vol
        self.name = f'{self.freq}Hz.wav'
        self.generate_tone()
        self.generate_data()
        self.sound = mixer.Sound(self.name)

    def generate_tone(self):
        os.system(f'sox -V0 -r 44100 -n -b 8 -c 1 {self.name} '
                  f'synth {self.tone_length} sin {self.freq} vol {self.vol}dB')

    def generate_data(self):
        '''
        Generates a dictionary self.data, which temprarily stores all relevant
        data that will be stored in the hdf5 data file.
        '''
        self.data = {}
        self.data['frequency'] = self.frequency
        self.data['duration'] = self.tone_length
        self.data['location'] = self.loc
        
        self.data['tone_onset'] = np.empty(self.n_trials, dtype=float)*np.nan
        self.data['tone_offset'] = np.empty(self.n_trials, dtype=float)*np.nan
 
class data():

    def __init__(self, protocol_name, protocol_description, n_trials,
                 mouse_number, block_number, experimenter, mouse_weight,
                 countdown=np.nan):
        '''
        Tracks relevant experimental parameters and data, to be stored in an
        HDF5 file and uploaded to a remote drive.

        Parameters:
        -----------
        protocol_name: str
            Name given to the current experimental protocol (eg 'classical')

        protocol_description: str
            A long string describing the current experiment in plain words.

        n_trials: int
            Number of trials in this experiment.

        mouse_number: int
            ID number of the mouse.

        block_number: str
            Intra-day block number for this experiment

        experimenter: str
            Initials of the experimenter whose lab book contains relevant info.

        mouse_weight: float
            Weight of the mouse (grams) measured prior to the experiment.

        Info:
        -----
        *All parameters are stored as attributes with the same name.*

        self.t_experiment: str
            Date and time for the start of the experiment.

        self.date_experiment: str
            Date of the experiment (for separate uses than above).

        self.filename: str
            Name of HDF5 file in which data will be stored.

        self.t_start: np.ndarray
            Start time for each trial.

        self.t_end: np.ndarray
            End time for each trial.

        self._t_start_abs: np.ndarray
            Internal variable, absolute start time for each trial.

        self.sample_tone: np.ndarray
            Stores whether the presented tone is associated with L or R port

        self.t_sample_tone: np.ndarray
            Time of tone onset relative to trial start

        self.sample_tone_end: np.ndarray
            Time of tone end relative to trial start

        self.response: np.ndarray
            Response(L/R/N; port registering first lick during response period)
            of the mouse on each trial.

        self.lick_r(l): dict
            A list of dictionaries where .lick_r(l)[trial]['t'] stores the times
            of each measurement, and .lick_r(l)[trial]['volt'] stores the voltage
            value of the measurement.

        self.v_rew_r(l) : np.ndarray
            Reward volume on each trial for r(l) lickport

        self.t_rew_r(l) : np.ndarray
            Time of reward delivery for r(l) lickport

        self.freq: np.ndarray
            Frequency (Hz) of tone presented on each trial.

        self.loc: np.ndarray
            Location of origin (in azimuth plane; L/R) of tone for each trial.

        self.multipulse: np.ndarray
            Indicates whether the presented tone is pulsed(1) or solid(0)

        self.freq_rule: np.ndarray
            Indicates, on each trial, whether the relevant cue dimension is
            frequency(1) or pulsing/location(0).

        self.left_port: np.ndarray
            Indicates, on each trial, the mapping between tones and
            corresponding ports. If freq rule, left_port==1 means the high
            frequency tone is mapped to L port and vice versa. If pulse rule,
            left_port==1 means pulsing tone is mapped to left port. If location
            rule, left_port==1 means tone origins match associated port.

        self.countdown: np.ndarray
            Once the performance criterion has been reached, keeps a running
            (trial-by-trial) countdown of trials until a rule switch will
            take place. If the mouse hasn't yet met criterion, each value
            will be set to None.

        self.exp_quality: str
            Indicates whether('y') or not('n') the experiment went smoothly.
            If there were any issues, the user can describe them in exp_msg.

        self.exp_msg: str
            Stores a user-generated string, in plain words, describing what
            went wrong with the experiment.

        self.total_reward: float
            Total volume (uL) of water received during the session.


        '''

        # Store method parameters as attributes
        self.protocol_name = protocol_name
        self.protocol_description = protocol_description
        self.n_trials = n_trials
        self.mouse_number = mouse_number
        self.block_number = block_number
        self.experimenter = experimenter
        self.mouse_weight = mouse_weight

        self.t_experiment = time.strftime("%Y-%m-%d__%H:%M:%S",
                                          time.localtime(time.time()))
        self.date_experiment = time.strftime("%Y-%m-%d",
                                             time.localtime(time.time()))
        self.filename = ('ms' + str(self.mouse_number) + '_'
                         + str(self.date_experiment) + '_' + 'block'
                         + str(self.block_number) + '.hdf5')

        # Initialize some empty attributes that will store experimental data
        self.t_start = np.empty(self.n_trials)
        self.t_end = np.empty(self.n_trials)
        self._t_start_abs = np.empty(self.n_trials)

        self.t_ttl = np.empty(self.n_trials)

        self.sample_tone = np.empty(self.n_trials, dtype='S1')
        self.t_sample_tone = np.empty(self.n_trials)
        self.sample_tone_end = np.empty(self.n_trials)

        self.response = np.empty(self.n_trials, dtype='S1')
        self.lick_r = np.empty(self.n_trials, dtype=dict)
        self.lick_l = np.empty_like(self.lick_r)

        self.v_rew_l = np.empty(self.n_trials) * np.nan
        self.t_rew_l = np.empty(self.n_trials) * np.nan
        self.v_rew_l_supp = np.empty(self.n_trials) * np.nan
        self.t_rew_l_supp = np.empty(self.n_trials) * np.nan
        self.v_rew_r = np.empty(self.n_trials) * np.nan
        self.t_rew_r = np.empty(self.n_trials) * np.nan
        self.v_rew_r_supp = np.empty(self.n_trials) * np.nan
        self.t_rew_r_supp = np.empty(self.n_trials) * np.nan

        self.freq = np.empty(self.n_trials)
        self.loc = np.empty(self.n_trials, dtype='S1')
        self.multipulse = np.empty(self.n_trials)

        self.p_index = np.empty(self.n_trials)
        self.left_port = np.empty(self.n_trials)
        self.countdown = np.empty(self.n_trials, dtype=np.single)
        self.opto_start = np.empty(self.n_trials) * np.nan
        self.opto_end = np.empty(self.n_trials) * np.nan
        self.expert = np.empty(self.n_trials, dtype=bool)
        self.rew_prob = np.empty(self.n_trials, dtype=np.double)

        self.iti_length = np.empty(self.n_trials)

        self.exp_quality = ''
        self.exp_msg = ''
        self.total_reward = 0

    def Store(self):
        '''
        Stores all relevant experimental data and parameters in an HDF5 file.
        '''

        if os.path.exists(self.filename):
            raise IOError(f'File {self.filename} already exists.')

        with h5py.File(self.filename, 'w') as f:
            # Set experimental parameters as HDF% attributes
            f.attrs['animal'] = self.mouse_number
            f.attrs['time_experiment'] = self.t_experiment
            f.attrs['protocol_name'] = self.protocol_name
            f.attrs['protocol_description'] = self.protocol_description
            f.attrs['experimenter'] = self.experimenter
            f.attrs['mouse_weight'] = self.mouse_weight
            f.attrs['experimental_quality'] = self.exp_quality
            f.attrs['experimental_message'] = self.exp_msg
            f.attrs['total_reward'] = self.total_reward

            # Predefine variable-length dtype for storing t, volt
            dtbool = h5py.special_dtype(vlen=np.dtype('bool'))
            dtfloat = h5py.special_dtype(vlen=np.dtype('float'))
            t_start = f.create_dataset('t_start', data=self.t_start)
            t_end = f.create_dataset('t_end', data=self.t_end)
            opto_start = f.create_dataset('opto_start', data=self.opto_start)
            opto_end = f.create_dataset('opto_end', data=self.opto_end)
            f.create_dataset('iti_length', data=self.iti_length)

            f.create_dataset('response', data=self.response,
                             dtype='S1')
            # Create HDF5 groups for licks, tones and rewards.
            lick_l = f.create_group('lick_l')
            lick_r = f.create_group('lick_r')

            ttl = f.create_group('ttl_marker')

            sample_tone = f.create_group('sample_tone')

            rew_l = f.create_group('rew_l')
            rew_r = f.create_group('rew_r')

            rule = f.create_group('rule')  # stores rules and tone assignments

            # Preinitialize datasets for each sub-datatype within licks, tones
            # and rewards
            lick_l_t = lick_l.create_dataset('t', (self.n_trials,),
                                             dtype=dtfloat)
            lick_l_volt = lick_l.create_dataset('volt', (self.n_trials,),
                                                dtype=dtbool)
            lick_r_t = lick_r.create_dataset('t', (self.n_trials,),
                                             dtype=dtfloat)
            lick_r_volt = lick_r.create_dataset('volt', (self.n_trials,),
                                                dtype=dtbool)

            ttl.create_dataset('t_ttl', data=self.t_ttl)

            sample_tone.create_dataset('t', data=self.t_sample_tone,
                                       dtype='f8')
            sample_tone.create_dataset('type', data=self.sample_tone,
                                       dtype='S1')
            sample_tone.create_dataset('end', data=self.sample_tone_end,
                                       dtype='f8')
            sample_tone.create_dataset('freq', data=self.freq, dtype=int)
            sample_tone.create_dataset('location', data=self.loc)
            sample_tone.create_dataset('multipulse', data=self.multipulse)

            rew_l.create_dataset('t', data=self.t_rew_l)
            rew_l.create_dataset('volume', data=self.v_rew_l)
            rew_l.create_dataset('supp_t', data=self.t_rew_l_supp)
            rew_l.create_dataset('supp_volume', data=self.v_rew_l_supp)
            rew_r.create_dataset('t', data=self.t_rew_r)
            rew_r.create_dataset('volume', data=self.v_rew_r)
            rew_r.create_dataset('supp_t', data=self.t_rew_r_supp)
            rew_r.create_dataset('supp_volume', data=self.v_rew_r_supp)

            rule.create_dataset('p_index', data=self.p_index)
            rule.create_dataset('left_port', data=self.left_port)
            rule.create_dataset('countdown', data=self.countdown)
            rule.create_dataset('expert', data=self.expert)
            rule.create_dataset('rew_prob', data=self.rew_prob)

            for trial in range(self.n_trials):
                lick_l_t[trial] = self.lick_l[trial]['t']
                lick_l_volt[trial] = self.lick_l[trial]['volt']
                lick_r_t[trial] = self.lick_r[trial]['t']
                lick_r_volt[trial] = self.lick_r[trial]['volt']

            # Finally, store metadata for each dataset/groups
            lick_l.attrs['title'] = ('Voltage(AU) and corresponding'
                                     'timestamps(s) from the left lickport')
            lick_r.attrs['title'] = ('Voltage(AU) and corresponding'
                                     'timestamps(s) from the right lickport')
            sample_tone.attrs['title'] = ('Information relevant to the sample'
                                          'tones presented each trial; contains'
                                          'times(s) and tone type ("correct"'
                                          'side, frequency, location, pulsing)')
            rew_l.attrs['title'] = ('Volume (uL) and delivery times for rewards'
                                    'delivered to the left lickport')
            rew_r.attrs['title'] = ('Volume (uL) and delivery times for rewards'
                                    'delivered to the left lickport')
            t_start.attrs['title'] = 'Start time for each trial (s)'
            t_end.attrs['title'] = 'End time for each trial (s)'
            opto_start.attrs['title'] = 'time stamp of when opto stimulation begins'
            opto_end.attrs['title'] = 'time stamp of when opto stimulation ends'
            rule.attrs['title'] = ('Rule and port assignment. '
                                   'Freq_rule(1) -> freq rule; '
                                   'freq_rule(0) -> pulse rule. If freq rule, '
                                   'left_port(1) -> highfreq on left port; '
                                   'if pulse rule, left_port(1) -> multipulse'
                                   'on left port.')

    def Rclone(self):
        '''
        Use rclone to upload the HDF5 data file to a remote drive.
        '''
        # Find yesterday's data for this mouse
        yesterday_files = [fname for fname in
                           os.listdir('/home/pi/Desktop/yesterday_data')
                           if self.mouse_number in fname]

        for fname in yesterday_files:  # Move files to temp data folder
            os.system(f'mv /home/pi/Desktop/yesterday_data/{fname} '
                      '/home/pi/Desktop/temporary-data')

        # Move current file to yesterday_data folder
        os.system(f'mv /home/pi/Desktop/behavior-experiments/'
                  f'behavior-experiments/{self.filename} '
                  f'/home/pi/Desktop/yesterday_data')
        # Create remote folder for today's data and copy file into that folder
        os.system(f'rclone mkdir data1:"Behaviour data/Jennifer/'
                  f'all mice/{self.mouse_number}"')
        os.system(f'rclone mkdir data1:"Behaviour data/Jennifer/'
                  f'all mice/{self.mouse_number}/{self.date_experiment}"')
        os.system(f'rclone copy /home/pi/Desktop/yesterday_data/{self.filename}'
                  f' data1:"Behaviour data/Jennifer/all mice/'
                  f'{self.mouse_number}/{self.date_experiment}"')

class Stepper():
    def __init__(self, n_trials, enablePIN, directionPIN, stepPIN, emptyPIN, side):
        self.n_trials = n_trials
        self.enablePIN = enablePIN
        self.directionPIN = directionPIN
        self.stepPIN = stepPIN
        self.emptyPIN = emptyPIN
        self.cont = False
        self.side = side

        GPIO.setup(self.enablePIN, GPIO.OUT, initial=1)
        GPIO.setup(self.directionPIN, GPIO.OUT, initial=0)
        GPIO.setup(self.stepPIN, GPIO.OUT, initial=0)
        GPIO.setup(self.emptyPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def generate_data(self):
        '''
        '''
        self.data = {}
        self.data['name'] = f'{self.side}_rewards'
        self.data['side'] = self.side
        self.data['volume'] = np.empty(self.n_trials, dtype=float)*np.nan
        self.data['steps'] = np.empty(self.n_trials, dtype=float)*np.nan
        self.data['']

        
class stepper():

    def __init__(self, enablePIN, directionPIN, stepPIN, emptyPIN):
        self.enablePIN = enablePIN
        self.directionPIN = directionPIN
        self.stepPIN = stepPIN
        self.emptyPIN = emptyPIN
        self.cont = False

        GPIO.setup(self.enablePIN, GPIO.OUT, initial=1)
        GPIO.setup(self.directionPIN, GPIO.OUT, initial=0)
        GPIO.setup(self.stepPIN, GPIO.OUT, initial=0)
        GPIO.setup(self.emptyPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def Motor(self, direction, steps):
        GPIO.output(self.enablePIN, 0)  # enable the stepper motor
        GPIO.output(self.directionPIN, direction)  # set direction

        # if GPIO.input(self.emptyPIN):

        for i in range(int(steps)):  # move in "direction" for "steps"
            GPIO.output(self.stepPIN, 1)
            time.sleep(0.0002)
            GPIO.output(self.stepPIN, 0)
            time.sleep(0.0002)

        # else:

            # print('the syringe is empty')
        self.Disable()  # disable stepper (to prevent overheating)

    def Reward(self,):
        steps = 250  # Calculate the number of steps needed to deliver
        # volume. 400 steps gives 8.2uL
        if GPIO.input(self.emptyPIN):
            self.Motor(1, steps)  # push syringe for "steps" until empty pin
            # is activated.
        else:
            print('the syringe is empty')

    def Refill(self):

        while GPIO.input(self.emptyPIN):  # Push syringe and check every 200
            # whether the empty pin is activated.
            self.Motor(1, 200)

        print('the syringe is empty')

        self.Motor(0, 30000)  # Pull the syringe for 60000 steps, ~3mL.

    def Disable(self):

        GPIO.output(self.enablePIN, 1)  # disable to prevent overheating

    def Run(self):
        self.start = True
        while self.start:

            self.cont = False
            while self.cont:

                if GPIO.input(self.emptyPIN):
                    self.Motor(1, 200)

    def empty(self):
        '''
        Empties the syringe pump.
        '''
        while GPIO.input(self.emptyPIN):  # Push syringe and check every 200
            # whether the empty pin is activated.
            self.Motor(1, 200)

        print('the syringe is empty')

    def fill(self):
        '''
        Fills the syringe pump.
        '''
        self.Motor(0, 60000)  # Pull the syringe for 60000 steps, ~3mL.


class lickometer():

    def __init__(self, pin,):
        self._licks = []
        self._t_licks = []
        self.num_samples = 0
        self.pin = pin
        self.GPIO_setup()

    def GPIO_setup(self):
        # Set up the GPIO pin you will be using as input
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def Lick(self, sampling_rate, sampling_duration):
        # records the licks at a given sampling rate
        self._licks = []
        self._t_licks = []

        # Calculate the number of samples needed.
        self.num_samples = int(sampling_duration * sampling_rate)

        for i in range(self.num_samples):

            if GPIO.input(self.pin):
                # register lick
                self._licks.append(True)
                self._t_licks.append(time.time()*1000)

            else:
                # register no lick
                self._licks.append(False)
                self._t_licks.append(time.time()*1000)

            # wait for next sample and update step
            time.sleep(1/sampling_rate)


class servo():
    # Controls a servo that will adjust the lickport position relative to the
    # animal.

    def __init__(self, pin):
        self.pin = pin
        self.GPIO_setup()

    def GPIO_setup(self):
        # Set up the GPIO pin you will be using as input
        GPIO.setup(self.pin, GPIO.OUT)
        self.position = GPIO.PWM(self.pin, 50)  # GPIO 17 for PWM with 50Hz
        self.position.start(0)  # Initialization

    def Adjust(self, PWM):

        self.position.ChangeDutyCycle(PWM)


class ttl():
    '''
    A class to handle communication between the RPi and other peripherals
    (e.g. laser scanning microscope) through TTL pulses.

    Attributes:
    -----------
    self.pin: int
        The GPIO pin through which pulses will be sent.

    self.opto_stim_length: float
        The length(sec) of TTL pulses.

    self.ISI_length: float
        The length(sec) of inter-stimulus-interval.

    self.total_length: float
        The length(sec) of total duration of opto per trial.
    '''
    def __init__(self, pin, opto_stim_length, ISI_length, total_length):
        self.pin = pin
        self.opto_stim_length = opto_stim_length
        self.ISI_length = ISI_length
        self.total_length = total_length
        self.pulsing = False
        # Setup GPIO pins for TTL pulses.
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, False)

    def pulsedata(self):
        '''
        Send a TTL pulse.
        '''
        start = time.time()
        while (time.time() - start) < self.total_length:
            GPIO.output(self.pin, True)
            time.sleep(self.opto_stim_length)
            GPIO.output(self.pin, False)
            time.sleep(self.ISI_length)

    def pulse_continuous(self):
        '''
        Pulse continuously, until an externald trigger is received.
        '''
        self.pulsing = True

        while self.pulsing:
            GPIO.output(self.pin, True)
            time.sleep(self.opto_stim_length)
            GPIO.output(self.pin, False)
            time.sleep(self.ISI_length)


class ProbSwitchRule():
    '''
    The rule maps the association between tones, actions and associated
    outcomes.

    Attributes:
    -----------
    self.tones: list
        A list of tone objects. For reversal learning, should be formatted as
        [high_freq, low_freq].

    self.initial_rule: int
        The initial rule governing tone-action mapping.

    self.criterion: list
        A list of two integers, indicating that the mouse is considered expert

        once it performs correctly on [0] out of [1] trials.

    self.countdown: int
        Once the criterion has been met, initiates a countdown of trials until
        a rule reversal.

    self.countdown_start: int
        Indicates where the trial countdown should start once the criterion has
        been reached.

    self.correct_trials: list
        Keeps a running count of the performance on recent trials. May be
        emptied after rule switch or supplementary rewards.
    '''

    def __init__(self, tones: list, initial_rule: int, p_index: int,
                 criterion: list, countdown_start: int, expert: bool,
                 countdown: int = np.nan):
        self.tones = tones
        self.actions = ['L', 'R', 'N']
        self.rule = initial_rule
        self.p_index = int(p_index)
        self.p_series = [0.9, 0.6, 1.0]
        self.p_rew = self.p_series[self.p_index]
        self.criterion = criterion
        self.countdown = countdown
        self.countdown_start = countdown_start
        self.expert = bool(expert)
        self.correct_trials = []
        # Initialize tone-action mapping to the initial rule.
        self.map_tones()
        print(f'countdown = {self.countdown}, p_index = {self.p_index}, '
              f'p_rew = {self.p_rew}')

    def map_tones(self):
        '''
        Given a rule, maps tones to their associated rewarded outcomes.
        '''
        print(f'Rule = [{int(self.rule)}]')
        # High frequency -> L port; Low frequency -> R port
        if self.rule == 1:
            self.L_tone = self.tones[0]
            self.R_tone = self.tones[1]

        elif self.rule == 0:
            # High frequency -> R port; Low frequency -> L port
            self.L_tone = self.tones[1]
            self.R_tone = self.tones[0]

        # If user inputs rule as 9, a random rule is selected.
        elif self.rule == 9:
            print('Selecting random rule.')
            self.rule = np.random.choice([0, 1])
            self.map_tones()

    def check(self):
        '''
        Checks to see if the criterion has been met, or if the trial countdown
        has reached 0.
        '''
        # Check whether the countdown has begun.
        if not self.expert:
            # If there is no countdown, check whether criterion has been met.
            if self.check_criterion():
                # Warn user that criterion was met, and begin trial countdown.
                print('-----Performance criterion has been met.-----')
                print(f'A probability switch will occur in '
                      f'{self.countdown_start} trials.')
                self.countdown = self.countdown_start
                self.expert = True

        else:
            if self.countdown == 0:
                self.countdown_end()

            else:
                self.countdown -= 1

    def check_criterion(self) -> bool:
        '''
        Checks to see if the criterion has been met.
        '''
        if sum(self.correct_trials[-self.criterion[1]:]) >= self.criterion[0]:
            return True
        else:
            return False

    def countdown_end(self):
        '''
        Determines what occurs when the trial countdown reaches 0.
        '''
        if self.p_index == len(self.p_series)-1:
            # If the mouse has gone through all p_rew values, switch rule.
            self.countdown = np.nan
            self.correct_trials = []
            self.rule = int(1-self.rule)
            self.map_tones()
            print('-------------------RULE SWITCH-------------------')
            print(f'Rule = {self.rule}')

        else:
            # Switch the reward probabilities.
            self.p_index += 1
            self.p_rew = self.p_series[self.p_index]
            self.countdown = self.countdown_start
            print('-------------------PROBABILITY SWITCH-------------------')
            print(f'Reward probability = {self.p_rew}')

     
class Rule():
    '''
    With this rule, the mouse will train at p_rew = 0.9 until they reach
    criterion for the first time. At this point, p_rew will change to a
    different value and start a trial countdown. Once that countdown reaches
    0, p_rew will change again and a new p_rew.
    '''
    def __init__(self, n_trials, tones: list, actions: list, mapping: int,
                 criterion: list, countdown_start: int, p_rew: float,
                 expert: bool = False, countdown: int = np.nan):
        '''
        '''
        self.n_trials = n_trials
        self.tones = tones
        self.actions = ['L', 'R', 'N']
        self.rule = mapping
        self.criterion = criterion
        self.countdown = countdown
        self.countdown_start = countdown_start
        self.expert = expert
        self.p_rew = p_rew
        # Initialize tone-action mapping to the initial rule.
        self.map_tones()
        print(f'initial countdown = {self.countdown}')

    def __init__(self, tones: list, initial_rule: int,
                 criterion: list, countdown_start: int, expert: bool = False,
                 countdown: int = np.nan):
        self.tones = tones
        self.actions = ['L', 'R', 'N']
        self.rule = initial_rule
        self.criterion = criterion
        self.countdown = countdown
        self.countdown_start = countdown_start
        self.expert = expert
        self.correct_trials = []
        # Initialize tone-action mapping to the initial rule.
        self.map_tones()
        print(f'initial countdown = {self.countdown}')

    def map_tones(self):
        '''
        Given a rule, maps tones to their associated rewarded outcomes.
        '''
        print(f'Rule = [{int(self.rule)}]')
        # High frequency -> L port; Low frequency -> R port
        if self.rule == 1:
            self.L_tone = self.tones[0]
            self.R_tone = self.tones[1]

        elif self.rule == 0:
            # High frequency -> R port; Low frequency -> L port
            self.L_tone = self.tones[1]
            self.R_tone = self.tones[0]

        # If user inputs rule as 9, a random rule is selected.
        elif self.rule == 9:
            print('Selecting random rule.')
            self.rule = np.random.choice([0, 1])
            self.map_tones()

    def check_criterion(self) -> bool:
        '''
        Checks to see if the criterion has been met.
        '''
        if sum(self.correct_trials[-self.criterion[1]:]) >= self.criterion[0]:
            return True
        else:
            return False

    def check(self):
        '''
        Checks to see if the criterion has been met, or if the trial countdown
        has reached 0.
        '''
        # Check whether the countdown has begun.
        if np.isnan(self.countdown):
            # If there is no countdown, check whether criterion has been met.
            if self.check_criterion():
                # Warn user that criterion was met, and begin trial countdown.
                print('-----Performance criterion has been met.-----')
                print('ya')
                print(f'A rule reversal will occur in '
                      f'{self.countdown_start} trials.')
                self.countdown = self.countdown_start

        else:
            print(f'Rule reversal in {self.countdown} trials.')
            if self.countdown == 0:
                # If countdown has reached 0, warn user and switch rule.
                self.countdown = np.nan
                self.correct_trials = []
                self.rule = int(1-self.rule)
                self.map_tones()
                print('-------------------RULE SWITCH-------------------')
                print(f'Rule = {self.rule}')

            else:
                self.countdown -= 1


def get_previous_data(mouse_number: str, protocol_name: str, countdown=True):
    '''
    Uses rclone to get the most recent experimental data available for this
    mouse. Prints some relevant information to the console for the experimenter

    Arguments:
    ----------
    mouse_number: str
        ID number of the mouse.

    protocol_name: str
        The name of the protocol currently being run. Will be compared to the
        protocol name from previous data, and will warn the user if they are
        different.

    countdown: bool, default = False
        Indicates whether to search for and return an inter-day countdown
        of trials between reaching criterion and a rule switch.

    Returns:
    --------
    A list, containing the following:
rff
    prev_freq_rule: int
        The value of freq_rule for the last trial of the previous session.

    prev_left_port: int
        The value of left_port for the last trial of the previous session.

    trial_countdown: int
        If countdown argument is set to True, indicates the last value of the
        reversal trial countdown from the previous session.
    '''
    # Paths for rclone config file, data repo (on rclone) and a local directory
    # to temporarily store the fetched data.
    rclone_cfg_path = '/home/pi/.config/rclone/rclone.conf'
    data_path = 'data1:Behaviour Data/Jennifer/all mice/'
    temp_rclone_path = '/home/pi/Desktop/temp_rclone/'
    temp_data_path = '/home/pi/Desktop/temporary-data/'

    # Empty the temporary data folder
    for item in os.listdir(temp_data_path):
        os.remove(temp_data_path + item)
    # Read rclone config file
    with open(rclone_cfg_path) as f:
        rclone_cfg = f.read()

    # Generate dictionary with a string listing all dates
    prev_dates = rclone.with_config(rclone_cfg).run_cmd(
        command='lsf', extra_args=[data_path+str(mouse_number)])
    # Get most recent date
    last_date = prev_dates['out'][-12:-2].decode()

    last_data_path = f'{data_path}{mouse_number}/{last_date}/'
    # Copy all files from most recent date to the temp_data folder

    rclone.with_config(rclone_cfg).run_cmd(
        command='copy', extra_args=[last_data_path, temp_data_path])

    # os.system(f'rclone copy "{last_data_path}" {temp_data_path} --progress')
    # Double quotes around last_data_path to make it a single argument.

    last_file = sorted(os.listdir(temp_data_path))[-1]

    with h5py.File(temp_data_path+last_file, 'r') as f:
        # Get relevant information from the data file.
        prev_protocol = f.attrs['protocol_name']
        prev_user = f.attrs['experimenter']
        prev_weight = f.attrs['mouse_weight']
        prev_countdown = f['rule']['countdown'][-1]
        prev_left_port = f['rule']['left_port'][-1]
        prev_p_index = f['rule']['p_index'][-1]
        prev_expert = f['rule']['expert'][-1]
        prev_water = f.attrs['total_reward']
        prev_trials = len(f['t_start'])
        prev_resp = f['response']
        prev_resp_decoded = np.array([i.decode('utf-8') for i in prev_resp])
        prev_L = round((np.sum(prev_resp_decoded == 'L') / prev_trials), 2)
        prev_R = round((np.sum(prev_resp_decoded == 'R') / prev_trials), 2)
        prev_N = round((np.sum(prev_resp_decoded == 'N') / prev_trials), 2)

        # Print some relevant information to the console
        print(f'Date of last experiment: {last_date}')
        print(f'Previous user: {prev_user}')
        print(f'Previous weight: {prev_weight}')
        print(f'Previous protocol: {prev_protocol}')
        print(f'Previous rule: [{int(prev_left_port)}]')
        print(f'Previous p_index: {prev_p_index}')
        print(f'Previous water total: {prev_water}')
        print(f'Previous trial number: {prev_trials}')
        print(f'Previous resp fraction: L:{prev_L}, R:{prev_R}, N:{prev_N}')
        if not np.isnan(prev_countdown):
            print(f'Reversal countdown: {prev_countdown}')

    # Verify that the protocol is the same as previous. If not, warn user.
    if prev_protocol != protocol_name:
        input('--WARNING-- using a different protocol than last time.'
              'Make sure this is intentional.')

    return [prev_p_index, prev_left_port, prev_countdown, prev_expert]


def delete_tones():
    tones = [i for i in os.listdir('.') if '.wav' in i]
    for tone in tones:
        os.remove(tone)
