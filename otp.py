import random
import urllib.request
import urllib.parse
import RPi.GPIO as GPIO
import time
import numpy as np
import cv2
import smtplib
import os
# Here are the email package modules we'll need
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart


GPIO.setmode(GPIO.BOARD)
MATRIX = [ [1,2,3,'A'],
                   [4,5,6,'B'],
                   [7,8,9,'C'],
                   ['*',0,'#','D'] ]
COL = [15,13,11,7]
ROW = [22,18,16,12]

MATCH_OTP=""
MASTER_PASS="12345678"

for j in range(4):
    GPIO.setup(COL[j], GPIO.OUT)
    GPIO.output(COL[j], 1)
    
for i in range(4):
    GPIO.setup(ROW[i], GPIO.IN, pull_up_down = GPIO.PUD_UP)

def sendsms(otp):
    username = 'rahsnh@gmail.com:kevinmitnick'
    sender = 'TEST SMS'
    numbers = '8763321018'
    
    message = 'Beware! Only Fraudster will ask your One Time Password(OTP) over phone.use OTP %s.Do not share it with any one'%otp
 
    values = {'user'   : username,
              'senderID'    : sender,
              'receipientno' : numbers,
              'msgtxt' : message
             }
    url = "http://api.mVaayoo.com/mvaayooapi/MessageCompose"
 
    data = urllib.parse.urlencode(values)
    data = data.encode('utf-8')
    req = urllib.request.Request(url,data)
 
    print ('\nAttempt to send SMS ...')

    status = 'Status=0'
 
    response = urllib.request.urlopen(req)
    response_url = response.read()
    print(response_url,'\n')

def sendMail():
    # Create the container (outer) email message.
    msg = MIMEMultipart()
    msg['Subject'] = 'DOOR LOCK SYSTEM-FACE DETECTED'
    # me == the sender's email address
    # family = the list of all recipients' email addresses
    msg['From'] = 'rahsnh@gmail.com'
    msg['To'] = 'rahsnh@hotmail.com'
    msg.preamble = 'DOOR LOCK SYSTEM'

    # Assume we know that the image files are all in PNG format
    # Open the files in binary mode.  Let the MIMEImage class automatically
    # guess the specific image type.
    img_data = open('facedetect.png', 'rb')
    image = MIMEImage(img_data.read())
    msg.attach(image)

    # Send the email via our own SMTP server.
    print("connecting")
    try:
        s = smtplib.SMTP('smtp.gmail.com', '587')
        s.ehlo()
        s.starttls()
        s.login('rahsnh@gmail.com', 'kevinmitnick')
        print("connected")
        s.send_message(msg)
        print("Image Sent")
        s.quit()
    except:
        print("Unable to send the email. Error: ", sys.exc_info()[0])
        raise


# FACE DETECTION

def face_detect():
    #https://github.com/Itseez/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml
    face_cascade = cv2.CascadeClassifier('/home/pi/opencv-3.1.0/data/haarcascades/haarcascade_frontalface_default.xml')

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

    while 1:
        ret, img = cap.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x,y,w,h) in faces:
            cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)

        cv2.imshow('img',img)
        k = cv2.waitKey(30) & 0xff
        if k == 27 or len(faces)>0:
            cv2.imwrite('facedetect.png',img)
            cap.release()
            cv2.destroyAllWindows()
            sendMail()
            break


def random_otp():
    otp = random.randrange(100000,1000000,3)
    face_detect()
#    sendsms(otp)
    global MATCH_OTP
    otp = str(otp)
    print (otp)
    MATCH_OTP=otp
    return check_otp(6)

def master_pass():
    return check_otp(8)

def check_otp(range_digit):
    flag = 0
    option = 0
    ctr = 0
    global MATCH_OTP
    st=""
    if range_digit == 6:
        print("ENTER 6 DIGIT OTP")
        option = 0
    else:
        print("ENTER MASTER PASSWORD")
        option = 1
    while (ctr<3):
        for c in range(range_digit):
            flag = 0
            while(True):
                if flag==1:
                    break
                for j in range(4):
                    GPIO.output(COL[j],0)
                    for i in range(4):
                        if GPIO.input(ROW[i]) == 0:                   
                            print (MATRIX[i][j],end="",flush=True)
                            time.sleep(0.2)
                            while(GPIO.input(ROW[i]) == 0):
                                pass
                            if MATRIX[i][j]=='A':
                                return 0
                            st = st+str(MATRIX[i][j])
                            flag=1
                    GPIO.output(COL[j],1)
            if c==5 and option==0:
                if st==MATCH_OTP:
                    print('\n\nOTP MATCHED,DOOR OPENED')
                    MATCH_OTP=""
                    return 1
                else:
                    print("\n\nINCORRECT OTP,RETRY AGAIN OR PRESS 'A' TO EXIT")
                    st=""
                    ctr=ctr+1
            if c==7 and option==1:
                if st==MASTER_PASS:
                    print('\n\nPASSWORD MATCHED,DOOR OPENED')
                    return 1
                else:
                    print("\n\nINCORRECT PASSWORD,RETRY AGAIN OR PRESS 'A' TO EXIT")
                    st=""
                    ctr=ctr+1
    return 0
                
                
def loopover(flag):
    try:
        if flag==1:
            print("\nPRESS 'A' TO SEND OTP OR 'B' TO ENTER MASTER PASSWORD")
        else:
            print("\nPRESS 'D' TO CLOSE DOOR")
        while(True):
            for j in range(4):
                GPIO.output(COL[j],0)
                for i in range(4):
                    if GPIO.input(ROW[i]) == 0:                   
                        print (MATRIX[i][j])  
                        time.sleep(0.2)
                        while(GPIO.input(ROW[i]) == 0):
                            pass
                        if MATRIX[i][j]=='A' and flag==1:
                            state = random_otp()
                            if state==0:
                                loopover(1)
                            else:
                                print("\nPRESS 'D' TO CLOSE DOOR")
                            flag = 0
                        elif MATRIX[i][j]=='B' and flag==1:
                            state = master_pass()
                            if state==0:
                                loopover(1)
                            else:
                                print("\nPRESS 'D' TO CLOSE DOOR")
                            flag = 0
                        elif MATRIX[i][j]=='D' and flag==0:
                            loopover(1)
                        else:
                            if flag==1:
                                print("\nPRESS 'A' TO SEND OTP")
                            else:
                                loopover(0)
                GPIO.output(COL[j],1)
    

    except KeyboardInterupt:
        GPIO.cleanup()

loopover(1)
