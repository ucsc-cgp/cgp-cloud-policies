from template import (
    config,
    emit_tf,
)

emit_tf({
    'terraform': {
        'required_providers': {
            'aws': {
                'source': 'hashicorp/aws',
                'version': '~> 3.0'
            },
            'local': {},
            'time': {}
        }
    },
    'provider': {
        'aws': [{
            'secret_key': config.aws_provider_secret_key,
            'access_key': config.aws_provider_access_key,
            'region': config.aws_primary_deployment.region,
            'assume_role': {
                'role_arn': config.aws_primary_deployment.account.role_arn
            }
        }] + [{
            'secret_key': config.aws_provider_secret_key,
            'access_key': config.aws_provider_access_key,
            'region': deployment.region,
            'assume_role': {
                'role_arn': deployment.account.role_arn
            },
            'alias': deployment.name
        } for deployment in config.aws_deployments]
    }
})
