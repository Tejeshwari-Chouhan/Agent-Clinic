import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    app_name: str = "Healthcare Triage System"
    debug: bool = os.getenv('FASTAPI_ENV', 'development') == 'development'
    port: int = int(os.getenv('PORT', 3000))
    
    # API Keys
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')
    google_maps_api_key: str = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    # Database
    database_url: str = os.getenv('DATABASE_URL', '')
    
    # CORS
    cors_origin: str = os.getenv('CORS_ORIGIN', 'http://localhost:5173')
    
    class Config:
        env_file = '.env'
        extra = 'ignore'

settings = Settings()
