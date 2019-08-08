#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 15:38:32 2019

@author: sebastienmaille
"""

import core
import RPi.GPIO as GPIO
from picamera import PiCamera

camera = PiCamera()
camera.start_preview(rotation = 180, fullscreen = False, window = (0,-44,350,400))

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

L_enablePIN = 23 #enable pin for left stepper motor
L_directionPIN = 24 #direction pin for left stepper motor
L_stepPIN = 25 #step pin for left stepper motor
L_emptyPIN = 20 #empty switch pin for left stepper motor
L_lickometer = 12 #input pin for lickometer (black wire)


R_enablePIN = 10 #enable pin for right stepper motor
R_directionPIN = 9 #direction pin for right stepper motor
R_stepPIN = 11 #step pin for right stepper motor
R_emptyPIN = 21 #empty switch pin for right stepper motor
R_lickometer = 16 #input pin for lickometer (black wire)

stepperL = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
stepperR = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)

syringe = True
while syringe == True:

    side = input('Which side? (L/R/Q): ')

    if side == 'L':
        steps = input('How many steps?: ')
        stepperL.Motor(1, steps)
    elif side == 'R':
        steps = input('How many steps?: ')
        stepperR.Motor(1, steps)
    elif side == 'Q':
        syringe = False
    else:
        print('Not recognized.')

camera.stop_preview()
