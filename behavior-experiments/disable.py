#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 14:42:52 2019

@author: sebastienmaille
"""
#When the EasyDriver is initiated, the enable pin will be set to 0 (enabled) by
#default, which will send power to the coils of the stepper motor and could lead
#to overheating. The purpose of this script is simply to reset the enable pins
#to 1 (disabled) to prevent this. This script should be run as soon as the 
#EasyDrivers are plugged in.

import core
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

L_enablePIN = 23 #enable pin for left stepper motor
L_directionPIN = 24 #direction pin for left stepper motor
L_stepPIN = 25 #step pin for left stepper motor
L_emptyPIN = 20 #empty switch pin for left stepper motor


R_enablePIN = 10 #enable pin for right stepper motor
R_directionPIN = 9 #direction pin for right stepper motor
R_stepPIN = 11 #step pin for right stepper motor
R_emptyPIN = 21 #empty switch pin for right stepper motor

#Create instances of class core.stepper for right and left
left = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
right = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)

#Call Disable method from class stepper to set enablePIN to 1 (disabled)
left.Disable()
right.Disable()

print('Disabled.')