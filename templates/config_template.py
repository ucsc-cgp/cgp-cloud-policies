from typing import Mapping
from utils.helpers import create_role_string, create_full_iam_resource_name

def custodian_organizations_config_template(config: Mapping) -> Mapping:
    dict_template = {
        "accounts": [
            {
                "account_id": account["account_id"],
                "name": account["account_name"],
                "regions": config["aws"]["regions"],
                "role": create_role_string(account["account_id"], create_full_iam_resource_name(config["aws"]["IAM_role_prefix"], account["account_name"]))
            } for account in config["aws"]["accounts"]
        ]
    }

    return dict_template
