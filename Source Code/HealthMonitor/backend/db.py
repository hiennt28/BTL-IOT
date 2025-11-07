import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()  # Đọc file .env nếu có

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", ""),
            database=os.getenv("DB_NAME", "health_monitor"),
            port=os.getenv("DB_PORT", 3306)
        )
        return conn
    except Error as e:
        print(f"Lỗi kết nối MySQL: {e}")
        return None
