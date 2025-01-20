# filepath: /app/models/workout.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Workout(BaseModel):
    user: str
    date: datetime
    duration: int  # duration in minutes
    type: str
    details: Optional[str] = None
    timestamps: List[datetime] = []
    heart_rate: List[int] = []
    speed: List[float] = []
    distance: List[float] = []
    calories: Optional[int] = None
    power: List[int] = []

class WorkoutAnalysis(BaseModel):
    user: str
    date: str
    duration: int
    type: str
    details: str
    analysis: str
    llm_feedback: str
    analysis_graph_url: str
    timestamps: List[str]
    heart_rate: List[int]
    speed: List[float]
    distance: List[float]
    calories: Optional[int]
    power: Optional[int]