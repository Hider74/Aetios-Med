"""
Test that all service files import required typing types correctly.
This test validates that the NameError fix for 'Any' is working.
"""
import ast
from pathlib import Path


def test_retention_service_imports_any():
    """Test that retention_service.py imports Any from typing."""
    retention_path = Path(__file__).parent.parent / "app" / "services" / "retention_service.py"
    
    with open(retention_path, 'r') as f:
        content = f.read()
    
    # Verify file can be parsed without syntax errors
    ast.parse(content)
    
    # Verify Any is in the typing import
    assert "from typing import" in content
    
    # Find the typing import line
    typing_imports = [line for line in content.split('\n') if 'from typing import' in line]
    assert len(typing_imports) > 0, "No typing import found"
    
    # Verify Any is imported
    assert any("Any" in line for line in typing_imports), "Any not found in typing imports"
    
    # Verify the expected import format
    assert "from typing import List, Dict, Optional, Tuple, Any" in content


def test_retention_service_uses_any():
    """Test that retention_service.py uses Any in type hints."""
    retention_path = Path(__file__).parent.parent / "app" / "services" / "retention_service.py"
    
    with open(retention_path, 'r') as f:
        content = f.read()
    
    # Verify Any is used in type hints
    assert "List[Dict[str, Any]]" in content, "Expected type hint List[Dict[str, Any]] not found"


def test_all_service_files_have_required_imports():
    """Test that all service files that use Any have it imported."""
    services_path = Path(__file__).parent.parent / "app" / "services"
    
    # Files that should have Any imported based on their usage
    files_using_any = [
        "retention_service.py",
        "llm_service.py",
        "vector_service.py",
        "quiz_service.py",
        "study_plan_service.py",
        "ingest_service.py",
        "graph_service.py",
    ]
    
    for filename in files_using_any:
        filepath = services_path / filename
        assert filepath.exists(), f"{filename} not found"
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check if file uses Any in type hints
        if "Dict[str, Any]" in content or ": Any" in content:
            # Verify Any is imported
            typing_imports = [line for line in content.split('\n')[:30] if 'from typing import' in line]
            has_any = any("Any" in line for line in typing_imports)
            assert has_any, f"{filename} uses Any but doesn't import it"


if __name__ == "__main__":
    test_retention_service_imports_any()
    test_retention_service_uses_any()
    test_all_service_files_have_required_imports()
    print("✓ All tests passed!")
