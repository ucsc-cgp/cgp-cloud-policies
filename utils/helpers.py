
def create_role_string(account_id: str, iam_role_name: str) -> str:
    return "arn:aws:iam::" + account_id + ":role/" + iam_role_name


def create_full_iam_resource_name(iam_resource_prefix: str, account_name:str) -> str:
    return iam_resource_prefix + account_name


def create_remote_bucket_string(remote_bucket_name: str) -> str:
    return "arn:aws:s3:::" + remote_bucket_name + "/*"


def create_config_policy_resource_name(policy_prefix: str, resource_type:str) -> str:
    return policy_prefix + resource_type


# Custodian prepends a prefix to resources.
def create_deployed_config_policy_resource_name(policy_prefix: str, resource_type:str) -> str:
    return "custodian-" + create_config_policy_resource_name(policy_prefix, resource_type)
