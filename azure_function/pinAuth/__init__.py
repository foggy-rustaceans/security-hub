import json
import logging

import azure.functions as func

import sys

from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import CloudToDeviceMethod, CloudToDeviceMethodResult
from azure.storage.blob import ContainerClient, BlobServiceClient
from datetime import datetime
from datetime import timedelta
import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person, QualityForRecognition

from builtins import input

from scipy.misc import face

# The service connection string to authenticate with your IoT hub.
# Using the Azure CLI:
# az iot hub show-connection-string --hub-name {your iot hub name} --policy-name service
CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=dzy3;AccountKey=wSMNtk6npOsvj47MIee3B6B+8mpm+faxhCUDoEFOYs57JK8JzGiCa2184MTBjWFVuQIRAs2g+CkD+AStxiZazA==;EndpointSuffix=core.windows.net"
DEVICE_ID = "accessControl"

# Details of the direct method to call.
METHOD_NAME = "grantAccess"
METHOD_PAYLOAD = "10"

HOST = 'https://dzy3.documents.azure.com:443/'
MASTER_KEY = 'KJpfeldPiTP5D0dZdezgghIMxjAdWPPs9MQ0LaEdFaEdYxyQ7iARcIVXV2zafoRHwRQ7kcsR9p77vgqy4B8lNA=='
DATABASE_ID = "Policies"
CONTAINER_ID = "policies"

KEY = "acd2fa6813bc417b9a9085bf266685d3"

# This endpoint will be used in all examples in this quickstart.
ENDPOINT = "https://securityface.cognitiveservices.azure.com/"

face_client = FaceClient(
    ENDPOINT,
    CognitiveServicesCredentials(KEY)
)


def iothub_devicemethod_sample_run():
    try:
        # Create IoTHubRegistryManager
        registry_manager = IoTHubRegistryManager(CONNECTION_STRING)

        # Call the direct method.
        deviceMethod = CloudToDeviceMethod(
            method_name=METHOD_NAME, payload=METHOD_PAYLOAD)
        response = registry_manager.invoke_device_method(
            DEVICE_ID, deviceMethod)

        print("")
        print("Device Method called")
        print("Device Method name       : {0}".format(METHOD_NAME))
        print("Device Method payload    : {0}".format(METHOD_PAYLOAD))
        print("")
        print("Response status          : {0}".format(response.status))
        print("Response payload         : {0}".format(response.payload))

        input("Press Enter to continue...\n")

    except Exception as ex:
        print("")
        print("Unexpected error {0}".format(ex))
        return
    except KeyboardInterrupt:
        print("")
        print("IoTHubDeviceMethod sample stopped")


def query_items(container, password):
    print('\nQuerying for an  Item by password\n')

    # Including the partition key value of password in the WHERE filter results in a more efficient query
    items = list(container.query_items(
        query="SELECT * FROM r WHERE r.password=@password",
        parameters=[
            {"name": "@password", "value": password}
        ],
        enable_cross_partition_query=True
    ))
    return items


def getPerson(personID, groupID='og'):
    return face_client.person_group_person.get(groupID, personID)


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

    for face in faces:
        # Only take the face if it is of sufficient quality.
        if (
                face.face_attributes.quality_for_recognition == QualityForRecognition.high or
                face.face_attributes.quality_for_recognition == QualityForRecognition.medium):
            face_ids.append(face.face_id)
    if face_ids:
        results = face_client.face.identify(face_ids, groupID)

        results = [getPerson(person.candidates[0].person_id, groupID).name
                   for person
                   in results
                   if len(person.candidates) > 0
                   and person.candidates[0].confidence > accepted_confidence]

        return results
    else:
        return []


def main(event: func.EventGridEvent):
    result = json.dumps({
        'id': event.id,
        'data': event.get_json(),
        'topic': event.topic,
        'subject': event.subject,
        'event_type': event.event_type,
    })
    result = json.loads(result)
    data = result["data"]
    body = data["body"]
    pin = body["pin"]
    policies = []
    client = cosmos_client.CosmosClient(
        HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    try:
        # setup database for this sample

        db = client.get_database_client(DATABASE_ID)
        print('Database with id \'{0}\' was found'.format(DATABASE_ID))

        container = db.get_container_client(CONTAINER_ID)
        print('Container with id \'{0}\' was found'.format(CONTAINER_ID))

        policies = query_items(container, pin)
    except exceptions.CosmosHttpResponseError as e:
        print('\npinAuth has caught an error. {0}'.format(e.message))
    print("policies", policies)
    # if not policies:
    #     return
    blob_service_client = BlobServiceClient.from_connection_string(
        CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(
        "video-storage")
    starts_with = "imageUpload/" + (datetime.now().strftime("%d-%m-%Y"))
    print("starts with", starts_with)
    blobs = (container_client.list_blobs(name_starts_with=starts_with))
    examine = []
    time = datetime.now()
    past = time - timedelta(minutes=10)
    past = past.strftime("%d-%m-%Y-%H:%M:%S$")
    for b in blobs:
        if "$" not in b['name']:
            continue
        end_idx = b['name'].index("$")
        upload_time = b['name'][12:end_idx]
        print(upload_time)
        if upload_time > past:
            examine.append(b['name'])
    face_names = []
    print("examine", examine)
    for b in examine:
        blob_client = blob_service_client.get_blob_client(
            container="video-storage", blob=b)
        try:
            with open("./temp.png", "wb") as my_blob:
                download_stream = blob_client.download_blob()
                my_blob.write(download_stream.readall())
            with open("./temp.png", "rb") as img:
                face_names.append(identifyFace(img))
        except e:
            print("No blob found.")
# with open("./temp.png", "rb")
    print("face names", face_names)
    for item in policies:
        if item["name"] in set(face_names):
            iothub_devicemethod_sample_run()
            return

            # if pin == "1234":
            #     iothub_devicemethod_sample_run()
    logging.info('Python EventGrid trigger processed an event: %s', result)
