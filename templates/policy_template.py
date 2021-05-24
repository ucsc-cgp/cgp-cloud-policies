from typing import Mapping
from utils.helpers import create_config_policy_resource_name, custodian_config_policy_dict


def custodian_policy_template(config: Mapping) -> Mapping:
    policies = []
    for resource in config["aws"]["resources"]:
        policies.append(custodian_compliance_policy(config, resource))
        policies.append(custodian_remove_marked_for_op(config, resource))
        policies.append(custodian_deleter_lambda(config, resource))

    dict_template = {
        "policies": policies
    }

    return dict_template


def custodian_compliance_policy(config: Mapping, resource: str) -> Mapping:
    return {
        "name": create_config_policy_resource_name(config["aws"]["custodian_policy_prefix"], resource),
        "description": "This policy will mark improperly tagged resources for deletion.",
        "mode": {
            "type": "periodic",
            "schedule": "rate(1 hour)"
        },
        "resource": resource,
        "filters": [{"and": [
            # Owner/owner tag [is absent] or [does not look like an email address AND does not have the word 'shared' (case
            # insensitive)]. Also include that the tag is not already there.
            custodian_config_policy_dict("Owner"),
            custodian_config_policy_dict("owner"),
            {f"tag:{config['aws']['custodian_marking_tag']}": "absent"}
        ]}
        ],
        "actions": [{
            "type": "mark-for-op",
            "tag": config["aws"]["custodian_marking_tag"],
            "op": "delete",
            "days": 0,
            "hours": 1
        }]
    }


def custodian_remove_marked_for_op(config: Mapping, resource: str) -> Mapping:
    return {
        "name": create_config_policy_resource_name(config["aws"]["custodian_policy_prefix"] + "untagger_", resource),
        "description": "This policy will remove tags that mark resources for deletion.",
        "mode": {
            "type": "periodic",
            "schedule": "rate(15 minutes)"
        },
        "resource": resource,
        "filters": [
            {"and": [
                {f"tag:{config['aws']['custodian_marking_tag']}": "not-null"},
                {"not": [
                    {"and": [
                        # Owner/owner tag [is absent] or [does not look like an email address AND does not have the word 'shared' (case
                        # insensitive)]
                        custodian_config_policy_dict("Owner"),
                        custodian_config_policy_dict("owner")
                    ]}
                ]}
            ]}
        ],
        "actions": [{
            "type": "remove-tag",
            "tags": [config["aws"]["custodian_marking_tag"]]
        }]
    }


def custodian_deleter_lambda(config: Mapping, resource: str) -> Mapping:
    dict = {
        "name": create_config_policy_resource_name(config["aws"]["custodian_policy_prefix"] + "deleter_", resource),
        "description": "This policy will delete resources that have been marked for deletion for a specific amount of time.",
        "mode": {
            "type": "periodic",
            "schedule": "rate(1 hour)"
        },
        "resource": resource,
        "filters": [
            {"and": [
                # *** Recheck the compliance status of a resource before performing any deletions ***
                # Owner/owner tag [is absent] or [does not look like an email address AND does not have the word 'shared' (case
                # insensitive)]
                custodian_config_policy_dict("Owner"),
                custodian_config_policy_dict("owner"),
                {
                    "type": "marked-for-op",
                    "tag": config["aws"]["custodian_marking_tag"],
                    "op": "delete"
                }
            ]}
        ],
        "actions": [{
            "type": "delete"
        }]
    }

    if resource == "s3":
        dict["actions"][0]["remove-contents"] = True

    return dict
