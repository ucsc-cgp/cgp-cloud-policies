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
        'aws_config_configuration_aggregator': {
            'config': {
                'name': 'account',
                'account_aggregation_source': {
                    'account_ids': ['${data.aws_caller_identity.current.account_id}'],
                    'regions': '${var.aggregated_regions}'
                }

            }
        }
    },
    'data': {
        'aws_caller_identity': {
            'current': {}  # to expose data.aws_caller_identity.current.account_id
        }
    },
    'variable': {
        'aggregated_regions': {
            'type': 'list',
            'description': 'regions to aggregate in this account'
        }
    },
    'output': {
        'config_bucket': {
            'value': '${aws_s3_bucket.config}'
        }
    }
})
