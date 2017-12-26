#!/bin/bash
set -e

region=$1

for vpc in `aws ec2 describe-vpcs --region $region --output json | jq -r '.[][] | select (.IsDefault==false) | .VpcId'`
do
  gatewayId=`aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$vpc" --region=$region --output=json | jq -r '.InternetGateways | .[] .InternetGatewayId'`
  echo $vpc$gatewayId
  echo "X$gatewayId"
  if [ "X$gatewayId" != "X" ]
  then
   echo "detach gateway: $gatewayId with vpc: $vpc" 
   aws ec2 detach-internet-gateway --internet-gateway-id $gatewayId --vpc-id $vpc --region $region
   aws ec2 delete-internet-gateway --internet-gateway-id $gatewayId --region $region
  fi
  #aws ec2 delete-vpc --vpc-id $vpc --region $region
done

