from typing import Mapping
from utils.helpers import create_config_policy_resource_name, custodian_config_policy_dict


def custodian_policy_template(config: Mapping) -> Mapping:
    policies = []
    for resource in config["aws"]["resources"]:
        policies.append(custodian_marking_policy(config, resource))
        policies.append(custodian_remove_marked_for_op(config, resource))
        policies.append(custodian_delete_marked_resource(config, resource))

    dict_template = {
        "policies": policies
    }

    return dict_template


def custodian_marking_policy(config: Mapping, resource: str) -> Mapping:
    return {
        "name": create_config_policy_resource_name(config["aws"]["custodian_policy_prefix"], resource),
        "description": "This policy will mark improperly tagged resources for deletion.",
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
        ],
        "actions": [{
            "type": "mark-for-op",
            "tag": config["aws"]["custodian_marking_tag"],
            "op": "delete",
            "hours": 1
        }
        ]
    }


def custodian_remove_marked_for_op(config: Mapping, resource: str) -> Mapping:
    return {
        "name": create_config_policy_resource_name(config["aws"]["custodian_policy_prefix"] + "untagger_", resource),
        "description": "This policy will remove tags that mark resources for deletion.",
        "mode": {
            "type": "config-rule"
        },
        "resource": resource,
        "filters": [
            {f"tag:{config['aws']['custodian_marking_tag']}": "not-null"}],
        "actions": [{
            "type": "remove-tag",
            "tags": [config["aws"]["custodian_marking_tag"]]
        }]
    }


def custodian_delete_marked_resource(config: Mapping, resource: str) -> Mapping:
    return {
        "name": create_config_policy_resource_name(config["aws"]["custodian_policy_prefix"] + "deleter_", resource),
        "description": "This policy will delete resources that have been marked for deletion for a specific amount of time.",
        "mode": {
            "type": "periodic",
            "schedule": "cron(0 * * * ? *)"
        },
        "resource": resource,
        "filters": [
            {"type": "marked-for-op",
             "tag": config["aws"]["custodian_marking_tag"],
             "op": "delete"}
        ],
        "actions": [{
            "type": "delete"
        }]
    }
