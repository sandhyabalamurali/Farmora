import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Farmora AI"
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME: str = "farmora_db"
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-immediately")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY")
settings = Settings()