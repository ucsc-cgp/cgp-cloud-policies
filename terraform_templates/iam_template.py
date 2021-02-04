from typing import Mapping


def terraform_iam_template(config: Mapping):
    dict_template = {
        "terraform": {
            "required_providers": {
                "aws": {
                    "source": "hashicorp/aws",
                    "version": "3.00"
                }
            }
        },
        "provider": {
            "aws": {
                "region": config["aws"]["provider"]["region"]
            }
        }
    }

    return dict_template
