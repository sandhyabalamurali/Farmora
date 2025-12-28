import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root directory (Farmora/.env)
# Path: config.py -> app -> farmora_backend -> Farmora/.env
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Debug: Print to verify .env is loaded correctly
# print(f"Loading .env from: {env_path}")
# print(f"MONGO_URL loaded: {os.getenv('MONGO_URL', 'NOT FOUND')[:30]}...")

class Settings:
    PROJECT_NAME: str = "Farmora AI"
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME: str = "farmora_db"
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-immediately")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY")
    
    # Model Configuration
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemma-3-27b-it")
    GEMINI_MULTI_MODEL: str = os.getenv("GEMINI_MULTI_MODEL", "models/gemini-3-flash-preview")
settings = Settings()