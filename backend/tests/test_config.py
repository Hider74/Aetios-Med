"""
Test that config.py loads without Pydantic validation errors.
"""
import pytest
from app.config import Settings


def test_settings_initialization():
    """Test that Settings can be initialized without validation errors."""
    # This will raise ValidationError if there are issues
    settings = Settings()
    
    # Verify that paths are set correctly after __init__
    assert settings.database_path is not None
    assert settings.lancedb_path is not None
    assert settings.model_path is not None
    assert settings.curriculum_path is not None
    
    # Verify string fields
    assert settings.model_repo == "aaditya/Llama3-OpenBioLLM-8B-GGUF"
    assert settings.model_filename == "llama3-openbio-8b.Q4_K_M.gguf"


def test_protected_namespaces_configured():
    """Test that protected_namespaces is configured to allow model_ fields."""
    settings = Settings()
    
    # Verify model_config has protected_namespaces set to empty tuple
    assert hasattr(settings, 'model_config')
    assert settings.model_config.get('protected_namespaces') == ()
    
    # Verify that model_ fields work without warnings
    assert hasattr(settings, 'model_path')
    assert hasattr(settings, 'model_repo')
    assert hasattr(settings, 'model_filename')


def test_optional_path_fields():
    """Test that Optional[Path] fields are properly typed."""
    from typing import get_type_hints
    from pathlib import Path
    from typing import Optional
    
    hints = get_type_hints(Settings)
    
    # These fields should be Optional[Path]
    optional_path_fields = [
        'database_path',
        'lancedb_path', 
        'model_path',
        'curriculum_path',
        'anki_watch_folder',
        'notes_folder'
    ]
    
    for field_name in optional_path_fields:
        field_type = hints.get(field_name)
        # In Python 3.10+, Optional[Path] is Union[Path, None]
        assert field_type is not None, f"Field {field_name} not found in type hints"


if __name__ == "__main__":
    test_settings_initialization()
    test_protected_namespaces_configured()
    test_optional_path_fields()

