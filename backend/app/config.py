"""
Aetios-Med Configuration
Handles cross-platform paths and settings.
"""
import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings


def get_app_data_dir() -> Path:
    """Get the appropriate app data directory for the current platform."""
    if sys.platform == "darwin":  # macOS
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":  # Windows
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:  # Linux and others
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    
    app_dir = base / "Aetios-Med"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


class Settings(BaseSettings):
    """Application settings with sensible defaults."""
    
    # Paths
    app_data_dir: Path = get_app_data_dir()
    database_path: Path = None
    lancedb_path: Path = None
    model_path: Path = None
    curriculum_path: Path = None
    anki_watch_folder: Path = None
    notes_folder: Path = None
    
    # Server
    port: int = 8741
    host: str = "127.0.0.1"
    
    # LLM Settings
    model_repo: str = "aaditya/Llama3-OpenBioLLM-8B-GGUF"
    model_filename: str = "llama3-openbio-8b.Q4_K_M.gguf"
    context_length: int = 8192
    gpu_layers: int = -1  # -1 = all layers on GPU (Metal)
    
    # Embedding Model
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    
    # HuggingFace
    hf_token: str = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Set derived paths
        self.database_path = self.app_data_dir / "aetios.db"
        self.lancedb_path = self.app_data_dir / "lancedb"
        self.model_path = self.app_data_dir / "models" / self.model_filename
        self.curriculum_path = self.app_data_dir / "curriculum" / "uk_curriculum.json"
        
        # Create directories
        (self.app_data_dir / "models").mkdir(parents=True, exist_ok=True)
        (self.app_data_dir / "curriculum").mkdir(parents=True, exist_ok=True)
        self.lancedb_path.mkdir(parents=True, exist_ok=True)


settings = Settings()
