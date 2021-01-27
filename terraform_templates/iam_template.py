from typing import Mapping


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
                        }
                    ]
                }
            }
        }
    }

    return dict_template
