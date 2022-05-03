import asyncio
import io
import cred
import glob
import os
import sys
import time
import uuid
import requests
from urllib.parse import urlparse
from io import BytesIO
# To install this module, run:
# python -m pip install Pillow
from PIL import Image, ImageDraw
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person, QualityForRecognition


# Create an authenticated FaceClient.
face_client = FaceClient(
    cred.ENDPOINT, 
    CognitiveServicesCredentials(cred.KEY)
  )

def generatePersonGroupID(instanceID):
  return instanceID

def createPersonGroup(groupID, face_client):
  face_client.person_group.create(person_group_id=groupID, name=groupID)

def createPerson(personID, groupID, face_client):
  face_client.person_group_person.create(groupID, personID)

def addImageToPerson(personID, groupID, face_client):
  images = [file for file 
    in glob.glob('*') 
    if file.startswith(groupID+'/'+personID)]
  
  for img in images:
    with open(img, 'rb') as img_stream:
      face_client.person_group_person.add_face_from_stream(groupID, personID, img_stream)

def trainModel(groupID):
  # train
  face_client.person_group.train(groupID)
  while(True):
    # wait for status
    training_status = face_client.person_group.get_training_status(groupID)
    print("Training status: {}.".format(training_status.status))
    print()

    if (training_status.status is TrainingStatusType.succeeded):
      break
    elif (training_status.status is TrainingStatusType.failed):
        face_client.person_group.delete(person_group_id=groupID)
        sys.exit('Training the person group has failed.')
    time.sleep(5)

def identifyFace(image_stream, groupID, accepted_confidence = 0.75):
  # Detect faces
  face_ids = []
  # We use detection model 3 to get better performance, recognition model 4 to support quality for recognition attribute.
  faces = face_client.face.detect_with_stream(
    image_stream, 
    detection_model='detection_03', 
    recognition_model='recognition_04', 
    return_face_attributes=['qualityForRecognition']
    )

  for face in faces:
      # Only take the face if it is of sufficient quality.
      if (
        face.face_attributes.quality_for_recognition == QualityForRecognition.high or 
        face.face_attributes.quality_for_recognition == QualityForRecognition.medium):
          face_ids.append(face.face_id)
  
  results = face_client.face.identify(face_ids, groupID)

  return [person for person 
    in results
    if len(person.candidates) > 0 
    and person.camdidates[0].confidence > accepted_confidence]


  


  