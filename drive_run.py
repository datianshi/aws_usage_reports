from pprint import pprint

import boto3

region = 'us-east-1'
client = boto3.client('ec2', region_name=region)
client.delete_vpc(
    VpcId='vpc-29f68252',
    DryRun=False
)