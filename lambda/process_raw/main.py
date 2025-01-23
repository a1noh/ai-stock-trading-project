# lambda/dummy-lambda/app.py

import json

def lambda_handler(event, context):
    # Just return a dummy response
    return {
        'statusCode': 200,
        'body': json.dumps('Hello, this is a dummy Lambda function!')
    }