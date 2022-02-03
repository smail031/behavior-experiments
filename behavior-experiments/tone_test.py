
import time
import numpy as np
import core
from pygame import mixer

mixer.init(frequency = 44100)

low_freq = 6000
high_freq = 10000

sample_tone_length = 2

lowfreq = core.PureTone(low_freq, sample_tone_length)
#lowfreq_R = core.LocalizedTone(low_freq, sample_tone_length) 
highfreq = core.PureTone(high_freq, sample_tone_length)
#highfreq_R = core.LocalizedTone(high_freq, sample_tone_length)


while True:

    lowfreq.play()
    #lowfreq_R.play()
    highfreq.play()
    #highfreq_R.play()


