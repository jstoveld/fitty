import os
import yaml
import fitparse
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_secret(secret_name, region_name):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Credentials error: {e}")
        return None
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        return None

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    return secret

def load_context():
    with open('/Users/js/code/roadmap/fitty/context.yaml', 'r') as file:
        context = yaml.safe_load(file)
    return context

# Load context and environment
context = load_context()
environment = os.getenv('ENVIRONMENT', 'dev')
env_config = context['environments'][environment]
secret_name = env_config['SECRET_KEY']
region_name = env_config['S3_REGION']

# Retrieve and set the secret key for AWS environments
if environment != 'dev':
    secret_key = get_secret(secret_name, region_name)
    if secret_key:
        os.environ['SECRET_KEY'] = secret_key
else:
    # Use the local secret key from .env for local development
    os.environ['SECRET_KEY'] = os.getenv('SECRET_KEY')

app = FastAPI()

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserInDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Secret key to encode the JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserCreate(User):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    return db.query(UserInDB).filter(UserInDB.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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
    calories: Optional[int] = None  # Changed to Optional[int]
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

# In-memory workout storage
workouts_db = []

# AWS S3 setup
S3_BUCKET = env_config["S3_BUCKET"]
s3_client = boto3.client('s3', region_name=region_name)

@app.post("/workouts/")
def upload_workout_file(file: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    if not file.filename.endswith('.fit'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .fit files are allowed.")
    
    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET, file.filename)
        return {"message": "File uploaded successfully", "filename": file.filename}
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_workout_file/{filename}")
def download_workout_file(filename: str):
    try:
        file_url = s3_client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': filename}, ExpiresIn=3600)
        return {"file_url": file_url}
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_workout/", response_model=WorkoutAnalysis)
def analyze_workout(file: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    if not file.filename.endswith('.fit'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .fit files are allowed.")
    
    # Parse the .fit file
    fitfile = fitparse.FitFile(file.file)
    
    # Extract data from the .fit file
    timestamps = []
    heart_rate = []
    speed = []
    distance = []
    calories = []
    power = []
    
    # Initialize calories as None
    calories = None

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
                power = data.value
    
    # Mock analysis process
    analysis_result = f"Analysis for workout on {timestamps[0]} for {len(timestamps)} records."

    # Placeholder for LLM feedback
    llm_feedback = "This is a placeholder for LLM feedback."

    # Placeholder for analysis graph URL
    analysis_graph_url = "https://example.com/analysis_graph.png"

    # Convert datetime objects to strings
    timestamps_str = [ts.isoformat() for ts in timestamps]

    # Return the workout data along with the analysis result, LLM feedback, and analysis graph URL
    return WorkoutAnalysis(
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

@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = UserInDB(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@app.get("/")
def read_root():
    return {"message": "This is Fitty. Under Construction."}