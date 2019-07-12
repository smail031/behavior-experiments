#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 10:32:10 2019

@author: sebastienmaille
"""

import core

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



#Create instances of class core.stepper for the left and right steppers
left = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
right = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)

left.Full_fill()
right.Full_fill()
