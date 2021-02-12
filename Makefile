PYTHON = python3
.DEFAULT_GOAL = help

help:
	@echo "TODO"

# Destroys custodian resources that are specified in a policy file.
destroy-custodian:
	if [ -f generated/custodian/generated_custodian_config.json ] && [ -f generated/custodian/generated_custodian_policy.json ] ; \
	then \
		c7n-org run-script -s custodian_output -c generated/custodian/generated_custodian_config.json "python3 utils/mugc.py --present -c generated/custodian/generated_custodian_policy.json"; \
	fi;