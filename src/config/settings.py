import os 
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    LLM_MODEL: str = "gemini-2.0-flash"
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY')
    TAVILY_API_KEY: str = os.getenv('TAVILY_API_KEY')

    REDIS_HOST: str = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.environ.get("REDIS_PORT", 6379))
    REDIS_PASSWORD: Optional[str] = str(os.environ.get("REDIS_PASSWORD", None))
    REDIS_DB: int = int(os.environ.get("REDIS_DB", 0))
    TTL_TIME: int = int(os.environ.get("SESSION_TTL_SECONDS", 86400)) # 1 Day

settings = Settings()