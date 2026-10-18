from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Base directory for backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "SellerBoost AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    # AI Provider Configuration
    # Options: "backboard", "ollama", "mock"
    AI_PROVIDER: str = "backboard"
    
    # Backboard Settings
    BACKBOARD_API_KEY: Optional[str] = None
    BACKBOARD_BASE_URL: str = "https://app.backboard.io/api"
    BACKBOARD_DEFAULT_PROVIDER: str = "openrouter"
    BACKBOARD_DEFAULT_MODEL: str = "meta-llama/llama-3.1-8b-instruct"
    BACKBOARD_MULTILINGUAL_MODEL: str = "qwen/qwen-2.5-72b-instruct"
    
    # Ollama Local Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3.1:8b"
    
    # Credit & Usage Tracking (For user's $5 promo credit safety)
    INITIAL_PROMO_CREDIT_USD: float = 5.0
    INPUT_COST_PER_MILLION: float = 0.055  # Llama 3.1 8B on OpenRouter
    OUTPUT_COST_PER_MILLION: float = 0.055
    
    # Database
    DATABASE_PATH: Path = BASE_DIR / "sellerboost.db"
    
    # Uploads
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    
    model_config = SettingsConfigDict(
        env_file=[str(BASE_DIR.parent / ".env"), str(BASE_DIR / ".env")],
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
