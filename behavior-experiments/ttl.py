import core
import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

ttlPIN = 3

pulse_length = 0.1

ttl_output = core.ttl(ttlPIN)

ttl_output.pulse(pulse_length)

for i in range(10):
    print('cool')
