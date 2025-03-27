import os
from dotenv import load_dotenv

# Get the base directory (ensure it's the correct location)
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, ".env")

# Load environment variables
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}")

class Config:
    """Application configuration settings."""
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "you-will-never-guess")
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")