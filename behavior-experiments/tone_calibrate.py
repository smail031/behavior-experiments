import time
import numpy as np
import core
from pygame import mixer

mixer.init(frequency = 44100)

low_freq = 6000
high_freq = 10000

sample_tone_length = 4

lowfreq = core.tones(low_freq, sample_tone_length, loc='B') #1000Hz single pulse
highfreq = core.tones(high_freq, sample_tone_length, loc='B') #1000Hz multi pulse

while True:

    lowfreq.Play()
    highfreq.Play()


