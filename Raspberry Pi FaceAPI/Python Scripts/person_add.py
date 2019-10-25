# -------------------------------------------
# this script adds a person to the database, for future facial recognition
# -------------------------------------------

import picamera
import datetime
import time
import os, json, sys
import faceapi
from configparser import SafeConfigParser

# -------------------------------------------
# local variables
# -------------------------------------------
config_file = r'/home/pi/config_faceapi.ini'
config=SafeConfigParser()
config.read(config_file)
image_folder = config.get('person_add','camera_image_folder')
person_group_id = config.get('person_add','person_group_id')
counter = 5

# -------------------------------------------
# Delete previous files
# -------------------------------------------
filelist = os.listdir(image_folder)

for file in filelist:
    os.remove(image_folder + "/" + file)

# -------------------------------------------
# Get the persons name via input and add to the database
# -------------------------------------------
person_name = input("Enter the person's name:")
person_deets = person_name + " " + time.strftime("%Y%m%d_%H%M%S")
print("Adding person:",person_name)
person_add = faceapi.person_create(person_group_id, person_name, person_deets)
person_id = json.loads(person_add.decode("utf-8"))["personId"]

print("Get ready for your 5 pictures to be taken..")

# -------------------------------------------
# 5 second countdown!
# -------------------------------------------
while counter >= 0:  
    print("in",counter)
    counter = counter-1
    time.sleep(1)

#reset the counter back to 1 for pictres to be taken
counter = 1    
camera = picamera.PiCamera()

camera.start_preview()
time.sleep(2)

# -------------------------------------------
# Take 5 photos with two seconds gap in between each one
# -------------------------------------------
while counter <= 5:
    now = datetime.datetime.now()
    image_file_name = "image_"+now.strftime("%Y%m%d_%H%M%S")+".jpg"
    image_full_name = image_folder+"/"+image_file_name
    camera.capture(image_full_name)
    print("captured image",counter,"of 5")
    counter +=1
    time.sleep(2)

camera.stop_preview()    
camera.close()

# -------------------------------------------
# Add each face to the database
# -------------------------------------------

print("Adding faces to the database...")

filelist = os.listdir(image_folder)

for file in filelist:
    add_file_name = image_folder + "/" + file
    person_face_id = faceapi.person_face_add(person_group_id, person_id, add_file_name)
    print("Added:",file)

print("Training the group")
faceapi.group_train(person_group_id)

print("-----------")
print("Done! Welcome",person_name,"!")
print("-----------")
