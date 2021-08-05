import core #Imports the classes from core.py, which are used for syringes, tones and lickometer
from pygame import mixer #Allows us to play .wav files through the speakers
import time #Allows us to take timestamps and wait for set amounts of time
import RPi.GPIO as GPIO #Allows us to control GPIO pins on the Raspberry Pi
import threading #Allows us to run different functions at the same time
from picamera import PiCamera #Allows us to control the Raspberry Pi camera

#----------------------------
#Assign General Purpose Input/Output (GPIO) pins:
#----------------------------

#Each syringe pump has 4 pins: enable, direction, step and empty(limit).
L_enablePIN = 23 #enable pin for left stepper motor
L_directionPIN = 24 #direction pin for left stepper motor
L_stepPIN = 25 #step pin for left stepper motor
L_emptyPIN = 20 #empty switch pin for left stepper motor

L_lickometer = 12 #input pin for lickometer (black wire)


R_enablePIN = 10 #enable pin for right stepper motor
R_directionPIN = 9 #direction pin for right stepper motor
R_stepPIN = 11 #step pin for right stepper motor
R_emptyPIN = 21 #empty switch pin for right stepper motor

R_lickometer = 16 #input pin for lickometer (black wire)


#----------------------------
#Initialize class instances:
#----------------------------

#Turn off the GPIO warnings
GPIO.setwarnings(False)

#Set the mode of the pins (broadcom vs local)
GPIO.setmode(GPIO.BCM)

#set the enable pins for L and R stepper motors to 1 to prevent overheating
GPIO.setup(L_enablePIN, GPIO.OUT, initial = 1)
GPIO.setup(R_enablePIN, GPIO.OUT, initial = 1)

#----------------------------
#Test and refill syringe pumps:
#----------------------------

refill = input('Refill tubes? (y/n): ')

if refill == 'y':
    #create Stepper class instances for left and right reward delivery
    water_L = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
    water_R = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)
    
    syringe_test = input('Prepare syringes for refill (ENTER) ')
    #nothing is stored, just to make sure user is ready
    
    left_thread = threading.Thread(target = water_L.Refill) #Initialize thread for L syringe
    right_thread = threading.Thread(target = water_R.Refill) #Initialize thread for R syringe
    #The thread will run the stepper.Refill method, and can run several instances simultaneously
    
    left_thread.start() #start thread for L syringe
    right_thread.start() #start thread for R syringe
    
    tube_fill = input('Reconnect and fill water tubes (ENTER) ')
    #reminder to reconnect and manually spin the syringe pumps

#----------------------------
#Test speakers:
#----------------------------

#initialize the mixer (for tones) at the proper sampling rate.
mixer.init(frequency = 44100)

test_tone = core.tones(1000,2) #generates a .wav file with a 2 second tone at 1000Hz

print('Testing speakers.')

speaker_test = 'a' #Initialize speaker_test variable to 'a'; see below
while speaker_test == 'a':

    test_tone.Play() #play the test tone
    speaker_test = input('Did you hear the tone? y:yes, a:again: ')

test_tone.Delete() #delete the .wav file that was created

#----------------------------
#Test lick detection:
#----------------------------

#create lickometer class instances for left and right lickometers
lick_port_L = core.lickometer(L_lickometer)
lick_port_R = core.lickometer(R_lickometer)

print('Testing lick detection.')

left_works = False #this will be set to True if a contact
while left_works == False:

    thread_L = threading.Thread(target=lick_port_L.Lick, args=(1000,10))                
    thread_L.start() #start left lickport thread
    
    print('Touch ground + left lickport')
    start_time = time.time() #get a timestamp for the start of lick detection

    while time.time() < start_time + 10: #run this loop for 10 seconds

        if sum(lick_port_L._licks) > 0:
            #lick_port_L._licks registers 0 with no contact but 1 with contact
            #if sum(lick_port_L._licks) > 0, there was a contact at some point

            left_works = True #register that a contact was detected
            break #exit the 10 second loop

    if left_works == True:
        print('Left contact detected')
        test_tone.Play()
    else:
        print('No contact detected')

        try_again = input('Try again? (y/n)')

        if try_again == 'n':
            left_works = True #Setting left_works to True will exit the outer while loop
            #Otherwise, the loop will run again

#Same thing for the R lickport
right_works = False
while right_works == False:

    thread_R = threading.Thread(target=lick_port_R.Lick, args=(1000,10))
    thread_R.start()
    
    print('Touch ground + right lickport')
    start_time = time.time()

    while time.time() < start_time + 10:

        if sum(lick_port_R._licks) > 0:
            right_works = True
            break

    if right_works == True:
        print('Right contact detected')
        test_tone.Play()
    else:
        print('No contact detected')

        try_again = input('Try again? (y/n)')

        if try_again == 'n':
            right_works = True 

#----------------------------
#Test camera:
#----------------------------

camera = PiCamera() #create camera object
camera.start_preview(fullscreen = False, window = (0,-44,350,400))
#starts the camera in preview mode

test_cam = input('Confirm that camera is working (ENTER)')
#Nothing is stored, just waits for the user to hit ENTER before exiting the program.


