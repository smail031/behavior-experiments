import os
from pygame import mixer

class tones():

    def __init__(self, frequency, tone_length):

        #Create a string that will be the name of the .wav file
        self.name = str(frequency) + 'Hz'
        self.freq = frequency
        self.length = tone_length

        #create a waveform called self.name from frequency and tone_length
        os.system(f'sox -V0 -r 44100 -n -b 8 -c 2 {self.name}.wav synth {self.length} sin {self.freq} vol -20dB')

        self.sound = mixer.Sound(f'{self.name}.wav')

    def Play(self):
        #play the .wav file and wait for it to end while self.cut is False
        self.sound.play()
        time.sleep(self.length)

    def Delete(self):
        # Delete the wav file
        os.system(f'rm {self.name}.wav')

mixer.init(frequency = 44100) #initialize the mixer at the proper sampling rate

tone_freq = input('Frequency (Hz):')
tone_length = input('Length (s):')

tone = tones(tone_freq,tone_length)

tone.Play() #play the tone

tone.Delete() #delete the tone
