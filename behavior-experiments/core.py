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



#------------------------------------------------------------------------------
#Define some classes!
#------------------------------------------------------------------------------

class tones():

    def __init__(self, frequency, tone_length, pulsing=False, loc='B'):

        #Create a string that will be the name of the .wav file
        if pulsing:           
            self.name = f'{frequency}Hz_{loc}_pulsing'

        else:
            self.name = f'{frequency}Hz_{loc}'
            
        self.freq = frequency
        self.tone_length = tone_length
        self.multi_pulse = pulsing
        self.loc = loc
        self.pulse_length = 0.2

        self.vol = -5
        if self.freq >= 4000:
            self.vol = -25

        if self.multi_pulse == False:
            #create a waveform called self.name from frequency and pulse_length
            os.system(f'sox -V0 -r 44100 -n -b 8 -c 1 {str(self.freq)}Hz_B.wav '
                      f'synth {self.tone_length} sin {self.freq} vol {self.vol}dB')

        elif self.multi_pulse == True:

            self.pulse_number = self.tone_length/(2*self.pulse_length) # 2 because of the interpulse interval
            
            #create an empty wav file that will be the inter-pulse interval
            os.system(f'sox -V0 -r 44100 -n -b 8 -c 1 pulse.wav synth {self.pulse_length} sin {self.freq} vol -20dB') #tone
            os.system(f'sox -V0 -r 44100 -n -b 8 -c 1 interpulse.wav synth {self.pulse_length} sin {self.freq} vol -150dB') #silent interpulse interval

            #string with pulse/interpulse repeated for number of pulses
            concat_files = ' pulse.wav interpulse.wav' * int(self.pulse_number)

            os.system(f'sox{concat_files} {self.name}.wav')

            os.system(f'rm pulse.wav') #delete the pulse and interpulse, no longer useful.
            os.system(f'rm interpulse.wav')

        if self.loc == 'L': #will create a tone coming from left speaker

            #create a silent channel called silent.wav 
            os.system(f'sox -V0 -r 44100 -n -b 8 -c 1 silent.wav synth 2 sin 4000 vol -200dB')

            #merge the two channels such that the silent is on the right
            os.system(f'sox -M {str(self.freq)}Hz_B.wav silent.wav {self.name}.wav')

            os.system('rm silent.wav') #delete silent channel
            os.system(f'rm {str(self.freq)}Hz_B.wav') #delete sound channel
            
        elif self.loc == 'R': #will create a tone coming from right speaker

            #create a silent channel called silent.wav 
            os.system(f'sox -V0 -r 44100 -n -b 8 -c 1 silent.wav synth 2 sin 4000 vol -200dB')

            #merge the two channels such that the silent is on the left
            os.system(f'sox -M silent.wav {str(self.freq)}Hz_B.wav {self.name}.wav')

            os.system(f'rm silent.wav') #delete silent channel
            os.system(f'rm {str(self.freq)}Hz_B.wav') #delete sound channel

        #elif self.loc == 'B': #will create a tone coming from both speakers

            #merge the tone with itself to get a sound from both speakers
            #os.system(f'sox -M {self.name}.wav {self.name}.wav {self.name}.wav')

        self.sound = mixer.Sound(f'{self.name}.wav')

    def Play(self):
 
        self.sound.play() #play the .wav file
        time.sleep(self.tone_length) #wait for it to end before continuing

    def Delete(self):
        # Delete the wav file
        os.system(f'rm {self.name}.wav')


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
            Stores whether the presented tone is associated with 'L' or 'R' port

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
        self.protocol_name  = protocol_name
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

        self.sample_tone = np.empty(self.n_trials, dtype='S1')
        self.t_sample_tone = np.empty(self.n_trials)
        self.sample_tone_end = np.empty(self.n_trials)

        self.response = np.empty(self.n_trials, dtype = 'S1')
        self.lick_r = np.empty(self.n_trials, dtype = dict)
        self.lick_l = np.empty_like(self.lick_r) 

        self.v_rew_l = np.empty(self.n_trials)
        self.v_rew_l.fill(np.nan)
        self.t_rew_l = np.empty(self.n_trials)
        self.t_rew_l.fill(np.nan)
        self.v_rew_r = np.empty(self.n_trials)
        self.v_rew_r.fill(np.nan)
        self.t_rew_r = np.empty(self.n_trials) 
        self.t_rew_r.fill(np.nan) 

        self.freq = np.empty(self.n_trials) 
        self.loc = np.empty(self.n_trials, dtype='S1') 
        self.multipulse = np.empty(self.n_trials)
        
        self.freq_rule = np.empty(self.n_trials)
        self.left_port = np.empty(self.n_trials)
        self.countdown = np.empty(self.n_trials)
        
        self.exp_quality = ''
        self.exp_msg = ''
        self.total_reward = 0
        self.countdown = countdown


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
            dtint = h5py.special_dtype(vlen = np.dtype('int32')) 
            dtfloat = h5py.special_dtype(vlen = np.dtype('float'))

            t_start = f.create_dataset('t_start', data = self.t_start)
            t_end = f.create_dataset('t_end', data = self.t_end)

            response = f.create_dataset('response', data=self.response,
                                        dtype='S1')
            # Create HDF5 groups for licks, tones and rewards.
            lick_l = f.create_group('lick_l')
            lick_r = f.create_group('lick_r')

            sample_tone = f.create_group('sample_tone')

            rew_l = f.create_group('rew_l')
            rew_r = f.create_group('rew_r')

            rule = f.create_group('rule') #stores rules and tone assignments

            #Preinitialize datasets for each sub-datatype within licks, tones
            #and rewards
            lick_l_t = lick_l.create_dataset('t', (self.n_trials,),
                                             dtype=dtfloat)
            lick_l_volt = lick_l.create_dataset('volt', (self.n_trials,),
                                                dtype=dtint)
            lick_r_t = lick_r.create_dataset('t', (self.n_trials,),
                                             dtype=dtfloat)
            lick_r_volt = lick_r.create_dataset('volt', (self.n_trials,),
                                                dtype=dtint)

            sample_tone_t = sample_tone.create_dataset('t',
                data=self.t_sample_tone, dtype='f8')
            sample_tone_type = sample_tone.create_dataset('type',
                data=self.sample_tone, dtype='S1')
            sample_tone_end = sample_tone.create_dataset('end',
                data=self.sample_tone_end, dtype='f8')
            sample_tone_freq = sample_tone.create_dataset('freq',
                data=self.freq, dtype=int)
            sample_tone_loc = sample_tone.create_dataset('location',
                                                         data=self.loc)
            sample_tone_multipulse = sample_tone.create_dataset('multipulse',
                data=self.multipulse)

            rew_l_t = rew_l.create_dataset('t', data = self.t_rew_l)
            rew_l_v = rew_l.create_dataset('volume', data = self.v_rew_l)
            rew_r_t = rew_r.create_dataset('t', data = self.t_rew_r)
            rew_r_v = rew_r.create_dataset('volume', data = self.v_rew_r)

            freq_rule = rule.create_dataset('freq_rule', data = self.freq_rule)
            left_port = rule.create_dataset('left_port', data = self.left_port)
            countdown = rule.create_dataset('countdown', data = self.countdown)

            for trial in range(self.n_trials):
                lick_l_t[trial] = self.lick_l[trial]['t']
                lick_l_volt[trial] = self.lick_l[trial]['volt']
                lick_r_t[trial] = self.lick_r[trial]['t']
                lick_r_volt[trial] = self.lick_r[trial]['volt']

            #Finally, store metadata for each dataset/groups
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

        for fname in yesterday_files: # Move yesterday files to temp data folder
            os.system(f'mv /home/pi/Desktop/yesterday_data/{fname} '
                      '/home/pi/Desktop/temporary-data')

        # Move current file to yesterday_data folder
        print(self.filename)
        os.system(f'mv /home/pi/Desktop/behavior-experiments/'
                  'behavior-experiments/{self.filename} '
                  '/home/pi/Desktop/yesterday_data')
        # Create remote folder for today's data and copy file into that folder
        os.system(f'rclone mkdir sharepoint:"Data/Behaviour data/Sebastien/'
                  'Dual_Lickport/Mice/{self.mouse_number}"')
        os.system(f'rclone mkdir sharepoint:"Data/Behaviour data/Sebastien/'
                  'Dual_Lickport/Mice/{self.mouse_number}/{self.date_experiment}"')
        os.system(f'rclone copy /home/pi/Desktop/yesterday_data/{self.filename}'
                  ' sharepoint:"Data/Behaviour data/Sebastien/Dual_Lickport/'
                  'Mice/{self.mouse_number}/{self.date_experiment}"')


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
        GPIO.output(self.enablePIN, 0) #enable the stepper motor
        GPIO.output(self.directionPIN, direction) #set direction

        #if GPIO.input(self.emptyPIN):
            
        for i in range(int(steps)): #move in "direction" for "steps"
            GPIO.output(self.stepPIN, 1)
            time.sleep(0.0002)
            GPIO.output(self.stepPIN, 0)
            time.sleep(0.0002)
            
        #else:

            #print('the syringe is empty')
        self.Disable() #disable stepper (to prevent overheating)

    def Reward(self,):
        steps = 250 #Calculate the number of steps needed to deliver
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

        self.Motor(0, 60000) #Pull the syringe for 96000 steps, ~3mL.

    def Disable(self):

        GPIO.output(self.enablePIN, 1) #disable stepper (to prevent overheating)

    def Run(self):
        self.start = True
        while self.start == True:

            self.cont = False
            while self.cont == True:
                
                if GPIO.input(self.emptyPIN):
                    self.Motor(1,200)
                    

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
    '''
    A class to handle communication between the RPi and other peripherals
    (e.g. laser scanning microscope) through TTL pulses.
    
    Attributes:
    -----------
    self.pin: int
        The GPIO pin through which pulses will be sent.
    
    self.pulse_length: float
        The length(sec) of TTL pulses.
    '''
    def __init__(self, pin):
        self.pin = pin
        self.pulse_length = 0.01
        # Setup GPIO pins for TTL pulses.
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, False)

    def pulse(self):
        '''
        Send a TTL pulse.
        '''
        GPIO.output(self.pin, True)
        time.sleep(self.pulse_length)
        GPIO.output(self.pin, False)

class Rule:
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
        A list of two integers, indicating that the mouse is considered "expert"
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

    def __init__(self, tones: list, initial_rule: int,
                 criterion: list, countdown_start: int, countdown:int = np.nan):
        self.tones = tones
        self.rule = initial_rule
        self.criterion = criterion
        self.countdown = countdown
        self.countdown_start = countdown_start
        self.correct_trials = []
        # Initialize tone-action mapping to the initial rule.
        self.map_tones()

    def map_tones(self):
        '''
        Given a rule, maps tones to their associated rewarded outcomes.
        '''
        print(f'Rule = [{int(self.rule)}]')
        # High frequency -> L port; Low frequency -> R port
        if self.rule == 1:
            self.L_tone = self.tones[0]
            self.R_tone = self.tones[1]
            
        elif self.rule ==0:
            # High frequency -> R port; Low frequency -> L port
            self.L_tone = self.tones[1]
            self.R_tone = self.tones[0]

        # If user inputs rule as 9, a random rule is selected.
        elif self.rule == 9:
            print('Selecting random rule.')
            self.rule = np.random.choice([0,1])
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
                print(f'A rule reversal will occur in '
                      '{self.countdown_start} trials.')
                self.countdown = self.countdown_start

        else:
            print(f'Rule reversal countdown: {self.countdown}')
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

            
def get_previous_data(mouse_number:str, protocol_name:str, countdown=False):
    '''
    Uses rclone to get the most recent experimental data available for this
    mouse. Prints some relevant information to the console for the experimenter.

    Arguments:
    ----------
    mouse_number: str
        ID number of the mouse.

    protocol_name: str
        The name of the protocol currently being run. Will be compared to the
        protocol name from previous data, and will warn the user if they are
        different.

    countdown: bool, default = False
        Indicates whether or not to search for and return an inter-day countdown
        of trials between reaching criterion and a rule switch.

    Returns:
    --------
    A list, containing the following:

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
    data_path = 'sharepoint:"Data/Behaviour data/Sebastien/Dual_Lickport/Mice/"'
    temp_data_path = '/home/pi/Desktop/temp_rclone/' 

    # Empty the temporary data folder
    for item in os.listdir(temp_data_path): 
        os.remove(temp_data_path + item)
    # Read rclone config file
    with open(rclone_cfg_path) as f:
        rclone_cfg = f.read() 

    # Generate dictionary with a string listing all dates
    prev_dates = rclone.with_config(rclone_cfg).run_cmd(
        command='lsf', extra_args=[data_path+mouse_number])
    # Get most recent date
    last_date = prev_dates['out'][-12:-2].decode()
    last_data_path = f'{data_path}{mouse_number}/{last_date}/'
    # Copy all files from most recent date to the temp_data folder
    rclone.with_config(rclone_cfg).copy(
        source=last_data_path, dest=temp_data_path)
    last_file = sorted(os.listdir(temp_data_path))[-1] 

    with h5py.File(temp_data_path+last_file, 'r') as f:
        # Get relevant information from the data file.
        prev_protocol = f.attrs['protocol_name']
        prev_user = f.attrs['experimenter']
        prev_weight = f.attrs['mouse_weight']
        prev_freq_rule = f['rule']['freq_rule'][-1]
        prev_left_port = f['rule']['left_port'][-1]
        prev_countdown = f['rule']['countdown'][-1]
        prev_water = f.atts['total_reward']
        prev_water += np.nansum(f['rew_r']['volume'])
        prev_trials = len(f['t_start'])
        
        # Print some relevant information to the console
        print(f'Date of last experiment: {last_date}')
        print(f'Previous user: {prev_user}')
        print(f'Previous weight: {prev_weight}')
        print(f'Previous protocol: {prev_protocol}')
        print(f'Previous rule: [{int(prev_left_port)}]')
        print(f'Previous water total: {prev_water}')

    # Verify that the protocol is the same as previous. If not, warn user.
    if prev_protocol != protocol_name: 
        warning = input('--WARNING-- using a different protocol than last time.'
                        'Make sure this is intentional.')

    return [prev_freq_rule, prev_left_port, prev_countdown]
