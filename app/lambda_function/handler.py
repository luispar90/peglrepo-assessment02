import json
import boto3
import os
from botocore.exceptions import ClientError

CLUSTER_NAME = os.environ["ECS_CLUSTER"]
TASK_DEFINITION = os.environ["TASK_DEFINITION"]
SUBNETS = os.environ["SUBNETS"].split(',')
SECURITY_GROUPS = os.environ["SECURITY_GROUPS"]

"""
Return db credentials
"""
def get_secret():

    secret_name = "prod/api/db/peglssm-assestment01"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    return get_secret_value_response['SecretString']

"""
Main function that launch an ECS Task
"""
def lambda_handler(event, context):

    # Get credentials from Secrets Manager
    secret_data = get_secret()

    # Formatting variables before sending to ECS
    container_env_vars = [
        {"name": key, "value": value}
        for key, value in secret_data.items()
    ]

    # Instance an ECS client
    ecs_client = boto3.client('ecs')

    try:

        response = ecs_client.run_task(
            cluster=CLUSTER_NAME,
            launchType='FARGATE',
            taskDefinition=TASK_DEFINITION,
            overrides={
                "containerOverrides": [
                    {
                        "name": "nombre-del-contenedor",
                        "environment": container_env_vars
                    }
                ]
            },
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': SUBNETS,
                    'securityGroups': SECURITY_GROUPS,
                    'assignPublicIp': 'ENABLED'
                }
            }
        )

        task_arn = response['tasks'][0]['taskArn']
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Task ejecutada correctamente', 'taskArn': task_arn})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

