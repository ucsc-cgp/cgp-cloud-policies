from template import (
    config,
    emit_tf,
)

emit_tf({
    'module': {
        **{
            deployment.module_name('custodian'): {
                'source': './custodian',
                'role_arn': f"${{module.{deployment.account.module_name('config')}.role.arn}}",
                'lambda_suffix': f'-{deployment.region}',
                'deployment': deployment.name,
                'mailer': '${aws_sqs_queue.mailer}',
                'providers': {
                    'aws': f'aws.{deployment.name}'
                },
                'depends_on': [f"module.{deployment.module_name('config')}"]
            }
            for deployment in config.aws_deployments
        },
        **{
            deployment.account.module_name('config'): {
                'source': './per-account',
                'mailer_arn': '${aws_sqs_queue.mailer.arn}',
                'aggregated_regions': deployment.account.regions,
                'providers': {
                    'aws': f'aws.{deployment.name}'
                }
            }
            for deployment in config.aws_primary_deployments
        },
        **{
            deployment.module_name('config'): {
                'source': './per-deployment',
                'region': deployment.region,
                'include_global': deployment.primary,
                'config_role_arn': f"${{module.{deployment.account.module_name('config')}.service_linked_role.arn}}",
                's3_bucket_name': f"${{module.{deployment.account.module_name('config')}.config_bucket.id}}",
                'providers': {
                    'aws': f'aws.{deployment.name}'
                }
            }
            for deployment in config.aws_deployments
        }
    }
})
