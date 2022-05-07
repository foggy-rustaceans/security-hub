import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
import datetime

import config

# ----------------------------------------------------------------------------------------------------------
# Prerequistes -
#
# 1. An Azure Cosmos account -
#    https://docs.microsoft.com/azure/cosmos-db/create-cosmosdb-resources-portal#create-an-azure-cosmos-db-account
#
# 2. Microsoft Azure Cosmos PyPi package -
#    https://pypi.python.org/pypi/azure-cosmos/
# ----------------------------------------------------------------------------------------------------------
# Sample - demonstrates the basic CRUD operations on a Item resource for Azure Cosmos
# ----------------------------------------------------------------------------------------------------------

HOST = config.settings['host']
MASTER_KEY = config.settings['master_key']
DATABASE_ID = config.settings['database_id']
CONTAINER_ID = config.settings['container_id']

print(HOST, MASTER_KEY)


def create_items(container):
    print('\nCreating Items\n')

    # Create a SalesOrder object. This object has nested properties and various types including numbers, DateTimes and strings.
    # This can be saved as JSON as is without converting into rows/columns.

    policy1 = {'id': '0',
               'partitionKey': 'Person1',
               'name': 'Daniel Ye',
               'password': '1234'
               }
    container.create_item(body=policy1)

    # As your app evolves, let's say your object has a new schema. You can insert SalesOrderV2 objects without any
    # changes to the database tier.
    # sales_order2 = get_sales_order_v2("SalesOrder2")
    # container.create_item(body=sales_order2)


def scale_container(container):
    print('\nScaling Container\n')

    # You can scale the throughput (RU/s) of your container up and down to meet the needs of the workload. Learn more: https://aka.ms/cosmos-request-units
    try:
        offer = container.read_offer()
        print('Found Offer and its throughput is \'{0}\''.format(
            offer.offer_throughput))

        offer.offer_throughput += 100
        container.replace_throughput(offer.offer_throughput)

        print('Replaced Offer. Offer Throughput is now \'{0}\''.format(
            offer.offer_throughput))

    except exceptions.CosmosHttpResponseError as e:
        if e.status_code == 400:
            print('Cannot read container throuthput.')
            print(e.http_error_message)
        else:
            raise


def read_item(container, doc_id, account_number):
    print('\nReading Item by Id\n')

    # We can do an efficient point read lookup on partition key and id
    response = container.read_item(item=doc_id, partition_key=account_number)

    print('Item read by Id {0}'.format(doc_id))
    print('Partition Key: {0}'.format(response.get('partitionKey')))
    print('Subtotal: {0}'.format(response.get('subtotal')))


def read_items(container):
    print('\nReading all items in a container\n')

    # NOTE: Use MaxItemCount on Options to control how many items come back per trip to the server
    #       Important to handle throttles whenever you are doing operations such as this that might
    #       result in a 429 (throttled request)
    item_list = list(container.read_all_items(max_item_count=10))

    print('Found {0} items'.format(item_list.__len__()))

    for doc in item_list:
        print('Item Id: {0}'.format(doc.get('id')))


def query_items(container, account_number):
    print('\nQuerying for an  Item by password\n')

    # Including the partition key value of account_number in the WHERE filter results in a more efficient query
    items = list(container.query_items(
        query="SELECT * FROM r WHERE r.password=@account_number",
        parameters=[
            {"name": "@account_number", "value": account_number}
        ],
        enable_cross_partition_query=True
    ))
    print(items)
    print('Item queried by Partition Key {0}'.format(items[0].get("id")))
    return items


def replace_item(container, doc_id, account_number):
    print('\nReplace an Item\n')

    read_item = container.read_item(item=doc_id, partition_key=account_number)
    read_item['subtotal'] = read_item['subtotal'] + 1
    response = container.replace_item(item=read_item, body=read_item)

    print('Replaced Item\'s Id is {0}, new subtotal={1}'.format(
        response['id'], response['subtotal']))


def upsert_item(container, doc_id, account_number):
    print('\nUpserting an item\n')

    read_item = container.read_item(item=doc_id, partition_key=account_number)
    read_item['subtotal'] = read_item['subtotal'] + 1
    response = container.upsert_item(body=read_item)

    print('Upserted Item\'s Id is {0}, new subtotal={1}'.format(
        response['id'], response['subtotal']))


def delete_item(container, doc_id, account_number):
    print('\nDeleting Item by Id\n')

    response = container.delete_item(item=doc_id, partition_key=account_number)

    print('Deleted item\'s Id is {0}'.format(doc_id))


def get_sales_order(item_id):
    order1 = {'id': item_id,
              'partitionKey': 'Account1',
              'purchase_order_number': 'PO18009186470',
              'order_date': datetime.date(2005, 1, 10).strftime('%c'),
              'subtotal': 419.4589,
              'tax_amount': 12.5838,
              'freight': 472.3108,
              'total_due': 985.018,
              'items': [
                  {'order_qty': 1,
                   'product_id': 100,
                   'unit_price': 418.4589,
                   'line_price': 418.4589
                   }
              ],
              'ttl': 60 * 60 * 24 * 30
              }

    return order1


def get_sales_order_v2(item_id):
    # notice new fields have been added to the sales order
    order2 = {'id': item_id,
              'partitionKey': 'Account2',
              'purchase_order_number': 'PO15428132599',
              'order_date': datetime.date(2005, 7, 11).strftime('%c'),
              'due_date': datetime.date(2005, 7, 21).strftime('%c'),
              'shipped_date': datetime.date(2005, 7, 15).strftime('%c'),
              'subtotal': 6107.0820,
              'tax_amount': 586.1203,
              'freight': 183.1626,
              'discount_amt': 1982.872,
              'total_due': 4893.3929,
              'items': [
                  {'order_qty': 3,
                   # notice how in item details we no longer reference a ProductId
                   'product_code': 'A-123',
                   # instead we have decided to denormalise our schema and include
                   'product_name': 'Product 1',
                   # the Product details relevant to the Order on to the Order directly
                   'currency_symbol': '$',
                   # this is a typical refactor that happens in the course of an application
                   'currency_code': 'USD',
                   # that would have previously required schema changes and data migrations etc.
                   'unit_price': 17.1,
                   'line_price': 5.7
                   }
              ],
              'ttl': 60 * 60 * 24 * 30
              }

    return order2


def run_sample():
    client = cosmos_client.CosmosClient(
        HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    try:
        # setup database for this sample
        try:
            db = client.create_database(id="Policies")
            print('Database with id \'{0}\' created'.format("Policies"))

        except exceptions.CosmosResourceExistsError:
            db = client.get_database_client("Policies")
            print('Database with id \'{0}\' was found'.format("Policies"))

        # setup container for this sample
        try:
            container = db.create_container(
                id="policies", partition_key=PartitionKey(path='/partitionKey'))
            print('Container with id \'{0}\' created'.format("policies"))

        except exceptions.CosmosResourceExistsError:
            container = db.get_container_client("policies")
            print('Container with id \'{0}\' was found'.format("policies"))

        # scale_container(container)
        # create_items(container)
        # read_item(container, 'SalesOrder1', 'Account1')
        # read_items(container)
        policies = query_items(container, '1234')
        # replace_item(container, 'SalesOrder1', 'Account1')
        # upsert_item(container, 'SalesOrder1', 'Account1')
        # delete_item(container, 'SalesOrder1', 'Account1')

        # # cleanup database after sample
        # try:
        #     client.delete_database(db)

        # except exceptions.CosmosResourceNotFoundError:
        #     pass

    except exceptions.CosmosHttpResponseError as e:
        print('\nrun_sample has caught an error. {0}'.format(e.message))

    finally:
        print("\nrun_sample done")
    for item in policies:
        print(item['name'])
        if item["name"] == "Daniel Ye":
            print("ok")


if __name__ == '__main__':

    run_sample()
