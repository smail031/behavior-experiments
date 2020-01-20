#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 10:40:57 2019

@author: sebastienmaille
"""
#from picamera import PiCamera

#camera = PiCamera()
#camera.start_preview(rotation = 180, fullscreen = False, window = (0,-44,350,400))

import core
import RPi.GPIO as GPIO


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

servo_PWM = 17 #PWM pin for servo that adjusts lickport distance

servo = core.servo(servo_PWM) #initialize instance of class servo

cont = True

while cont == True:

    new_DC = input('Input new duty cycle (quit:Q): ') #ask user for new duty cycle

    if new_DC == 'Q':
        cont = False

    else:
        servo.Adjust(float(new_DC)) #change duty cycle'

#camera.stop_preview()
