import os

from template import (
    config,
    emit_yaml,
    terraform,
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
                'role': terraform.get_attribute('aws_iam_role.custodian', 'arn', '${var.role_arn}')
            } if 'REPORT_ONLY' not in os.environ else {
                'type': 'pull'
            },
            'filters': [{'tag:Owner': 'absent'}],
            'actions': [{
                'type': 'notify',
                'to': ['resource-owner', 'event-owner'],
                'owner_absent_contact': [config.admin_email],
                'template': 'default',
                'subject': 'Untagged resource found',
                'transport': {
                    'type': 'sqs',
                    'queue': terraform.get_attribute('aws_sqs_queue.mailer', 'arn')
                }
            }],
        } for resource_type in managed_resource_types
    ]
})

