#In this test protocol, licks are simultaneously registered (in separate threads)
#from the two lickports at a given sampling rate. For each sample, the thread
#either prints (no lick) or (R/L lick).

import RPi.GPIO as GPIO
import time
import threading

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class lickport():

    def __init__(self, lickport_pin, side):

        self.lickport_pin = lickport_pin
        self.side = side


    def Lick(self, sampling_rate, sampling_duration):

        GPIO.setup(self.lickport_pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
        #records the licks at a given sampling rate

        num_samples = int(sampling_duration * sampling_rate) #calculate number of samples

        for i in range(num_samples):

            if GPIO.input(self.lickport_pin): #register lick
                print(f'{self.side} lick')

            else: #register no lick
                print('No lick')

            time.sleep(1/sampling_rate) #wait for next sample

left = lickport(12, 'left')
right = lickport(16, 'right')

thread_L = threading.Thread(target = left.Lick, args = (20, 300))
thread_R = threading.Thread(target = right.Lick, args = (20, 300))

thread_L.start()
thread_R.start()
