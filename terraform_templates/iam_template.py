from typing import Mapping


def terraform_iam_template(config: Mapping):
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
        }
    }

    return dict_template
