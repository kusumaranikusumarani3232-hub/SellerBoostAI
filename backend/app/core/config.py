from typing import List, Optional, Union
from pydantic import field_validator
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
    # Regex to permit Vercel production and preview domains (*.vercel.app)
    CORS_ORIGIN_REGEX: Optional[str] = r"^https:\/\/.*\.vercel\.app$"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        default_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000"
        ]
        parsed: List[str] = []
        if isinstance(v, str):
            v = v.strip()
            if v:
                if v.startswith("[") and v.endswith("]"):
                    import json
                    try:
                        parsed = json.loads(v)
                    except Exception:
                        parsed = [origin.strip() for origin in v.split(",") if origin.strip()]
                else:
                    parsed = [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, (list, tuple)):
            parsed = [str(origin).strip() for origin in v if str(origin).strip()]

        # Combine configured origins with local defaults, preserving unique items
        combined = list(dict.fromkeys(parsed + default_origins))
        return combined
    
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
