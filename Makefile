PYTHON = python3
.DEFAULT_GOAL = help
.PHONY: help package deploy destroy

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

destroy:
	if [ -f generated/custodian/generated_custodian_config.json ] && [ -f generated/custodian/generated_custodian_policy.json ] ; \
	then \
	  	source deployment_variables.env && \
		c7n-org run-script --output-dir s3://$$S3_STATE_BUCKET/$$CUSTODIAN_PREFIX -c generated/custodian/generated_custodian_config.json "python3 utils/mugc.py --present -c generated/custodian/generated_custodian_policy.json"; \
	fi;
	cd generated/terraform/ && terraform destroy