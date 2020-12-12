"""
Generates a Terraform module from cloud-custodian policy YAML.

If you reference a Terraform variable in your policy YAML, the Terraform module
will be configured to expect it. Other variables are required; refer to the
generated vars.tf file.

The `local` and `aws` providers are required.
"""
import argparse
import json
from pathlib import (
    Path,
)
import re
import tempfile
from typing import (
    Any,
    Mapping,
    Sequence,
    Tuple,
)

from c7n import (
    mu,
)
from c7n.config import (
    Config,
)
from c7n.loader import (
    PolicyLoader,
)
import c7n.policy


JSON = Mapping[str, Any]  # TODO: not correct, but close enough for now
required_tf_vars = {
    'role_arn': {
        'type': 'string',
        'description': 'ARN of the IAM role that the policy lambdas should assume'
    },
    'lambda_suffix': {
        'type': 'string',
        'description': 'suffix for each lambda name, used to prevent collisions'
                       ' when deploying to multiple regions'
    },
    'deployment': {  # TODO: remove, find another way to reference
        'type': 'string',
        'description': 'a unique ID for each invocation of the module'
    }
}


# TODO: mkdtemp pattern is messy


def generate_tf_from_config(config_file: Path, output_dir: Path) -> None:
    """
    Writes Terraform configuration for policies defined in a given
    cloud-custodian config file to the specified output directory.
    """
    collection = PolicyLoader(Config.empty()).load_file(config_file)

    tf_config_files = []
    user_vars = set()
    for policy in collection:
        tf_config_files.extend(generate_tf_from_policy(policy))
        user_vars.update(find_terraform_vars(policy.data))
    for tf_config in tf_config_files:
        tf_config.replace(output_dir.joinpath(tf_config.name))

    # Variables can only be defined once per module
    user_vars = {var: {} for var in user_vars ^ set(required_tf_vars)}
    vars_tf = {
        'variable': {
            **required_tf_vars,
            **user_vars
        }
    }
    with output_dir.joinpath('vars.tf.json').open('w') as tf:
        json.dump(vars_tf, tf)


def generate_tf_from_policy(policy: c7n.policy.Policy) -> Sequence[Path]:
    """
    Given a :class:`c7n.policy.Policy`, create Terraform configuration.
    Returns a list of paths to the Terraform configuration file(s).
    """
    if policy.provider_name == 'aws':
        try:
            render_func = mode_dispatch[policy.execution_mode]
        except KeyError:
            raise NotImplementedError(f'{policy.execution_mode=} on {policy.name=} '
                                      'currently unsupported')
        else:
            event_tf = render_func(policy)
            lambda_tf, lambda_source_path = _render_lambda(policy)
            tmpdir = Path(tempfile.mkdtemp())
            tf_json_path = tmpdir.joinpath(f'{policy.name}.tf.json')
            with tf_json_path.open('w') as tf_json:
                json.dump(merge_tf(event_tf, lambda_tf), tf_json, indent=4)
            return tf_json_path, lambda_source_path
    else:
        raise NotImplementedError(f'Provider {policy.provider_name} not implemented')


def render_config_rule_tf(policy: c7n.policy.Policy) -> JSON:
    policy_lambda = mu.PolicyLambda(policy)
    policy_lambda.arn = f'${{aws_lambda_function.{policy.name}.arn}}'
    config_rule = policy_lambda.get_events(None).pop()
    raw_properties = config_rule.get_rule_params(policy_lambda)
    config_properties = convert_keys_to_snake_case(raw_properties)
    config_properties['name'] = config_properties.pop('config_rule_name')
    config_properties['source']['source_detail'] = config_properties['source'].pop('source_details')
    return {
        'resource': {
            'aws_config_config_rule': {
                policy.name: {
                    **config_properties,
                    'depends_on': [f'aws_lambda_permission.{policy.name}']
                }
            },
            'aws_lambda_permission': {
                policy.name: {
                    'action': 'lambda:InvokeFunction',
                    'function_name': f'${{aws_lambda_function.{policy.name}.function_name}}',
                    'principal': 'config.amazonaws.com',
                }
            }
        }
    }


def _render_lambda(policy: c7n.policy.Policy) -> Tuple[JSON, Path]:
    policy_lambda = mu.PolicyLambda(policy)

    # TODO: Find a saner way to manage per-account config
    # cloud-custodian Lambda configuration is packaged with the lambda itself
    # (instead of using something, like, you know, environment variables) so to
    # use Terraform interpolations that change per account (which happens if
    # we're using module-scoped variables) we need to get a little messy:
    # 1. Copy the generated archive to the module directory. The archive
    #    contains the lambda code and config.json, which contains the
    #    interpolations we're interested in.
    archive_path = Path(tempfile.mkdtemp()).joinpath(f'{policy.name}.zip')
    with archive_path.open('wb') as archive:
        archive.write(policy_lambda.get_archive().get_bytes())
    # 2. Duplicate config.json in memory (see c7n.mu.PolicyLambda.get_archive())
    #    then inline it into the Terraform JSON as a local_file to eval
    #    interpolations then write to disk when we `terraform apply`
    config_json = json.dumps({
        'execution-options': mu.get_exec_options(policy_lambda.policy.options),
        'policies': [policy_lambda.policy.data]
    }, indent=4)
    # 3. In the Terraform JSON, use local-exec to combine the config.json (with
    #    evaluated interpolations) with the archive, and upload that.
    workdir = f'${{var.deployment}}/{policy.name}'
    new_archive_path = workdir + f'/{policy.name}.zip'
    commands = [
        f'mkdir -p {workdir}',
        f'cp {policy.name}.zip {new_archive_path}',
        f'cd {workdir}',
        f'zip {policy.name}.zip config.json'
    ]

    properties = policy_lambda.get_config()
    tf_config = convert_keys_to_snake_case(properties)
    tf_config['kms_key_arn'] = tf_config.pop('k_m_s_key_arn', '')
    tf_config['function_name'] = f'{tf_config["function_name"]}${{var.lambda_suffix}}'
    lambda_tf = {
        'resource': {
            'aws_lambda_function': {
                policy.name: {
                    **tf_config,
                    'filename': f'${{path.module}}/{new_archive_path}',
                    'source_code_hash': f'${{filesha256("${{path.module}}/{policy.name}.zip")}}',
                    'depends_on': [
                        f'local_file.{policy.name}',
                        f'aws_cloudwatch_log_group.{policy.name}'
                    ]
                }
            },
            'aws_cloudwatch_log_group': {
                policy.name: {
                    'name': f'/aws/lambda/{tf_config["function_name"]}',
                    'retention_in_days': '30'
                }
            },
            'local_file': {
                policy.name: {
                    'content': config_json,
                    'filename': f'${{path.module}}/{workdir}/config.json',
                    'provisioner': {
                        'local-exec': {
                            'command': ' && '.join(commands),
                            'working_dir': '${path.module}'
                        }
                    }
                }
            }
        },
    }
    return lambda_tf, archive_path.resolve()


mode_dispatch = {
    'config-rule': render_config_rule_tf
}


def merge_tf(tf_config_1: JSON, tf_config_2: JSON) -> JSON:
    return {
        key: tf_config_1.get(key, {}) | tf_config_2.get(key, {})
        for key in set(tf_config_1) | set(tf_config_2)
    }


def conditional_key_val(obj: JSON, key: str) -> JSON:
    """
    >>> conditional_key_val({'FooBar': 'bar'}, 'FooBar')
    {'foo_bar': 'bar'}

    >>> conditional_key_val({'bar': 'foo'}, 'foo')
    {}

    >>> {**conditional_key_val({'bar': 'foo'}, 'foo')}
    {}
    """
    try:
        return {convert_camel_case_to_snake_case(key): obj[key]}
    except KeyError:
        return {}


def convert_camel_case_to_snake_case(camel_case: str) -> str:
    """
    >>> convert_camel_case_to_snake_case('FooBarBaz')
    'foo_bar_baz'
    """
    return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_case).lower()


def convert_keys_to_snake_case(camel_case):
    """
    >>> convert_keys_to_snake_case({'FooBarBaz': 123})
    {'foo_bar_baz': 123}

    >>> convert_keys_to_snake_case({'FooBar': {'BarBaz': {'FooBarBaz': 123}}})
    {'foo_bar': {'bar_baz': {'foo_bar_baz': 123}}}
    """
    if isinstance(camel_case, dict):
        return {
            convert_camel_case_to_snake_case(k): convert_keys_to_snake_case(v)
            for k, v in camel_case.items() if convert_keys_to_snake_case(v)  # TODO
        }
    elif isinstance(camel_case, list):
        return [convert_keys_to_snake_case(item) for item in camel_case]
    else:
        return camel_case


def find_terraform_vars(config) -> set[str]:
    """
    >>> find_terraform_vars({
    ...     'foo': {'bar': '${var.foo}'},
    ...     'baz': '${var.three.bar}',
    ...     'qux': 'var.two.bar'
    ... })
    {'three', 'foo'}
    """
    variables = set()
    if isinstance(config, dict):
        for values in config.values():
            variables.update(find_terraform_vars(values))
    elif isinstance(config, list):
        for value in config:
            variables.update(find_terraform_vars(value))
    elif isinstance(config, str):
        matches = re.finditer(r'\${var\.(\w+)(\w|\.)*}', config)
        variables = set(match.group(1) for match in matches)
    else:
        raise RuntimeError

    return variables


if __name__ == '__main__':
    # https://youtrack.jetbrains.com/issue/PY-41806
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--config-file',
                        required=True,
                        help='Policy configuration file')
    parser.add_argument('-o', '--output-dir',
                        required=True,
                        help='Output directory for Terraform configuration')
    arguments = parser.parse_args()

    config_file = Path(arguments.config_file).resolve()
    output_dir = Path(arguments.output_dir).resolve()
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError(f'{output_dir=} is not a directory')
    elif config_file.exists() and not config_file.is_file():
        raise ValueError(f'{config_file=} is not a file')
    else:
        output_dir.mkdir(exist_ok=True)
        generate_tf_from_config(config_file=config_file, output_dir=output_dir)
