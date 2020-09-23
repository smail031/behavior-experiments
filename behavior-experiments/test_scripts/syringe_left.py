import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

L_enablePIN = 23 #enable pin for left stepper motor
L_directionPIN = 24 #direction pin for left stepper motor
L_stepPIN = 25 #step pin for left stepper motor
L_emptyPIN = 20 #empty switch pin for left stepper motor

class stepper():

    def __init__(self, enablePIN, directionPIN, stepPIN, emptyPIN):
        self.enablePIN = enablePIN
        self.directionPIN = directionPIN
        self.stepPIN = stepPIN
        self.emptyPIN = emptyPIN

        GPIO.setup(self.enablePIN, GPIO.OUT, initial=1) #disabled
        GPIO.setup(self.directionPIN, GPIO.OUT, initial=0)
        GPIO.setup(self.stepPIN, GPIO.OUT, initial=0)
        GPIO.setup(self.emptyPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def Motor(self, direction, steps):
        GPIO.output(self.enablePIN, 0) #enable the stepper motor
        GPIO.output(self.directionPIN, direction) #set direction

        for i in range(int(steps)): #move in "direction" for "steps"
            GPIO.output(self.stepPIN, 1)
            time.sleep(0.0001)
            GPIO.output(self.stepPIN, 0)
            time.sleep(0.0001)

        GPIO.output(self.enablePIN, 1) #disable stepper (to prevent overheating)

stepperL = stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)


while True:

        stepperL.Motor(1, 2000) #move forward 2000 steps
        stepperL.Motor(0,2000) #move backward 2000 steps
