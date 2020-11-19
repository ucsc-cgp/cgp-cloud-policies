import json

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
                's3_bucket_name': '${var.s3_bucket.id}',
                's3_key_prefix': '${var.region}',
                'depends_on': ['aws_config_configuration_recorder.custodian']
            }
        },
        'aws_config_configuration_recorder': {
            'custodian': {
                'role_arn': '${var.config_role.arn}',
                'recording_group': {
                    'all_supported': True,
                    'include_global_resource_types': '${var.include_global}'
                }
            }
        },
    },
    'data': {
        'aws_caller_identity': {
            'current': {}  # to expose data.aws_caller_identity.current.account_id
        }
    },
    'variable': {
        'region': {},
        'include_global': {},
        's3_bucket': {},
        'config_role': {}
    }
})