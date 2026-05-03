import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings   # 👈 use your existing config


def get_connection():
    return psycopg2.connect(settings.DATABASE_URL)


def run_query(query: str, params: tuple = ()):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(query, params)
        result = cursor.fetchall()

        cursor.close()
        return result

    except Exception as e:
        print("DB ERROR:", e)
        return []

    finally:
        if conn:
            conn.close()