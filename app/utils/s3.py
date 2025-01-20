# filepath: /app/utils/s3.py
import boto3

S3_BUCKET = "your-s3-bucket-name"
s3_client = boto3.client('s3')

def upload_file_to_s3(file, key):
    try:
        s3_client.upload_fileobj(file, S3_BUCKET, key)
    except Exception as e:
        raise Exception("Failed to upload file to S3")

def get_file_from_s3(key):
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
        return response['Body']
    except Exception as e:
        raise Exception("Failed to retrieve file from S3")