import config
from parsers.tools.ResumeCSVParser import ResumeCSVParser
from parsers.tools.DBHandler import DBHandler

if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': config.db_host,
        'database': config.db_database,
        'user': config.db_user,
        'password': config.db_password,
        'port': config.db_port
    }
    
    CSV_PATH = 'resume_dataset_kaggle/Resume/Resume.csv'
    DOWNLOAD_URL = 'https://www.kaggle.com/api/v1/datasets/download/snehaanbhawal/resume-dataset' 
    BASE_DATASET_DIR = 'datasets'
    
    source_name = "resume_dataset_kaggle"
    
    try:
        db_handler = DBHandler(db_config)
        db_handler.connect()

        parser = ResumeCSVParser(db_handler, base_datasets_dir=BASE_DATASET_DIR)
        successful, failed = parser.parse_csv(
            csv_relative_path=CSV_PATH,
            source_name='Kaggle Resume Dataset',
            download_url=DOWNLOAD_URL
        )
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    finally:
        db_handler.disconnect()
