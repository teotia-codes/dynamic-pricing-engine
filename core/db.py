from psycopg2.pool import SimpleConnectionPool
from core.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from backend.app.logger import logger

_db_pool = None


def init_db_pool():
    global _db_pool

    if _db_pool is None:
        logger.info(
            "Initializing DB pool | host=%s port=%s db=%s user=%s",
            DB_HOST,
            DB_PORT,
            DB_NAME,
            DB_USER,
        )

        _db_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )

        logger.info("Database connection pool initialized successfully")

    return _db_pool


def get_connection():
    pool = init_db_pool()
    return pool.getconn()


def release_connection(conn):
    global _db_pool

    if _db_pool and conn:
        _db_pool.putconn(conn)


def close_all_connections():
    global _db_pool

    if _db_pool:
        _db_pool.closeall()
        logger.info("All database connections closed")
        _db_pool = None