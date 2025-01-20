import os
import yaml
from fastapi import FastAPI
from dotenv import load_dotenv
from .routers import upload_router, analyze_router, users_router, auth_router

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

app = FastAPI()

# Include routers
app.include_router(upload_router)
app.include_router(analyze_router)
app.include_router(users_router)
app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "This is Fitty. Under Construction."}