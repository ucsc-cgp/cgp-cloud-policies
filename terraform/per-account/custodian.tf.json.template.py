import json

from template import (
    emit_tf,
)


emit_tf({
    'resource': {
        # It would make more sense to create this on a per-deployment basis
        # but we can only have one service-linked of a given type per account
        'aws_iam_service_linked_role': {
            'config': {
                'aws_service_name': 'config.amazonaws.com'
            }
        },
        'aws_iam_role': {
            'custodian': {
                'name': 'cloud-custodian',
                'assume_role_policy': json.dumps({
                    'Version': '2012-10-17',
                    'Statement': [
                        {
                            'Action': 'sts:AssumeRole',
                            'Principal': {
                                'Service': 'lambda.amazonaws.com'
                            },
                            'Effect': 'Allow',
                            'Sid': ''
                        }
                    ]
                })
            }
        },
        'aws_iam_role_policy': {
            'custodian': {
                'name': 'cloud-custodian',
                'role': '${aws_iam_role.custodian.id}',
                'policy': json.dumps({
                    'Version': '2012-10-17',
                    'Statement': [
                        {
                            'Effect': 'Allow',
                            'Action': [
                                'sqs:SendMessage'
                            ],
                            'Resource': '${var.mailer_arn}'
                        },
                        {
                            'Effect': 'Allow',
                            'Action': [
                                'iam:ListAccountAliases'
                            ],
                            'Resource': '*'
                        }
                    ]
                })
            }
        },
        'aws_iam_role_policy_attachment': {
            name: {
                'role': '${aws_iam_role.custodian.name}',
                'policy_arn': f'arn:aws:iam::aws:policy/service-role/{role}'
            } for name, role in (('custodian_lambda', 'AWSLambdaBasicExecutionRole'),
                                 ('custodian_config', 'AWSConfigRulesExecutionRole'))
        },
    },
    'variable': {
        'mailer_arn': {
            'type': 'string',
            'description': 'arn for c7n-mailer mail aws_sqs_queue'
        }
    },
    'output': {
        'service_linked_role': {
            'value': '${aws_iam_service_linked_role.config}'
        },
        'role': {
            'value': '${aws_iam_role.custodian}'
        }
    }
})
