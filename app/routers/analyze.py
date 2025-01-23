from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..dependencies import get_db, get_current_user
from ..utils.s3 import get_file_from_s3
import boto3
import json

router = APIRouter()

class AnalyzeRequest(BaseModel):
    file_id: str

sagemaker_client = boto3.client('sagemaker-runtime')

@router.post("/analyze/")
async def analyze_workout(request: AnalyzeRequest, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.username  # Assuming `username` is the unique identifier for the user
    s3_key = f"{user_id}/workouts/{request.file_id}"
    
    try:
        file_body = get_file_from_s3(s3_key)
        file_content = file_body.read().decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve or process file from S3: {e}")
    
    try:
        response = sagemaker_client.invoke_endpoint(
            EndpointName='your-sagemaker-endpoint',
            ContentType='text/csv',
            Body=file_content
        )
        result = json.loads(response['Body'].read().decode())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invoke SageMaker endpoint: {e}")
    
    return result