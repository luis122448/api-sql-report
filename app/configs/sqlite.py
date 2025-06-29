import sqlite3
import logging

DATABASE_FILE = "./db/metadata.db"

logging.basicConfig(level=logging.INFO)

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS METADATA_REPORT (
                id_cia INTEGER NOT NULL,
                id_report INTEGER NOT NULL,
                name TEXT NOT NULL,
                cadsql TEXT NOT NULL,
                object_name TEXT NOT NULL,
                last_exec TIMESTAMP NOT NULL,
                PRIMARY KEY (id_cia, id_report, last_exec)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_id_cia_id_report ON METADATA_REPORT (id_cia, id_report)
        """)
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully. Table METADATA_REPORT is ready.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")
        raise

init_db()
