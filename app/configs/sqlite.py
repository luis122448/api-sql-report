import os
import sqlite3
import logging
from utils.path import BASEDIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

database_path = os.path.join(BASEDIR, "database","metadata.db")

def get_db_connection():
    logger.info(f"Connecting to database at {database_path}")
    try:
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}")
        return None

def init_db():
    try:
        conn = get_db_connection()
        if not conn:
            raise sqlite3.Error("Failed to get database connection.")
        cursor = conn.cursor()
        
        # Create METADATA_REPORT table (no changes needed here, but ensure it exists)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS METADATA_REPORT (
                id_cia INTEGER NOT NULL,
                id_report INTEGER NOT NULL,
                name TEXT NOT NULL,
                cadsql TEXT NOT NULL,
                object_name_parquet TEXT,
                object_name_csv TEXT,
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
        
        cursor.execute("""DROP TABLE IF EXISTS SCHEDULED_JOBS_LOG""")
        # Create SCHEDULED_JOBS_LOG table (no changes needed here, but ensure it exists)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SCHEDULED_JOBS_LOG (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                id_cia INTEGER,
                id_report INTEGER,
                name TEXT,
                company TEXT, 
                event_type TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                message TEXT,
                next_run_time TIMESTAMP,
                duration_ms INTEGER,
                status TEXT,
                refresh_time INTEGER,
                schedule_type TEXT
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_job_id ON SCHEDULED_JOBS_LOG (job_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_report_ids ON SCHEDULED_JOBS_LOG (id_cia, id_report)
        """)

        cursor.execute("""DROP TABLE IF EXISTS SCHEDULED_JOBS""")
        # Create SCHEDULED_JOBS table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SCHEDULED_JOBS (
                job_id TEXT PRIMARY KEY NOT NULL,
                id_cia INTEGER,
                id_report INTEGER,
                name TEXT,
                company TEXT, 
                event_type TEXT NOT NULL,
                refresh_time INTEGER,
                schedule_type TEXT,
                schedule_date TIMESTAMP NOT NULL
            )
        """)

        # Create API_USAGE_LOG table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS API_USAGE_LOG (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                id_cia INTEGER NOT NULL,
                id_report INTEGER,
                requester_ip TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                user_agent TEXT,
                token_coduser TEXT,
                processing_time_ms INTEGER
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_cia_report ON API_USAGE_LOG (id_cia, id_report)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON API_USAGE_LOG (timestamp)
        """)

        cursor.execute("""DROP TABLE IF EXISTS STALE_JOBS_LOG""")
        # Create STALE_JOBS_LOG table for the guardian process
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS STALE_JOBS_LOG (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_timestamp TIMESTAMP NOT NULL,
                job_id TEXT NOT NULL,
                id_cia INTEGER,
                id_report INTEGER,
                name TEXT,
                last_successful_exec TIMESTAMP,
                refresh_time INTEGER
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stale_job_id ON STALE_JOBS_LOG (job_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stale_detection_timestamp ON STALE_JOBS_LOG (detection_timestamp)
        """)

        conn.commit()
        conn.close()
        logging.info("Database initialized successfully. All tables are ready.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")
        raise

init_db()
