from pydantic import BaseModel
from typing import Optional
from sqlalchemy import Boolean, Column, String, Integer, ARRAY
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# SQLAlchemy model
class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)
    power_zones = Column(ARRAY(Integer), nullable=True)
    heart_rate_zones = Column(ARRAY(Integer), nullable=True)

# Pydantic models
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

class UserResponse(UserBase):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None