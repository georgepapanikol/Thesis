import pandas as pd
import psycopg2
import os 
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=os.environ['DB_DATABASE'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    host=os.environ['DB_HOST'],
    port=os.environ['DB_PORT']
)

# Output folder (create it if it doesn't exist)
output_dir = Path(__file__).parent / "csv_exports"
output_dir.mkdir(exist_ok=True)

# Tables list
tables = [
    "companies",
    "job_postings",
    "seniority_levels",
    "job_posting_seniority",
    "categories",
    "job_posting_categories",
    "parent_categories",
    "job_posting_parent_categories",
    "location_restrictions",
    "job_posting_location_restrictions",
    "timezone_restrictions",
    "job_posting_timezone_restrictions",
    "tags",
    "job_posting_tags"
]

# Export each table to CSV
for table in tables:
    print(f"Exporting {table}...")
    
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    
    file_path = output_dir / f"{table}.csv"
    
    df.to_csv(file_path, sep=';', index=False, encoding='utf-8')
    
print("Export completed!")

# Close connection
conn.close()