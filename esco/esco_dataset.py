import esco.config as config
from esco.EscoDatasetParser import ESCODatasetParser
from esco.ESCODBHandler import ESCODBHandler
from pathlib import Path
import traceback 

if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': config.db_host,
        'database': config.db_database,
        'user': config.db_user,
        'password': config.db_password,
        'port': config.db_port
    }


    DATASET_DIR = Path(__file__).parent.parent / 'datasets' / 'ESCO'

    try:
        esco_db_handler = ESCODBHandler(db_config)
        esco_db_handler.connect()

        parser = ESCODatasetParser(esco_db_handler, dataset_dir=DATASET_DIR)
        successful, failed = parser.parse_dataset()

    except Exception as e:
        print(f"\n✗ Error: {e}. Traceback: {traceback.format_exc()}")

    finally:
        esco_db_handler.disconnect()
