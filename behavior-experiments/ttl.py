import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

ttlPIN = 40
pulse_length = 5

GPIO.setup(ttlPIN, GPIO.OUT)

print('low')
GPIO.output(ttlPIN, 0)

time.sleep(5)

print('high')
GPIO.output(ttlPIN, 1)

time.sleep(5)

print('low')
GPIO.output(ttlPIN, 0)
