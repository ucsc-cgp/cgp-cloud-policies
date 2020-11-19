from template import (
    config,
    emit_tf,
)

emit_tf({
    'module': {
        **{f'custodian-{region}': {
            'source': './custodian',
            'role_arn': '${aws_iam_role.custodian.arn}',
            'lambda_suffix': f'-{region}',
            'providers': {
                'aws': f'aws.{region}'
            },
            'depends_on': [f'module.config-{region}']
        } for region in ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']},
        # TODO: Use config
        **{f'config-{region}': {
            'source': './config',
            'region': region,
            'include_global': region == config.admin_region,
            'config_role': '${aws_iam_service_linked_role.config}',
            's3_bucket': '${aws_s3_bucket.config}',
            'providers': {
                'aws': f'aws.{region}'
            }
        } for region in ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']}
    }
})
