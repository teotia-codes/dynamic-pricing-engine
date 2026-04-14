import os
from dotenv import load_dotenv
from psycopg2.pool import SimpleConnectionPool

load_dotenv()

_db_pool = None

def init_db_pool():
    global _db_pool

    if _db_pool is None:
        _db_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )

    return _db_pool

def get_connection():
    pool = init_db_pool()
    return pool.getconn()

def release_connection(conn):
    pool = init_db_pool()
    pool.putconn(conn)

def close_all_connections():
    global _db_pool
    if _db_pool:
        _db_pool.closeall()
        _db_pool = None