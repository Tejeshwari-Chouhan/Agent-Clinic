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
    google_maps_timeout_seconds: float = float(os.getenv('GOOGLE_MAPS_TIMEOUT_SECONDS', 2.0))
    emergency_max_facilities: int = int(os.getenv('EMERGENCY_MAX_FACILITIES', 3))
    emergency_fallback_data_path: str = os.getenv(
        'EMERGENCY_FALLBACK_DATA_PATH',
        'src/data/emergency_facilities_fallback.json'
    )

    # ML dataset path relative to backend root (see data/ml/symptom_disease_training.csv)
    ml_dataset_path: str = os.getenv('ML_DATASET_PATH', 'data/ml/symptom_disease_training.csv')
    # Pickle cache for DecisionTree model (matches notebooks/disease_ml_pipeline.ipynb)
    ml_model_cache_path: str = os.getenv('ML_MODEL_CACHE_PATH', 'src/data/disease_dt_model.pkl')
    
    # Database
    database_url: str = os.getenv('DATABASE_URL', '')
    
    # CORS
    cors_origin: str = os.getenv('CORS_ORIGIN', 'http://localhost:5173')
    
    class Config:
        env_file = '.env'

settings = Settings()
