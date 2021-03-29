PYTHON = python3
.DEFAULT_GOAL = help
.PHONY: help package deploy destroy-custodian destroy-terraform

help:
	@echo "make package : Generates Terraform and CloudCustodian files from templates"
	@echo "make deploy : Deploys Terraform and CloudCustodian generated files"
	@echo "make destroy : Destroys deployed Terraform and CloudCustodian resources"

package:
	PYTHON generate.py

deploy:
	cd generated/terraform/ && terraform apply
	sleep 20
	source deployment_variables.env && \
	c7n-org run -c generated/custodian/generated_custodian_config.json -u generated/custodian/generated_custodian_policy.json --output-dir s3://$$S3_STATE_BUCKET/$$CUSTODIAN_PREFIX

destroy-custodian:
	bash destroyCloudCustodianResources.sh

# Destroying terraform IAM roles causes permissions with resources that have linked the ARN in trust policies/relationships. Do this only if necessary
destroy-terraform:
	cd generated/terraform/ && terraform destroy
