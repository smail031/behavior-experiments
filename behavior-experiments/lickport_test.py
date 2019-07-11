import RPi.GPIO as GPIO
import time

lickport_pin = 12

GPIO.setmode(GPIO.BCM)
GPIO.setup(lickport_pin, GPIO.IN)



def Lick(sampling_rate, sampling_duration):
    #records the licks at a given sampling rate
#    _licks = []
#    _t_licks = []

    #calculate the number of samples needed
    num_samples = int(sampling_duration * sampling_rate)

    for i in range(num_samples):

        if GPIO.input(lickport_pin):
#            #register lick
#            _licks.append(1)
#            _t_licks.append(time.time())
            print('Lick')

        else:
#            #register no lick
#            _licks.append(0)
#            _t_licks.append(time.time())
            print('No lick')

        #wait for next sample and update step
        time.sleep(1/sampling_rate)

Lick(1, 40)
