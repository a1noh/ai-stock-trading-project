import boto3
import json
import pandas as pd
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from awsglue.dynamicframe import DynamicFrame

# Initialize Glue Context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Parameters for the Glue job
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'source_bucket', 'source_key', 'target_bucket', 'target_key'])

source_bucket = args['source_bucket']
source_key = args['source_key']
target_bucket = args['target_bucket']
target_key = args['target_key']

# Read the raw data from the S3 source bucket
raw_data_path = f's3://{source_bucket}/{source_key}'
raw_data = spark.read.option("header", "true").csv(raw_data_path)

# Convert the raw data to a pandas dataframe for easier manipulation
raw_data_df = raw_data.toPandas()

# Preprocess the stock data (convert to the DeepAR format)
def preprocess_stock_data(df):
    # Add time index to the data
    df['time_idx'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d')

    # Prepare the time-series data for DeepAR
    time_series_data = []

    # Group by stock symbol to process each stock's time series separately
    for stock_symbol, stock_data in df.groupby('stock_symbol'):
        stock_data = stock_data.sort_values(by='timestamp')

        series = {
            "start": stock_data['time_idx'].iloc[0],  # Start date for the time-series
            "target": stock_data['price'].values.tolist(),  # Stock price as the target
            "feat_static_cat": [stock_symbol],  # Stock symbol as a categorical feature
            "feat_dynamic_real": stock_data[['volume']].values.tolist(),  # Additional features like volume
            "time_idx": list(range(len(stock_data)))  # Time index
        }
        
        time_series_data.append(series)

    return time_series_data

# Preprocess the raw stock data
processed_data = preprocess_stock_data(raw_data_df)

# Convert processed data to JSONLines format for DeepAR
jsonl_data = [json.dumps(item) for item in processed_data]

# Write the processed data to the target S3 location
processed_data_path = f's3://{target_bucket}/{target_key}'
with open('/tmp/processed_stock_data.jsonl', 'w') as f:
    for item in jsonl_data:
        f.write(item + '\n')

# Upload processed data to the target S3 path
s3 = boto3.client('s3')
s3.upload_file('/tmp/processed_stock_data.jsonl', target_bucket, target_key)

print(f"Processed data uploaded to s3://{target_bucket}/{target_key}")
