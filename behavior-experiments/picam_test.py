import picamera

camera = picamera.PiCamera()
camera.resolution = (640, 480)
camera.rotation = (180)
camera.start_recording('my_video.mjpeg')
camera.wait_recording(10)
camera.stop_recording()
