from template import (
    emit_tf
)

emit_tf({
    'resource': {
        'aws_config_configuration_recorder_status': {
            'custodian': {
                'name': '${aws_config_configuration_recorder.custodian.name}',
                'is_enabled': True,
                'depends_on': ['aws_config_delivery_channel.custodian']
            }
        },
        'aws_config_delivery_channel': {
            'custodian': {
                'name': 'custodian-${var.region}',
                's3_bucket_name': '${var.s3_bucket_name}',
                's3_key_prefix': '${var.region}',
                'depends_on': ['aws_config_configuration_recorder.custodian']
            }
        },
        'aws_config_configuration_recorder': {
            'custodian': {
                'role_arn': '${var.config_role_arn}',
                'recording_group': {
                    'all_supported': True,
                    'include_global_resource_types': '${var.include_global}'
                }
            }
        },
    },
    'variable': {
        'region': {
            'type': 'string',
            'description': 'used as a prefix for AWS Config objects in the given'
                           ' S3 bucket'
        },
        'include_global': {
            'type': 'bool',
            'description': 'record global resource types in this region'
        },
        's3_bucket_name': {
            'type': 'string',
            'description': 'S3 bucket to store AWS Config objects in'
        },
        'config_role_arn': {
            'type': 'string',
            'description': 'role for AWS Config to assume'
        }
    }
})
