import asyncio
from email.errors import ObsoleteHeaderDefect
import io
from unittest import result
import const
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
    const.ENDPOINT,
    CognitiveServicesCredentials(const.KEY)
)

'''
Get a list of all the defined person objects
'''


def getPersonList(groupID='og'):
    return face_client.person_group_person.list('og')


def getPerson(personID, groupID='og'):
    return face_client.person_group_person.get(groupID, personID)


'''
groupings of people we are using to distinguish between customers
'''


def createPersonGroup(groupID='og', face_client=face_client):
    face_client.person_group.create(
        person_group_id=groupID, name=groupID, recognition_model='recognition_04'
    )


def deletePersonGroup(groupID='og'):
    face_client.person_group.delete(groupID)


'''
create a person object
'''


def createPerson(personID, groupID='og', face_client=face_client):
    return face_client.person_group_person.create(groupID, personID)


'''
assign images to a person object, 
NOTE: helper function, use the bulk function
'''


def addImageToPerson(person, groupID='og', face_client=face_client):
    images = [file for file
              in glob.glob(groupID + '/*')
              if file.startswith(groupID + '/' + person.name)]

    print(images)

    for img in images:
        with open(img, 'rb') as img_stream:
            face_client.person_group_person.add_face_from_stream(
                groupID, person.person_id, img_stream)
            print(img)


'''
train model post adding images
'''


def trainModelWithAssignedImages(groupID='og'):
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


'''
this function will handle all the training. 
remember to delete the current person group to make a new one with the same name.
'''


def trainModel(groupID='og'):
    createPersonGroup(groupID)
    for user in const.USERS:
        createPerson(user, groupID=groupID)

    for person in getPersonList(groupID):
        addImageToPerson(person, groupID)

    trainModelWithAssignedImages(groupID)


def identifyFace(image_stream, groupID='og', accepted_confidence=0.75):
    # Detect faces
    face_ids = []
    # We use detection model 3 to get better performance, recognition model 4 to support quality for recognition attribute.
    faces = face_client.face.detect_with_stream(
        image_stream,
        detection_model='detection_03',
        recognition_model='recognition_04',
        return_face_attributes=['qualityForRecognition']
    )

    results = [getPerson(person.candidates[0].person_id, groupID).name
               for person
               in results
               if len(person.candidates) > 0
               and person.candidates[0].confidence > accepted_confidence]

    return results
