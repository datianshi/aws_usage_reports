from pprint import pprint

import boto3
import botocore
from functions import aggregate_region_resources
from functions import resources_per_vpc
from functions import resources_per_resource
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
        self.Instances = list(filter(lambda x: x.get('VpcId', '')  == self.VpcId, instances))

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
    def findFlowLogs(self):
        def find_flow_logs(client, filters):
            flow_logs=client.describe_flow_logs(
                Filters= filters
            )
            return list(map(lambda x: {'FlowLogId': x['FlowLogId'], 'Region': self.Region}, flow_logs['FlowLogs']))
        self.VpcFlowLogs = resources_per_resource(self.VpcId, self.Region, find_flow_logs)
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
                            filter(lambda x: len(x['Associations']) > 0 and x['Associations'][0]['Main'] == False, subnets['RouteTables'])))
        self.RouteTables = resources_per_vpc(self.VpcId, self.Region, find_route_tables)

def get_vpcs(client):
    return client.describe_vpcs()

def get_elastic_addresses(client):
    return client.describe_addresses()


vpcs=list(filter(lambda x: not x['IsDefault'], aggregate_region_resources(get_resource({'func' : get_vpcs, 'key': 'Vpcs'}))))
addresses=list(aggregate_region_resources(get_resource({'func' : get_elastic_addresses, 'key': 'Addresses'})))


def findElb(region):
    client = boto3.client('elbv2', region_name=region)
    response = client.describe_load_balancers()
    return list(map(lambda x: {'LoadBalancerName': x['LoadBalancerName'], 'VPCId': x['VpcId'], 'Region': region, 'LoadBalancerArn': x['LoadBalancerArn']}, response['LoadBalancers']))

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
    v.findFlowLogs()
    if len(v.Instances) == 0 :
        Vpcs.append(v)
        _vpcs.append(vpc)

def delete_load_balancer(client, load_balancer):
    print("clean load balancer: {}".format(load_balancer))
    client.delete_load_balancer(
        LoadBalancerArn=load_balancer['LoadBalancerArn']
    )

def delete_vpc(client, vpc):
    print("delete vpc: {}".format(vpc))
    client.associate_dhcp_options(
        DhcpOptionsId='default',
        VpcId=vpc['VpcId'],
        DryRun=False
    )

    # client.delete_dhcp_options(
    #     DhcpOptionsId=vpc['DhcpOptionsId'],
    #     DryRun=False
    # )

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

    sg = client.describe_security_groups(
        Filters = [
            {
                'Name' : 'group-id',
                'Values': [
                    security_group['GroupId']
                ]
            }
        ]
    )

    # Clean the references to another security group
    if len(sg['SecurityGroups']) != 0:
        delete_sg_rules = list(filter(lambda x : len(x['UserIdGroupPairs']) > 0, sg['SecurityGroups'][0]['IpPermissions']))
        if len(delete_sg_rules) > 0 :
            pprint(delete_sg_rules)
            client.revoke_security_group_ingress(
                GroupId=security_group['GroupId'],
                IpPermissions=delete_sg_rules
            )

    sgp_references = client.describe_security_groups(
        Filters=[
            {
                'Name': 'ip-permission.group-id',
                'Values': [
                    security_group['GroupId'],
                ]
            },
        ]
    )

    # Recursive to handle the circular dependencies
    if len(sgp_references['SecurityGroups']) == 0:
        try:
            client.delete_security_group(
                GroupId=security_group['GroupId'],
            )
        except botocore.exceptions.ClientError as e:
            pprint(e.response)
        return
    else:
        print("the references for {}".format(format(security_group['GroupId'])))
        pprint(sgp_references)
        for sgp in sgp_references['SecurityGroups']:
            try:
                delete_security_group(client, sgp)
            except botocore.exceptions.ClientError as e:
                pprint(e.response)
            return

    try:
        delete_security_group(client, security_group)
    except botocore.exceptions.ClientError as e:
        pprint(e.response)


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

def delete_vpc_flowlogs(client, vpc_flow_log):
    print("delete vpc flow log: {}".format(vpc_flow_log['FlowLogId']))
    client.delete_flow_logs(
        FlowLogIds=[
            vpc_flow_log['FlowLogId']
        ]
    )

def delete_subnets(client, subnet):
    print("delete subnet: {}".format(subnet['SubnetId']))
    client.delete_subnet(
        SubnetId=subnet['SubnetId'],
        DryRun=False
    )

#Clean Region Elastic IPs

def get_addresses(region):
    addresses=[]
    client = boto3.client('ec2', region_name=region)
    response = client.describe_addresses()

    for i in response['Addresses']:
        if i.get('AssociationId', None) == None:
            i['Region'] = region
            addresses.append(i)
    return addresses

eips = aggregate_region_resources(get_addresses)

def delete_eip(client, eip):
    print("delete eip: {}".format(eip['PublicIp']))
    client.release_address(
        AllocationId=eip['AllocationId'],
        DryRun=False
    )

clean_region_resources("ec2", eips, delete_eip)

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
    clean_region_resources("elbv2", vpc.Elbs, delete_load_balancer)
    clean_region_resources("ec2", vpc.InternetGateways, detach_internet_gateway)
    clean_region_resources("ec2", vpc.InternetGateways, delete_internet_gateway)
    clean_region_resources("ec2", vpc.VpcFlowLogs, delete_vpc_flowlogs)
    clean_region_resources("ec2", vpc.SecurityGroups, delete_security_group)
    clean_region_resources("ec2", vpc.Subnets, delete_subnets)
    clean_region_resources("ec2", vpc.RouteTables, delete_route_table)
    clean_region_resources("ec2", vpc.VpcEndpoints, delete_vpc_endpoints)

clean_region_resources("ec2", _vpcs, delete_vpc)





