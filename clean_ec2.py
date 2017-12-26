import boto3
from pprint import pprint
from datetime import datetime
from datetime import timezone


client = boto3.client('ec2')

response = client.describe_instances(
    Filters=[
        {
        }
    ]
)

instances=[]
for i in response['Reservations']:
    for instance in i['Instances']:
        instances.append(instance)

FIVE_DAYS_AGO = datetime.now(timezone.utc)


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
                    'LaunchTime': x['LaunchTime']},
         filter(should_delete,
                filter(lambda x: x['LaunchTime'] < FIVE_DAYS_AGO, instances))))

pprint(delete_instances)
print("\n\n\n\n")
print("These are the instances more than 5 days. But not going to delete them, because people tags it:")



not_delete_instances = list(map(lambda x: {'InstanceId': x['InstanceId'],
                                           'KeyName': x['KeyName'],
                                           'Tags': x.get('Tags', []),
                                           'LaunchTime': x['LaunchTime']},
                                filter(do_not_delete,
                                       filter(lambda x: x['LaunchTime'] < FIVE_DAYS_AGO, instances))))

pprint(not_delete_instances)


print("Terminating instances.................:")


client.terminate_instances(
    InstanceIds = list(map(lambda x: x['InstanceId'], delete_instances)),
    DryRun=False
)






