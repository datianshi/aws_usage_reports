import boto3
from functools import reduce
def aggregate_region_resources(func):
    client = boto3.client('ec2')
    regionsResponse = client.describe_regions()
    regions = list(map(lambda x: x['RegionName'], regionsResponse['Regions']))
    return list(reduce(lambda x, y: x + y, map(func, regions)))