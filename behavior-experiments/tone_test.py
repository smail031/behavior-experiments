
import time
import numpy as np
import core
from pygame import mixer

mixer.init(frequency = 44100)

low_freq = 8000
high_freq = 12000

sample_tone_length = 2

lowfreq_L = core.LocalizedTone(low_freq, sample_tone_length, loc='L')
lowfreq_R = core.LocalizedTone(low_freq, sample_tone_length, loc='R') 
highfreq_L = core.LocalizedTone(high_freq, sample_tone_length, loc='L')
highfreq_R = core.LocalizedTone(high_freq, sample_tone_length, loc='R')


while True:

    lowfreq_L.play()
    lowfreq_R.play()
    highfreq_L.play()
    highfreq_R.play()


