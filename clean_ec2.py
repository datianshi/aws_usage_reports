import boto3
import functions
from functions import TWO_DAYS_AGO
from pprint import pprint

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

print("These instances will be deleted. Since they expired and no do_not_delete tag")
delete_instances = list(map(lambda x: {'InstanceId': x['InstanceId'],
                    'KeyName': x.get('KeyName', ''),
                    'Tags': x.get('Tags', []),
                    'Region': x['Region'],
                    'LaunchTime': x['LaunchTime']},
         filter(should_delete,
                filter(lambda x: x['LaunchTime'] < TWO_DAYS_AGO, instances))))

pprint(delete_instances)
print("\n\n\n\n")
print("These are the instances more than 2 days. But not going to delete them, because people tag them with do_not_delete:")



not_delete_instances = list(map(lambda x: {'InstanceId': x['InstanceId'],
                                           'KeyName': x['KeyName'],
                                           'Tags': x.get('Tags', []),
                                           'Region': x['Region'],
                                           'LaunchTime': x['LaunchTime']},
                                filter(do_not_delete,
                                       filter(lambda x: x['LaunchTime'] < TWO_DAYS_AGO, instances))))

pprint(not_delete_instances)


print("Terminating instances.................:")


for instance in delete_instances:
    client = boto3.client("ec2", region_name = instance['Region'])
    client.terminate_instances(
        InstanceIds = [instance['InstanceId']],
        DryRun=False
)
