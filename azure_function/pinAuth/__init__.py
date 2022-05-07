import json
import logging

import azure.functions as func

import sys

from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import CloudToDeviceMethod, CloudToDeviceMethodResult
import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey


from builtins import input

# The service connection string to authenticate with your IoT hub.
# Using the Azure CLI:
# az iot hub show-connection-string --hub-name {your iot hub name} --policy-name service
CONNECTION_STRING = "HostName=SecurityHub.azure-devices.net;SharedAccessKeyName=service;SharedAccessKey=TDfQdS0BWjkCkXG6QYDm+q6WenA1xkyoTEkU2DBhWyQ="
DEVICE_ID = "accessControl"

# Details of the direct method to call.
METHOD_NAME = "grantAccess"
METHOD_PAYLOAD = "10"

HOST = 'https://dzy3.documents.azure.com:443/'
MASTER_KEY = 'KJpfeldPiTP5D0dZdezgghIMxjAdWPPs9MQ0LaEdFaEdYxyQ7iARcIVXV2zafoRHwRQ7kcsR9p77vgqy4B8lNA=='
DATABASE_ID = "Policies"
CONTAINER_ID = "policies"


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
    for item in policies:
        if item["name"] == "Daniel Ye":
            iothub_devicemethod_sample_run()

            # if pin == "1234":
            #     iothub_devicemethod_sample_run()
    logging.info('Python EventGrid trigger processed an event: %s', result)
