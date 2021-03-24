from typing import Mapping


def custodian_organizations_config_template(config: Mapping) -> Mapping:
    dict_template = {
        "accounts": [
            {
                "account_id": account["account_id"],
                "name": account["account_name"],
                "regions": config["aws"]["regions"],
                "role": create_role_string(account["account_id"], config["aws"]["IAM_role_prefix"] + account["account_name"])
            } for account in config["aws"]["accounts"]
        ]
    }

    return dict_template


def create_role_string(account_id: str, iam_role_name: str) -> str:
    return "arn:aws:iam::" + account_id + ":role/" + iam_role_name
