from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from ..dependencies import get_db, get_current_user

router = APIRouter()

class ZoneConfig(BaseModel):
    power_zones: List[int]
    heart_rate_zones: List[int]

@router.post("/zones/")
async def configure_zones(config: ZoneConfig, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.username
    # Save the zones to the database (implementation depends on your database schema)
    # Example:
    # db_user = get_user(db, user_id)
    # db_user.power_zones = config.power_zones
    # db_user.heart_rate_zones = config.heart_rate_zones
    # db.commit()
    return {"message": "Zones configured successfully"}

@router.get("/zones/")
async def get_zones(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.username
    # Retrieve the zones from the database (implementation depends on your database schema)
    # Example:
    # db_user = get_user(db, user_id)
    # return {"power_zones": db_user.power_zones, "heart_rate_zones": db_user.heart_rate_zones}
    return {"power_zones": [100, 200, 300], "heart_rate_zones": [60, 120, 180]}  # Placeholder