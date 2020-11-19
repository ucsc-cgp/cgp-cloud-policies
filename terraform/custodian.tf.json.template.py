import json

from template import (
    emit_tf,
)


emit_tf({
    'resource': {
        'aws_s3_bucket': {
            'config': {
                'bucket_prefix': 'aws-config',
                'force_destroy': True
            }
        },
        'aws_s3_bucket_policy': {
            'config': {
                'bucket': '${aws_s3_bucket.config.id}',
                'policy': json.dumps({
                    'Version': '2012-10-17',
                    'Statement': [
                        {
                            'Sid': 'AWSConfigBucketPermissionsCheck',
                            'Effect': 'Allow',
                            'Principal': {
                                'Service': ['config.amazonaws.com']
                            },
                            'Action': 's3:GetBucketAcl',
                            'Resource': '${aws_s3_bucket.config.arn}'
                        },
                        {
                            'Sid': 'AWSConfigBucketExistenceCheck',
                            'Effect': 'Allow',
                            'Principal': {
                                'Service': ['config.amazonaws.com']
                            },
                            'Action': 's3:ListBucket',
                            'Resource': '${aws_s3_bucket.config.arn}'
                        },
                        {
                            'Sid': 'AWSConfigBucketDelivery',
                            'Effect': 'Allow',
                            'Principal': {
                                'Service': ['config.amazonaws.com']
                            },
                            'Action': 's3:PutObject',
                            'Resource': '${aws_s3_bucket.config.arn}/*/AWSLogs/'
                                        '${data.aws_caller_identity.current.account_id}/Config/*',
                            'Condition': {
                                'StringEquals': {
                                    's3:x-amz-acl': 'bucket-owner-full-control'
                                }
                            }
                        }
                    ]
                })
            }
        },
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
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "sqs:SendMessage"
                            ],
                            "Resource": "${aws_sqs_queue.mailer.arn}"
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
        }
    },
    'data': {
        'aws_caller_identity': {
            'current': {}  # to expose data.aws_caller_identity.current.account_id
        }
    }
})
