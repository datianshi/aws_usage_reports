#!/bin/bash

for region in `aws ec2 describe-regions --output text | cut -f3`
do
  echo -e "Listing EC2 Instances in Region: '$region'\n"
  aws ec2 describe-instances --output=json --region=${region} | jq -r '[.[][].Instances[] | {InstanceType,Tags,InstanceId, LaunchTime: .LaunchTime, Date: .LaunchTime|sub(".[0-9]+Z$"; "Z") | fromdate, AZ: .Placement.AvailabilityZone, KeyName, State: .State.Name}]' | jq 'sort_by(.Date)'
  echo -e "Listing RDS in Region: $region \n"
  aws rds describe-db-instances --output=json --region=${region} | jq -r \
      '.DBInstances | .[] | {InstanceCreateTime, DBInstanceIdentifier, MasterUsername, vpc: .DBSubnetGroup.VpcId}'
done
