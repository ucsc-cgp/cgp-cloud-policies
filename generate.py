from typing import Mapping

import json
import os
import yaml

from templates import config_template, policy_template, iam_template
from utils.helpers import create_deployed_config_policy_resource_name

# generates all the necessary files to deploy policies given a configuration file in the format specified in /config.yml.template
class ConfigGenerator:
    CUSTODIAN_GENERATED_DIR = "generated/custodian/"
    TERRAFORM_GENERATED_DIR = "generated/terraform/"
    TERRAFORM_FILE = "generated_terraform.tf.json"
    CUSTODIAN_CONFIG_FILE = "generated_custodian_config.json"
    CUSTODIAN_POLICY_FILE = "generated_custodian_policy.json"
    ENV_FILE = "deployment_variables.env"

    def __init__(self, config_path="config.yml"):
        self.config_path = config_path  # path to the config YAML file that we will use to describe resources

        # load the config file
        with open(self.config_path) as file:
            self.config: Mapping = yaml.load(file, Loader=yaml.FullLoader)

    # Generates the config file used by c7n-org, which specifies all the accounts, regions, and roles we will use to deploy policies
    def generate_custodian_config(self):
        generated_cc = config_template.custodian_organizations_config_template(self.config)
        filepath = os.path.join(self.CUSTODIAN_GENERATED_DIR, self.CUSTODIAN_CONFIG_FILE)
        with open(filepath, "w") as outfile:
            json.dump(generated_cc, outfile, indent=2)

    # Generates the policy file that will be deployed as a resource using custodian
    def generate_custodian_policy(self):
        generated_cc = policy_template.custodian_policy_template(self.config)
        filepath = os.path.join(self.CUSTODIAN_GENERATED_DIR, self.CUSTODIAN_POLICY_FILE)
        with open(filepath, "w") as outfile:
            json.dump(generated_cc, outfile, indent=2)

    # Generates the terraform file that will deploy the IAM roles and policies needed by custodian
    def generate_terraform(self):
        generated_terraform = iam_template.terraform_iam_template(self.config)
        filepath = os.path.join(self.TERRAFORM_GENERATED_DIR, self.TERRAFORM_FILE)
        with open(filepath, "w") as outfile:
            json.dump(generated_terraform, outfile, indent=2)

    # Generates an environment variable file from the config file, this is used when deploying and destroying resources
    def generate_environment_variables(self):
        accounts_str = " ".join([a["account_name"] for a in self.config["aws"]["accounts"]])
        roles_str = " ".join([a["role"] for a in self.config["aws"]["accounts"]])

        policies_str = " ".join([create_deployed_config_policy_resource_name(self.config["aws"]["custodian_policy_prefix"], r) for r in self.config["aws"]["resources"]])
        policies_str += " " + " ".join([create_deployed_config_policy_resource_name(self.config["aws"]["custodian_policy_prefix"] + "untagger_", r) for r in self.config["aws"]["resources"]])

        file_contents = ""
        file_contents += f'S3_STATE_BUCKET=\"{self.config["aws"]["remote_S3_bucket_name"]}\"\n'
        file_contents += f'CUSTODIAN_PREFIX=\"{self.config["aws"]["remote_S3_custodian_key"]}\"\n'
        file_contents += f'ACCOUNTS=\"{accounts_str}\"\n'
        file_contents += f'ROLES=\"{roles_str}\"\n'
        file_contents += f'POLICIES=\"{policies_str}\"\n'

        with open(self.ENV_FILE, "w") as outfile:
            outfile.write(file_contents)


if __name__ == "__main__":
    G = ConfigGenerator()
    G.generate_terraform()
    G.generate_custodian_config()
    G.generate_custodian_policy()
    G.generate_environment_variables()
