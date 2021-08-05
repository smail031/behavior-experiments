#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 05 10:32:10 2021

@author: sebastienmaille
"""

import core
import RPi.GPIO as GPIO
import threading

#setup GPIOs
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#----------------------------
#Assign GPIO pins:
#----------------------------

L_enablePIN = 23 #enable pin for left stepper motor
L_directionPIN = 24 #direction pin for left stepper motor
L_stepPIN = 25 #step pin for left stepper motor
L_emptyPIN = 20 #empty switch pin for left stepper motor


R_enablePIN = 10 #enable pin for right stepper motor
R_directionPIN = 9 #direction pin for right stepper motor
R_stepPIN = 11 #step pin for right stepper motor
R_emptyPIN = 21 #empty switch pin for right stepper motor

#----------------------------
#Ask which side and call refill:
#----------------------------

n_flush = 5 #how many times to flush

wait = input(f'Will flush {n_flush} times. Hit ENTER when ready')

for flush in range(n_flush):
    
    left = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
    right = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)
    
    left_thread = threading.Thread(target = left.Refill)
    right_thread = threading.Thread(target = right.Refill)
    
    left_thread.start()
    right_thread.start()

    left_thread.join()
    right_thread.join()

