import time
import RPi.GPIO as GPIO
import numpy as np
import core
from picamera import PiCamera
from pygame import mixer

protocol_name = 'classical_single'
protocol_description = ('In this protocol, one of 2 tones (differing based'
                        'on frequency) is played each trial. This is followed'
                        'by a 2s waiting period, after which reward is '
                        'delivered from a single port the tone indicates the '
                        'volume of the reward.')

camera = PiCamera()  # Create camera object
camera.start_preview(fullscreen=False, window=(0, -44, 350, 400))

# ------------------------------------------------------------------------------
# Set experimental parameters:
# ------------------------------------------------------------------------------

experimenter = input('Initials: ')
mouse_number = input('mouse number: ')
mouse_weight = float(input('mouse weight(g): '))

block_number = input('Block number: ')
n_trials = int(input('How many trials?: '))
random_delay = input('Random delays?: ') == 'y'
syringe_check = input('Syringe check: ')

sample_tone_length = 1  # Length of sample tone (s)
low_freq = 3000  # Frequency(Hz) of high frequency sample tone.
high_freq = 6000  # Frequency(Hz) of high frequency sample tone.

end_tone_freq = 2000
end_tone_length = 8

reward_size = 10  # Volume(uL) of water rewards.

# -----------------------------------------------------------------------------
# Assign GPIO pins:
# -----------------------------------------------------------------------------

servo_PWM = 17  # PWM pin for servo that adjusts lickport distance

R_enablePIN = 10  # Enable pin for right stepper motor
R_directionPIN = 9  # Direction pin for right stepper motor
R_stepPIN = 11  # Step pin for right stepper motor
R_emptyPIN = 21  # Empty switch pin for right stepper motor
R_lickometer = 16  # Input pin for lickometer (black wire)

TTL_trigger_PIN = 15  # Output for TTL pulse triggers to start/end laser scans
TTL_marker_PIN = 27  # Output for TTL pulse markers

# -----------------------------------------------------------------------------
# Initialize class instances for experiment:
# -----------------------------------------------------------------------------

# Turn off the GPIO warnings
GPIO.setwarnings(False)

# Set the mode of the pins (broadcom vs local)
GPIO.setmode(GPIO.BCM)

# Set the enable pins for L and R stepper motors to 1 to prevent overheating
GPIO.setup(R_enablePIN, GPIO.OUT, initial=1)

# Initialize the mixer (for tones) at the proper sampling rate.
mixer.init(frequency=44100)

# Create Stepper class instances for left and right reward delivery
water_R = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)

# Create lickometer class instances for left and right lickometers
lick_port_R = core.lickometer(R_lickometer)

# Create instruction tones
lowfreq_tone = core.PureTone(low_freq, sample_tone_length)
highfreq_tone = core.PureTone(high_freq, sample_tone_length)

# Create tone that is used as an error signal
tone_end = core.PureTone(end_tone_freq, end_tone_length, vol=-25)

# -----------------------------------------------------------------------------
# Initialize experiment:
# -----------------------------------------------------------------------------

trials = np.arange(n_trials)
data = core.data(protocol_name, protocol_description, n_trials, mouse_number,
                 block_number, experimenter, mouse_weight)

tones = [lowfreq_tone, highfreq_tone]
volumes = [10, 5]
steps = [250, 125]

trial_types = np.random.choice([0, 1], len(trials))
trial_tone = [tones[i] for i in trial_types]
trial_vol = [volumes[i] for i in trial_types]
trial_steps = [steps[i] for i in trial_types]

# Set reward delays.
if random_delay:
    delays = np.random.normal(loc=2, scale=4, size=len(trials))
else:
    delays = np.full(shape=len(trials), fill_value=2)

total_reward = 0

# -----------------------------------------------------------------------------
# Iterate through trials:
# -----------------------------------------------------------------------------

for trial, tone, vol, step, delay in zip(trials, trial_tone, trial_vol,
                                         trial_steps, delays):

    # Take time at trial start
    data._t_start_abs[trial] = time.time()*1000
    data.t_start[trial] = data._t_start_abs[trial] - data._t_start_abs[0]

    # Start lick recording
    lick_port_R.Lick(1000, 11)

    # Baseline licking.
    time.sleep(4)

    # Tone delivery.
    data.t_sample_tone[trial] = time.time()*1000 - data._t_start_abs[trial]
    tone.Play()  # Play left tone
    data.sample_tone_end[trial] = (time.time()*1000
                                   - data._t_start_abs[trial])

    # Trace period.
    time.sleep(delay)

    # Reward delivery.
    data.t_rew_r[trial] = (time.time()*1000 - data._t_start_abs[trial])
    water_R.Reward(steps=step)
    data.v_rew_r[trial] = vol
    total_reward += vol

    # Take time at trial end
    data.t_end[trial] = time.time()*1000 - data._t_start_abs[0]

    # -------------------------------------------------------------------------
    # Post-trial data storage
    # -------------------------------------------------------------------------

    # Process and store lick data.
    lick_port_R._t_licks -= data._t_start_abs[trial]

    data.lick_r[trial] = {}
    data.lick_r[trial]['t'] = lick_port_R._t_licks
    data.lick_r[trial]['volt'] = lick_port_R._licks

    data.freq[trial] = tone.freq  # Store tone frequency

    licks_detected = ''
    # Will indicate which ports recorded any licks in the entire trial.
    if sum(lick_port_R._licks) != 0:
        licks_detected += 'R'

    print(f'Trial: {trial+1}, Tone:{tone.freq}, Licks:{licks_detected}')

    # -------------------------------------------------------------------------
    # Deliver supplementary rewards:
    # -------------------------------------------------------------------------

    ITI_ = 0
    while ITI_ > 30 or ITI_ < 10:
        ITI_ = np.random.exponential(scale=20)

    time.sleep(ITI_)


tone_end.play()
camera.stop_preview()

print(f'Total reward: {total_reward} uL')
data.total_reward = total_reward

# Ask the user if there were any problems with the experiment. If so, prompt
# the user for an explanation that will be stored in the data file.
data.exp_quality = input('Should this data be used? (y/n): ')
if data.exp_quality == 'n':
    data.exp_msg = input('What went wrong?: ')

# Store the data in an HDF5 file and upload this file to a remote drive.
data.Store()
data.Rclone()

# Delete the .wav files created for the experiment
core.delete_tones()
