import os
import sqlite3
import logging
from utils.path import BASEDIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

database_path = os.path.join(BASEDIR, "database","metadata.db")

def get_db_connection():
    logger.info(f"Connecting to database at {database_path}")
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Drop and recreate METADATA_REPORT table to apply schema changes
        # WARNING: This will delete all existing data in METADATA_REPORT table.
        cursor.execute("DROP TABLE IF EXISTS METADATA_REPORT")
        cursor.execute("""
            CREATE TABLE METADATA_REPORT (
                id_cia INTEGER NOT NULL,
                id_report INTEGER NOT NULL,
                name TEXT NOT NULL,
                cadsql TEXT NOT NULL,
                object_name TEXT, 
                last_exec TIMESTAMP NOT NULL,
                processing_time_ms INTEGER, 
                status TEXT NOT NULL DEFAULT 'OK', 
                error_message TEXT, 
                PRIMARY KEY (id_cia, id_report, last_exec)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_id_cia_id_report ON METADATA_REPORT (id_cia, id_report)
        """)
        
        # Create SCHEDULED_JOBS_LOG table (no changes needed here, but ensure it exists)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SCHEDULED_JOBS_LOG (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                report_id_cia INTEGER,
                report_id_report INTEGER,
                report_name TEXT,
                report_company TEXT, 
                event_type TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                message TEXT,
                next_run_time TIMESTAMP,
                duration_ms INTEGER,
                status TEXT
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_job_id ON SCHEDULED_JOBS_LOG (job_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_report_ids ON SCHEDULED_JOBS_LOG (report_id_cia, report_id_report)
        """)

        conn.commit()
        conn.close()
        logging.info("Database initialized successfully. Table METADATA_REPORT and SCHEDULED_JOBS_LOG are ready.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")
        raise

init_db()
