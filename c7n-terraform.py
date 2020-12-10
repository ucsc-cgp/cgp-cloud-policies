"""
Generates a Terraform module from cloud-custodian policy YAML. To use the
module, two variables must be specified in the module block:

* role_arn: the ARN of the IAM role that the policy lambdas should assume, and

* lambda_suffix: a suffix for each lambda name, used to prevent collisions if
  using modules to deploy to multiple regions.
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


JSON = Mapping[str, Any]  # not correct, but close enough for now
tf_vars = ['role_arn', 'lambda_suffix']


# TODO: mkdtemp pattern is messy


def generate_tf_from_config(config_file: Path, output_dir: Path) -> None:
    """
    Writes Terraform configuration for policies defined in a given
    cloud-custodian config file to the specified output directory.
    """
    collection = PolicyLoader(Config.empty()).load_file(config_file)
    tf_config_files = []
    for policy in collection:
        tf_config_files.extend(generate_tf_from_policy(policy))
    for tf_config in tf_config_files:
        tf_config.replace(output_dir.joinpath(tf_config.name))
    # Variables can only be defined once per module
    vars_tf = {'variable': {tf_var: {} for tf_var in tf_vars}}
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
    properties = config_rule.get_rule_params(policy_lambda)
    # TODO: Use convert_keys_to_snake_case here
    return {
        'resource': {
            'aws_config_config_rule': {
                policy.name: {
                    'name': properties['ConfigRuleName'],
                    'description': properties['Description'],
                    **conditional_key_val(properties, 'InputParameters'),
                    **conditional_key_val(properties, 'MaximumExecutionFrequency'),
                    'scope': convert_keys_to_snake_case(properties['Scope']),
                    'source': {
                        'owner': properties['Source']['Owner'],
                        'source_identifier': f'${{aws_lambda_function.{policy.name}.arn}}',
                        'source_detail': {
                            'event_source': 'aws.config',
                            'message_type': 'ConfigurationItemChangeNotification'
                        }
                    },
                    **conditional_key_val(properties, 'tags'),
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

    archive_path = Path(tempfile.mkdtemp()).joinpath(f'{policy.name}.zip')
    with archive_path.open('wb') as archive:
        archive.write(policy_lambda.get_archive().get_bytes())

    properties = policy_lambda.get_config()
    tf_config = dict(convert_keys_to_snake_case(properties))
    tf_config['kms_key_arn'] = tf_config.pop('k_m_s_key_arn', '')
    tf_config['function_name'] = f'{tf_config["function_name"]}${{var.lambda_suffix}}'
    filename = f'${{path.module}}/{policy.name}.zip'

    lambda_tf = {
        'resource': {
            'aws_lambda_function': {
                policy.name: {
                    **tf_config,
                    'filename': filename,
                    'source_code_hash': f'${{filebase64sha256("{filename}")}}'
                }
            },
            'aws_cloudwatch_log_group': {
                policy.name: {
                    'name': f'/aws/lambda/{tf_config["function_name"]}',
                    'retention_in_days': '30'
                }
            },
        }
    }
    return lambda_tf, archive_path.resolve()


mode_dispatch = {
    'config-rule': render_config_rule_tf
}


def merge_tf(tf_config_1: JSON, tf_config_2: JSON) -> JSON:
    return {
        key: tf_config_1.get(key, {}) | tf_config_2.get(key, {})
        for key in tf_config_1 | tf_config_2
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
        return {convert_camel_to_snake(key): obj[key]}
    except KeyError:
        return {}


def convert_camel_to_snake(camel_case: str) -> str:
    """
    >>> convert_camel_to_snake('FooBarBaz')
    'foo_bar_baz'
    """
    if isinstance(camel_case, str):
        return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_case).lower()
    else:
        return camel_case


# TODO: Rename this to be more appropriate
def convert_keys_to_snake_case(camel_case: JSON) -> JSON:
    """
    >>> convert_keys_to_snake_case({'FooBarBaz': 123})
    {'foo_bar_baz': 123}

    >>> convert_keys_to_snake_case({'FooBar': {'BarBaz': {'FooBarBaz': 123}}})
    {'foo_bar': {'bar_baz': {'foo_bar_baz': 123}}}
    """
    if isinstance(camel_case, dict):
        return {
            convert_camel_to_snake(k): convert_keys_to_snake_case(v)
            for k, v in camel_case.items() if convert_keys_to_snake_case(v)
        }
    else:
        return camel_case


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
