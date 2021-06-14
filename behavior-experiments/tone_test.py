
import time
import numpy as np
import core
from pygame import mixer

mixer.init(frequency = 44100)

lowfreq_L = core.tones(low_freq, sample_tone_length, loc='L') #1000Hz single pulse
lowfreq_R = core.tones(low_freq, sample_tone_length, loc='R') #1000Hz multi pulse
highfreq_L = core.tones(high_freq, sample_tone_length, loc='L') #4000Hz single pulse
highfreq_R = core.tones(high_freq, sample_tone_length, loc='R') #4000Hz multi pulse


while True:

    lowfreq_L.Play()
    lowfreq_R.Play()
    highfreq_L.Play()
    highfreq_R.Play()


