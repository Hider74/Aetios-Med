"""
Aetios-Med Configuration
Handles cross-platform paths and settings.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

logger = logging.getLogger(__name__)


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
    
    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        protected_namespaces=()
    )
    
    # Paths
    app_data_dir: Path = get_app_data_dir()
    database_path: Optional[Path] = None
    lancedb_path: Optional[Path] = None
    model_path: Optional[Path] = None
    curriculum_path: Optional[Path] = None
    ukmla_curriculum_path: Optional[Path] = None
    legacy_curriculum_path: Optional[Path] = None
    uploaded_curriculum_path: Optional[Path] = None
    anki_watch_folder: Optional[Path] = None
    notes_folder: Optional[Path] = None

    # Curriculum
    active_curriculum_key: Optional[str] = None
    
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
    
    # HuggingFace - uses SecretStr to prevent accidental exposure in logs/serialization
    hf_token: Optional[SecretStr] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Set derived paths
        self.database_path = self.app_data_dir / "aetios.db"
        self.lancedb_path = self.app_data_dir / "lancedb"
        self.model_path = self.app_data_dir / "models" / self.model_filename
        self.ukmla_curriculum_path = self.app_data_dir / "curriculum" / "ukmla_graph.json"
        self.legacy_curriculum_path = self.app_data_dir / "curriculum" / "uk_curriculum.json"
        self.uploaded_curriculum_path = self.app_data_dir / "curriculum" / "uploaded_curriculum.json"
        # Backwards compatibility: curriculum_path mirrors UKMLA path
        self.curriculum_path = self.ukmla_curriculum_path
        
        # Create directories
        (self.app_data_dir / "models").mkdir(parents=True, exist_ok=True)
        (self.app_data_dir / "curriculum").mkdir(parents=True, exist_ok=True)
        self.lancedb_path.mkdir(parents=True, exist_ok=True)
        
        # GPU detection logging
        if self.gpu_layers != 0:
            self._log_gpu_availability()
    
    def _log_gpu_availability(self):
        """Log GPU availability and potential issues."""
        try:
            # Try to import llama-cpp-python to check for GPU support
            import llama_cpp
            
            # Check platform-specific GPU availability
            if sys.platform == "darwin":
                # macOS: Check for Metal support
                logger.info(f"GPU offloading requested (gpu_layers={self.gpu_layers}). "
                           "Metal GPU acceleration should be available on Apple Silicon.")
            elif sys.platform == "win32" or sys.platform == "linux":
                # Windows/Linux: Check for CUDA
                try:
                    import subprocess
                    result = subprocess.run(['nvidia-smi'], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=5)
                    if result.returncode == 0:
                        logger.info(f"GPU offloading requested (gpu_layers={self.gpu_layers}). "
                                   "NVIDIA GPU detected.")
                    else:
                        logger.warning(f"GPU offloading requested (gpu_layers={self.gpu_layers}) "
                                     "but nvidia-smi failed. Model will fall back to CPU, "
                                     "which may be significantly slower.")
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    logger.warning(f"GPU offloading requested (gpu_layers={self.gpu_layers}) "
                                 "but CUDA/NVIDIA GPU not detected. Model will fall back to CPU, "
                                 "which may be significantly slower.")
            else:
                logger.info(f"GPU offloading requested (gpu_layers={self.gpu_layers}) "
                           f"on platform {sys.platform}.")
        except ImportError:
            logger.warning("llama-cpp-python not installed. GPU detection skipped.")


settings = Settings()
