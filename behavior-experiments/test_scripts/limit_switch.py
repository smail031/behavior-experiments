import RPi.GPIO as GPIO
import time
import threading

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class limit_switch():

    def __init__(self, pin, side):

        self.pin = pin
        self.side = side


    def Switch(self, sampling_rate, sampling_duration):

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        #records the licks at a given sampling rate

        num_samples = int(sampling_duration * sampling_rate) #calculate number of samples

        for i in range(num_samples):

            if GPIO.input(self.pin) == 0: #register switch
                print(f'{self.side} switch')

            else: #register no switch
                print('No switch')

            time.sleep(1/sampling_rate) #wait for next sample

L_limit_PIN = 20 #empty switch pin for left syringe pump
R_limit_PIN = 21 #empty switch pin for right syringe pump

left = limit_switch(L_limit_PIN, 'left')
right = limit_switch(R_limit_PIN, 'right')

thread_L = threading.Thread(target = left.Switch, args = (20, 30))
thread_R = threading.Thread(target = right.Switch, args = (20, 30))

thread_L.start()
thread_R.start()
