#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 10:40:57 2019

@author: sebastienmaille
"""
from picamera import PiCamera

camera = PiCamera()
camera.start_preview(rotation = 180, fullscreen = False, window = (0,-44,350,400))

import core
import RPi.GPIO as GPIO


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

servo_PWM = 17 #PWM pin for servo that adjusts lickport distance

servo = core.servo(servo_PWM) #initialize instance of class servo

cont = True

while cont == True:

    new_DC = float(input('Input new duty cycle (quit:q): ')) #ask user for new duty cycle

    if new_DC == 'q':
        cont = False

    elif new_DC > 11 or new_DC < 7:
        veto = input('Duty cycly is unusually high/low. Proceed? (y/n)')
        #warns user if DC is too high or low, to avoid hurting the mouse or damaging the rig

        if veto = 'y':
            servo.Adjust(new_DC) #change duty cycle'

    else:
        servo.Adjust(new_DC) #change duty cycle'

camera.stop_preview()
