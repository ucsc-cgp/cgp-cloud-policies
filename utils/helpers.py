from typing import Mapping


def create_role_string(account_id: str, iam_role_name: str) -> str:
    return "arn:aws:iam::" + account_id + ":role/" + iam_role_name


def create_full_iam_resource_name(iam_resource_prefix: str, account_name: str) -> str:
    return iam_resource_prefix + account_name


def create_remote_bucket_string(remote_bucket_name: str) -> str:
    return "arn:aws:s3:::" + remote_bucket_name + "/*"


def create_config_policy_resource_name(policy_prefix: str, resource_type: str) -> str:
    return policy_prefix + resource_type.replace(".", "-")


# Custodian prepends a prefix to resources.
def create_deployed_config_policy_resource_name(policy_prefix: str, resource_type: str) -> str:
    return "custodian-" + create_config_policy_resource_name(policy_prefix, resource_type)


def owner_tag_email_regex() -> str:
    return "^((?!(@.*\\.)).)*$"


def owner_tag_shared_regex() -> str:
    return "(?i)^((?!shared).)*$"


# Because we are duplicating the filtering logic, keep it in a function.
# The specified 'desired_tag' parameter will be the resource tag that we are viewing for compliance.
def custodian_config_policy_dict(desired_tag: str) -> Mapping:
    return {"or": [
        {
            f"tag:{desired_tag}": "absent"
        },
        {"and": [
            {  # The general sequence '{content}@{content}.{content}' is not followed in the owner tag
                "type": "value",
                "key": f"tag:{desired_tag}",
                "op": "regex",
                "value": owner_tag_email_regex()
            },
            {  # Case insensitive match of 'shared' in the owner tag
                "type": "value",
                "key": f"tag:{desired_tag}",
                "op": "regex",
                "value": owner_tag_shared_regex()
            }]
        }
    ]}
