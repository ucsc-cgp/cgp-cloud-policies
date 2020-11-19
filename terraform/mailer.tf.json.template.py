import json

from template import (
    config,
    emit_tf,
)

emit_tf({
    'resource': {
        'aws_sqs_queue': {
            'mailer': {
                'name': 'cloud-custodian-mailer'
            }
        },
        'aws_ses_email_identity': {
            'mailer': {
                'email': config.admin_email
            }
        },
        'aws_iam_role': {
            'mailer': {
                'name': 'cloud-custodian-mailer',
                'assume_role_policy': json.dumps({
                    'Version': '2012-10-17',
                    'Statement': [
                        {
                            'Action': 'sts:AssumeRole',
                            'Principal': {'Service': 'lambda.amazonaws.com'},
                            'Effect': 'Allow',
                            'Sid': ''
                        }
                    ]
                })
            }
        },
        'aws_iam_role_policy': {
            'mailer': {
                'name': 'cloud-custodian-mailer',
                'role': '${aws_iam_role.mailer.id}',
                'policy': json.dumps({
                    'Version': '2012-10-17',
                    'Statement': [
                        {
                            'Effect': 'Allow',
                            'Action': [
                                'sqs:ReceiveMessage',
                                'sqs:GetQueueAttributes',
                                'sqs:ListQueueTags',
                                'sqs:DeleteMessage'
                            ],
                            'Resource': '${aws_sqs_queue.mailer.arn}'
                        },
                        {
                            'Effect': 'Allow',
                            'Action': ['ses:SendRawEmail'],
                            'Resource': '${aws_ses_email_identity.mailer.arn}'
                        }
                    ]
                })
            }
        },
        'aws_iam_role_policy_attachment': {
            'mailer': {
                'role': '${aws_iam_role.mailer.name}',
                'policy_arn': 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            }
        },
        'aws_cloudwatch_log_group': {
            'mailer': {
                'name': '/aws/lambda/cloud-custodian-mailer',
                'retention_in_days': '30'
            }
        },
        'aws_lambda_function': {
            'mailer': {
                'function_name': 'cloud-custodian-mailer',  # hardcoded into c7n-mailer
                'handler': 'periodic.dispatch',  # hardcoded into c7n-mailer
                'runtime': 'python3.7',
                'role': '${aws_iam_role.mailer.arn}',
                'filename': 'mailer.zip',
                'source_code_hash': '${filebase64sha256("mailer.zip")}',
                'description': 'mailer agent for cloud-custodian',
                'timeout': '300'
            }
        }
    }
})
