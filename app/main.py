import os
import yaml
from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_context():
    with open('/Users/js/code/roadmap/fitty/context.yaml', 'r') as file:
        context = yaml.safe_load(file)
    return context

# Load context and environment
context = load_context()
environment = os.getenv('ENVIRONMENT', 'dev')
env_config = context['environments'][environment]

# Set environment variables programmatically
os.environ['S3_BUCKET'] = env_config['S3_BUCKET']
os.environ['S3_REGION'] = env_config['S3_REGION']
os.environ['SECRET_KEY'] = env_config['SECRET_KEY']

# Debugging statements
print(f"S3_BUCKET: {os.getenv('S3_BUCKET')}")
print(f"S3_REGION: {os.getenv('S3_REGION')}")
print(f"SECRET_KEY: {os.getenv('SECRET_KEY')}")

from app.routers import upload_router, analyze_router, users_router, auth_router

app = FastAPI()

# Include routers
app.include_router(upload_router)
app.include_router(analyze_router)
app.include_router(users_router)
app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "This is Fitty. Under Construction."}