# App package

def __getattr__(name: str):
    """Allow uvicorn app:app to resolve gracefully to the FastAPI app in main.py."""
    if name == "app":
        from main import app
        return app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
