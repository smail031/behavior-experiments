import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

ttl_out_PIN = 21
ttl_in_PIN
pulse_length = 1
pulse_received = False

GPIO.setup(ttl_in_PIN, GPIO.IN)
GPIO.setup(ttl_out_PIN, GPIO.OUT)
GPIO.output(ttl_out_PIN, False)

go = input('ready?')

start_time = time.time()

GPIO.output(ttlPIN, True)
time.sleep(pulse_length)
GPIO.output(ttlPIN, False)

sent_time = time.time() - start_time

while pulse_received == False:
    if GPIO.input(ttl_in_PIN):
        pulse_received == True

received_time = time.time() - start_time

print(sent_time)
print(received_time)
