from pprint import pprint

import boto3

region = 'us-east-1'
client = boto3.client('elb', region_name=region)
response = client.describe_load_balancers()
pprint(response)
result = list(map(lambda x: {'LoadBalancerName': x['LoadBalancerName'], 'VPCId': x['VPCId'], 'Region': region}, response['LoadBalancerDescriptions']))
pprint(result)