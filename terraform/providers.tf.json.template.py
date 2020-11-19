from template import (
    config,
    emit_tf,
)

emit_tf({
    'terraform': {
        'required_providers': {
            'aws': {
                'source': 'hashicorp/aws',
                'version': '~> 3.0'
            }
        }
    },
    'provider': {
        'aws': [{
            'region': config.admin_region
        }] + [{
            'alias': region,
            'region': region
        } for region in ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']]
        # TODO: Use config
    }
})
