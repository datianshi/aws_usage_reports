from pprint import pprint

import boto3
from functions import aggregate_region_resources
from functions import resources_per_vpc
from functions import get_instances
from functions import get_internet_gateways
from functions import clean_region_resources
from functions import get_resource

client = boto3.client('ec2')

class Vpc(object):
    def __init__(self, vpcId, region):
        self.VpcId = vpcId
        self.Region = region

    def findElbs(self, elbs):
        self.Elbs = list(filter(lambda x: x['VPCId'] == self.VpcId, elbs))
    def findInstances(self, instances):
        self.Instances = list(filter(lambda x: x['VpcId'] == self.VpcId, instances))
    def findInternetGateways(self, internetGateways):
        self.InternetGateways = list(filter(lambda x: len(x['Attachments']) > 0 and x['Attachments'][0]['VpcId'] == self.VpcId, internetGateways))
    def findSecurityGroups(self):
        def find_security_group(client, filters):
            sgs= client.describe_security_groups(
                Filters= filters
            )
            return list(map(lambda x: {'GroupId': x['GroupId'], 'Region': self.Region},
                            filter(lambda x: x['GroupName'] != 'default', sgs['SecurityGroups'])))
        self.SecurityGroups = resources_per_vpc(self.VpcId, self.Region, find_security_group)
    def findSubnets(self):
        def find_subnets(client, filters):
            subnets=client.describe_subnets(
                Filters= filters
            )
            return list(map(lambda x: {'SubnetId': x['SubnetId'], 'Region': self.Region}, subnets['Subnets']))
        self.Subnets = resources_per_vpc(self.VpcId, self.Region, find_subnets)
    def findVpcEndpoints(self):
        def find_vpc_endpoints(client, filters):
            vpc_endpoints=client.describe_vpc_endpoints(
                Filters= filters
            )
            return list(map(lambda x: {'VpcEndpointId': x['VpcEndpointId'], 'Region': self.Region}, vpc_endpoints['VpcEndpoints']))
        self.VpcEndpoints = resources_per_vpc(self.VpcId, self.Region, find_vpc_endpoints)
    def findRouteTables(self):
        def find_route_tables(client, filters):
            subnets=client.describe_route_tables(
                Filters= filters
            )
            return list(map(lambda x: {'RouteTableId': x['RouteTableId'], 'Region': self.Region},
                            filter(lambda x: x['Associations'][0]['Main'] == False, subnets['RouteTables'])))
        self.RouteTables = resources_per_vpc(self.VpcId, self.Region, find_route_tables)

def get_vpcs(client):
    return client.describe_vpcs()

def get_elastic_addresses(client):
    return client.describe_addresses()


vpcs=list(filter(lambda x: not x['IsDefault'], aggregate_region_resources(get_resource({'func' : get_vpcs, 'key': 'Vpcs'}))))
addresses=list(aggregate_region_resources(get_resource({'func' : get_elastic_addresses, 'key': 'Addresses'})))


def findElb(region):
    client = boto3.client('elb', region_name=region)
    response = client.describe_load_balancers()
    return list(map(lambda x: {'LoadBalancerName': x['LoadBalancerName'], 'VPCId': x['VPCId'], 'Region': region}, response['LoadBalancerDescriptions']))

elbs = aggregate_region_resources(findElb)
instances = aggregate_region_resources(get_instances)
internetGateways = aggregate_region_resources(get_internet_gateways)

Vpcs=[]
_vpcs=[]
for vpc in vpcs:
    v = Vpc(vpc['VpcId'], vpc['Region'])
    v.findElbs(elbs)
    v.findInstances(instances)
    v.findInternetGateways(internetGateways)
    v.findSecurityGroups()
    v.findSubnets()
    v.findRouteTables()
    v.findVpcEndpoints()
    if len(v.Instances) == 0 and vpc['VpcId'] != 'vpc-9c1924f9':
        Vpcs.append(v)
        _vpcs.append(vpc)

def delete_load_balancer(client, load_balancer):
    print("clean load balancer: {}".format(load_balancer))
    client.delete_load_balancer(
        LoadBalancerName=load_balancer['LoadBalancerName']
    )

def delete_vpc(client, vpc):
    print("delete vpc: {}".format(vpc))
    client.delete_vpc(
        VpcId=vpc['VpcId'],
        DryRun=False
    )


def detach_internet_gateway(client, gateway):
    print("detach internet_gateways: {}".format(gateway))
    client.detach_internet_gateway(
        InternetGatewayId=gateway['InternetGatewayId'],
        VpcId=gateway['Attachments'][0]['VpcId'],
        DryRun=False
    )

def delete_internet_gateway(client, gateway):
    print("delete internet gateway: {}".format(gateway['InternetGatewayId']))
    client.delete_internet_gateway(
        InternetGatewayId=gateway['InternetGatewayId'],
        DryRun=False
    )

def delete_security_group(client, security_group):
    print("delete security group: {}".format(security_group['GroupId']))
    client.delete_security_group(
        GroupId=security_group['GroupId'],
        DryRun=False
    )

def delete_route_table(client, route_table):
    print("delete route table: {}".format(route_table['RouteTableId']))
    client.delete_route_table(
        RouteTableId=route_table['RouteTableId'],
        DryRun=False
    )

def delete_vpc_endpoints(client, vpc_endpoint):
    print("delete vpc endpoint: {}".format(vpc_endpoint['VpcEndpointId']))
    client.delete_vpc_endpoints(
        DryRun=False,
        VpcEndpointIds=[
            vpc_endpoint['VpcEndpointId']
        ]
    )

def delete_subnets(client, subnet):
    print("delete subnet: {}".format(subnet['SubnetId']))
    client.delete_subnet(
        SubnetId=subnet['SubnetId'],
        DryRun=False
    )

for vpc in Vpcs:
    print(vpc.VpcId)
    ...
    pprint(vpc.Elbs)
    ...
    pprint(vpc.Instances)
    ...
    pprint(vpc.InternetGateways)
    ...
    pprint(vpc.SecurityGroups)
    ...
    pprint(vpc.Subnets)

pprint("delete {} vpcs".format(len(Vpcs)))

for vpc in Vpcs:
    clean_region_resources("elb", vpc.Elbs, delete_load_balancer)
    clean_region_resources("ec2", vpc.InternetGateways, detach_internet_gateway)
    clean_region_resources("ec2", vpc.InternetGateways, delete_internet_gateway)
    clean_region_resources("ec2", vpc.SecurityGroups, delete_security_group)
    clean_region_resources("ec2", vpc.Subnets, delete_subnets)
    clean_region_resources("ec2", vpc.RouteTables, delete_route_table)
    clean_region_resources("ec2", vpc.VpcEndpoints, delete_vpc_endpoints)

clean_region_resources("ec2", _vpcs, delete_vpc)





