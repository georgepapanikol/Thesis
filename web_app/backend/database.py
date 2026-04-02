import psycopg2
import psycopg2.extras
from backend.config import ESCO_DB, OJA_DB


def get_esco_conn():
    return psycopg2.connect(**ESCO_DB, cursor_factory=psycopg2.extras.RealDictCursor)


def get_oja_conn():
    return psycopg2.connect(**OJA_DB, cursor_factory=psycopg2.extras.RealDictCursor)
