

import boto3
from functools import reduce

from datetime import datetime
from datetime import timedelta
from datetime import timezone


FIVE_DAYS_AGO = datetime.now(timezone.utc) - timedelta(5)

def aggregate_region_resources(func):
    client = boto3.client('ec2')
    regionsResponse = client.describe_regions()
    regions = list(map(lambda x: x['RegionName'], regionsResponse['Regions']))
    return list(reduce(lambda x, y: x + y, map(func, regions)))

def clean_region_resources(resources, delete_resource):
    for resource in resources:
        client = boto3.client("ec2", region_name = resource['Region'])
        delete_resource(client, resource)
