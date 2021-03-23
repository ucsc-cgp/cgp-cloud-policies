#!/bin/bash

source deployment_variables.env
accountsArray=(${ACCOUNTS})
rolesArray=(${ROLES})
for (( i=0; i<${#accountsArray[@]}; i++));
  do
    echo "Destroying CloudCustodian resources on ${accountsArray[$i]}"
    c7n-org run-script --output-dir s3://$S3_STATE_BUCKET/$CUSTODIAN_PREFIX -c generated/custodian/generated_custodian_config.json -a ${accountsArray[$i]} "python3 utils/mugc.py --assume ${rolesArray[$i]} --present -c generated/custodian/generated_custodian_policy.json"
  done
