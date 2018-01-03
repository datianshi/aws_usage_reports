

import boto3
from functools import reduce

from datetime import datetime
from datetime import timedelta
from datetime import timezone


FIVE_DAYS_AGO = datetime.now(timezone.utc) - timedelta(5)
TWO_DAYS_AGO = datetime.now(timezone.utc) - timedelta(2)

def aggregate_region_resources(func):
    client = boto3.client('ec2')
    regionsResponse = client.describe_regions()
    regions = list(map(lambda x: x['RegionName'], regionsResponse['Regions']))
    return list(reduce(lambda x, y: x + y, map(func, regions)))

def clean_region_resources(type, resources, delete_resource):
    for resource in resources:
        client = boto3.client(type, region_name = resource['Region'])
        delete_resource(client, resource)

def resources_per_vpc(vpcId, region, func):
    filters=[
        {
            'Name': 'vpc-id',
            'Values': [vpcId]
        }

    ]
    client = boto3.client('ec2', region_name=region)
    return func(client, filters)

def get_instances(region):
    instances=[]
    client = boto3.client('ec2', region_name=region)
    response = client.describe_instances()

    for i in response['Reservations']:
        for instance in i['Instances']:
            instance['Region'] = region
            instances.append(instance)
    return instances

def get_internet_gateways(region):
    gateways=[]
    client = boto3.client('ec2', region_name=region)
    response = client.describe_internet_gateways()

    for i in response['InternetGateways']:
        i['Region'] = region
        gateways.append(i)
    return gateways

def get_resource(func_map):
    def retFunc(region):
        resources=[]
        client = boto3.client('ec2', region_name=region)
        response = func_map['func'](client)
        for resource in response[func_map['key']]:
            resource['Region'] = region
            resources.append(resource)
        return resources
    return retFunc

