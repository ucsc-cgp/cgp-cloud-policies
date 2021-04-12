from typing import Mapping
from utils.helpers import create_config_policy_resource_name


def custodian_policy_template(config: Mapping) -> Mapping:
    dict_template = {
        "policies": [
            {
                "name": create_config_policy_resource_name(config["aws"]["custodian_policy_prefix"], resource),
                "mode": {
                    "type": "config-rule"
                },
                "resource": resource,
                "filters": [
                    # Owner tag [is absent] or [does not look like an email address AND does not have the word 'shared' (case insensitive)]
                    {"or": [
                        {
                            "tag:Owner": "absent"
                        },
                        {"and": [
                            {  # The general sequence '{content}@{content}.{content}' is not followed in the owner tag
                                "type": "value",
                                "key": "tag:Owner",
                                "op": "regex",
                                "value": "^((?!(@.*\\.)).)*$"
                            },
                            {  # Case insensitive match of 'shared' in the owner tag
                                "type": "value",
                                "key": "tag:Owner",
                                "op": "regex",
                                "value": "(?i)^((?!shared).)*$"
                            }]
                        }
                    ]},
                ]
            } for resource in config["aws"]["resources"]
        ]
    }

    return dict_template
