from template import (
    config,
    emit_yaml,
    terraform,
)

emit_yaml({
    'queue_url': terraform.get_attribute('aws_sqs_queue.mailer', 'id'),
    'role': terraform.get_attribute('aws_iam_role.mailer', 'arn'),
    'runtime': terraform.get_attribute('aws_lambda_function.mailer', 'runtime'),
    'from_address': config.admin_email,
    'region': config.aws_primary_deployment.region
})
