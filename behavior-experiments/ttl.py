import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

ttlPIN = 21
pulse_length = 1

GPIO.setup(ttlPIN, GPIO.OUT)
GPIO.output(ttlPIN, False)

go = input('ready?')

GPIO.output(ttlPIN, True)
time.sleep(pulse_length)
GPIO.output(ttlPIN, False)

print('done')
