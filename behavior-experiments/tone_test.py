import time
import numpy as np
import os
from pygame import mixer

mixer.init(frequency = 44100)

class tones():

    def __init__(self, frequency, tone_length, pulse_length):

        #Create a string that will be the name of the .wav file
        self.name = f'{frequency}Hz_{pulse_length}sec'
        self.freq = frequency
        self.tone_length = tone_length
        self.pulse_length = pulse_length

        if self.tone_length == self.pulse_length: #determine if single or multi pulse tone
            self.multi_pulse = False
        else:
            self.multi_pulse = True

        if self.multi_pulse == False:
        #create a waveform called self.name from frequency and pulse_length
            os.system(f'sox -V0 -r 44100 -n -b 8 -c 2 {self.name}.wav synth {self.pulse_length} sin {self.freq} vol -20dB')

        elif self.multi_pulse == True:
            #create an empty wav file that will be the inter-pulse interval
            os.system(f'sox -V0 -r 44100 -n -b 8 -c 2 pulse.wav synth {self.pulse_length} sin {self.freq} vol -20dB')
            os.system(f'sox -V0 -r 44100 -n -b 8 -c 2 interpulse.wav synth {self.pulse_length} sin {self.freq/2} vol -20dB')

            os.system(f'sox pulse.wav interpulse.wav {self.name}.wav')

        self.sound = mixer.Sound(f'{self.name}.wav')

    def Play(self):


        self.sound.play() #play the .wav file and wait for it to end
        time.sleep(self.tone_length)

    def Delete(self):
        # Delete the wav file
        os.system(f'rm {self.name}.wav')

sound = tones(4000, 2, 1)

sound.Play()
sound.Delete()
