PYTHON = python3
.DEFAULT_GOAL = help
.PHONY: help package deploy destroy

# Uses the form 's3://{s3Bucket}/{CloudCustodianStateDirectoryName}. You do not need to create
# the CloudCustodian dir beforehand. The S3 bucket must already exist for the CloudCustodian state to be stored here.
# These values are parsed from the config.yml file.
S3_STATE_DIR=$$(yq -r .aws.remote_S3_bucket_name config.yml)
CUSTODIAN_PREFIX=$$(yq -r .aws.remote_S3_custodian_key config.yml)

help:
	@echo "make package : Generates Terraform and CloudCustodian files from templates"
	@echo "make deploy : Deploys Terraform and CloudCustodian generated files"
	@echo "make destroy : Destroys deployed Terraform and CloudCustodian resources"

package:
	PYTHON generate.py

deploy:
	cd generated/terraform/ && terraform apply
	sleep 20
	c7n-org run -c generated/custodian/generated_custodian_config.json -u generated/custodian/generated_custodian_policy.json --output-dir s3://$(S3_STATE_DIR)/$(CUSTODIAN_PREFIX)

destroy:
	if [ -f generated/custodian/generated_custodian_config.json ] && [ -f generated/custodian/generated_custodian_policy.json ] ; \
	then \
		c7n-org run-script --output-dir s3://$(S3_STATE_DIR)/$(CUSTODIAN_PREFIX) -c generated/custodian/generated_custodian_config.json "python3 utils/mugc.py --present -c generated/custodian/generated_custodian_policy.json"; \
	fi;
	cd generated/terraform/ && terraform destroy