#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 17:25:47 2019

@author: sebastienmaille
"""
import numpy as np
import h5py
import matplotlib.pyplot as plt

f = h5py.File('2002019.Jul.17.hdf5', 'r')

lick_r = f['lick_r']

t = lick_r['t']

trial1 = t[0]

dt = np.diff(trial1)

plt.plot(dt) 