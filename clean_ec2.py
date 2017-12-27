import boto3
import functions
from pprint import pprint
from datetime import datetime
from datetime import timedelta
from datetime import timezone

FIVE_DAYS_AGO = datetime.now(timezone.utc)

client = boto3.client('ec2')

def get_instances(region):
    instances=[]
    client = boto3.client('ec2', region_name=region)
    response = client.describe_instances()

    for i in response['Reservations']:
        for instance in i['Instances']:
            instance['Region'] = region
            instances.append(instance)
    return instances

instances=functions.aggregate_region_resources(get_instances)

def do_not_delete(instance):
    tags = instance.get('Tags', [])
    for tag in tags:
        if tag.get('Key', '') == 'do_not_delete' and tag.get('Value', '') == 'true':
            return True
    return False

def should_delete(instance):
    return not do_not_delete(instance)

print("These instances will be deleted. Since they expired and no do not delete tag")
delete_instances = list(map(lambda x: {'InstanceId': x['InstanceId'],
                    'KeyName': x['KeyName'],
                    'Tags': x.get('Tags', []),
                    'Region': x['Region'],
                    'LaunchTime': x['LaunchTime']},
         filter(should_delete,
                filter(lambda x: x['LaunchTime'] < FIVE_DAYS_AGO, instances))))

pprint(delete_instances)
print("\n\n\n\n")
print("These are the instances more than 5 days. But not going to delete them, because people have do_not_delete tag on it:")



not_delete_instances = list(map(lambda x: {'InstanceId': x['InstanceId'],
                                           'KeyName': x['KeyName'],
                                           'Tags': x.get('Tags', []),
                                           'Region': x['Region'],
                                           'LaunchTime': x['LaunchTime']},
                                filter(do_not_delete,
                                       filter(lambda x: x['LaunchTime'] < FIVE_DAYS_AGO, instances))))

pprint(not_delete_instances)


print("Terminating instances.................:")


for instance in delete_instances:
    client = boto3.client("ec2", region_name = instance['Region'])
    client.terminate_instances(
        InstanceIds = [instance['InstanceId']],
        DryRun=False
)

