# filepath: /app/routers/upload.py
from fastapi import APIRouter, File, UploadFile, HTTPException
import uuid
from ..utils.s3 import upload_file_to_s3

router = APIRouter()

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    s3_key = f"workouts/{file_id}.fit"
    
    try:
        upload_file_to_s3(file.file, s3_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload file to S3")
    
    return {"file_id": file_id}