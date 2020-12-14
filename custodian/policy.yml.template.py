import os

from template import (
    emit_yaml,
)

managed_resource_types = [
    'aws.ebs',
    'aws.ec2',
    'aws.s3'
]

emit_yaml({
    'policies': [
        {
            'name': f'mandatory-tags-{resource_type.split(".")[1]}',
            'resource': resource_type,
            'mode': {
                'type': 'config-rule',
                'role': '${var.role_arn}'
            } if 'REPORT_ONLY' not in os.environ else {
                'type': 'pull'
            },
            'filters': [{'tag:Owner': 'absent'}],
            'actions': [{
                'type': 'notify',
                'to': ['resource-owner', 'event-owner'],
                'template': 'default',
                'subject': 'Untagged resource found',
                'transport': {
                    'type': 'sqs',
                    'queue': '${var.mailer.arn}'
                }
            }],
        } for resource_type in managed_resource_types
    ]
})
