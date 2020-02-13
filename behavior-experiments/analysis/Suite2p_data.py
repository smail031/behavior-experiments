import numpy as np
import matplotlib.pyplot as plt
import os

os.chdir('/Users/sebastienmaille/Desktop/4514_block9_TIFF/suite2p/plane0/')

F = np.load('F.npy')

num_roi = F.shape[0]

plt.plot(F[13])

plt.show()
