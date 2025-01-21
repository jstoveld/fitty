import boto3
import os
import logging

# Load the S3 bucket name from environment variables
S3_BUCKET = os.getenv("S3_BUCKET")

# Log the S3_BUCKET value for debugging
if S3_BUCKET is None:
    logging.error("S3_BUCKET environment variable is not set.")
else:
    logging.info(f"S3_BUCKET is set to: {S3_BUCKET}")

# Initialize the S3 client
s3_client = boto3.client('s3')

def upload_file_to_s3(file, key):
    try:
        s3_client.upload_fileobj(file, S3_BUCKET, key)
    except Exception as e:
        logging.error(f"Failed to upload file to S3: {e}")
        raise Exception("Failed to upload file to S3")

def get_file_from_s3(key):
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
        return response['Body']
    except Exception as e:
        logging.error(f"Failed to retrieve file from S3: {e}")
        raise Exception("Failed to retrieve file from S3")