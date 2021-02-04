from typing import Mapping


def custodian_policy_template(config: Mapping) -> Mapping:
    dict_template = {
        "policies": [
            {
                "name": config["aws"]["custodian_policy_prefix"] + resource,
                "mode": {
                    "type": "config-rule"
                },
                "resource": resource,
                "filters": [{
                    "tag:Owner": "absent"
                }]
            } for resource in config["aws"]["resources"]
        ]
    }

    return dict_template