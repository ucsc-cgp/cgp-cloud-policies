SHELL = /bin/sh

destroy-custodian:
	c7n-org run-script -s custodian_output -c generated/custodian/generated_custodian_config.json "python3 tools/ops/mugc.py --present -c generated/custodian/generated_custodian_policy.json" 	
