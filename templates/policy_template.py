from typing import Mapping
from utils.helpers import create_config_policy_resource_name, custodian_config_policy_dict


def custodian_policy_template(config: Mapping) -> Mapping:
    dict_template = {
        "policies": [
            {
                "name": create_config_policy_resource_name(config["aws"]["custodian_policy_prefix"], resource),
                "mode": {
                    "type": "config-rule"
                },
                "resource": resource,
                "filters": [{"and": [
                    # Owner/owner tag [is absent] or [does not look like an email address AND does not have the word 'shared' (case
                    # insensitive)]
                    custodian_config_policy_dict("Owner"),
                    custodian_config_policy_dict("owner")
                ]}
                ]
            } for resource in config["aws"]["resources"]
        ]
    }

    return dict_template
