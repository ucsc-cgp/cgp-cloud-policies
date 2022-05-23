# cgp-cloud-policies

Policies for CGP cloud resources, managed by [cloud-custodian] policies. Uses [terraform] to set up permissions' infrastructure.

  [cloud-custodian]: https://github.com/cloud-custodian/cloud-custodian
  [terraform]: https://github.com/hashicorp/terraform

## How it works

Terraform
* Deploys IAM roles and policies that are needed to deploy and enforce CloudCustodian policies.

CloudCustodian
* While assuming a role created by Terraform, deploy policies using AWS Lambda that will manage resources.

CloudCustodian allows us to deploy policies to AWS accounts. These policies are AWS resources
that can be viewed under AWS Lambdas of the AWS Console. CloudCustodian policies will continuously monitor resources,
and if specified, take actions against resources that are non-compliant. 

Of course, we need to have the appropriate permissions to deploy such policies, this is where Terraform comes into play. 
Terraform can be used to easily specify and deploy IAM roles and policies, 
which CloudCustodian can subsequently assume to perform it functionality.

### Requirements
* Docker
* Python 3.9.0

```console
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

You will also need to set up the remote S3 bucket that you want Terraform and CloudCustodian state/log files to be store
in. The bucket will need to have an access policy setup if you want the CloudCustodian run logs to be written.

### The full process
```console
# get the repository
$ git clone https://github.com/ucsc-cgp/cgp-cloud-policies.git
$ cd cgp-cloud_policies

# setup the environment
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt

# Create a config.yml file, copy the contents of config_example.yml into it, and fill it out
# Then, generate the first set of files from templates
$ make package

# We have to initialize terraform locally. You'll need AWS credentials to setup the remote
# s3 bucket.
$ cd generated/terraform
$ AWS_PROFILE='...' terraform init

# If all goes well, terraform initialized correctly. If there was an error initializing,
# make sure all the config info is typo-free (especially for the remote s3 bucket).
# You may need to delete the .terraform file.

# Go back to the root of the project, and run!
$ cd ../..
$ AWS_PROFILE='...' make deploy

# Until you setup the access policy in the S3 bucket that will be storing logs, the config rules will not evaluate
# as they will error out when attempting to write logs to a bucket. To resolve this, update the S3 access policy
# with each of the IAM roles that were just deployed.

# This will perform an initial execution of all the config policies deployed. If you choose not to run this
# only new/modified resources will be evaluated for compliance with the rule.
$ AWS_PROFILE='...' make initial-evaluate

# Destroy the resources afterwards. This will destroy the Terraform IAM roles, which will modify existing access
# policies on the remote S3 bucket.
$ AWS_PROFILE='...' make destroy-custodian
$ AWS_PROFILE='...' make destroy-terraform

```

### Common tasks
All resource deployments and destructions will rely on your config.yml file. Make sure to populate it with the necessary resources.

#####  Tearing down deployed resources
*Note*: don't forget to provide credentials (such as through AWS_PROFILE=... env variable)

Run the command ```make destroy```

##### Adding, removing, or adjusting a policy
1. Update config.yml with your new information
2. Run the command ```make package```
3. Run the command ```make deploy```
