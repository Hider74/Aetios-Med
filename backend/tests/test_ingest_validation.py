import pytest
import tempfile
import os
from pathlib import Path
from fastapi import HTTPException
from app.routers.ingest import validate_file_path, ALLOWED_ANKI_EXTENSIONS, ALLOWED_NOTES_EXTENSIONS


def test_validate_file_path_valid_anki():
    """Test validation with a valid .apkg file path"""
    # Create a temporary .apkg file
    with tempfile.NamedTemporaryFile(suffix='.apkg', delete=False) as f:
        temp_path = f.name
    
    try:
        result = validate_file_path(temp_path, ALLOWED_ANKI_EXTENSIONS)
        assert result.exists()
        assert result.suffix == '.apkg'
    finally:
        os.unlink(temp_path)


def test_validate_file_path_valid_notes():
    """Test validation with valid .txt and .md file paths"""
    # Test .txt
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        temp_path = f.name
    
    try:
        result = validate_file_path(temp_path, ALLOWED_NOTES_EXTENSIONS)
        assert result.exists()
        assert result.suffix == '.txt'
    finally:
        os.unlink(temp_path)
    
    # Test .md
    with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
        temp_path = f.name
    
    try:
        result = validate_file_path(temp_path, ALLOWED_NOTES_EXTENSIONS)
        assert result.exists()
        assert result.suffix == '.md'
    finally:
        os.unlink(temp_path)


def test_validate_file_path_directory_traversal():
    """Test that directory traversal attempts are rejected"""
    # Test with .. in path
    with pytest.raises(HTTPException) as exc_info:
        validate_file_path("../../etc/passwd", ALLOWED_ANKI_EXTENSIONS)
    assert exc_info.value.status_code == 400
    assert "directory traversal" in exc_info.value.detail.lower()
    
    # Test with .. in middle of path
    with pytest.raises(HTTPException) as exc_info:
        validate_file_path("/tmp/../etc/passwd", ALLOWED_ANKI_EXTENSIONS)
    assert exc_info.value.status_code == 400
    assert "directory traversal" in exc_info.value.detail.lower()


def test_validate_file_path_invalid_extension_anki():
    """Test that invalid extensions are rejected for Anki endpoint"""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        temp_path = f.name
    
    try:
        with pytest.raises(HTTPException) as exc_info:
            validate_file_path(temp_path, ALLOWED_ANKI_EXTENSIONS)
        assert exc_info.value.status_code == 400
        assert "invalid file type" in exc_info.value.detail.lower()
        assert ".apkg" in exc_info.value.detail
    finally:
        os.unlink(temp_path)


def test_validate_file_path_invalid_extension_notes():
    """Test that invalid extensions are rejected for notes endpoint"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_path = f.name
    
    try:
        with pytest.raises(HTTPException) as exc_info:
            validate_file_path(temp_path, ALLOWED_NOTES_EXTENSIONS)
        assert exc_info.value.status_code == 400
        assert "invalid file type" in exc_info.value.detail.lower()
    finally:
        os.unlink(temp_path)


def test_validate_file_path_empty_string():
    """Test that empty string is rejected"""
    with pytest.raises(HTTPException) as exc_info:
        validate_file_path("", ALLOWED_ANKI_EXTENSIONS)
    assert exc_info.value.status_code == 400
    assert "file path is required" in exc_info.value.detail.lower()


def test_validate_file_path_none():
    """Test that None is rejected"""
    with pytest.raises(HTTPException) as exc_info:
        validate_file_path(None, ALLOWED_ANKI_EXTENSIONS)
    assert exc_info.value.status_code == 400
    assert "file path is required" in exc_info.value.detail.lower()


def test_validate_file_path_case_insensitive():
    """Test that extension check is case-insensitive"""
    # Test .APKG (uppercase)
    with tempfile.NamedTemporaryFile(suffix='.APKG', delete=False) as f:
        temp_path = f.name
    
    try:
        result = validate_file_path(temp_path, ALLOWED_ANKI_EXTENSIONS)
        assert result.exists()
    finally:
        os.unlink(temp_path)
    
    # Test .TXT (uppercase)
    with tempfile.NamedTemporaryFile(suffix='.TXT', delete=False) as f:
        temp_path = f.name
    
    try:
        result = validate_file_path(temp_path, ALLOWED_NOTES_EXTENSIONS)
        assert result.exists()
    finally:
        os.unlink(temp_path)
