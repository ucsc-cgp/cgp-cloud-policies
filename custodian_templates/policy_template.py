from typing import Mapping


def custodian_policy_template(config: Mapping) -> Mapping:
    dict_template = {
        "policies": [
            {
                "name": _create_policy_name(config["aws"]["custodian_policy_prefix"], resource),
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


def _create_policy_name(prefix: str, resource: str) -> str:
    provider, resource_type = resource.split(".")
    return prefix + resource_type
