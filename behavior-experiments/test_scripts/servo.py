#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 10:40:57 2019

@author: sebastienmaille
"""
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

servo_pin = 17 #PWM pin for servo that adjusts lickport distance

GPIO.setup(servo_pin, GPIO.OUT)

servo = GPIO.PWM(servo_pin, 50)  # instantiate PWM with pin and 50Hz frequency
servo.start(1)  # Initialization

cont = True
while cont == True:

    new_DC = input('Input new duty cycle (quit:Q): ') #ask user for new duty cycle

    if new_DC == 'Q':
        cont = False

    else:
        servo.ChangeDutyCycle(float(new_DC)) #change duty cycle'
