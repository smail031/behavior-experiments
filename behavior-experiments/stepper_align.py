#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 24 15:38:32 2021

@author: sebastienmaille
"""

import core
import RPi.GPIO as GPIO
from pynput.keyboard import Key, Listener
import threading

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
R_emptyPIN = 21 #empty switch pin for right stepper msotor
R_lickometer = 16 #input pin for lickometer (black wire)

def press_callback(key):

    #print('SPACE:move motor, BACKSPACE:quit')
    
    if key == Key.space:

        stepper.start = True
        stepper.cont = True

    elif key == Key.backspace:

        stepper.cont = False
        
        
def release_callback(key):

    #if key == Key.space:

    stepper.cont = False
    

syringe = True
while syringe == True:

    side = input('Which side? (L/R/Q): ')

    if side == 'L':

        stepper = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
        
    elif side == 'R':

        stepper = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)
        
    elif side == 'Q':
        syringe = False
        
    else:
        print('Not recognized.')

    testing = True
    while testing == True:
        
        listen = Listener(on_press=press_callback, on_release=release_callback)
        motor = threading.Thread(target = stepper.Run)

        motor.start()
        listen.start()

        motor.join()
        listen.join()

        print('ya')
