from typing import Mapping
from utils.helpers import create_remote_bucket_string, create_full_iam_resource_name
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
            },
            "backend": {
                "s3": {
                    "bucket": config["aws"]["remote_S3_bucket_name"],
                    "key": config["aws"]["remote_S3_terraform_key"],
                    "region": config["aws"]["provider"]["region"]
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
            create_full_iam_resource_name(config["aws"]["IAM_role_prefix"], account_name): {
                "provider": "aws." + account_name,
                "name": create_full_iam_resource_name(config["aws"]["IAM_role_prefix"], account_name),
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
            create_full_iam_resource_name(config["aws"]["IAM_policy_prefix"], account_name): {
                "provider": "aws." + account_name,
                "name": create_full_iam_resource_name(config["aws"]["IAM_policy_prefix"], account_name),
                "description": "The policy that will give the IAM role permissions to deploy custodian resources. "
                               "See https://github.com/ucsc-cgp/cgp-cloud-policies.",
                "policy": json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {   # required actions to deploy custodian https://github.com/cloud-custodian/cloud-custodian/issues/2291 (
                            # slightly out-of-date)
                            "Action": [
                                "events:DescribeRule",
                                "events:EnableRule",
                                "events:ListTargetsByRule",
                                "events:PutRule",
                                "events:PutTargets",
                                "iam:PassRole",
                                "lambda:AddPermission",
                                "lambda:CreateAlias",
                                "lambda:CreateFunction",
                                "lambda:GetAlias",
                                "lambda:GetFunction",
                                "lambda:ListTags",
                                "lambda:UpdateAlias",
                                "lambda:UpdateFunctionCode",
                                "lambda:UpdateFunctionConfiguration",
                                "config:DescribeConfigRules",
                                "config:PutConfigRule",
                                "config:StartConfigRulesEvaluation",
                                "config:PutEvaluations",
                                "config:GetComplianceDetailsByConfigRule",
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            "Effect": "Allow",
                            "Resource": "*"
                        },
                        {
                            "Action": [
                                "s3:*"
                            ],
                            "Effect": "Allow",
                            "Resource": "arn:aws:s3:::*"
                        },
                        {
                            "Action": [
                                "*"
                            ],
                            "Effect": "Allow",
                            "Resource": create_remote_bucket_string(config["aws"]["remote_S3_bucket_name"])
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
                "role": "${aws_iam_role." + create_full_iam_resource_name(config["aws"]["IAM_role_prefix"], account_name) + ".name}",
                "policy_arn": "${aws_iam_policy." + create_full_iam_resource_name(config["aws"]["IAM_policy_prefix"], account_name) + ".arn}"
            }
        }
    }

    return dict_template
