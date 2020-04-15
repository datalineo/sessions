print("Image Processor is starting...")

# -------------------------------------------
# import modules for calling functions
# -------------------------------------------

import time
import grovepi
import faceapi
import datetime
import json
import operator
import os, uuid, sys
from azure.storage.blob import BlockBlobService, PublicAccess, ContentSettings
import uuid
import cv2
from configparser import ConfigParser

# -------------------------------------------
# Tell the raspberry pi where the sensor is attached 
# -------------------------------------------
button = 3  # digital port D3
grovepi.pinMode(button,"INPUT")

# -------------------------------------------
# set local variables
# -------------------------------------------
face_identity_count = 0
mouse_confidence = 0
program_version = '2.0.1'
boxcolour = (255,255,255)

# -------------------------------------------
# get config values
# -------------------------------------------
config_file = r'/home/pi/config_faceapi.ini'
config=ConfigParser()
config.read(config_file)
camera_image_folder = config.get('image_processor','camera_image_folder')
detect_image_folder = config.get('image_processor','detect_image_folder')
person_group_id = config.get('image_processor','person_group_id')
azure_storage_uri = config.get('image_processor','azure_storage_uri')

print("Image Processor is waiting for your capture...")

# -------------------------------------------
# Enter the while loop - this is the main part of the program
# -------------------------------------------

while True:
    try:
        # -------------------------------------------
        # waiting for button to be  pressed
        # -------------------------------------------
        if grovepi.digitalRead(button) == 1:
            print("image captured, processing...")

            # -------------------------------------------
            # Capture the image ******
            # -------------------------------------------            
            now = datetime.datetime.now()
            camera_image_file_name = "camera_"+now.strftime("%Y%m%d_%H%M%S")+".jpg"
            camera_image_full_name = camera_image_folder+"/"+camera_image_file_name
            faceapi.capture_image(camera_image_full_name) # photo taken here!
            screen_message = ""
            # set initial SQL & detect filename variables, more after the recognition loop
            visit_id = uuid.uuid4()
            visit_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
            detect_image_file_name = "detect_"+now.strftime("%Y%m%d_%H%M%S")+".jpg"
            detect_image_full_name = detect_image_folder+"/"+detect_image_file_name
            detect_image_url = azure_storage_uri+detect_image_file_name
            
            # -------------------------------------------
            # Send the image to Microsoft Face API to Detect
            # -------------------------------------------
            print("Performing Facial recognition & Custom Vision...")
            detect_json = faceapi.person_face_detect(camera_image_full_name)
            #print(detect_json)
            detect_py = json.loads(detect_json.decode("utf-8"))
            if "error" in detect_py:
                print("Error found:",detect_py["error"]["message"])
                break
            # -------------------------------------------
            # Read the image to create rectangled version
            # -------------------------------------------
            detect_image_read = cv2.imread(camera_image_full_name)

            # -------------------------------------------
            # Second loop: 
            # For every face it detects in the image, grab the details & check if they are in the database
            # -------------------------------------------
            for x in detect_py:
                face_identity_count +=1
                # Get the facial detection attributes
                age = x["faceAttributes"]["age"]
                gender = x["faceAttributes"]["gender"]
                emotion = x["faceAttributes"]["emotion"]
                emotion_sorted = sorted(emotion.items(), key=operator.itemgetter(1),reverse=True)
                expression = emotion_sorted[0][0]
                expression_confidence = emotion_sorted[0][1]
                # Get the rectangle details
                rectop = x["faceRectangle"]["top"]
                recleft = x["faceRectangle"]["left"]
                recwidth = x["faceRectangle"]["width"]
                recheight = x["faceRectangle"]["height"]
                recbottom = rectop + recheight
                recright = recleft + recwidth
                textleft = recleft
                texttop = rectop - 30 
                textright = recleft+100
                textbottom = rectop
                gender_short = gender[:1].upper()
                agetext = gender_short+"-"+str(int(round(age,0)))
                # write the rectangles on the image
                cv2.rectangle(detect_image_read,(recleft,rectop),(recright,recbottom),(255,255,255),2)
                cv2.rectangle(detect_image_read,(textleft,texttop),(textright,textbottom),boxcolour,cv2.FILLED)
                cv2.putText(detect_image_read,agetext,(recleft,rectop),cv2.FONT_HERSHEY_PLAIN,2,(0,0,0),1,cv2.LINE_AA)

                # Look up the face to identify
                identify_json = faceapi.face_identify(person_group_id, x["faceId"])
                identify_py = json.loads(identify_json.decode("utf-8"))
                if "error" in identify_py:
                    print("Error found:",identify_py["error"]["message"])
                    break

                #faceapi.json_print(identify_json)
                
                # if the identify found candidates, grab their details-
                if len(identify_py[0]["candidates"]) > 0:
                    #print(identify_py)
                    person_get_json = faceapi.person_get(person_group_id, identify_py[0]["candidates"][0]["personId"])
                    person_get_py = json.loads(person_get_json.decode("utf-8"))
                    if "error" in person_get_py:
                        print("Error found:",person_get_py["error"]["message"])
                        break
                    person_name = person_get_py["name"]
                    identify_confidence = identify_py[0]["candidates"][0]["confidence"]
                else:
                    person_name = "Unknown"
                    identify_confidence = 0

                # ----------------------------------------
                # Insert the identity row to SQL Server
                # ----------------------------------------
                #print("Inserting to SQL VisitFaces table...")
                visitfaces_tsql = "insert rpi.VisitFaces(VisitGUID,PersonName,PersonConfidence,Age,Gender,Expression,ExpressionConfidence,DetectJSON) values ('{0}','{1}',{2},{3},'{4}','{5}',{6},'{7}')".format(visit_id, person_name, identify_confidence, age, gender, expression, expression_confidence, json.dumps(x))
                faceapi.insert_to_sql(visitfaces_tsql)
                               
                # ----------------------------------------
                # Build up the message to output to the screen 
                # ----------------------------------------
                screen_message+='\n'+'I see '+person_name+' who is a '+gender+' aged '+str(round(age,1))+', with facial expression of '+'{0:.0%}'.format(expression_confidence)+' '+expression

            # --------------------------------------------
            # Insert the photo visit row to SQL Azure
            # --------------------------------------------
            #print("Inserting to SQL Visit table...")
            visit_tsql = "insert rpi.Visit (VisitGUID,VisitDateTime,ProgramVersion,VisitImageURL,FaceCount) values ('{0}', '{1}', '{2}', '{3}', {4})".format(visit_id, visit_datetime, program_version, detect_image_url,face_identity_count)
            faceapi.insert_to_sql(visit_tsql)

            # --------------------------------------------
            # Detect the mouse with Custom Vision
            # --------------------------------------------

            json_out_cv = faceapi.custom_vision_mouse(camera_image_full_name)
            json_py_cv = json.loads(json_out_cv.decode("utf-8"))

            for x in json_py_cv["predictions"]:
                if x["probability"] > mouse_confidence:
                    mouse_confidence = x["probability"]

            #print(json_py_cv)
            
            #print(json.dumps(json.loads(json_out_cv.decode("utf-8")),indent=2))
        
            # -------------------------------------------
            # Save the rectangle image, write to blob & output text to screen
            # -------------------------------------------
            print("------------------------")


            if mouse_confidence > 0.85:
                print('** I SEE THE MOUSE!! ** Hey I\'m pretty confident I can see the mouse!')
            elif mouse_confidence > 0.65:
                print('** I SEE THE MOUSE!! ** I\'m marginally confident I can see it there!')
            #elif mouse_confidence > 0.5:
            #    print('I can see something that could be the mouse, no overly confident though')
            #elif mouse_confidence > 0.3:
            #    print('I\'m squinting, something looks mousey, but hard to tell')

               
            if face_identity_count > 0:
                cv2.imwrite(detect_image_full_name,detect_image_read)
                faceapi.copy_to_blob (detect_image_full_name, detect_image_file_name)
                face_text = 'face'
                if face_identity_count > 1:
                    face_text+='s'
                print('I detected '+str(face_identity_count)+' '+face_text+' in this image!')
                print(screen_message)
                face_text = ''
            else:
                faceapi.copy_to_blob (camera_image_full_name, camera_image_file_name)
                print('>>> I did not identify any faces in this image!')

            print("------------------------")

            # ----------------------------------------
            # Finished processing the image, return to monitoring
            # ----------------------------------------
            face_identity_count = 0
            mouse_confidence = 0
            #print(screen_message)
            print("Done. Back to monitoring mode...")
                
        time.sleep(.5)

    except IOError:
        print ("Error")
    except KeyboardInterrupt:
        print("Goodbye")
        break
