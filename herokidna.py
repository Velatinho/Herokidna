import RPi.GPIO as GPIO
import time
import telepot
import random
import math
import imutils
import cv2
import numpy as np
import emo_functions
import threading
import subprocess
import sys
import os
from telegramCredentials import tokenHero

#Music
MUSIC_DIRECTORY = "MusicEffects/"
omxprocess = 0
omxprocess_started = False
volume = -600
GPIO.setmode(GPIO.BCM)

#Color sensors
signal_pond = 5
signal_targ = 6
S2 = 26
S3 = 2
NUM_CYCLES = 10
blue_treshold = 1996
red_treshold  = 874
COLOR_BLUE = 0
COLOR_RED  = 1
redexcesslight = 0
blueexcesslight = 0
GPIO.setup(signal_pond, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(signal_targ, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(S2,GPIO.OUT)
GPIO.setup(S3,GPIO.OUT)
print("Color sensor ok")

#Motors wheels
IN1_WHEEL = 17
IN2_WHEEL = 27
IN3_WHEEL = 23
IN4_WHEEL = 22
ENA_WHEEL = 19
ENB_WHEEL = 12
GPIO.setup(IN1_WHEEL, GPIO.OUT)
GPIO.setup(IN2_WHEEL, GPIO.OUT)
GPIO.setup(IN3_WHEEL, GPIO.OUT)
GPIO.setup(IN4_WHEEL, GPIO.OUT)
GPIO.setup(ENA_WHEEL, GPIO.OUT)
GPIO.setup(ENB_WHEEL, GPIO.OUT)
GPIO.output(ENA_WHEEL,GPIO.HIGH)
GPIO.output(ENB_WHEEL,GPIO.HIGH)
TIME_TO_ROTATE_90       = 1.6   #Default time to rotate of 90°  ---> can be set via /rotate90  1.6
TIME_TO_ROTATE_135      = 2.4   #Default time to rotate of 135° ---> can be set via /rotate135 2.4
print("Wheel ok")


#Motors target
IN_TARGET = 20
GPIO.setup(IN_TARGET, GPIO.OUT)
print("Target ok")

#Motors spines
IN_SPINES = 24
GPIO.setup(IN_SPINES, GPIO.OUT)
print("Spines ok")

#Target
PIN_t = 3
GPIO.setup(PIN_t, GPIO.OUT)
print("Target ok")

#ServoMotor
servoPin = 13
SERVO_MAX = 12.5
SERVO_MID = 7.5
SERVO_MIN = 2.5
GPIO.setup(servoPin, GPIO.OUT)
servo_pwm = GPIO.PWM(servoPin, 50)
servo_pwm.start(SERVO_MAX)
time.sleep(1)
servo_pwm.ChangeDutyCycle(0)
print("Servo ok")

#Ultrasonic sensor
ULTRA_TRIGGER          = 25
ULTRA_ECHO_FRONT       = 8
ULTRA_ECHO_BACK        = 10
ULTRA_ECHO_RIGHT       = 9
ULTRA_ECHO_LEFT_FRONT  = 11
ULTRA_ECHO_LEFT_BACK   = 7
GPIO.setup(ULTRA_TRIGGER, GPIO.OUT)
GPIO.setup(ULTRA_ECHO_FRONT, GPIO.IN)
GPIO.setup(ULTRA_ECHO_BACK, GPIO.IN)
GPIO.setup(ULTRA_ECHO_LEFT_FRONT, GPIO.IN)
GPIO.setup(ULTRA_ECHO_LEFT_BACK, GPIO.IN)
GPIO.setup(ULTRA_ECHO_RIGHT, GPIO.IN)
print("Ultrasonic ok")

#Game info
POINTS_FOR_DRINKING = 20
POINTS_FOR_EATING   = 10
POINTS_FOR_EATEN    = -30
POINTS_FOR_INACTIVE = -1
GAME_DURATION       = 300

#Emotions
EMOTION_DRINKING  = 0
EMOTION_EATING    = 1
EMOTION_ATTACKING = 2
EMOTION_DEFENDING = 3
EMOTION_EATEN     = 4
EMOTION_SLEEP     = 5
EMOTION_NORMAL    = 6
EMOTION_POND_NEAR = 7
current_emotion   = EMOTION_NORMAL

#Set the camera
camera = cv2.VideoCapture(0)
camera.set(3,600)
HUE_VALUE = 170 #red
colorLower = np.array([HUE_VALUE - 10, 100, 100], dtype=np.uint8) #Lower and upper boundary target color
colorUpper = np.array([HUE_VALUE + 10, 255, 255], dtype=np.uint8)
print("Camera ok")

#Attacking info
ENEMY_FORWARD = 0
ENEMY_LEFT    = 1
ENEMY_RIGHT   = 2

#Functions to control the wheels
def forward():
    GPIO.output(IN1_WHEEL, GPIO.HIGH)
    GPIO.output(IN2_WHEEL, GPIO.LOW)
    GPIO.output(IN3_WHEEL, GPIO.HIGH)
    GPIO.output(IN4_WHEEL, GPIO.LOW)

def right():
    GPIO.output(IN1_WHEEL, GPIO.LOW)
    GPIO.output(IN2_WHEEL, GPIO.LOW)
    GPIO.output(IN3_WHEEL, GPIO.HIGH)
    GPIO.output(IN4_WHEEL, GPIO.LOW)

def left():
    GPIO.output(IN1_WHEEL, GPIO.HIGH)
    GPIO.output(IN2_WHEEL, GPIO.LOW)
    GPIO.output(IN3_WHEEL, GPIO.LOW)
    GPIO.output(IN4_WHEEL, GPIO.LOW)

def backward():
    GPIO.output(IN1_WHEEL, GPIO.LOW)
    GPIO.output(IN2_WHEEL, GPIO.HIGH)
    GPIO.output(IN3_WHEEL, GPIO.LOW)
    GPIO.output(IN4_WHEEL, GPIO.HIGH)

def backwardRight():
    GPIO.output(IN1_WHEEL, GPIO.LOW)
    GPIO.output(IN2_WHEEL, GPIO.LOW)
    GPIO.output(IN3_WHEEL, GPIO.LOW)
    GPIO.output(IN4_WHEEL, GPIO.HIGH)

def backwardLeft():
    GPIO.output(IN1_WHEEL, GPIO.LOW)
    GPIO.output(IN2_WHEEL, GPIO.HIGH)
    GPIO.output(IN3_WHEEL, GPIO.LOW)
    GPIO.output(IN4_WHEEL, GPIO.LOW)

def stop():
    GPIO.output(IN1_WHEEL, GPIO.LOW)
    GPIO.output(IN2_WHEEL, GPIO.LOW)
    GPIO.output(IN3_WHEEL, GPIO.LOW)
    GPIO.output(IN4_WHEEL, GPIO.LOW)
stop()

#Returns whether from input 'signal' the specified color is detected
def is_color(signal, color):
    if color == COLOR_BLUE:
        if (blueexcesslight == 0):
            return get_color(signal, color) > blue_treshold
        else:
            return get_color(signal, color) < blue_treshold
    if (redexcesslight == 0):
        return get_color(signal, color) > red_treshold
    else:
        return get_color(signal, color) < red_treshold

#Returns the value of the color from "signal" sensor
#low_high for BLUE      #high_high for RED
def get_color(signal, color):

    if color == COLOR_BLUE:
        GPIO.output(S2,GPIO.LOW)
        GPIO.output(S3,GPIO.HIGH)
    else:
        GPIO.output(S2,GPIO.LOW)
        GPIO.output(S3,GPIO.LOW)

    start = time.time()
    for impulse_count in range(NUM_CYCLES):
        GPIO.wait_for_edge(signal,GPIO.FALLING)
    duration = time.time() - start
    result = NUM_CYCLES/duration
    return result

#Used to calibrate the sensors
def calibrate(chat_id):
    bot.sendMessage(chat_id, "I will need you to place me in sequence:\n\
     - on the pond\n\
     - outside of the pond\n\
     - in front of a target\n\
     - away from a target\n\
You will have ten seconds between each step")
    time.sleep(5)

    #In pond calibration
    bot.sendMessage(chat_id, "Place me on pond")
    time.sleep(10)
    bot.sendMessage(chat_id, "Detecting blue")
    i = 0
    blue = []
    while(i < 100):
        blue.append(get_color(signal_pond, COLOR_BLUE))
        time.sleep(0.01)
        i += 1
    avg_blue = sum(blue)/100

    #Outside pond calibration
    bot.sendMessage(chat_id, "Place me out of the pond")
    time.sleep(10)
    bot.sendMessage(chat_id, "Detecting not blue")
    i = 0
    not_blue = []
    while(i < 100):
        not_blue.append(get_color(signal_pond, COLOR_BLUE))
        time.sleep(0.01)
        i += 1
    avg_not_blue = sum(not_blue)/100

    #Check if red is detected
    bot.sendMessage(chat_id, "Place red target in front of the beak")
    time.sleep(10)
    bot.sendMessage(chat_id, "Detecting red")
    i = 0
    red = []
    while(i < 100):
        red.append(get_color(signal_targ, COLOR_RED))
        time.sleep(0.01)
        i += 1
    avg_red = sum(red)/100

    #Check if red is detected
    bot.sendMessage(chat_id, "Remove red target in front of the beak")
    time.sleep(10)
    bot.sendMessage(chat_id, "Detecting not red")
    i = 0
    not_red = []
    while(i < 100):
        not_red.append(get_color(signal_targ, COLOR_RED))
        time.sleep(0.01)
        i += 1
    avg_not_red = sum(not_red)/100


    #Treshold computation
    global blue_treshold
    global red_treshold
    global redexcesslight
    global blueexcesslight
    blue_treshold = avg_not_blue + (avg_blue - avg_not_blue)/2
    red_treshold = avg_not_red + (avg_red - avg_not_red)/2
    if (avg_not_red > avg_red):
        redexcesslight = 1
        red_treshold = min(red_treshold, avg_red * 2)
    if (avg_not_blue > avg_blue):
        blueexcesslight = 1
        blue_treshold = min(blue_treshold, avg_blue * 2)-100

    #Done
    bot.sendMessage(chat_id, "Calibration done! Here's the results:\n\
        - Blue average: {0:.2f}\n\
        - Not-blue average: {1:.2f}\n\
        - Blue treshold: {2:.2f}\n\
        - Red average: {3:.2f}\n\
        - Not-red average: {4:.2f}\n\
        - Red treshold: {5:.2f}\n".format(avg_blue, avg_not_blue, blue_treshold, avg_red, avg_not_red, red_treshold))


#Moves the servomotor
#Angle from 0 to 180
def rotateServo(angle):

    pulse = angle * (SERVO_MAX - SERVO_MIN) / 180 + SERVO_MIN
    servo_pwm.ChangeDutyCycle(pulse)
    time.sleep(0.03)
    servo_pwm.ChangeDutyCycle(0)

#Computes distance from ultrasonic sensor
#Trigger is the same for all sensors, echo changes
def computeDistance(echo):

    #Trigger up for 0.01ms
    GPIO.output(ULTRA_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(ULTRA_TRIGGER, False)

    Start = time.time()
    StartWaveTime = time.time()
    StopWaveTime = time.time()

    #Save StartTime
    while GPIO.input(echo) == 0 and (StartWaveTime - Start) < 0.2:
        StartWaveTime = time.time()

    #Save time of arrival
    while GPIO.input(echo) == 1 and (StopWaveTime - Start) < 0.2:
        StopWaveTime = time.time()

    #Time difference between start and arrival
    TimeElapsed = StopWaveTime - StartWaveTime
    distance = (TimeElapsed * 343) / 2

    #To avoid interferences beetween consecutive calls
    time.sleep(0.005)

    return distance



#Sends a message with the new emotion
def changeEmotion(emotion, chat_id):

    if emotion == EMOTION_DRINKING:
        msg = "I'm drinking!"
        playMusic("Drinking.mp3")
    if emotion == EMOTION_SLEEP:
        msg = "Going to sleep zzzz"
        playMusic("End.mp3")
    if emotion == EMOTION_NORMAL:
        msg = "Just hanging around"
        playMusic("Normal.mp3")
    if emotion == EMOTION_EATEN:
        msg = "Oh no! I've been hit :("
        playMusic("Eaten.mp3")
    if emotion == EMOTION_EATING:
        msg = "Gnam! I'm eating a really good tasting robot! Bon appetit to me :)"
    if emotion == EMOTION_DEFENDING:
        msg = "Damn! I saw something"
    if emotion == EMOTION_POND_NEAR:
        msg = "Sniff sniff... water is close"
    if emotion == EMOTION_ATTACKING:
        msg = "Sniff sniff... someone is close"
        playMusic("Attacking.mp3")

    global current_emotion
    current_emotion = emotion
    bot.sendMessage(chat_id, msg)


#Thread which takes care of spawning the correct emotion thread
def emotionsHandlerTh():
    while True:
        if (current_emotion == EMOTION_NORMAL or current_emotion == EMOTION_POND_NEAR):
            emoTh = threading.Thread(target=emo_functions.standardTh, args=())
        elif (current_emotion == EMOTION_ATTACKING or current_emotion == EMOTION_EATING):
            emoTh = threading.Thread(target=emo_functions.attackTh, args=())
        elif (current_emotion == EMOTION_DRINKING):
            emoTh = threading.Thread(target=emo_functions.drinkTh, args=())
        elif (current_emotion == EMOTION_DEFENDING or current_emotion == EMOTION_EATEN):
            emoTh = threading.Thread(target=emo_functions.defenseTh, args=())
        else:   #elif GAME_ENDED
            emoTh = threading.Thread(target=emo_functions.idleTh, args=())
        emoTh.start()
        emoTh.join()


#Updates score
def updateScore(startTime, stopTime, points, score):
    difTime = int(math.floor(stopTime - startTime)) / 5
    score += difTime * points
    return score



#Checks if target is our being touched
def checkTarget():
    value = GPIO.input(PIN_t)
    return (value == 1)



#Returns True if there are at least 3 True in last 5 measures
def threeMeasuresResults(measures):
    return sum(measures)>=3


#Lowers neck
def lowerNeck():

    delta_angle = -2.8
    current_angle = 180

    while current_angle > 90:
        rotateServo(current_angle + delta_angle)
        current_angle += delta_angle

#Raises neck
def raiseNeck():
    delta_angle = 3.0
    current_angle = 90

    while current_angle < 180:
        rotateServo(current_angle + delta_angle)
        current_angle += delta_angle


#Complete version of checkEnemy (merges checkEnemy and checkEnemyDirection)
#NOTE: if we have time, it would be better to implement this version (to check enemy size)
def checkEnemy(frame, direction):

    MIN_RADIUS = 75

    #Resize the frame, inverted ("vertical flip" w/ 180degrees),
    #Blur it, and convert it to the HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    #Construct a mask for the target color, then perform
    #a series of dilations and erosions to remove any small
    #blobs left in the mask
    mask = cv2.inRange(hsv, colorLower, colorUpper)
    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=1)

    #Find contours in the mask and initialize the current
    #(x, y) center of the ball
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

    if len(cnts) == 0:
        return (False, direction)

    #Find the largest contour in the mask, then use
    #it to compute the minimum enclosing circle and centroid

    c = max(cnts, key=cv2.contourArea)
    ((x, y), radius) = cv2.minEnclosingCircle(c)

    # only proceed if the radius meets a minimum size
    if radius > MIN_RADIUS:
        print(x)
        if x > 500:
            return (True, ENEMY_RIGHT)
        if x < 100:
            return (True, ENEMY_LEFT)
        if (x > 100 and x < 500):
            return (True, ENEMY_FORWARD)

    return (False, direction)


#Checks whether the robot is parallel to the wall on its left (with a tolerance of 5%)
def isParallel():
    distBackLeft = computeDistance(ULTRA_ECHO_LEFT_BACK)
    time.sleep(0.01)
    distFrontLeft = computeDistance(ULTRA_ECHO_LEFT_FRONT)

    tolerance = 0.05 * (distBackLeft + distFrontLeft)/2
    return (abs(distBackLeft - distFrontLeft) < tolerance)


#Plays the music contained in file_name
def playMusic(file_name):
    global omxprocess
    global omxprocess_started
    if omxprocess_started:
        omxprocess.stdin.write(b'q')
    omxprocess = subprocess.Popen(['omxplayer', MUSIC_DIRECTORY + file_name, '--loop', '--vol', str(volume)], stdin=subprocess.PIPE, stdout=None, stderr=None, bufsize=0)
    omxprocess_started = True

#Stops the music
def stopMusic():
    global omxprocess
    global omxprocess_started
    if omxprocess_started:
        omxprocess.stdin.write(b'q')
    omxprocess_started = False


#Open or close the spines
def moveSpines():
    GPIO.output(IN_SPINES, GPIO.HIGH)
    time.sleep(0.148)
    GPIO.output(IN_SPINES, GPIO.LOW)

#Rotate the target of 90°
def moveTarget():
	GPIO.output(IN_TARGET, GPIO.HIGH)
	time.sleep(0.14)
	GPIO.output(IN_TARGET, GPIO.LOW)

#Core of the robot
def startGame(chat_id):

    #Activate camera
    global camera
    camera.release()
    camera = cv2.VideoCapture(0)
    camera.set(3,600)

    #Wait to begin
    time.sleep(5)

    #Parameters to test
    MAX_DISTANCE_WALL       = 0.7   #Distance from wall to reach before turning
    ATTACK_DISTANCE         = 0.2   #Distance from which it is possible to attempt an attack
    TIME_TO_DROP_POND       = 3.0   #Time that needs to pass after having last seen the pond before dropping the research
    TIME_TO_DROP_ATTACK     = 2.0   #Time that needs to pass after having last seen an enemy before dropping an attack
    GO_FOR_POND_TIME        = 5.0   #Starting time for reaching the pond

    #States for pond research
    WALKING          = 0
    WALKING_PARALLEL = 1
    WALKING_DIAGONAL = 2
    POND_NEAR        = 3
    DRINKING         = 4

    #States for attacking
    ATTACKING        = 5
    EATING           = 6

    #States for defending
    DEFENDING        = 7
    EATEN            = 8

    OLD_STATE        = 0

    #Info on the robot
    state                   = WALKING
    isDrinking              = False
    isEating                = False
    isEaten                 = False
    lastTimePondWasSeen     = 0
    lastTimeEnemyWasSeen    = 0
    lastTimeNeckWasRaised   = 0
    lastTimeTargetWasMoved  = 0
    escapedTime             = 0
    startDiagonalTime       = 0
    score                   = 60
    isNeckLow               = False
    enemy_direction         = ENEMY_FORWARD
    check_on_the_sides      = 0
    distanceRight           = 1.0
    distanceLeft            = 1.0
    distanceBack            = 1.0
    spinesAreOpen           = False


    #Timers to keep score updated
    start_time_drinking = 0
    start_time_inactive = 0
    start_time_eating   = 0
    start_time_eaten    = 0

    #Array containing the last three measures from some of the sensors
    #(to make robot resilient to measurement errors)
    pond_measures   = [False, False, False, False, False]
    eaten_measures  = [False, False, False, False, False]
    eating_measures = [False, False, False, False, False]
    index_measures  = 0

    #Start
    changeEmotion(EMOTION_NORMAL, chat_id)
    startTime = time.time()
    lastTimeWasStuck = startTime
    index_measures = 0

    #For the first 5s the robot just goes forward to get to the pond
    while time.time() < startTime + GO_FOR_POND_TIME:
        forward()
        is_on_pond = is_color(signal_pond, COLOR_BLUE)
        if is_on_pond:
            print(is_on_pond)
            isDrinking = True
            state = DRINKING
            stop()
            changeEmotion(EMOTION_DRINKING, chat_id)
            start_time_drinking = time.time()
            pond_measures = [True, True, True, True, True]
            break


    #Main part of the algorithm
    while time.time() < startTime + GAME_DURATION:

        ############# SENSORS #################
        (grabbed, frame)  = camera.read()
        (enemy_in_sight, enemy_direction)    = checkEnemy(frame, enemy_direction)
        is_target_touched = checkTarget()
        is_on_pond        = is_color(signal_pond, COLOR_BLUE)
        is_touching       = is_color(signal_targ, COLOR_RED)
        pond_measures[index_measures]   = is_on_pond
        eating_measures[index_measures] = is_touching
        eaten_measures[index_measures]  = is_target_touched
        index_measures = (index_measures + 1) % 5


        #Check if there's threats on the sides (only do it every 20 cycles to avoid wasting time in the computeDistances)
        check_on_the_sides += 1
        if(check_on_the_sides % 20 == 0):
            distanceRight = computeDistance(ULTRA_ECHO_RIGHT)
            distanceLeft  = computeDistance(ULTRA_ECHO_LEFT_FRONT)
            distanceBack  = computeDistance(ULTRA_ECHO_BACK)


        ############ ENEMY SIGHT #############
        if enemy_in_sight and state != ATTACKING and not isDrinking and not isEaten:
            stop()
            state = ATTACKING
            changeEmotion(EMOTION_ATTACKING, chat_id)
            lastTimeEnemyWasSeen = time.time()



        ############    POND    ##############
        #Check if robot happend by chance on the pond
        if threeMeasuresResults(pond_measures) and not isDrinking:
            isDrinking = True
            state = DRINKING
            stop()
            changeEmotion(EMOTION_DRINKING, chat_id)
            start_time_drinking = time.time()

        #Check if robot was drinking and exited the pond
        if not threeMeasuresResults(pond_measures) and isDrinking:
            state = POND_NEAR
            isDrinking = False
            changeEmotion(EMOTION_POND_NEAR, chat_id)
            stop_time_drinking = time.time()
            score = updateScore(start_time_drinking, stop_time_drinking, POINTS_FOR_DRINKING, score)
            lastTimePondWasSeen = stop_time_drinking



        ###############  OUR TARGET  ###############
        #Check if someone is touching our target
        if threeMeasuresResults(eaten_measures) and not isEaten:
            isEaten = True
            state = EATEN
            changeEmotion(EMOTION_EATEN, chat_id)
            start_time_eaten = time.time()
            escapedTime = start_time_eaten

        #Check if target is free
        if not threeMeasuresResults(eaten_measures) and isEaten:
            isEaten = False
            state = WALKING
            changeEmotion(EMOTION_NORMAL, chat_id)
            stop_time_eaten = time.time()
            score = updateScore(start_time_eaten, stop_time_eaten, POINTS_FOR_EATEN, score)


        ################    ENEMY'S TARGET  ###############
        #Check if i am touching enemy's target
        if threeMeasuresResults(eating_measures) and not isEating and isNeckLow:
            isEating = True
            state = EATING
            changeEmotion(EMOTION_EATING, chat_id)
            stop()
            start_time_eating = time.time()

        #Check if we are still hooked at the target
        if not threeMeasuresResults(eating_measures) and isEating:
            isEating = False
            state = ATTACKING
            changeEmotion(EMOTION_ATTACKING, chat_id)
            stop_time_eating = time.time()
            score = updateScore(start_time_eating, stop_time_eating, POINTS_FOR_EATING, score)


        ################ PERIODICALLY GO BACKWARDS ###################
        if time.time() > (lastTimeWasStuck + 30) and not isEating and not isDrinking:
            lastTimeNeckWasStuck = time.time()
            backwardLeft()
            time.sleep(1.5)
            stop()
            time.sleep(0.1)
            right()
            time.sleep(0.5)



        ###############    MOVING TARGET + SPINES    ####################
        #Moves the target if there's a threat approaching or if robot has stopped to drink
        if (distanceBack < 0.2 or distanceLeft < 0.2 or distanceRight < 0.2 or state == DRINKING):
            if time.time() > (lastTimeTargetWasMoved + 3.5):
                lastTimeTargetWasMoved = time.time()
                moveTarget()
            if (not spinesAreOpen):
                moveSpines()
                spinesAreOpen = True

        else:
            if (spinesAreOpen):
                moveSpines()
                spinesAreOpen = False



        ###############      INACTIVITY  ##################
        #Update score for inactivity
        if not isDrinking and not isEaten and not isEating:
            if time.time() - start_time_inactive > 5.0:
                score = updateScore(0,5,POINTS_FOR_INACTIVE, score)
                start_time_inactive = time.time()
        else:
            start_time_inactive = time.time()




        #STATE: WALKING
        #No threat detected and still looking for the pond
        if (state == WALKING):
            if (OLD_STATE != state):
                OLD_STATE = state
                bot.sendMessage(chat_id, "walking")

            forward()

            #Check for obstacles
            distFront = computeDistance(ULTRA_ECHO_FRONT)
            if (distFront < MAX_DISTANCE_WALL):
                stop()
                time.sleep(0.1)
                right()
                time.sleep(TIME_TO_ROTATE_90)
                stop()
                state = WALKING_PARALLEL

        #STATE: WALKING PARALLEL
        #Walking parallel to the wall on its the left, looking for an angle of the field
        if (state == WALKING_PARALLEL):
            if (OLD_STATE != state):
                OLD_STATE = state
                bot.sendMessage(chat_id, "walking parallel")

            forward()
            #Check for obstacles
            distFront = computeDistance(ULTRA_ECHO_FRONT)
            if (distFront < MAX_DISTANCE_WALL):
                stop()
                time.sleep(0.1)
                right()
                time.sleep(TIME_TO_ROTATE_135)
                forward()
                state = WALKING


        #STATE: POND_NEAR
        #Pond is assumed to be close to the robot, so robot looks for it (at most for 2s if pond not in sight)
        if (state == POND_NEAR):
            if (OLD_STATE != state):
                OLD_STATE = state
                bot.sendMessage(chat_id, "pond_near")

            if time.time() < lastTimePondWasSeen + 1.0:
                backward()
            else:
                forward()

            if time.time() > lastTimePondWasSeen + TIME_TO_DROP_POND:
                state = WALKING
                changeEmotion(EMOTION_NORMAL, chat_id)



        #STATE: DRINKING
        if (state == DRINKING):
            if (OLD_STATE != state):
                OLD_STATE = state
                bot.sendMessage(chat_id, "drinking")

        #STATE: EATING
        if (state == EATING):
            if (OLD_STATE != state):
                OLD_STATE = state
                bot.sendMessage(chat_id, "eating")

        #STATE: EATEN
        #Try to escape from the enemies
        if (state == EATEN):
            if (OLD_STATE != state):
                OLD_STATE = state
                bot.sendMessage(chat_id, "eaten")
            distFront = computeDistance(ULTRA_ECHO_FRONT)
            distBack = computeDistance(ULTRA_ECHO_BACK)

            if time.time() > (lastTimeTargetWasMoved + 3.5):
                lastTimeTargetWasMoved = time.time()
                moveTarget()

            if (distBack < MAX_DISTANCE_WALL):
                if (time.time() < escapedTime + 2):
                    forward()
                else:
                    right()
                    time.sleep(TIME_TO_ROTATE_90)
                    escapedTime = time.time()

            elif (distFront < MAX_DISTANCE_WALL):
                if (time.time() < escapedTime + 2):
                    backward()
                else:
                    stop()
                    time.sleep(0.1)
                    left()
                    time.sleep(TIME_TO_ROTATE_90)
                    escapedTime = time.time()
            else:
                stop()
                time.sleep(0.1)
                right()
                time.sleep(TIME_TO_ROTATE_90)
                forward()



        #STATE: ATTACKING
        if (state == ATTACKING):
            if (OLD_STATE != state):
                OLD_STATE = state
                bot.sendMessage(chat_id, "attacking")
            ### Check if enemy is still in sight
            if enemy_in_sight:
                lastTimeEnemyWasSeen = time.time()

            #Change direction according to the camera
            if enemy_direction == ENEMY_FORWARD:
                forward()
            if enemy_direction == ENEMY_RIGHT:
                stop()
                time.sleep(0.05)
                right()
            if enemy_direction == ENEMY_LEFT:
                stop()
                time.sleep(0.05)
                left()

            ### Attack not yet performed
            if (not isNeckLow):
                distFront = computeDistance(ULTRA_ECHO_FRONT)

                ###### Enemy can be attacked
                if (distFront <= ATTACK_DISTANCE):
                    stop()
                    lowerNeck()
                    isNeckLow = True

            ### Attack performed unsuccessfully
            else:
                raiseNeck()
                isNeckLow = False

            ### Drop attack
            if time.time() > lastTimeEnemyWasSeen + TIME_TO_DROP_ATTACK:
                state = WALKING
                changeEmotion(EMOTION_NORMAL, chat_id)


    stop()
    stopTime = time.time()
    changeEmotion(EMOTION_SLEEP, chat_id)

    if isDrinking:
        score = updateScore(start_time_drinking, stopTime, POINTS_FOR_DRINKING, score)
    if isEating:
        score = updateScore(start_time_eating, stopTime, POINTS_FOR_EATING, score)
    if isEaten:
        score = updateScore(start_time_eaten, stopTime, POINTS_FOR_EATEN, score)

    return score





#Waits for commands from telegram
#If we make the start a separate thread, this could become more complicated
def wait_msg(msg):

    global camera
    global current_emotion
    global volume
    global TIME_TO_ROTATE_90
    global TIME_TO_ROTATE_135
    chat_id = msg['chat']['id']
    command_text = msg['text'].split(" ")
    command = command_text[0]

    if command == '/help':
        bot.sendMessage(chat_id,
"/photo - Sends a picture\n\n\
-------------------> SENSORS <---------------------\n\
/pond - Checks if on pond\n\
/eating - Checks if eating\n\
/eaten - Checks if eaten\n\
/ultra - Returns distance from ultrasonic sensors\n\n\
-------------------> MOTORS <----------------------\n\
/moveTarget - Moves the target of 90°\n\
/moveSpines - Open or close the spines\n\
/neck - Lowers and then raises the neck\n\
/moveForward - Moves forward for 1.5 s\n\
/moveRight - Moves right 90°\n\
/moveLeft - Moves left 90°\n\
/moveBackward - Moves backward for 1.5 s\n\
/stop - Stops the robot\n\n\
------------------> EMOTIONS <---------------------\n\
/em1 - Normal emotions\n\
/em2 - Attacking emotions\n\
/em3 - Drinking emotions\n\
/em4 - Defending emotions\n\
/em5 - Sleeping emotions\n\n\
--------------------> MUSIC <----------------------\n\
/playMusic - plays some music\n\
/stopMusic - stops playing music\n\
/lowerVolume - decrease the level of volume\n\
/raiseVolume - increase the level of volume\n\n\
-------------------> FUNCTIONS <-------------------\n\
/checkEnemy - checks if an enemy is in sight\n\
/IP - returns the IP address of the robot\n\
/controls - Simplified controls\n\
/shutdown - turns off the robot\n\n\
------------------> CALIBRATIONS <-----------------\n\
/calibrate - Calibrates the color sensors\n\
/rotate90 <x.y> - Calibration of TIME_TO_ROTATE_90\n\
/rotate135 <x.y> - Calibration of TIME_TO_ROTATE_135\n\
")

    if command == '/start':
        bot.sendMessage(chat_id, "Starting!")
        score = startGame(chat_id)
        bot.sendMessage(chat_id, "Game over, final score {0}".format(str(int(score))))


    if command == '/photo':
        (grabbed, frame) = camera.read()
        cv2.imwrite('photo.jpg',frame)
        camera.release()
        camera = cv2.VideoCapture(0)
        camera.set(3,600)
        bot.sendPhoto(chat_id, photo = open('photo.jpg','rb'))

    if command == '/pond':
        result = is_color(signal_pond, COLOR_BLUE)
        bot.sendMessage(chat_id, str(result))

    if command == '/eating':
        result = is_color(signal_targ, COLOR_RED)
        bot.sendMessage(chat_id, str(result))

    if command == '/calibrate':
        bot.sendMessage(chat_id, "Blue treshold is now: {0}\n\
Red treshold is now: {1}\n\
Proceeding to calibration".format(blue_treshold, red_treshold))
        calibrate(chat_id)

    if command == '/eaten':
        result = checkTarget()
        bot.sendMessage(chat_id, str(result))

    if command == '/ultra':
        distLeftFront = computeDistance(ULTRA_ECHO_LEFT_FRONT)*100
        time.sleep(0.03)
        distLeftBack  = computeDistance(ULTRA_ECHO_LEFT_BACK)*100
        distRight     = computeDistance(ULTRA_ECHO_RIGHT)*100
        distFront     = computeDistance(ULTRA_ECHO_FRONT)*100
        distBack      = computeDistance(ULTRA_ECHO_BACK)*100
        bot.sendMessage(chat_id, "Front: {0} cm\nBack: {1} cm\nRight: {2} cm\nLeft Front: {3} cm\nLeft Back: {4} cm".format(distFront,distBack,distRight,distLeftFront,distLeftBack))

    if command == '/moveForward':
        forward()
        time.sleep(1.5)
        stop()

    if command == '/moveRight':
        right()
        time.sleep(TIME_TO_ROTATE_90)
        stop()

    if command == '/moveLeft':
        left()
        time.sleep(TIME_TO_ROTATE_90)
        stop()

    if command == '/moveBackward':
        backward()
        time.sleep(1.5)
        stop()

    if command == '/stop':
        stop()

    if command == '/moveTarget':
        moveTarget()

    if command == '/moveSpines':
        moveSpines()

    if command == '/neck':
        lowerNeck()
        time.sleep(2.0)
        raiseNeck()

    if command == '/em1':
        changeEmotion(EMOTION_NORMAL, chat_id)
    if command == '/em2':
        changeEmotion(EMOTION_ATTACKING, chat_id)
    if command == '/em3':
        changeEmotion(EMOTION_DRINKING, chat_id)
    if command == '/em4':
        changeEmotion(EMOTION_SLEEP, chat_id)
    if command == '/em5':
        changeEmotion(EMOTION_EATEN, chat_id)

    if command == '/isParallel':
        result = isParallel()
        bot.sendMessage(chat_id, str(result))


    if command == '/playMusic':
        if len(command_text) > 1:
            args = command_text[1]
        else:
            args = "Normal.mp3"
        playMusic(args)

    if command == '/stopMusic':
        stopMusic()

    if command == '/lowerVolume':
        if (volume > -5699):
            volume -= 300

    if command == '/raiseVolume':
        if (volume < -299):
            volume += 300

    if command == '/checkEnemy':
        (grabbed, frame) = camera.read()
        (isEnemy, _) = checkEnemy(frame, ENEMY_FORWARD)
        #camera.release()
        #camera = cv2.VideoCapture(0)
        #camera.set(3,600)
        bot.sendMessage(chat_id, "{0}".format(str(isEnemy)))

    if command == '/IP':
        cli_command = "hostname -I"
        proc = subprocess.Popen(cli_command, shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE)
        line = proc.stdout.readline()
        address = line.rstrip().decode("utf-8")
        bot.sendMessage(chat_id, address)

    if command == '/shutdown':
        bot.sendMessage(chat_id, "Bye!\nRemember to switch off the motors, turn off the speaker and unplug the powerbank")
        stop()
        stopMusic()
        GPIO.cleanup()
        subprocess.call('sudo shutdown -h now', shell = True)

    if command == '/rotate90':
        bot.sendMessage(chat_id, "rotating time was: {0}".format(TIME_TO_ROTATE_90))
        if len(command_text) > 1:
            TIME_TO_ROTATE_90 = float(command_text[1])
        bot.sendMessage(chat_id, "start rotating with: {0}".format(TIME_TO_ROTATE_90))
        right()
        time.sleep(TIME_TO_ROTATE_90)
        stop()

    if command == '/rotate135':
        bot.sendMessage(chat_id, "rotating time was: {0}".format(TIME_TO_ROTATE_135))
        if len(command_text) > 1:
            TIME_TO_ROTATE_135 = float(command_text[1])
        bot.sendMessage(chat_id, "start rotating with: {0}".format(TIME_TO_ROTATE_135))
        right()
        time.sleep(TIME_TO_ROTATE_135)
        stop()



#Thread of the emotions
emotionsHandler = threading.Thread(target=emotionsHandlerTh, args=())
emotionsHandler.start()

if __name__ == '__main__':

    print("Activating bot!")
    bot = telepot.Bot(tokenHero)
    print("Bot activated!")
    bot.message_loop(wait_msg)
    while 1:
        time.sleep(10)
