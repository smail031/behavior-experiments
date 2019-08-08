from picamera import PiCamera
import time

camera = PiCamera()

camera.start_preview(rotation = 180, fullscreen = False, window = (0,-44,350,400))
time.sleep(15)
camera.stop_preview()