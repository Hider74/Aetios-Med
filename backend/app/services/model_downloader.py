"""
Model Downloader Service
Download LLM models from HuggingFace with progress tracking and resume support.
"""
import os
import hashlib
from pathlib import Path
from typing import Optional, Callable
from huggingface_hub import hf_hub_download, HfApi
from huggingface_hub.utils import HfHubHTTPError
from tqdm import tqdm


class ModelDownloader:
    """Service for downloading models from HuggingFace."""
    
    def __init__(self, hf_token: Optional[str] = None):
        self.hf_token = hf_token
        self.api = HfApi(token=hf_token)
    
    def download_model(
        self,
        repo_id: str,
        filename: str,
        output_path: Path,
        resume: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Download a model file from HuggingFace Hub.
        
        Args:
            repo_id: HuggingFace repo ID (e.g., "username/model-name")
            filename: Model filename (e.g., "model.gguf")
            output_path: Local path to save the model
            resume: Whether to resume interrupted downloads
            progress_callback: Optional callback(downloaded_bytes, total_bytes)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file already exists and is complete
            if output_path.exists():
                if self._verify_file_integrity(repo_id, filename, output_path):
                    print(f"Model already downloaded: {output_path}")
                    return True
                elif not resume:
                    # Delete partial file if not resuming
                    output_path.unlink()
            
            print(f"Downloading {repo_id}/{filename}...")
            
            # Get file info for progress
            file_info = None
            try:
                file_info = self.api.model_info(repo_id, files_metadata=True)
                for sibling in file_info.siblings:
                    if sibling.rfilename == filename:
                        total_size = sibling.size
                        break
                else:
                    total_size = None
            except:
                total_size = None
            
            # Download with progress bar
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir=output_path.parent,
                local_dir=output_path.parent,
                local_dir_use_symlinks=False,
                token=self.hf_token,
                resume_download=resume,
                tqdm_class=TqdmCallback if progress_callback else tqdm
            )
            
            # Move to final location if needed
            downloaded_path = Path(downloaded_path)
            if downloaded_path != output_path:
                if output_path.exists():
                    output_path.unlink()
                downloaded_path.rename(output_path)
            
            print(f"✓ Downloaded successfully: {output_path}")
            return True
            
        except HfHubHTTPError as e:
            if e.response.status_code == 401:
                print("Error: Authentication required. Please provide a valid HuggingFace token.")
            elif e.response.status_code == 404:
                print(f"Error: Model or file not found: {repo_id}/{filename}")
            else:
                print(f"Error downloading model: {e}")
            return False
            
        except Exception as e:
            print(f"Error downloading model: {e}")
            return False
    
    def _verify_file_integrity(
        self,
        repo_id: str,
        filename: str,
        local_path: Path
    ) -> bool:
        """
        Verify file integrity by comparing size with HuggingFace.
        
        Returns:
            True if file is complete and valid
        """
        try:
            # Get file info from HuggingFace
            file_info = self.api.model_info(repo_id, files_metadata=True)
            
            expected_size = None
            for sibling in file_info.siblings:
                if sibling.rfilename == filename:
                    expected_size = sibling.size
                    break
            
            if expected_size is None:
                return False
            
            # Compare with local file size
            local_size = local_path.stat().st_size
            
            if local_size == expected_size:
                return True
            else:
                print(f"File size mismatch: expected {expected_size}, got {local_size}")
                return False
                
        except Exception as e:
            print(f"Error verifying file: {e}")
            return False
    
    def get_model_info(
        self,
        repo_id: str
    ) -> Optional[dict]:
        """
        Get information about a model from HuggingFace.
        
        Returns:
            Dictionary with model info or None if not found
        """
        try:
            info = self.api.model_info(repo_id, files_metadata=True)
            
            # Extract relevant information
            model_info = {
                'repo_id': repo_id,
                'author': info.author if hasattr(info, 'author') else None,
                'downloads': info.downloads if hasattr(info, 'downloads') else 0,
                'likes': info.likes if hasattr(info, 'likes') else 0,
                'tags': info.tags if hasattr(info, 'tags') else [],
                'files': []
            }
            
            # List all files
            for sibling in info.siblings:
                model_info['files'].append({
                    'filename': sibling.rfilename,
                    'size': sibling.size,
                    'size_mb': round(sibling.size / (1024 * 1024), 2)
                })
            
            return model_info
            
        except Exception as e:
            print(f"Error getting model info: {e}")
            return None
    
    def list_model_files(
        self,
        repo_id: str,
        pattern: Optional[str] = None
    ) -> list:
        """
        List files in a model repository.
        
        Args:
            repo_id: HuggingFace repo ID
            pattern: Optional pattern to filter files (e.g., "*.gguf")
        
        Returns:
            List of file information dictionaries
        """
        try:
            info = self.api.model_info(repo_id, files_metadata=True)
            
            files = []
            for sibling in info.siblings:
                filename = sibling.rfilename
                
                # Filter by pattern if provided
                if pattern:
                    from fnmatch import fnmatch
                    if not fnmatch(filename, pattern):
                        continue
                
                files.append({
                    'filename': filename,
                    'size': sibling.size,
                    'size_mb': round(sibling.size / (1024 * 1024), 2),
                    'size_gb': round(sibling.size / (1024 * 1024 * 1024), 2)
                })
            
            return files
            
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def calculate_file_hash(
        self,
        file_path: Path,
        algorithm: str = 'sha256'
    ) -> Optional[str]:
        """
        Calculate hash of a file.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('sha256', 'md5', etc.)
        
        Returns:
            Hex digest of the hash
        """
        try:
            hash_obj = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096 * 1024), b''):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            print(f"Error calculating hash: {e}")
            return None
    
    def get_download_size(
        self,
        repo_id: str,
        filename: str
    ) -> Optional[int]:
        """
        Get the size of a file without downloading it.
        
        Returns:
            File size in bytes or None if not found
        """
        try:
            info = self.api.model_info(repo_id, files_metadata=True)
            
            for sibling in info.siblings:
                if sibling.rfilename == filename:
                    return sibling.size
            
            return None
            
        except Exception as e:
            print(f"Error getting file size: {e}")
            return None
    
    def check_model_exists(
        self,
        repo_id: str,
        filename: Optional[str] = None
    ) -> bool:
        """
        Check if a model (or specific file) exists on HuggingFace.
        
        Args:
            repo_id: HuggingFace repo ID
            filename: Optional specific filename to check
        
        Returns:
            True if exists, False otherwise
        """
        try:
            info = self.api.model_info(repo_id, files_metadata=True)
            
            if filename:
                # Check for specific file
                for sibling in info.siblings:
                    if sibling.rfilename == filename:
                        return True
                return False
            else:
                # Just check if repo exists
                return True
                
        except:
            return False


class TqdmCallback(tqdm):
    """Custom tqdm class for progress callbacks."""
    
    def __init__(self, *args, callback: Optional[Callable] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback
    
    def update(self, n=1):
        super().update(n)
        if self.callback:
            self.callback(self.n, self.total)
