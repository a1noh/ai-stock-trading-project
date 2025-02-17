import json
import boto3
import requests
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the Secrets Manager client
secrets_client = boto3.client('secretsmanager')

def get_secret():
    secret_name = "AlphaVantageAPIKey"  # The secret name from Secrets Manager
    region_name = "us-east-1"  # Adjust region if necessary

    try:
        # Fetch the secret value from Secrets Manager
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = response['SecretString']
        secret_dict = json.loads(secret)
        return secret_dict["ALPHA_VANTAGE_API_KEY"]
    except Exception as e:
        logger.error(f"Error retrieving secret: {e}")
        raise

def lambda_handler(event, context):
    logger.info("Lambda function started.")

    # API details
    api_key =  get_secret()  # Replace with your Alpha Vantage API key
    symbol = "IBM"  # Replace with your desired stock symbol
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=1min&apikey={api_key}"

    logger.info(f"Fetching stock data for symbol: {symbol}")

    try:
        # Fetch data from API
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        logger.info("Stock data fetched successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching stock data: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error fetching stock data!')
        }

    # Save data to S3
    s3 = boto3.client('s3')
    bucket_name = "ai-stock-trading-raw-data"  # Your S3 bucket name
    folder_name = "data"  # Folder name inside the bucket
    file_name = f"{folder_name}/{symbol}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"  # File path

    try:
        s3.put_object(Bucket=bucket_name, Key=file_name, Body=json.dumps(data))
        logger.info(f"Stock data saved to S3: s3://{bucket_name}/{file_name}")
    except Exception as e:
        logger.error(f"Error saving data to S3: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error saving data to S3!')
        }

    return {
        'statusCode': 200,
        'body': json.dumps('Stock data saved to S3!')
    }