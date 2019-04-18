import boto3
import functions
from functions import TWO_DAYS_AGO
from pprint import pprint

client = boto3.client('rds')

def get_db_instances(region):
    instances=[]
    client = boto3.client('rds', region_name=region)
    response = client.describe_db_instances()

    for instance in response['DBInstances']:
        response = client.list_tags_for_resource( ResourceName=instance['DBInstanceArn'] )
        instance['Tags'] = response['TagList']
        instance['Region'] = region
        instances.append(instance)
    return instances

instances=functions.aggregate_region_resources(get_db_instances)

def do_not_delete(instance):
    tags = instance.get('Tags', [])
    for tag in tags:
        if tag.get('Key', '') == 'do_not_delete' and tag.get('Value', '') == 'true':
            return True
    return False

def should_delete(instance):
    return not do_not_delete(instance)

print("These instances will be deleted. Since they expired and no do_not_delete tag")
delete_instances = list(map(lambda x: {'DBInstanceIdentifier': x['DBInstanceIdentifier'],
                    'Tags': x.get('Tags', []),
                    'Region': x['Region'],
                    'InstanceCreateTime': x['InstanceCreateTime']},
         filter(should_delete,
                filter(lambda x: x['InstanceCreateTime'] < TWO_DAYS_AGO, instances))))

pprint(delete_instances)
print("\n\n\n\n")
print("These are the rds instances more than 2 days. But not going to delete them, because people tag them with do_not_delete:")



not_delete_instances = list(map(lambda x: {'DBInstanceIdentifier': x['DBInstanceIdentifier'],
                                           'Tags': x.get('Tags', []),
                                           'Region': x['Region'],
                                           'InstanceCreateTime': x['InstanceCreateTime']},
                                filter(do_not_delete,
                                       filter(lambda x: x['InstanceCreateTime'] < TWO_DAYS_AGO, instances))))

pprint(not_delete_instances)


print("Terminating rds instances.................:")


for instance in delete_instances:
    client = boto3.client("rds", region_name = instance['Region'])
    client.delete_db_instance(
        DBInstanceIdentifier = instance['DBInstanceIdentifier'],
        SkipFinalSnapshot = True
)
