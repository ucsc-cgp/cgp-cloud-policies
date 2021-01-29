import yaml
from typing import Mapping
from terraform_templates import iam_template


# generates all the necessary files to deploy policies given a configuration file in the format specified in /config.yml.template
class Generator:
    CUSTODIAN_GENERATED_DIR = "generated/custodian/"
    TERRAFORM_GENERATED_DIR = "generated/terraform/"

    def __init__(self, config_path="config.yml"):
        self.config_path = config_path  # path to the config YAML file that we will use to describe resources

        # load the config file
        with open(self.config_path) as file:
            self.config: Mapping = yaml.load(file)

    # Generates the config file used by c7n-org, which specifies all the accounts, regions, and roles we will use to deploy policies
    def generate_custodian_config(self):
        raise NotImplementedError()

    # Generates the policy file that will be deployed as a resource using custodian
    def generate_custodian_policy(self):
        raise NotImplementedError()

    # Generates the terraform file that will deploy the IAM roles and policies needed by custodian
    def generate_terraform(self):
        return iam_template.terraform_iam_template(self.config)
