import time
import RPi.GPIO as GPIO
import numpy as np
import os
import h5py
from pygame import mixer
import rclone


class Trial():
    '''
    A class to handle and store trial structure-related data.
    '''
    def __init__(self, name, n_trials):
        '''
        '''
        self.name = name
        self.n_trials = n_trials
        self.curr_t = 0
        self.generate_data()

    def generate_data(self):
        '''
        '''
        self.data = {}
        self.data['n_trials'] = self.n_trials
        self.data['trial_start_time'] = np.empty(self.n_trials, dtype=float)
        self.data['trial_end_time'] = np.empty(self.n_trials, dtype=float)
        self.data['iti_length'] = np.empty(self.n_trials, dtype=float)

    def trial_start(self):
        '''
        '''
        self.trial_start_time = time.time()*1000
        self.data['trial_start_time'][self.curr_t] = self.trial_start_time

    def inter_trial_interval(self):
        '''
        '''
        iti = 0

        while iti > 30 or iti < 10:
            iti = np.random.exponential(scale=20)

        self.data['iti_length'][self.curr_t] = iti
        self.data['trial_end_time'][self.curr_t] = (time.time()*1000
                                                    - self.trial_start_time)
        time.sleep(iti)
        self.curr_t += 1


class Tone:
    '''
    A parent class to handle auditory tones to be used during the task.

    Attributes:
    -----------
    self.filename: str
        The filename of the corresponding wav file (e.g. '1000Hz.wav').

    self.tone_length: float
        The total duration (in seconds) of the tone.

    self.sound: object
        A pygame.mixer object corresponding to the tone.
    '''
    def __init__(self, name, trial):
        self.name = name
        self.trial = trial
        self.generate_data()

    def generate_tone(self):
        '''
        Use the sox library to generate a wav file corresponding to this tone.
        '''
        raise NotImplementedError

    def generate_data(self):
        '''
        '''
        n_trials = self.trial.n_trials
        self.data = {}
        self.data['tone_start'] = np.empty(n_trials, dtype=float)*np.nan
        self.data['tone_end'] = np.empty(n_trials, dtype=float)*np.nan

    def play(self):
        '''Play the sound over the speakers.'''
        trial_start = self.trial.trial_start_time
        self.data['tone_start'][self.trial.curr_t] = (time.time()*1000
                                                      - trial_start)
        self.sound.play()
        time.sleep(self.tone_length)
        self.data['tone_end'][self.trial.curr_t] = (time.time()*1000
                                                    - trial_start)

    def delete(self):
        ''' Delete the file from the local directory.'''
        os.system(f'rm {self.filename}')


class PureTone(Tone):
    '''
    A tone with a single frequency, playing continuously from both channels for
    a given amount of time.
    '''
    def __init__(self, name, trial, frequency: int,
                 tone_length: float, vol: int = -20):
        '''
        '''
        self.name = name
        self.trial = trial
        self.freq = frequency
        self.tone_length = tone_length
        self.loc = 'B'
        self.vol = vol
        self.filename = f'{self.freq}Hz.wav'

        self.generate_tone()
        self.generate_data()
        self.sound = mixer.Sound(self.filename)

    def generate_tone(self):
        os.system(f'sox -V0 -r 44100 -n -b 8 -c 1 {self.filename} '
                  f'synth {self.tone_length} sin {self.freq} vol {self.vol}dB')

    def generate_data(self):
        '''
        '''
        n_trials = self.trial.n_trials
        self.data = {}
        self.data['name'] = self.name
        self.data['freq'] = self.freq
        self.data['tone_length'] = self.tone_length
        self.data['localization'] = self.loc
        self.data['volume'] = self.vol

        self.data['tone_start'] = np.empty(n_trials, dtype=float)*np.nan
        self.data['tone_end'] = np.empty(n_trials, dtype=float)*np.nan


class Stepper():
    def __init__(self, name, trial, enablePIN, directionPIN,
                 stepPIN, emptyPIN, steps=250):
        self.name = name
        self.trial = trial
        self.enablePIN = enablePIN
        self.directionPIN = directionPIN
        self.stepPIN = stepPIN
        self.emptyPIN = emptyPIN
        self.steps = steps

        GPIO.setup(self.enablePIN, GPIO.OUT, initial=1)
        GPIO.setup(self.directionPIN, GPIO.OUT, initial=0)
        GPIO.setup(self.stepPIN, GPIO.OUT, initial=0)
        GPIO.setup(self.emptyPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.generate_data()
        self.disable()

    def generate_data(self):
        '''
        '''
        self.data = {}
        self.data['name'] = self.name
        self.data['volume'] = np.empty(self.trial.n_trials, dtype=float)*np.nan
        self.data['steps'] = np.empty(self.trial.n_trials, dtype=float)*np.nan
        self.data['reward_time'] = np.empty(self.trial.n_trials,
                                            dtype=float)*np.nan

    def disable(self):
        '''
        Disable the stepper motor, to prevent overheating.
        '''
        GPIO.output(self.enablePIN, 1)

    def motor(self, direction: int, steps: int, block: int = 100):
        '''
        Turn the stepper motor in a given direction for a given
        number of steps.

        Arguments:
        ----------
        direction: int
            Direction in which to move the motor. 1 pushes the syringe
            and 0 pulls it.
        steps: int
            Number of steps the motor should move.
        block: int, default = 100
            Number of steps to complete before checking the limit switch.
        '''
        GPIO.output(self.enablePIN, 0)  # Enable the stepper motor.
        GPIO.output(self.directionPIN, direction)

        step_countdown = steps
        block_countdown = block

        while step_countdown > 0:
            # Check whether the syringe is empty (limit switch)
            if GPIO.input(self.emptyPIN):

                while block_countdown > 0:
                    GPIO.output(self.stepPIN, 1)
                    time.sleep(0.0002)
                    GPIO.output(self.stepPIN, 0)
                    time.sleep(0.0002)
                    step_countdown -= 1
                    block_countdown -= 1
            else:
                print('---The syringe is empty.---')
                break
        self.disable()

    def reward(self, steps: int = 250, volume: float = 10):
        '''
        '''
        trial = self.trial.curr_t
        trial_start_time = self.trial.trial_start_time
        print(trial_start_time)
        self.data['reward_time'][trial] = time.time*1000 - trial_start_time
        self.motor(1, steps)
        self.data['steps'][trial] = steps
        self.data['volume'][trial] = volume


class TTL():
    '''
    A class to handle communication between the RPi and other peripherals
    (e.g. laser scanning microscope) through TTL pulses.
    '''
    def __init__(self, name, trial, pin):
        self.pin = pin
        self.trial = trial
        self.generate_data(name)

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, False)

    def generate_data(self, name):
        n_trials = self.trial.n_trials
        self.data = {}
        self.data['name'] = name
        self.data['pulse_start'] = np.empty(n_trials, dtype=float)*np.nan
        self.data['pulse_end'] = np.empty(n_trials, dtype=float)*np.nan

    def ttl_pulse(self):
        raise NotImplementedError

    def pulse(self):
        '''
        '''
        curr_t = self.trial.curr_t
        trial_start_time = self.trial.trial_start_time

        self.data['pulse_start'][curr_t] = time.time()*1000 - trial_start_time
        self.ttl_pulse()
        self.data['pulse_end'][curr_t] = time.time()*1000 - trial_start_time


class ImagingTTL(TTL):
    '''
    A TTL pulse from RPi to an imaging laser, to either 1) trigger the start
    and end of scans, or 2) to mark frames for alignment.
    '''
    def __init__(self, name, trial, pin, pulse_length=0.01):
        self.pin = pin
        self.pulse_length = pulse_length
        self.trial = trial
        self.generate_data(name)

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, False)

    def generate_data(self, name):
        n_trials = self.trial.n_trials
        self.data = {}
        self.data['name'] = name
        self.data['pulse_length'] = self.pulse_length
        self.data['pulse_start'] = np.empty(n_trials, dtype=float)*np.nan
        self.data['pulse_end'] = np.empty(n_trials, dtype=float)*np.nan

    def ttl_pulse(self):
        GPIO.output(self.pin, True)
        time.sleep(self.pulse_length)
        GPIO.output(self.pin, False)


class OptoStim(TTL):
    '''
    A TTL pulse to control a driver for in vivo optogenetic stimulation.
    '''
    def __init__(self, name, trial, pin, stim_length,
                 pulse_length, pulse_frequency):
        self.pin = pin
        self.stim_length = stim_length
        self.pulse_length = pulse_length
        self.pulse_frequency = pulse_frequency
        self.trial = trial
        self.generate_data(name)

        self.pulse_number = (self.stim_length/1000) * self.pulse_frequency
        self.cycle_length = self.stim_length/self.pulse_number
        self.off_time = self.cycle_length - self.pulse_length

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, False)

    def generate_data(self, name):
        '''
        '''
        n_trials = self.trial.n_trials
        self.data = {}
        self.data['name'] = name
        self.data['stim_length'] = self.stim_length
        self.data['pulse_length'] = self.pulse_length
        self.data['pulse_frequency'] = self.pulse_frequency
        self.data['pulse_start'] = np.empty(n_trials, dtype=float)*np.nan
        self.data['pulse_end'] = np.empty(n_trials, dtype=float)*np.nan

    def ttl_pulse(self):
        '''
        '''
        for pulse in range(len(self.pulse_number)):
            GPIO.output(self.pin, True)
            time.sleep(self.pulse_length)
            GPIO.output(self.pin, False)
            time.sleep(self.off_time)


class Rule():
    def __init__(self, name: str, trial: object, tones: list, actions: list,
                 mapping: int):
        '''
        '''
        self.name = name
        self.tones = self.tones
        self.actions = self.actions
        self.mapping = self.initial_rule
        self.map_tones()
        self.generate_data()

    def generate_data(self):
        '''
        '''
        self.data = {}
        self.data['name'] = self.name

    def map_tones(self):
        '''
        Maps tones-action pairs to associated reward probabilities and
        correct/incorrect trials.
        '''
        raise NotImplementedError

    def evaluate(self):
        '''
        Given a tone and action, will determine whether the mouse responded
        correctly and whether the mouse should be rewarded.
        '''
        raise NotImplementedError


class ProbSwitchRule(Rule):
    '''
    With this rule, the mouse will train at p_rew = 0.9 until they reach
    criterion for the first time. At this point, p_rew will change to a
    different value and start a trial countdown. Once that countdown reaches
    0, p_rew will change again and a new p_rew.
    '''
    def __init__(self, name: str, trial: object, tones: list, params: dict):
        '''
        '''
        self.name = name
        self.trial = trial
        self.tones = np.array([tone.freq for tone in tones])
        self.actions = np.array(['L', 'R', 'N'])
        self.mapping = int(params['mapping'])
        self.criterion = [19, 20]
        self.expert = int(params['expert'])
        self.countdown = params['countdown']
        if self.countdown == 'n':
            self.countdown = np.nan
        else:
            self.countdown = float(self.countdown)
        self.countdown_start = 500
        self.p_series = [0.9, 0.7, 0.8, 1, 0.9]
        self.p_index = int(params['p_index'])
        self.rewarded_side = []
        self.supp_rew_counter = 0
        # Initialize tone-action mapping to the initial rule.
        self.map_tones()
        self.generate_data()
        print(f'initial countdown = {self.countdown}')

    def generate_data(self):
        n_trials = self.trial.n_trials
        self.data = {}
        self.data['name'] = self.name
        self.data['mapping'] = np.empty(n_trials, dtype=int)
        self.data['expert'] = np.empty(n_trials, dtype=bool)
        self.data['countdown'] = np.empty(n_trials, dtype=float)*np.nan
        self.data['tone_freq'] = np.empty(n_trials, dtype=int)
        self.data['response'] = np.empty(n_trials, dtype=str)
        self.data['performance'] = np.empty(n_trials, dtype=bool)
        self.data['corr_resp'] = np.empty(n_trials, dtype=str)
        self.data['reward'] = np.empty(n_trials, dtype=bool)
        self.data['p_rew'] = np.empty(n_trials, dtype=float)
        self.data['p_rew_trial'] = np.empty(n_trials, dtype=float)

    def store_data(self, tone, action, performance, correct_choice,
                   reward, rew_prob):
        '''
        Store relevant trial data in the self.data dictionary.
        '''
        trial = self.trial.curr_t
        self.data['tone_freq'][trial] = tone.freq
        self.data['response'][trial] = action
        self.data['performance'][trial] = performance
        self.data['corr_resp'][trial] = correct_choice
        self.data['reward'][trial] = reward
        self.data['p_rew_trial'][trial] = rew_prob
        self.data['mapping'][trial] = self.mapping
        self.data['expert'][trial] = self.expert
        self.data['p_rew'][trial] = self.p_rew
        self.data['countdown'][trial] = self.countdown

    def map_tones(self):
        '''
        Given a rule, maps tones to their associated rewarded outcomes.
        correct and probs matrices are formatted as: lowf[L,R,N], highf[L,R,N].
        '''
        self.p_rew = self.p_series[self.p_index]
        p_corr = self.p_rew
        p_incorr = 1-p_corr
        print(f'Rule = [{int(self.mapping)}], '
              f'Reward Probability = {self.p_rew}')
        # High frequency -> L port; Low frequency -> R port
        if self.mapping == 1:
            self.correct = np.array([[0, 1, 0],
                                     [1, 0, 0]])
            self.probs = np.array([[p_incorr, p_corr, 0],
                                   [p_corr, p_incorr, 0]])

        elif self.mapping == 0:
            # High frequency -> R port; Low frequency -> L port
            self.correct = np.array([[1, 0, 0],
                                     [0, 1, 0]])
            self.probs = np.array([[p_corr, p_incorr, 0],
                                   [p_incorr, p_corr, 0]])

        # If user inputs rule as 9, a random rule is selected.
        elif self.mapping == 9:
            print('Selecting random rule.')
            self.mapping = np.random.choice([0, 1])
            self.map_tones()

    def evaluate(self, tone, action) -> bool:
        '''
        Given a tone and an action, will determine 1)whether the response
        was correct, and 2) whether a reward will be delivered.
        '''
        # Determine where the tone/action pair is in self.correct/probs.
        tone_index = np.where(self.tones == tone.freq)[0]
        action_index = np.where(self.actions == action)[0]

        # Determine whether response is "correct" and reward probability
        performance = self.correct[tone_index, action_index]
        rew_prob = self.probs[tone_index, action_index]
        correct_choice = self.actions[np.where(self.correct[tone_index]
                                               == 1)[0][0]]
        print(correct_choice)

        # Determine whether the mouse will receive a reward.
        if np.random.rand() < rew_prob:
            reward = True
            self.rewarded_side.append(action)
        else:
            reward = False

        # Store trial-related data.
        self.store_data(tone, action, performance, correct_choice,
                        reward, rew_prob)

        return reward

    def print_trial_stats(self, l_licks: object, r_licks: object):
        '''
        '''
        detected_licks = ''
        # Will indicate which ports recorded any licks in the entire trial.
        if sum(l_licks.lick_voltage) != 0:
            detected_licks += 'L'
        if sum(r_licks.lick_voltage) != 0:
            detected_licks += 'R'

        trial = self.trial.curr_t
        tone = self.data['tone_freq'][trial]
        resp = self.data['response'][trial]
        rew = int(self.data['reward'][trial])
        corr = self.data['performance'][trial]
        perf = f'{sum(self.data["performance"])}/{trial}'
        countdown = self.countdown

        print(f'Tone:{tone}, Resp:{resp}, Licks:{detected_licks}, Rew:{rew}, '
              f'Corr:{corr}, Perf:{perf}, Count:{countdown}')

    def supplementary_rewards(self, left_rewards, right_rewards):
        '''
        '''
        # If 5 last rewards are from L, deliver 2x R rewards.
        if self.rewarded_side[-5:] == ['L', 'L', 'L', 'L', 'L']:
            for i in range(2):
                left_rewards.reward()
                print('Delivering supplementary reward from L port.')
                time.sleep(1)
            self.rewarded_side.append('R')

        # If 5 last rewards are from R, deliver 2x L rewards.
        elif self.rewarded_side[-5:] == ['R', 'R', 'R', 'R', 'R']:
            for i in range(2):
                right_rewards.reward()
                print('Delivering supplementary reward from R port.')
                time.sleep(1)
            self.rewarded_side.append('L')

        trial = self.trial.curr_t

        # If there are no rewards in the last 8 trials, deliver a reward
        # from each port.
        if self.supp_rew_counter > 8:
            if sum(self.data['rewards'][trial-8:trial]) == 0:
                self.left_rewards.reward()
                print('Delivering supplementary reward from L port.')
                self.right_rewards.reward()
                print('Delivering supplementary reward from R port.')
                self.supp_rew_counter = 0

        else:
            self.supp_rew_counter += 1

    def check_criterion(self):
        '''
        '''
        if not self.expert:
            # Check recent trials ([1]) to see whether the number of correct
            # responses is higher than or equal to a criterion ([0]).
            trial = self.trial.curr_t
            if ((trial > self.criterion[1]) and
                (sum(self.correct[trial-self.criterion[1]:trial])
                 >= self.criterion[0])):

                print('---- Performance criterion has been met. ----')
                self.expert = True
                self.p_index = 1
                self.countdown = self.countdown_start
                self.map_tones()

    def trial_countdown(self):
        '''
        '''
        if not np.isnan(self.countdown):
            self.countdown -= 1

        if self.countdown == 0:

            if self.p_index == len(self.p_series):
                self.mapping = 1-self.mapping
                print('This mouse has gone through all reward probabilities. '
                      'Tone-port mapping will now be switched.')
                self.countdown = np.nan

            else:
                self.p_index += 1
                p = self.p_series[self.p_index]
                print(f'New reward probabilities: {p}/{1-p}')


class LickDetect():
    '''
    A class to handle detection of lick contacts between the mouse
    and a lickspout.
    '''
    def __init__(self, name, trial, pin):
        self.name = name
        self.trial = trial
        self.pin = pin
        self.generate_data()

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def generate_data(self):
        n_trials = self.trial.n_trials
        self.data = {}
        self.data['name'] = self.name
        self.data['lick_onset'] = np.empty(n_trials, dtype=np.ndarray)
        self.data['lick_offset'] = np.empty(n_trials, dtype=np.ndarray)

    def lick_detection(self, sampling_rate=1000, sampling_duration=8):
        '''
        Samples the value of the lickport at a given sampling rate for
        a given time to detect licks.

        Arguments:
        ----------
        sampling_rate: int, default = 10000
            The frequency, in Hz, at which the lickport should be sampled.
        sampling_duration: float, default = 8
            The time, in seconds, during which the lickport should be sampled.
        '''
        num_samples = int(sampling_duration * sampling_rate)

        self.lick_voltage = []
        self.lick_timestamps = []

        for i in range(num_samples):
            self.lick_voltage.append(GPIO.input(self.pin))
            self.lick_timestamps.append(time.time()*1000)
            time.sleep(1/sampling_rate)

        diff_volt = np.diff(np.array(self.lick_voltage)*1)
        trial_start = self.trial.trial_start_time
        t = self.trial.curr_t
        onset_index = np.where(diff_volt == 1)[0]
        offset_index = np.where(diff_volt == -1)[0]

        print(onset_index)
        print(offset_index)

        if (len(onset_index) > 0) and (len(offset_index) > 0):
            self.data['lick_onset'][t] = (self.lick_timestamps[onset_index]
                                          - trial_start)
            self.data['lick_offset'][t] = (self.lick_timestamps[offset_index]
                                           - trial_start)
        else:
            self.data['lick_onset'][t] = []
            self.data['lick_offset'][t] = []


class Data():
    '''
    Packages all relevant experimental data into an hdf5 file and uploads
    it using rclone.
    '''
    def __init__(self, objects: list, params: dict):
        '''
        '''
        self.objects = objects
        self.date_experiment = time.strftime("%Y-%m-%d",
                                             time.localtime(time.time()))
        self.filename = ('ms' + params['mouse_number'] + '_'
                         + self.date_experiment + '_' + 'block'
                         + str(params['block_number']) + '.hdf5')

        self.hdf = h5py.File(self.filename, 'w')

    def package_data(self):
        '''
        Package experimental parameters and all data from each item in
        self.objects into an hdf5 file.
        '''
        # Store experimental parameters as hdf5 attributes.
        for key, item in self.params.items():
            self.hdf.attrs[key] = item
        # Create an hdf5 group for each object.
        for obj in self.objects:
            group = self.hdf.create_group(obj.data['name'])
            # Create an hdf5 dataset for each item in obj.data.
            for key, item in obj.data.items():
                group.create_dataset(key, item)

    def rclone_upload(self, rclone_cfg_path, data_repo_path, temp_data_path):
        '''
        Use rclone to create a directory in the data repository for the current
        experiment, then copy the data file to that directory. A copy is also
        kept locally in a temporary data directory.
        '''
        # Open rclone configuration
        with open(rclone_cfg_path) as f:
            rclone_cfg = f.read()

        # If no directory for this mouse in data repo, create one.
        mouse_path = data_repo_path + self.mouse
        rclone.with_config(rclone_cfg).run_cmd(command='mkdir',
                                               extra_args=[mouse_path])
        # If no directory for this date, create one.
        date_path = mouse_path + self.date_experiment
        rclone.with_config(rclone_cfg).run_cmd(command='mkdir',
                                               extra_args=[date_path])
        # Copy data file into the date directory in data repo.
        rclone.with_config(rclone_cfg).run_cmd(
            command='copy', extra_args=[self.filename, date_path])
        # Move the data file into the local temporary data folder
        rclone.with_config(rclone_cfg).run_cmd(
            command='mv', extra_args=[self.filename, temp_data_path])


def delete_tones():
    tones = [i for i in os.listdir('.') if '.wav' in i]
    for tone in tones:
        os.remove(tone)


def input_params(params):
    for key, value in params.items():
        if value is None:
            params[key] = input(f'Please enter value for {key}: ')

    [print(key, ':', value) for key, value in params.items()]

    while True:
        key = input('Enter the parameter you would like to change '
                    '(n:none, p:print):')

        if key == 'n':
            break

        elif key == 'p':
            [print(key, ':', value) for key, value in params.items()]

        elif key in params.keys():
            params[key] = input(f'Enter new value for {key}: ')


def get_previous_data(params: dict, rclone_cfg_path: str,
                      data_path: str, temp_data_path: str):
    '''
    Uses rclone to get the most recent experimental data available for this
    mouse. Prints some relevant information to the console for the experimenter
    and stores experimental parameters in a dict for use in this experiment.

    Arguments:
    ----------
    params: dict
        A dictionary containing the parameters for the current experiment.

    rclone_cfg_path: str
        A local path to an rclone.conf file.

    data_path: str
        A path from a remote drive (through rclone) to a data repository.

    temp_data_path: str
        Local path to a directory where data files will be temporarily stored.
    '''
    # Paths for rclone config file, data repo (on rclone) and a local directory
    # to temporarily store the fetched data.

    # Empty the temporary data folder
    for item in os.listdir(temp_data_path):
        os.remove(temp_data_path + item)
    # Read rclone config file
    with open(rclone_cfg_path) as f:
        rclone_cfg = f.read()

    # Generate dictionary with a string listing all dates
    prev_dates = rclone.with_config(rclone_cfg).run_cmd(
        command='lsf', extra_args=[data_path+params['mouse_number']])
    # Get most recent date
    last_date = prev_dates['out'][-12:-2].decode()

    last_data_path = f'{data_path}{params["mouse_number"]}/{last_date}/'
    # Copy all files from most recent date to the temp_data folder

    rclone.with_config(rclone_cfg).run_cmd(
        command='copy', extra_args=[last_data_path, temp_data_path])

    # os.system(f'rclone copy "{last_data_path}" {temp_data_path} --progress')
    # Double quotes around last_data_path to make it a single argument.

    last_file = sorted(os.listdir(temp_data_path))[-1]

    with h5py.File(temp_data_path+last_file, 'r') as f:
        # Get relevant information from the data file.

        prev_mapping = f['rule']['mapping'][-1]
        prev_countdown = f['rule']['countdown'][-1]
        prev_expert = f['rule']['expert'][-1]
        prev_p_rew = f['rule']['p_rew'][-1]
        prev_p_index = f['rule']['p_index'][-1]

        prev_resp = f['response']
        prev_trials = len(prev_resp)
        prev_resp_decoded = np.array([i.decode('utf-8') for i in prev_resp])
        prev_L = round((np.sum(prev_resp_decoded == 'L') / prev_trials), 2)
        prev_R = round((np.sum(prev_resp_decoded == 'R') / prev_trials), 2)
        prev_N = round((np.sum(prev_resp_decoded == 'N') / prev_trials), 2)

        # Print some relevant information to the console
        print(f'Date of last experiment: {last_date}')
        print(f'Previous user: {f["params"]["experimenter"]}')
        print(f'Previous weight: {f["params"]["mouse_weight"]}')
        print(f'Previous protocol: {f["params"]["protocol_name"]}')

        print(f'Previous trial number: {prev_trials}')
        print(f'Previous resp fraction: L:{prev_L}, R:{prev_R}, N:{prev_N}')
        print('-----------------------------------')
        print(f'Previous rule: [{prev_mapping}]')
        print(f'Reversal countdown: {prev_countdown}')
        print(f'Previous reward probability: {prev_p_rew}')
        print(f'Previous reward index: {prev_p_index}')
        print(f'Previous expert status: {prev_expert}')

        # Verify that the protocol is the same as previous. If not, warn user.
        if f.attrs['protocol_name'] != params['protocol_name']:
            input('--WARNING-- using a different protocol than last time.'
                  'Make sure this is intentional.')

        params['mapping'] = prev_mapping
        params['expert'] = prev_expert
        params['countdown'] = prev_countdown
        params['p_index'] = prev_p_index
