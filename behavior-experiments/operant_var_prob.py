import time
import RPi.GPIO as GPIO
import numpy as np
import threading
import core2
from picamera import PiCamera
from pygame import mixer

protocol_name = 'operant_var_prob'
protocol_description = ('Each trial, 1 of 2 sample cues (differing based'
                        'on frequency) is immediately followed by a response '
                        'period. During this period, the first lickport that '
                        'registers a lick determines the animals response. '
                        'Correct responses trigger reward delivery from the '
                        'correct port with probability p_rew, while incorrect '
                        'or null responses are unrewarded. if 19/20 trials are'
                        ' correct, the mouse is considered an "expert".')

rclone_cfg_path = '/home/pi/.config/rclone/rclone.conf'
data_path = 'sharepoint:Data/Behaviour Data/Sebastien/Dual_Lickport/Mice/'
temp_rclone_path = '/home/pi/Desktop/temp_rclone/'
temp_data_path = '/home/pi/Desktop/temporary_data/'

camera = PiCamera()  # Create camera object
camera.start_preview(fullscreen=False, window=(0, -44, 350, 400))

# ------------------------------------------------------------------------------
# Set experimental parameters:
# ------------------------------------------------------------------------------

keys = ['mapping', 'expert', 'countdown', 'p_index']
params = dict.fromkeys(keys)

params['protocol_name'] = protocol_name
params['experimenter'] = input('Initials: ')
params['mouse_number'] = input('mouse number: ')
params['mouse_weight'] = float(input('mouse weight(g): '))

if input('Fetch previous data? (y/n) ') == 'y':
    core2.get_previous_data(params, rclone_cfg_path,
                            data_path, temp_rclone_path)

core2.input_params(params)
params['protocol_description'] = protocol_description

block_number = input('block number: ')
n_trials = int(input('How many trials?: '))
# Ask Kirk if we can omit the statement below (always send TTL)
ttl_experiment = input('Send trigger pulses to imaging laser? (y/n): ')
syringe_check = input('Syringe check: ')

response_window = 2000  # Time window(ms) for animals to respond after cue.

sample_tone_length = 2  # Length of sample tone (s)
low_freq = 6000  # Frequency(Hz) of high frequency sample tone.
high_freq = 10000  # Frequency(Hz) of high frequency sample tone.

wrong_tone_freq = 14000
wrong_tone_length = 1
end_tone_freq = 4000  # Tone to signal the end of the experiment.
end_tone_length = 8

# ------------------------------------------------------------------------------
# Assign GPIO pins:
# ------------------------------------------------------------------------------

servo_PWM = 17  # PWM pin for servo that adjusts lickport distance

L_enablePIN = 23  # Enable pin for left stepper motor
L_directionPIN = 24  # Direction pin for left stepper motor
L_stepPIN = 25  # Step pin for left stepper motor
L_emptyPIN = 20  # Empty switch pin for left stepper motor
L_lickometer = 12  # Input pin for lickometer (black wire)


R_enablePIN = 10  # Enable pin for right stepper motor
R_directionPIN = 9  # Direction pin for right stepper motor
R_stepPIN = 11  # Step pin for right stepper motor
R_emptyPIN = 21  # Empty switch pin for right stepper motor
R_lickometer = 16  # Input pin for lickometer (black wire)

TTL_trigger_PIN = 15  # output for TTL pulse triggers to start/end laser scans
TTL_marker_PIN = 27  # output for TTL pulse markers

# ------------------------------------------------------------------------------
# Initialize class instances for experiment:

# ------------------------------------------------------------------------------

# Turn off the GPIO warnings
GPIO.setwarnings(False)

# Set the mode of the pins (broadcom vs local)
GPIO.setmode(GPIO.BCM)

# Initialize the mixer (for tones) at the proper sampling rate.
mixer.init(frequency=44100)

# Initialize trial object.
trial_obj = core2.Trial('trial', n_trials)

# Initialize reward delivery.
water_L = core2.Stepper('left reward', trial_obj, L_enablePIN, L_directionPIN,
                        L_stepPIN, L_emptyPIN)
water_R = core2.Stepper('right reward', trial_obj, R_enablePIN, R_directionPIN,
                        R_stepPIN, R_emptyPIN)

# Inialize supplementary reward delivery.
supp_water_L = core2.Stepper('left reward', trial_obj, L_enablePIN,
                             L_directionPIN, L_stepPIN, L_emptyPIN)
supp_water_R = core2.Stepper('right reward', trial_obj, R_enablePIN,
                             R_directionPIN, R_stepPIN, R_emptyPIN)

# Initialize lick detection.
lick_port_L = core2.LickDetect('left licks', trial_obj, L_lickometer)
lick_port_R = core2.LickDetect('right licks', trial_obj, R_lickometer)

# Initialize instruction tones.
lowfreq = core2.PureTone('6kHz tone', trial_obj, low_freq, sample_tone_length)
highfreq = core2.PureTone('10kHz tone', trial_obj, high_freq,
                          sample_tone_length)

# Initialize other tones.
tone_wrong = core2.PureTone('error tone', trial_obj, wrong_tone_freq,
                            wrong_tone_length)
tone_end = core2.PureTone('end tone', trial_obj, end_tone_freq,
                          end_tone_length, vol=-25)

# Initialize the rule.
sample_tones = [lick_port_L, lick_port_R]
rule = core2.ProbSwitchRule('rule', trial_obj, sample_tones, params)

if ttl_experiment == 'y':
    # Initialize TTL trigger and marker for imaging.
    TTL_trigger = core2.ImagingTTL('trigger TTL', trial_obj, TTL_trigger_PIN)
    TTL_marker = core2.ImagingTTL('marker TTL', trial_obj, TTL_marker_PIN)

# Initialize data collection
objects = [trial_obj, water_L, water_R, lick_port_L, lick_port_R, lowfreq,
           highfreq, tone_wrong, rule, TTL_trigger, TTL_marker]
data = core2.Data(objects, params['mouse_number'], params)

# -------------------------------------------------------------------------------
# Iterate through trials:
# -------------------------------------------------------------------------------

# Start imaging laser scanning
if ttl_experiment == 'y':
    TTL_trigger.pulse()

for trial in range(n_trials):
    # Initialize thread objects for left and right lickport recording
    thread_L = threading.Thread(target=lick_port_L.lick_detection)
    thread_R = threading.Thread(target=lick_port_R.lick_detection)

    trial_obj.trial_start()

    # Start lick recording threads
    thread_L.start()
    thread_R.start()

    time.sleep(2)

    # Mark the start of the trial
    if ttl_experiment == 'y':
        TTL_marker.pulse()

    tone = np.random.choice(sample_tones)
    tone.play()

    response = 'N'
    length_L = len(lick_port_L.lick_voltage)
    length_R = len(lick_port_R.lick_voltage)
    resp_window_end = time.time()*1000 + response_window

    while time.time() * 1000 < resp_window_end:
        # Check for any lick on the left port
        if sum(lick_port_L.lick[(length_L-1):]) > 0:
            response = 'L'
            reward_port = water_L
            break

        # Check for any lick on the right port
        elif sum(lick_port_R._licks[(length_R-1):]) > 0:
            response = 'R'
            reward_port = water_R
            break

    if rule.evaluate(tone, response):
        reward_port.reward()

    else:
        tone_wrong.play()

    # Wait until the lick detection threads are finished.
    thread_L.join()
    thread_R.join()

    # Print some trial data for to the console for the experimenter.
    rule.print_trial_stats(lick_port_L, lick_port_R)

    # Deliver supplementary rewards if needed.
    rule.supplementary_rewards(supp_water_L, supp_water_R)

    rule.check_criterion()

    trial_obj.inter_trial_interval()

# Stop imaging laser scanning.
if ttl_experiment == 'y':
    TTL_trigger.pulse()

tone_end.play()
camera.stop_preview()

reward_L = np.nansum(water_L.data['volume'])
supp_reward_L = np.nansum(supp_water_L.data['volume'])
reward_R = np.nansum(water_R.data['volume'])
supp_reward_R = np.nansum(supp_water_R.data['volume'])
print(f'Total L reward: {reward_L} uL + {supp_reward_L}')
print(f'Total R reward: {reward_R} uL + {supp_reward_R}')
total_reward = sum([reward_L, supp_reward_L, reward_R, supp_reward_R])
print(f'Total reward: {total_reward}uL')

# Ask the user if there were any problems with the experiment. If so, prompt
# the user for an explanation that will be stored in the data file.
params['exp_quality'] = input('Should this data be used? (y/n): ')
if params['exp_quality'] == 'n':
    params['exp_msg'] = input('What went wrong?: ')

# Store the data in an HDF5 file and upload this file to a remote drive.
data.package_data()
data.rclone_upload(rclone_cfg_path, data_path, temp_data_path)

# Delete the .wav files created for the experiment
core2.delete_tones()
