#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:04:50 2019

@author: sebastienmaille
"""

import RPi.GPIO as GPIO
import time
 
enablePIN = 23
directionPIN = 24
stepPIN = 25
emptyPIN = 20
 
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(enablePIN, GPIO.OUT, initial=0)
GPIO.setup(directionPIN, GPIO.OUT, initial=0)
GPIO.setup(stepPIN, GPIO.OUT, initial=0)
GPIO.setup(emptyPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
 
if GPIO.input(emptyPIN):
    GPIO.output(enablePIN, 0)
    GPIO.output(directionPIN, 1)
    for i in range(800):
        GPIO.output(stepPIN, 1)
        time.sleep(0.0005)
        GPIO.output(stepPIN, 0)
        time.sleep(0.0005)
#    GPIO.cleanup()
else:
    GPIO.output(enablePIN, 1)
GPIO.output(enablePIN, 1)