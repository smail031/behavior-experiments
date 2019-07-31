#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 10:40:57 2019

@author: sebastienmaille
"""

import core
import RPi.GPIO as GPIO

servo_PWM = 17 #PWM pin for servo that adjusts lickport distance

servo = core.servo(servo_PWM) #initialize instance of class servo

new_DC = input('Input new duty cycle: ') #ask user for new duty cycle

servo.Adjust(new_DC) #change duty cycle'

