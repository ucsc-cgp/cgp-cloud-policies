PYTHON = python3
.DEFAULT_GOAL = help
.PHONY: help package deploy destroy

# Use the form 's3://{s3Bucket}/{CloudCustodianStateDirectoryName}. You do not need to create
# the CloudCustodian dir beforehand. The S3 bucket must already exist for the CloudCustodian state to be stored here.
S3_STATE_DIR = s3://tf-cc-bucket/CCstate

help:
	@echo "make package : Generates Terraform and CloudCustodian files from templates"
	@echo "make deploy : Deploys Terraform and CloudCustodian generated files"
	@echo "make destroy : Destroys deployed Terraform and CloudCustodian resources"

package:
	PYTHON generate.py

deploy:
	cd generated/terraform/ && terraform apply
	sleep 20 # If the terraform resources are used too soon after creation we may run into permission issues, wait a few seconds for creation to complete
	c7n-org run -c generated/custodian/generated_custodian_config.json -u generated/custodian/generated_custodian_policy.json --output-dir $(S3_STATE_DIR)

destroy:
	if [ -f generated/custodian/generated_custodian_config.json ] && [ -f generated/custodian/generated_custodian_policy.json ] ; \
	then \
		c7n-org run-script --output-dir $(S3_STATE_DIR) -c generated/custodian/generated_custodian_config.json "python3 utils/mugc.py --present -c generated/custodian/generated_custodian_policy.json"; \
	fi;
	cd generated/terraform/ && terraform destroy