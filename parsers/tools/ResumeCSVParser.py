import csv
from typing import Tuple, Optional
from parsers.tools.DBHandler import DBHandler
from parsers.tools.DatasetDownloader import DatasetDownloader
from pathlib import Path

class ResumeCSVParser:
    """Parser to read resume CSV data with automatic dataset downloading"""
    
    def __init__(self, db_handler: DBHandler, base_datasets_dir: str = "datasets"):
        """
        Initialize parser with database handler
        
        Args:
            db_handler: DBHandler instance for database operations
            base_datasets_dir: Base directory for datasets (default: "datasets")
        """
        self.db_handler = db_handler
        self.downloader = DatasetDownloader(base_datasets_dir)
        
    def validate_csv(self, csv_path: Path) -> None:
        """
        Validate CSV file exists and has required columns
        
        Args:
            csv_path: Path to CSV file
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If required columns are missing
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
            
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            required_cols = {'ID', 'Resume_str', 'Category'}
            if not required_cols.issubset(reader.fieldnames):
                raise ValueError(
                    f"CSV missing required columns. Required: {required_cols}, "
                    f"Found: {set(reader.fieldnames)}"
                )
    
    def ensure_dataset(self, csv_relative_path: str, download_url: Optional[str] = None) -> Path:
        """
        Ensure dataset exists, download if necessary
        
        Args:
            csv_relative_path: Relative path to CSV within datasets dir
                              e.g., 'resume_dataset_kaggle/Resume/Resume.csv'
            download_url: URL to download dataset if not found (optional)
            
        Returns:
            Full path to the CSV file
            
        Raises:
            FileNotFoundError: If CSV not found and no download URL provided
        """
        # Convert to Path object
        csv_path = Path(self.downloader.base_dir) / csv_relative_path
        
        # If CSV exists, return it
        if csv_path.exists():
            print(f"✓ Found CSV at: {csv_path}")
            return csv_path
        
        # If CSV doesn't exist and no URL provided, raise error
        if download_url is None:
            raise FileNotFoundError(
                f"CSV not found at: {csv_path}\n"
                f"Please provide a download_url to automatically download the dataset."
            )
        
        # Extract dataset name (first directory in relative path)
        dataset_name = Path(csv_relative_path).parts[0]
        
        # Download and extract dataset
        self.downloader.download_and_extract(download_url, dataset_name)
        
        # Verify CSV now exists
        if not csv_path.exists():
            raise FileNotFoundError(
                f"CSV still not found after extraction: {csv_path}\n"
                f"The archive structure may be different than expected."
            )
        
        print(f"✓ CSV ready at: {csv_path}")
        return csv_path
    
    def parse_csv(self, 
                  csv_relative_path: str, 
                  source_name: str,
                  download_url: Optional[str] = None) -> Tuple[int, int]:
        """
        Parse CSV file and insert data into database
        Automatically downloads dataset if not found and URL is provided
        
        Args:
            csv_relative_path: Relative path to CSV file within datasets directory
                              e.g., 'resume_dataset_kaggle/Resume/Resume.csv'
            source_name: Name to use as source_name in database
            download_url: Optional URL to download dataset if not found
            
        Returns:
            Tuple of (successful_inserts, failed_inserts)
        """
        # Ensure dataset exists (download if necessary)
        csv_path = self.ensure_dataset(csv_relative_path, download_url)
        
        # Validate CSV before processing
        self.validate_csv(csv_path)
        
        successful = 0
        failed = 0
        
        print(f"\nParsing CSV: {csv_path}")
        print("-" * 50)
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):  # start=2 for line numbers
                # Extract and clean data
                source_id = row['ID'].strip()               
                resume_content = row['Resume_str'].strip()
                category = row['Category'].strip()
                
                # Skip empty rows
                if not source_id or not resume_content or not category:
                    print(f"  ⚠ Skipping row {row_num}: missing data")
                    failed += 1
                    continue
                
                # Insert into database via handler
                if self.db_handler.insert_resume(source_id, resume_content, category, source_name):
                    successful += 1
                    if successful % 100 == 0:  # Progress indicator
                        print(f"  Processed {successful} resumes...")
                else:
                    failed += 1
                    
        print("-" * 50)
        print("\n✓ Import complete!")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total: {successful + failed}")
        
        return successful, failed