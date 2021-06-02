#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 02 11:47:22 2021

@author: sebastienmaille
"""
import time
import RPi.GPIO as GPIO
import core
from pygame import mixer

#------------------------------------------------------------------------------
#Set experimental parameters:
#------------------------------------------------------------------------------


sample_tone_length = 2 #length of sample tone
single_pulse_length = 2

tone_freq = 4000 #frequency of sample tone in left lick trials

reward_size = 8.2 #size of water rewards in uL

#----------------------------
#Assign GPIO pins:
#----------------------------

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

#----------------------------
#Initialize class instances for experiment:
#----------------------------

#Turn off the GPIO warnings
GPIO.setwarnings(False)

#Set the mode of the pins (broadcom vs local)
GPIO.setmode(GPIO.BCM)

#set the enable pins for L and R stepper motors to 1 to prevent overheating
GPIO.setup(L_enablePIN, GPIO.OUT, initial = 1)
GPIO.setup(R_enablePIN, GPIO.OUT, initial = 1)

#initialize the mixer (for tones) at the proper sampling rate.
mixer.init(frequency = 44100)

#create Stepper class instance
water = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)

#create  tone
tone = core.tones(tone_freq, sample_tone_length, single_pulse_length) #1000Hz single pulse

loop = True

while loop == True:
    
    raw_input = input('Ready to play tone (ENTER) ')
    
    tone.Play()
    water.Reward()

    time.sleep(2)

    water.Reward()
    tone.play()

    again = input('Try again? (y/n): ')

    if again == 'n':
        
        loop = False

    
tone.Delete()
