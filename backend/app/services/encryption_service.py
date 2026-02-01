"""
Encryption Service
AES-256 encryption with secure key storage using system keyring.
"""
import os
import base64
from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding as sym_padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import keyring


class EncryptionService:
    """Service for encrypting/decrypting sensitive data."""
    
    SERVICE_NAME = "Aetios-Med"
    KEY_NAME = "encryption_key"
    
    def __init__(self):
        self._key: Optional[bytes] = None
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from keyring or create new one."""
        if self._key:
            return self._key
        
        # Try to get existing key from keyring
        key_b64 = keyring.get_password(self.SERVICE_NAME, self.KEY_NAME)
        
        if key_b64:
            # Decode existing key
            self._key = base64.b64decode(key_b64)
        else:
            # Generate new key
            self._key = os.urandom(32)  # 256 bits for AES-256
            
            # Store in keyring
            key_b64 = base64.b64encode(self._key).decode('utf-8')
            keyring.set_password(self.SERVICE_NAME, self.KEY_NAME, key_b64)
        
        return self._key
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())
    
    def encrypt_text(
        self, 
        plaintext: str, 
        password: Optional[str] = None
    ) -> str:
        """
        Encrypt text using AES-256-CBC.
        
        Args:
            plaintext: Text to encrypt
            password: Optional password (uses keyring key if not provided)
        
        Returns:
            Base64-encoded encrypted data with IV and salt
        """
        if not plaintext:
            return ""
        
        # Get or derive encryption key
        if password:
            salt = os.urandom(16)
            key = self._derive_key(password, salt)
        else:
            key = self._get_or_create_key()
            salt = b''
        
        # Generate random IV
        iv = os.urandom(16)
        
        # Pad plaintext to block size (16 bytes for AES)
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        
        # Encrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine salt (if used), IV, and ciphertext
        if password:
            encrypted_data = salt + iv + ciphertext
            prefix = b'PWD:'
        else:
            encrypted_data = iv + ciphertext
            prefix = b'KEY:'
        
        # Encode to base64 for storage
        return (prefix + base64.b64encode(encrypted_data)).decode('utf-8')
    
    def decrypt_text(
        self, 
        encrypted_text: str, 
        password: Optional[str] = None
    ) -> str:
        """
        Decrypt text encrypted with encrypt_text.
        
        Args:
            encrypted_text: Base64-encoded encrypted data
            password: Optional password (uses keyring key if not provided)
        
        Returns:
            Decrypted plaintext
        """
        if not encrypted_text:
            return ""
        
        # Check prefix to determine encryption type
        if encrypted_text.startswith('PWD:'):
            encrypted_text = encrypted_text[4:]
            uses_password = True
        elif encrypted_text.startswith('KEY:'):
            encrypted_text = encrypted_text[4:]
            uses_password = False
        else:
            # Legacy format, assume keyring key
            uses_password = False
        
        # Decode from base64
        encrypted_data = base64.b64decode(encrypted_text)
        
        # Extract components
        if uses_password:
            if not password:
                raise ValueError("Password required for decryption")
            
            salt = encrypted_data[:16]
            iv = encrypted_data[16:32]
            ciphertext = encrypted_data[32:]
            key = self._derive_key(password, salt)
        else:
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            key = self._get_or_create_key()
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad
        unpadder = sym_padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext.decode('utf-8')
    
    def encrypt_file(
        self, 
        input_path: str, 
        output_path: str,
        password: Optional[str] = None
    ) -> None:
        """Encrypt a file."""
        with open(input_path, 'rb') as f:
            plaintext = f.read()
        
        # Convert to text for encryption
        plaintext_b64 = base64.b64encode(plaintext).decode('utf-8')
        encrypted = self.encrypt_text(plaintext_b64, password)
        
        with open(output_path, 'w') as f:
            f.write(encrypted)
    
    def decrypt_file(
        self, 
        input_path: str, 
        output_path: str,
        password: Optional[str] = None
    ) -> None:
        """Decrypt a file."""
        with open(input_path, 'r') as f:
            encrypted = f.read()
        
        plaintext_b64 = self.decrypt_text(encrypted, password)
        plaintext = base64.b64decode(plaintext_b64)
        
        with open(output_path, 'wb') as f:
            f.write(plaintext)
    
    def change_keyring_key(self) -> None:
        """Generate and store a new encryption key in keyring."""
        self._key = os.urandom(32)
        key_b64 = base64.b64encode(self._key).decode('utf-8')
        keyring.set_password(self.SERVICE_NAME, self.KEY_NAME, key_b64)
    
    def delete_keyring_key(self) -> None:
        """Delete the encryption key from keyring."""
        try:
            keyring.delete_password(self.SERVICE_NAME, self.KEY_NAME)
            self._key = None
        except keyring.errors.PasswordDeleteError:
            pass
    
    def has_keyring_key(self) -> bool:
        """Check if encryption key exists in keyring."""
        return keyring.get_password(self.SERVICE_NAME, self.KEY_NAME) is not None
    
    def test_encryption(self) -> bool:
        """Test encryption/decryption functionality."""
        try:
            test_text = "Hello, Aetios-Med! 🔒"
            
            # Test with keyring key
            encrypted = self.encrypt_text(test_text)
            decrypted = self.decrypt_text(encrypted)
            
            if decrypted != test_text:
                return False
            
            # Test with password
            password = "test_password_123"
            encrypted_pwd = self.encrypt_text(test_text, password)
            decrypted_pwd = self.decrypt_text(encrypted_pwd, password)
            
            if decrypted_pwd != test_text:
                return False
            
            return True
            
        except Exception as e:
            print(f"Encryption test failed: {e}")
            return False
    
    @staticmethod
    def is_encrypted(text: str) -> bool:
        """Check if text appears to be encrypted."""
        if not text:
            return False
        
        # Check for our prefixes
        if text.startswith('PWD:') or text.startswith('KEY:'):
            return True
        
        # Check if it looks like base64
        try:
            base64.b64decode(text)
            # If it decodes and is long enough, probably encrypted
            return len(text) > 32 and '=' in text[-3:]
        except:
            return False
