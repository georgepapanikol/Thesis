import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

ESCO_DB = {
    "host":     os.environ["ESCO_DB_HOST"],
    "database": os.environ["ESCO_DB_NAME"],
    "user":     os.environ["ESCO_DB_USER"],
    "password": os.environ["ESCO_DB_PASSWORD"],
    "port":     os.environ["ESCO_DB_PORT"],
}

OJA_DB = {
    "host":     os.environ["OJA_DB_HOST"],
    "database": os.environ["OJA_DB_NAME"],
    "user":     os.environ["OJA_DB_USER"],
    "password": os.environ["OJA_DB_PASSWORD"],
    "port":     os.environ["OJA_DB_PORT"],
}

frontend_dir = Path(__file__).parent.parent / "frontend"
server_ip = os.environ["SERVER_IP"]
server_port = int(os.environ["SERVER_PORT"])