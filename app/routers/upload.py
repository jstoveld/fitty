from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
import uuid
from ..utils.s3 import upload_file_to_s3
from ..dependencies import get_current_user

router = APIRouter()

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    user_id = current_user.username  # Assuming `username` is the unique identifier for the user
    file_id = str(uuid.uuid4())
    s3_key = f"{user_id}/workouts/{file_id}.fit"
    
    try:
        upload_file_to_s3(file.file, s3_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload file to S3")
    
    return {"file_id": file_id}