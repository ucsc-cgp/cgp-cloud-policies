
# generates all the necessary files to deploy policies given a configuration file in the format specified in /config.yml.template
class Generator:
    CUSTODIAN_GENERATED_DIR = "generated/custodian/"
    TERRAFORM_GENERATED_DIR = "generated/terraform/"

    def __init__(self):
        pass
    # Generates the config file used by c7n-org, which specifies all the accounts, regions, and roles we will use to deploy policies
    def generate_custodian_config(self):
        pass

    # Generates the policy file that will be deployed as a resource using custodian
    def generate_custodian_policy(self):
        pass

    # Generates the terraform file that will deploy the IAM roles and policies needed by custodian
    def generate_terraform(self):
        pass
