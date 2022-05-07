import os

settings = {
    'host': os.environ.get('ACCOUNT_HOST', 'https://dzy3.documents.azure.com:443/'),
    'master_key': os.environ.get('ACCOUNT_KEY', 'KJpfeldPiTP5D0dZdezgghIMxjAdWPPs9MQ0LaEdFaEdYxyQ7iARcIVXV2zafoRHwRQ7kcsR9p77vgqy4B8lNA=='),
    'database_id': os.environ.get('COSMOS_DATABASE', 'ToDoList'),
    'container_id': os.environ.get('COSMOS_CONTAINER', 'Items'),
}