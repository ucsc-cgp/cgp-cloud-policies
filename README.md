# cgp-cloud-policies

Policies for CGP cloud resources, managed by [cloud-custodian] policies. Uses [terraform] to set up permissions' infrastructure.

  [cloud-custodian]: https://github.com/cloud-custodian/cloud-custodian
  [terraform]: https://github.com/hashicorp/terraform

## How it works

Terraform
* Deploys IAM roles and policies that are needed to deploy and enforce CloudCustodian policies.

CloudCustodian
* While assuming a role created by Terraform, deploy policies in [AWS Config] that will manage resources.

CloudCustodian allows us to deploy policies to AWS accounts. These policies are AWS resources
that can be viewed in the AWS console (see [AWS config]). CloudCustodian policies will continuously monitor resources,
and if specified, take actions against resources that are non-compliant. 

Of course, we need to have the appropriate permissions to deploy such policies, this is where Terraform comes into play. 
Terraform can be used to easily specify and deploy IAM roles and policies, 
which CloudCustodian can subsequently assume to perform it functionality.

## How you use it



   [AWS config]: https://aws.amazon.com/config/#:~:text=AWS%20Config%20is%20a%20service,configurations%20of%20your%20AWS%20resources.&text=This%20enables%20you%20to%20simplify,change%20management%2C%20and%20operational%20troubleshooting.

### Multi-account and multi-region

## Usage

### Requirements
* Docker

##### Manual configuration
* Terraform v0.14.0
* Python 3.9.0

```console
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

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

# Destroy the resources afterwards
$ AWS_PROFILE='...' make destroy

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

##### Configuring c7n-mailer templates
TODO
