from functools import reduce
from pprint import pprint

import boto3

import functions
from functions import aggregate_region_resources
from functions import get_resource
from functions import TWO_DAYS_AGO


#Clean not used volumes
def get_volumes(region):
    volumes=[]
    client = boto3.client('ec2', region_name=region)
    response = client.describe_volumes()

    for volume in response['Volumes']:
        volume['Region'] = region
        volumes.append(volume)
    return volumes

volumes= aggregate_region_resources(get_volumes)

delete_volumes=list(filter(lambda x: len(x['Attachments']) == 0 and x['CreateTime'] < TWO_DAYS_AGO, volumes))
pprint(delete_volumes)

total_disk_size = reduce(lambda x,y: x + y, map(lambda x: x['Size'], delete_volumes))

pprint("There are {} disks will be deleted and this will release {} GB".format(len(delete_volumes), total_disk_size))

def delete_volume(client, volume):
    client.delete_volume(
        VolumeId=volume['VolumeId'],
        DryRun=True
    )

functions.clean_region_resources('ec2', delete_volumes, delete_volume)


