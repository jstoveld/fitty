from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..models.workout import WorkoutAnalysis
from ..dependencies import get_db, get_current_user
from ..utils.s3 import get_file_from_s3
import fitparse

router = APIRouter()

class AnalyzeRequest(BaseModel):
    file_id: str

@router.post("/analyze/")
async def analyze_workout(request: AnalyzeRequest, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.username  # Assuming `username` is the unique identifier for the user
    s3_key = f"{user_id}/workouts/{request.file_id}"
    
    try:
        file_body = get_file_from_s3(s3_key)
        fitfile = fitparse.FitFile(file_body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve or process file from S3: {e}")
    
    timestamps = []
    heart_rate = []
    speed = []
    distance = []
    calories = None
    power = []

    for record in fitfile.get_messages("record"):
        for data in record:
            if data.name == "timestamp":
                timestamps.append(data.value)
            elif data.name == "heart_rate":
                heart_rate.append(data.value)
            elif data.name == "speed":
                speed.append(data.value)
            elif data.name == "distance":
                distance.append(data.value)
            elif data.name == "calories":
                calories = data.value
            elif data.name == "power":
                power.append(data.value)
    
    analysis_result = f"Analysis for workout on {timestamps[0]} for {len(timestamps)} records."
    llm_feedback = "This is a placeholder for LLM feedback."
    analysis_graph_url = "https://example.com/analysis_graph.png"
    timestamps_str = [ts.isoformat() for ts in timestamps]

    workout_analysis = WorkoutAnalysis(
        user=user_id,
        date=timestamps_str[0],
        duration=len(timestamps),
        type="example_type",
        details="example_details",
        analysis=analysis_result,
        llm_feedback=llm_feedback,
        analysis_graph_url=analysis_graph_url,
        timestamps=timestamps_str,
        heart_rate=heart_rate,
        speed=speed,
        distance=distance,
        calories=calories,
        power=power
    )

    return workout_analysis