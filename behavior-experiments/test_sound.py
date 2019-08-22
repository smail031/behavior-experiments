from pygame import mixer
import os
import core
import time
import threading

mixer.init(frequency = 44100)

tone_1 = core.tones(1000, 3)
tone_2 = core.tones(4000, 3)

tone_1_thread = threading.Thread(target = tone_1.sound.play())
tone_1_thread.start()

# tone_1.Play()
time.sleep(0.5)
tone_1.sound.stop()
tone_2.Play()
time.sleep(1)

tone_1_thread.join()
tone_1.Delete()
tone_2.Delete()
