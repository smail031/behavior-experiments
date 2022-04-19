import core
import RPi.GPIO as GPIO
import threading

#setup GPIOs
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

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

#----------------------------
# Empty the syringes.
#----------------------------

wait = input(f'Will empty the syringe. Hit ENTER when ready')

left = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
right = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)
    
left_thread = threading.Thread(target = left.empty)
right_thread = threading.Thread(target = right.empty)
    
left_thread.start()
right_thread.start()

left_thread.join()
right_thread.join()

#----------------------------
# Fill the syringes.
#----------------------------

wait = input(f'Will fill the syringe. Hit ENTER when ready')

left_thread = threading.Thread(target = left.fill)
right_thread = threading.Thread(target = right.fill)
    
left_thread.start()
right_thread.start()

left_thread.join()
right_thread.join()
