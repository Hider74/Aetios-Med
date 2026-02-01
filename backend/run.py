"""
Aetios-Med Backend Entry Point for PyInstaller
This module is the entry point when the backend is bundled as a standalone executable.
"""
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    from app.config import settings
    
    # Run the FastAPI application
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info"
    )
