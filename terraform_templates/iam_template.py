from typing import Mapping
import json


# Creates a dictionary that specifies how Terraform should deploy IAM roles and policies.
# For each account, we will specify an AWS provider role that will be used to deploy resources.
# The provided principal resource in config.yml must be able to assume each role in each account.
def terraform_iam_template(config: Mapping) -> Mapping:
    dict_template = {
        "terraform": {
            "required_providers": {
                "aws": {
                    "source": "hashicorp/aws",
                    "version": "3.00"
                }
            }
        },
        "provider":
        [{
            "aws": {
                "region": config["aws"]["provider"]["region"]
            }
        }] +
        [{
            "aws": {
                "alias": account["account_name"],
                "region": config["aws"]["provider"]["region"],
                "assume_role": {
                    "role_arn": account["role"]
                }
            }
        } for account in config["aws"]["accounts"]],
        "resource":
            [__iam_role_resource(config, account["account_name"]) for account in config["aws"]["accounts"]] +
            [__iam_policy_resource(config, account["account_name"]) for account in config["aws"]["accounts"]] +
            [__iam_role_policy_attachment(config, account["account_name"]) for account in config["aws"]["accounts"]]
    }

    return dict_template


# Creates the IAM role that will be deployed
def __iam_role_resource(config: Mapping, account_name: str) -> Mapping:
    dict_template = {
        "aws_iam_role": {
            config["aws"]["IAM_role_name"] + "_" + account_name: {
                "provider": "aws." + account_name,
                "name": config["aws"]["IAM_role_name"],
                "tags": {
                    "owner": config["aws"]["resource_owner"]
                },
                "description": "The role that CloudCustodian will be acting as to implement cloud enforcement policies. "
                               "See https://github.com/ucsc-cgp/cgp-cloud-policies.",
                "assume_role_policy": json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": config["aws"]["provider"]["principal"]
                            },
                            "Action": "sts:AssumeRole",
                            "Condition": {}
                        },
                        {  # we need to allow AWS Lambda to use this role, as this is how the custodian policies will take actions
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "lambda.amazonaws.com"
                            },
                            "Action": "sts:AssumeRole",
                            "Condition": {}
                        }
                    ]
                })
            }
        }
    }

    return dict_template


# Creates the IAM policy that will give the role permissions
def __iam_policy_resource(config: Mapping, account_name: str) -> Mapping:
    dict_template = {
        "aws_iam_policy": {
            config["aws"]["IAM_policy_name"] + "_" + account_name: {
                "provider": "aws." + account_name,
                "name": config["aws"]["IAM_policy_name"],
                "description": "The policy that will give the IAM role permissions to deploy custodian resources. "
                               "See https://github.com/ucsc-cgp/cgp-cloud-policies.",
                "policy": json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": [
                                "s3:ListAllMyBuckets",
                                "s3:GetObjectTagging"
                            ],
                            "Effect": "Allow",
                            "Resource": "arn:aws:s3:::*"
                        }
                    ]
                })
            }
        },
    }

    return dict_template


# Attaches the above roles and policies
def __iam_role_policy_attachment(config: Mapping, account_name: str) -> Mapping:
    dict_template = {
        "aws_iam_role_policy_attachment": {
            "attach_" + account_name: {
                "provider": "aws." + account_name,
                "role": "${aws_iam_role." + config["aws"]["IAM_role_name"] + "_" + account_name + ".name}",
                "policy_arn": "${aws_iam_policy." + config["aws"]["IAM_policy_name"] + "_" + account_name + ".arn}"
            }
        }
    }

    return dict_template
