from typing import Mapping

import json
import os
import yaml

from terraform_templates import iam_template


# generates all the necessary files to deploy policies given a configuration file in the format specified in /config.yml.template
class ConfigGenerator:
    CUSTODIAN_GENERATED_DIR = "generated/custodian/"
    TERRAFORM_GENERATED_DIR = "generated/terraform/"
    TERRAFORM_FILE = "generated_terraform.tf.json"

    def __init__(self, config_path="config.yml"):
        self.config_path = config_path  # path to the config YAML file that we will use to describe resources

        # load the config file
        with open(self.config_path) as file:
            self.config: Mapping = yaml.load(file, Loader=yaml.FullLoader)

    # Generates the config file used by c7n-org, which specifies all the accounts, regions, and roles we will use to deploy policies
    def generate_custodian_config(self):
        raise NotImplementedError()

    # Generates the policy file that will be deployed as a resource using custodian
    def generate_custodian_policy(self):
        raise NotImplementedError()

    # Generates the terraform file that will deploy the IAM roles and policies needed by custodian
    def generate_terraform(self):
        generated_terraform = iam_template.terraform_iam_template(self.config)
        filepath = os.path.join(self.TERRAFORM_GENERATED_DIR, self.TERRAFORM_FILE)
        with open(filepath, "w") as outfile:
            json.dump(generated_terraform, outfile, indent=2)


if __name__ == "__main__":
    G = ConfigGenerator()
    G.generate_terraform()

