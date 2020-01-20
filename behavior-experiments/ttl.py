import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

ttl_out_PIN = 21
ttl_in_PIN = 20
pulse_length = 0.01

GPIO.setup(ttl_in_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ttl_out_PIN, GPIO.OUT)
GPIO.output(ttl_out_PIN, False)

go = input('ready?')

start_time = time.time()*1000
pulse_time = time.time()*1000 - start_time

GPIO.output(ttl_out_PIN, True)
time.sleep(pulse_length)
GPIO.output(ttl_out_PIN, False)

sent_time = time.time()*1000 - start_time

while GPIO.input(ttl_in_PIN) == False:
    print('cool')

received_time = time.time()*1000 - start_time

print(pulse_time)
print(sent_time)
print(received_time)
