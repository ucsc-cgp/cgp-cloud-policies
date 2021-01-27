from typing import Mapping


# Creates a dictionary that specifies how Terraform should deploy IAM roles and policies
def terraform_iam_template(config: Mapping) -> Mapping:
    dict_template = {
        "terraform": {
            "required_providers": {
                "aws": {
                    "source": "hashicorp/aws",
                    "version": "~> 3.00"
                }
            }
        },
        "provider": {
            "aws": {
                "access_key": config["aws"]["provider"]["access_key"],
                "secret_key": config["aws"]["provider"]["secret_key"],
                "region": config["aws"]["primary_region"]
            }
        },
        "resource": __iam_role_resource(config)
    }

    return dict_template


# Creates the IAM role that will be deployed
def __iam_role_resource(config: Mapping) -> Mapping:
    dict_template = {
        "aws_iam_role": {
            config["aws"]["IAM_role_name"]: {
                "name": config["aws"]["IAM_role_name"],
                "description": "The role that CloudCustodian will be acting as to implement cloud enforcement policies",
                "assume_role_policy": {
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
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "lambda.amazonaws.com"
                            },
                            "Action": "sts:AssumeRole",
                            "Condition": {}
                        }
                    ]
                }
            }
        }
    }

    return dict_template


# Creates the IAM policy that will give the role permissions
def __iam_policy_resource(config: Mapping) -> Mapping:
    dict_template = {
        "aws_iam_policy": {
            config["aws"]["IAM_policy_name"]: {
                "name": config["aws"]["IAM_policy_name"],
                "description": "The policy that will give the IAM role permissions to deploy custodian resources",
                "policy": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": [
                                "*"
                            ],
                            "resource": "*",
                            "Effect": "Allow"
                        }
                    ]
                }
            }
        }
    }

    return dict_template


# Attaches the above roles and policies
def __iam_role_policy_attachment(config: Mapping) -> Mapping:
    dict_template = {
        "aws_iam_role_policy_attachment": {
            "attach": {
                "role": "aws_iam_role." + config["aws"]["IAM_role_name"] + ".name",
                "policy_arn": "aws_iam_policy." + config["aws"]["IAM_policy_name"] + ".arn"
            }
        }
    }

    return dict_template
