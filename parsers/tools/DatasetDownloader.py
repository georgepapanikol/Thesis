from pathlib import Path 
import requests 
import shutil 
import zipfile 

class DatasetDownloader:
    """Handles dataset downloading and extraction"""
    
    def __init__(self, base_dir: str = "datasets"):
        """
        Initialize downloader
        
        Args:
            base_dir: Base directory for all datasets (default: "datasets")
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def download_and_extract(self, url: str, dataset_name: str) -> Path:
        """
        Download and extract dataset from URL
        
        Args:
            url: URL to download the dataset from
            dataset_name: Name for the dataset folder (e.g., 'resume_dataset_kaggle')
            
        Returns:
            Path to the extracted dataset directory
            
        Raises:
            Exception: If download or extraction fails
        """
        dataset_path = self.base_dir / dataset_name
        
        # If dataset already exists, return it
        if dataset_path.exists():
            print(f"✓ Dataset already exists at: {dataset_path}")
            return dataset_path
        
        print(f"\n📥 Downloading dataset from: {url}")
        print("-" * 50)
        
        try:
            # Download the file
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Determine file extension from URL or Content-Type
            file_ext = self._get_file_extension(url, response)
            temp_file = self.base_dir / f"temp_download{file_ext}"
            
            # Save to temporary file with progress indicator
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r  Progress: {progress:.1f}%", end='', flush=True)
            
            print(f"\n✓ Download complete: {temp_file}")
            
            # Extract the file
            print(f"\n📦 Extracting to: {dataset_path}")
            self._extract_archive(temp_file, dataset_path)
            
            # Clean up temporary file
            temp_file.unlink()
            print("✓ Extraction complete!")
            print("-" * 50)
            
            return dataset_path
            
        except Exception as e:
            print(f"\n✗ Error downloading/extracting dataset: {e}")
            # Clean up on failure
            if temp_file.exists():
                temp_file.unlink()
            if dataset_path.exists():
                shutil.rmtree(dataset_path)
            raise
    
    def _get_file_extension(self, url: str, response: requests.Response) -> str:
        """Determine file extension from URL or headers"""
        # Try to get from URL
        url_path = Path(url)
        if url_path.suffix in ['.zip', '.tar', '.gz', '.tgz']:
            return url_path.suffix
        
        # Try to get from Content-Type header
        content_type = response.headers.get('Content-Type', '')
        if 'zip' in content_type:
            return '.zip'
        elif 'tar' in content_type or 'gzip' in content_type:
            return '.tar.gz'
        
        # Default to zip
        return '.zip'
    
    def _extract_archive(self, archive_path: Path, extract_to: Path):
        """Extract archive file to destination"""
        extract_to.mkdir(parents=True, exist_ok=True)
        
        if archive_path.suffix == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.suffix in ['.tar', '.gz', '.tgz']:
            import tarfile
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_to)
        else:
            raise ValueError(f"Unsupported archive format: {archive_path.suffix}")
