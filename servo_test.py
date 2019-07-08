#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 15:57:01 2019

@author: sebastienmaille
"""

import RPi.GPIO as GPIO
import time
 
servoPIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(servoPIN, GPIO.OUT)
 
p = GPIO.PWM(servoPIN, 50)  # GPIO 17 for PWM with 50Hz
p.start(3.5)  # Initialization
try:
    while True:
#        p.ChangeDutyCycle(2.5)
#        time.sleep(0.5)
#        p.ChangeDutyCycle(3.5)
#        time.sleep(0.5)
        p.ChangeDutyCycle(4.5)
        time.sleep(0.5)
        p.ChangeDutyCycle(5.5)
        time.sleep(0.5)
        p.ChangeDutyCycle(6.5)
        time.sleep(0.5)
        p.ChangeDutyCycle(7.5)
        time.sleep(0.5)
        p.ChangeDutyCycle(8.5)
        time.sleep(0.5)
        p.ChangeDutyCycle(9.5)
        time.sleep(1)
#        p.ChangeDutyCycle(10.5)
#        time.sleep(0.5)
#        p.ChangeDutyCycle(11.5)
#        time.sleep(0.5)
#        p.ChangeDutyCycle(12.5)
#        time.sleep(1)
except KeyboardInterrupt:
    p.stop()
    GPIO.cleanup()
