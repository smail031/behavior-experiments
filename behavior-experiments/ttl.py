import core
import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

ttlPIN = 40

pulse_length = 5

ttl_output = core.ttl(ttlPIN)
print('low')
time.sleep(5)
print('high')
ttl_output.pulse(pulse_length)

for i in range(10):
    print('cool')
