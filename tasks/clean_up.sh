#!/bin/bash

python3 clean-aws-resources/clean_ec2.py
python3 clean-aws-resources/clean_rds.py
python3 clean-aws-resources/clean_snapshots.py
python3 clean-aws-resources/clean_volumes.py
python3 clean-aws-resources/clean_vpc.py
