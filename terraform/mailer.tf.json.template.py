import json

from template import (
    config,
    emit_tf,
)

emit_tf({
    'resource': {
        'aws_sqs_queue': {
            'mailer': {
                'name': 'cloud-custodian-mailer',
            }
        },
        # TODO: https://github.com/hashicorp/terraform-provider-aws/issues/13980
        # aws_sqs_queue_policy needs to wait up to 60s after aws_sqs_queue creation
        'time_sleep': {
            'mailer': {
                'create_duration': '60s',
                'depends_on': ['aws_sqs_queue.mailer']
            }
        },
        'aws_sqs_queue_policy': {
            'mailer': {
                'queue_url': '${aws_sqs_queue.mailer.id}',
                'policy': json.dumps({
                    'Version': '2012-10-17',
                    'Id': 'CrossAccountAccess',
                    'Statement': [{
                        'Sid': 'AuthorizedRoles',
                        'Effect': 'Allow',
                        'Principal': {
                            'AWS': [
                                f'${{module.{account.module_name("config")}.role.arn}}'
                                for account in config.aws_accounts
                            ]
                        },
                        'Action': ['sqs:SendMessage'],
                        'Resource': '${aws_sqs_queue.mailer.arn}'
                    }]
                }),
                'depends_on': ['time_sleep.mailer']
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
                'name': '/aws/lambda/${aws_lambda_function.mailer.function_name}',
                'retention_in_days': '30'
            }
        },
        'aws_lambda_function': {
            'mailer': {
                'function_name': 'cloud-custodian-mailer',  # hardcoded into c7n-mailer
                'handler': 'periodic.dispatch',  # hardcoded into c7n-mailer
                'role': '${aws_iam_role.mailer.arn}',
                'runtime': 'python3.7',
                'filename': 'mailer.zip',
                'source_code_hash': '${filebase64sha256("mailer.zip")}',
                'description': 'mailer agent for cloud-custodian',
                'timeout': '30'
            }
        },
        # TODO: use aws_lambda_event_source_mapping instead
        'aws_cloudwatch_event_rule': {
            'mailer': {
                'schedule_expression': 'rate(5 minutes)',

            }
        },
        'aws_cloudwatch_event_target': {
            'mailer': {
                'rule': '${aws_cloudwatch_event_rule.mailer.name}',
                'arn': '${aws_lambda_function.mailer.arn}',
            }
        },
        'aws_lambda_permission': {
            'mailer': {
                'action': 'lambda:InvokeFunction',
                'function_name': '${aws_lambda_function.mailer.function_name}',
                'principal': 'events.amazonaws.com',
                'source_arn': '${aws_cloudwatch_event_rule.mailer.arn}'
            }
        }
    }
})
