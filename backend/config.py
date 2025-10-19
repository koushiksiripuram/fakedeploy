import os
from dotenv import load_dotenv

# Load variables from .env if present (for local development)
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
    MONGO_URI = os.environ.get("MONGO_URI")
