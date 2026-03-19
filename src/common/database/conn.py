import os
import psycopg2
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()

DB_NAME = os.getenv('DB_NAME', 'multimedia_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')


def get_conn():
    """Tạo và trả về connection PostgreSQL."""
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
