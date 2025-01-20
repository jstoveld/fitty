# filepath: /app/routers/analyze.py
from fastapi import APIRouter, HTTPException
import fitparse
from ..models.workout import WorkoutAnalysis
from ..utils.s3 import get_file_from_s3

router = APIRouter()

@router.post("/analyze/")
async def analyze_workout(file_id: str):
    s3_key = f"workouts/{file_id}.fit"
    
    try:
        file_body = get_file_from_s3(s3_key)
        fitfile = fitparse.FitFile(file_body)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve file from S3")
    
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
        user="example_user",
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