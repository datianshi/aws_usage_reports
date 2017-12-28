import boto3

from functions import FIVE_DAYS_AGO
from functools import reduce
from functions import aggregate_region_resources
from functions import get_resource
from functions import clean_region_resources
from pprint import pprint

#Clean not used snapshots
def get_snapshots(client):
    return client.describe_snapshots(
        OwnerIds=[
            '375783000519'
        ]
    )

def get_images(client):
    return client.describe_images(
        Owners=[
            '375783000519'
        ]
    )

snapshots= aggregate_region_resources(get_resource({'func': get_snapshots, 'key': 'Snapshots'}))
image_snapshots= list(map(lambda x: x['BlockDeviceMappings'][0]['Ebs']['SnapshotId'],
                     aggregate_region_resources(get_resource({'func': get_images, 'key': 'Images'}))))
pprint(image_snapshots)


delete_snapshots=list(filter(lambda x: x['VolumeId'] == 'vol-ffffffff' and x['SnapshotId'] not in image_snapshots and x['StartTime'] < FIVE_DAYS_AGO, snapshots))
pprint(delete_snapshots)
#
# total_disk_size = reduce(lambda x,y: x + y, map(lambda x: x['Size'], delete_volumes))
#
pprint("There are {} snapshots will be deleted".format(len(delete_snapshots)))

def delete_snapshot(client, snapshot):
    pprint("Delete Snapshot ID: {}".format(snapshot['SnapshotId']))
    client.delete_snapshot(
        SnapshotId=snapshot['SnapshotId'],
        DryRun=False
    )

clean_region_resources('ec2', delete_snapshots, delete_snapshot)


