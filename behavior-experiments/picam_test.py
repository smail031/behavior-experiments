import picamera

camera = picamera.PiCamera()
camera.start_preview(rotation = 180, fullscreen = False, window = (0,-44,350,400))
camera.resolution = (640, 480)
camera.rotation = (180)
camera.start_recording('my_video.mjpeg')
camera.wait_recording(10)
camera.stop_recording()
camera.stop_preview()
