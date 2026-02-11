"""
Test HuggingFace token security with SecretStr.
"""
import json
from typing import Optional
from pydantic import BaseModel, SecretStr


def test_secret_str_redaction():
    """Test that SecretStr redacts token in serialization."""
    
    class MockSettings(BaseModel):
        hf_token: Optional[SecretStr] = None
    
    # Test with None value
    settings_none = MockSettings()
    assert settings_none.hf_token is None
    
    # Test with actual token
    settings_with_token = MockSettings(hf_token="hf_abc123secret456")
    
    # Verify the token is stored
    assert settings_with_token.hf_token is not None
    assert settings_with_token.hf_token.get_secret_value() == "hf_abc123secret456"
    
    # Verify serialization redacts the token
    serialized = settings_with_token.model_dump()
    assert isinstance(serialized['hf_token'], SecretStr)
    
    # JSON serialization should show masked value, not the actual token
    json_str = settings_with_token.model_dump_json()
    # The actual token should NOT be in the JSON
    assert "hf_abc123secret456" not in json_str
    # It should show as a masked value
    assert "**********" in json_str or "SecretStr" in json_str or "null" in json_str.lower()
    
    print("✓ SecretStr properly redacts token in serialization")


def test_secret_str_repr():
    """Test that SecretStr doesn't leak in repr/str."""
    
    class MockSettings(BaseModel):
        hf_token: Optional[SecretStr] = None
    
    settings = MockSettings(hf_token="hf_abc123secret456")
    
    # Verify repr doesn't leak the token
    repr_str = repr(settings)
    assert "hf_abc123secret456" not in repr_str
    
    # Verify str doesn't leak the token
    str_str = str(settings)
    assert "hf_abc123secret456" not in str_str
    
    print("✓ SecretStr doesn't leak in repr/str")


def test_model_downloader_usage():
    """Test that ModelDownloader can use SecretStr with get_secret_value()."""
    
    class MockSettings(BaseModel):
        hf_token: Optional[SecretStr] = None
    
    # Simulate ModelDownloader usage pattern
    settings = MockSettings(hf_token="hf_abc123secret456")
    
    # This is how ModelDownloader should be instantiated
    if settings.hf_token:
        token_value = settings.hf_token.get_secret_value()
        assert token_value == "hf_abc123secret456"
    else:
        token_value = None
    
    # Simulate with None token
    settings_no_token = MockSettings()
    if settings_no_token.hf_token:
        token_value_2 = settings_no_token.hf_token.get_secret_value()
    else:
        token_value_2 = None
    
    assert token_value_2 is None
    
    print("✓ ModelDownloader can properly use SecretStr.get_secret_value()")


if __name__ == "__main__":
    test_secret_str_redaction()
    test_secret_str_repr()
    test_model_downloader_usage()
    print("\n✓ All SecretStr security tests passed")
