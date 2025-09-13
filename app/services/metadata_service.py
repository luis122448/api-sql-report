import sqlite3
import pytz
import logging
from datetime import datetime, timedelta
from configs.sqlite import get_db_connection
from schemas.api_response_schema import ApiResponseObject
from scheduling.report_config_loader import ReportConfigLoader # Import the loader
from typing import Any # Import Any

logger = logging.getLogger(__name__)

class MetadataService:
    def log_report_metadata(self, id_cia: int, id_report: int, name: str, cadsql: str, 
                            object_name_parquet: str = None, object_name_csv: str = None, 
                            last_exec: datetime = None, 
                            processing_time_ms: int = None, status: str = 'OK', 
                            error_message: str = None, execution_type: str = 'AUTO') -> ApiResponseObject:
        # Logs the metadata of a generated report into the SQLite database.
        response = ApiResponseObject(status=1, message="Metadata logged successfully.")
        conn = get_db_connection()
        if not conn:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = "Failed to connect to the database."
            return response
        try:
            peru_tz = pytz.timezone('America/Lima')
            now_in_peru = datetime.now(peru_tz)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO METADATA_REPORT (id_cia, id_report, name, cadsql, object_name_parquet, object_name_csv, last_exec, processing_time_ms, status, error_message, execution_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_cia, id_report, name, cadsql, object_name_parquet, object_name_csv, last_exec or now_in_peru, processing_time_ms, status, error_message, execution_type))
            conn.commit()
            response.object = {"id_cia": id_cia, "id_report": id_report}
        except sqlite3.IntegrityError:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = f"Metadata logging failed: A report with id_cia={id_cia} and id_report={id_report} already exists."
        except sqlite3.Error as e:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = f"Failed to log metadata: {e}"
        finally:
            conn.close()
            return response

    def get_report_metadata(self, id_cia: int, object_name: str):
        # Retrieves metadata for a specific report based on id_cia and object_name.
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to the database.")
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_cia, id_report, name, cadsql, object_name_parquet, object_name_csv, last_exec, processing_time_ms, status, error_message
                FROM METADATA_REPORT
                WHERE id_cia = ? AND (object_name_parquet = ? OR object_name_csv = ?) AND status = 'OK'
            """, (id_cia, object_name, object_name))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving metadata: {e}")
            return None
        finally:
            conn.close()

    def get_latest_report_metadata(self, id_cia: int, id_report: int):
        # Retrieves the most recent metadata entry for a given id_cia and id_report.
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to the database.")
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_cia, id_report, name, cadsql, object_name_parquet, object_name_csv, last_exec, processing_time_ms, status, error_message
                FROM METADATA_REPORT
                WHERE id_cia = ? AND id_report = ? AND status = 'OK'
                ORDER BY last_exec DESC
                LIMIT 1
            """, (id_cia, id_report))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving latest metadata: {e}")
            return None
        finally:
            conn.close()

    def log_scheduler_event(self, job_id: str, event_type: str, message: str = None, 
                            id_cia: int = None, id_report: int = None, 
                            name: str = None, next_run_time: datetime = None,
                            duration_ms: int = None, status: str = None, company: str = None, 
                            refresh_time: int = None, schedule_type: str = None):
        # Logs events related to scheduled jobs into the SCHEDULED_JOBS_LOG table.
        # event_type can be 'job_added', 'job_removed', 'job_started', 'job_completed', 'job_failed'.
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to the database.")
            return
        try:
            peru_tz = pytz.timezone('America/Lima')
            now_in_peru = datetime.now(peru_tz)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO SCHEDULED_JOBS_LOG (
                    job_id, id_cia, id_report, name, company, 
                    event_type, timestamp, message, next_run_time, duration_ms, status,
                    refresh_time, schedule_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, id_cia, id_report, name, company, 
                event_type, now_in_peru, message, next_run_time, duration_ms, status,
                refresh_time, schedule_type
            ))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error logging scheduler event: {e}")
        finally:
            conn.close()

    def get_total_scheduled_reports_metadata(self) -> list[dict[str, Any]]: # Changed List[Dict[str, Any]] to list[dict[str, Any]]
        # Returns a list of all currently scheduled reports with their configuration details.
        # This data comes from the Oracle configuration, not the execution log.
        reports = ReportConfigLoader.get_reports_from_oracle()
        return [report.dict() for report in reports]

    def get_weekly_report_execution_details_metadata(self, id_cia: int = -1) -> list[dict[str, Any]]: # Changed List[Dict[str, Any]] to list[dict[str, Any]]
        # Returns a list of all report executions in the last week with their status and details.
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to the database.")
            return []
        try:
            cursor = conn.cursor()
            
            query = """
                SELECT
                    sj.job_id,
                    sj.id_cia,
                    sj.id_report,
                    sj.name,
                    sj.company,
                    sj.event_type,
                    sj.refresh_time,
                    sj.schedule_type,
                    sj.schedule_date,
                    mre.processing_time_ms AS last_execution_duration_ms,
                    mre.status AS last_execution_status,
                    mre.last_exec AS last_execution_time
                FROM
                    SCHEDULED_JOBS sj
                LEFT JOIN (
                    SELECT
                        id_cia,
                        id_report,
                        processing_time_ms,
                        status,
                        last_exec,
                        ROW_NUMBER() OVER (PARTITION BY id_cia, id_report ORDER BY last_exec DESC) as rn
                    FROM
                        METADATA_REPORT
                ) mre ON sj.id_cia = mre.id_cia
                     AND sj.id_report = mre.id_report
                     AND mre.rn = 1
                WHERE
                    0 = 0
            """
            
            params = []
            if id_cia != -1:
                query += " AND sj.id_cia = ?"
                params.append(id_cia)
                
            query += " ORDER BY sj.schedule_date DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving weekly execution details: {e}")
            return []
        finally:
            conn.close()

    def clean_old_scheduler_logs(self):
        # Deletes scheduler logs older than one week.
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to the database.")
            return
        try:
            peru_tz = pytz.timezone('America/Lima')
            now_in_peru = datetime.now(peru_tz)
            cursor = conn.cursor()
            one_week_ago = now_in_peru - timedelta(weeks=1)
            cursor.execute("DELETE FROM SCHEDULED_JOBS_LOG WHERE timestamp < ?", (one_week_ago,))
            conn.commit()
            logger.info(f"Cleaned old scheduler logs. Deleted {cursor.rowcount} entries.")
        except sqlite3.Error as e:
            logger.error(f"Error cleaning old scheduler logs: {e}")
        finally:
            conn.close()

    def cleanup_and_get_reports_to_reprocess(self, urgent_only=False):
        # Cleans up failed reports and identifies reports that need to be reprocessed.
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to the database.")
            return []
        try:
            peru_tz = pytz.timezone('America/Lima')
            cursor = conn.cursor()

            # 1. Delete failed reports
            cursor.execute("DELETE FROM METADATA_REPORT WHERE status = 'FAILED'")
            conn.commit()
            logger.info(f"Deleted {cursor.rowcount} failed reports from METADATA_REPORT.")

            # 2. Get all configured reports from Oracle
            all_reports = ReportConfigLoader.get_reports_from_oracle()
            reports_to_reprocess = []

            # Filter for urgent reports if requested
            reports_to_check = [r for r in all_reports if r.refreshtime <= 30] if urgent_only else all_reports

            for report in reports_to_check:
                # 3. Check for the latest successful execution of the report
                latest_successful_exec = self.get_latest_report_metadata(report.id_cia, report.id_report)

                if not latest_successful_exec:
                    # Reprocess if no successful execution exists
                    reports_to_reprocess.append(report)
                    logger.info(f"Report {report.name} marked for reprocessing (no successful execution found).")
                else:
                    # Reprocess if the report is outdated
                    last_exec_str = latest_successful_exec['last_exec']
                    # Convert string to datetime object
                    last_exec_time = datetime.fromisoformat(last_exec_str)
                    
                    # Ensure last_exec_time is offset-aware for comparison
                    if last_exec_time.tzinfo is None:
                        last_exec_time = last_exec_time.astimezone()

                    now_aware = datetime.now(peru_tz)
                    if now_aware - last_exec_time > timedelta(minutes=report.refreshtime):
                        reports_to_reprocess.append(report)
                        logger.info(f"Report {report.name} marked for reprocessing (outdated).")

            return reports_to_reprocess

        except sqlite3.Error as e:
            logger.error(f"Error during cleanup and reprocessing check: {e}")
            return []
        finally:
            conn.close()

    def get_deprecated_reports(self):
        # Identifies reports that need to be reprocessed without cleaning up existing data.
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to the database.")
            return []
        try:
            peru_tz = pytz.timezone('America/Lima')
            # 1. Get all configured reports from Oracle
            all_reports = ReportConfigLoader.get_reports_from_oracle()
            reports_to_reprocess = []

            for report in all_reports:
                # 2. Check for the latest successful execution of the report
                latest_successful_exec = self.get_latest_report_metadata(report.id_cia, report.id_report)

                if not latest_successful_exec:
                    # Reprocess if no successful execution exists
                    reports_to_reprocess.append(report)
                    logger.info(f"Report {report.name} marked for reprocessing (no successful execution found).")
                else:
                    # Reprocess if the report is outdated
                    last_exec_str = latest_successful_exec['last_exec']
                    # Convert string to datetime object
                    last_exec_time = datetime.fromisoformat(last_exec_str)
                    
                    # Ensure last_exec_time is offset-aware for comparison
                    if last_exec_time.tzinfo is None:
                        last_exec_time = last_exec_time.astimezone()

                    now_aware = datetime.now(peru_tz)
                    if now_aware - last_exec_time > timedelta(minutes=report.refreshtime):
                        reports_to_reprocess.append(report)
                        logger.info(f"Report {report.name} marked for reprocessing (outdated).")

            return reports_to_reprocess

        except sqlite3.Error as e:
            logger.error(f"Error during check for deprecated reports: {e}")
            return []
        finally:
            conn.close()

    def clear_scheduler_logs_on_startup(self):
        # Clears all entries from SCHEDULED_JOBS_LOG table. Used on application startup.
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to the database.")
            return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM SCHEDULED_JOBS_LOG")
            conn.commit()
            logger.info(f"Cleared SCHEDULED_JOBS_LOG table on startup. Deleted {cursor.rowcount} entries.")
        except sqlite3.Error as e:
            logger.error(f"Error clearing scheduler logs on startup: {e}")
        finally:
            conn.close()

    def add_scheduled_job(self, job_id, id_cia, id_report, name, company, event_type, refresh_time, schedule_type, schedule_date):
        # Adds or replaces a new scheduled job to the SCHEDULED_JOBS table.
        try:
            conn = get_db_connection()
            if not conn:
                raise sqlite3.Error("Failed to get database connection.")
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO SCHEDULED_JOBS (job_id, id_cia, id_report, name, company, event_type, refresh_time, schedule_type, schedule_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job_id, id_cia, id_report, name, company, event_type, refresh_time, schedule_type, schedule_date))
            
            conn.commit()
            conn.close()
            logger.info(f"Scheduled job {job_id} added or updated successfully.")
        except sqlite3.Error as e:
            logger.error(f"Failed to add or update scheduled job {job_id}: {e}")
            raise

    def get_executions_by_report(self, id_cia, id_report) -> list[dict[str, Any]]:
        """Returns a list of the last 100 report executions for a given report."""
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to the database.")
            return []
        try:
            params = [id_cia, id_report]
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id_cia,
                    id_report,
                    name,
                    cadsql,
                    object_name_parquet,
                    object_name_csv,
                    last_exec,
                    processing_time_ms,
                    status,
                    error_message,
                    execution_type
                FROM
                    METADATA_REPORT
                WHERE
                    id_cia = ?
                    AND id_report = ?
                ORDER BY
                    last_exec DESC
                LIMIT 100
            """, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving executions by report: {e}")
            return []
        finally:
            conn.close()


    def get_all_executions(self) -> list[dict[str, Any]]:
        """Returns a list of all report executions, ordered by last_exec DESC."""
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to the database.")
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id_cia,
                    id_report,
                    name,
                    cadsql,
                    object_name_parquet,
                    object_name_csv,
                    last_exec,
                    processing_time_ms,
                    status,
                    error_message
                FROM
                    METADATA_REPORT
                ORDER BY
                    last_exec DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all executions: {e}")
            return []
        finally:
            conn.close()

    def get_stale_reports(self) -> list[Any]:
        """
        Identifies reports that are considered 'stale'. A report is stale if it hasn't
        had a successful execution in more than twice its configured refresh interval.
        This version uses METADATA_REPORT for more reliable tracking.
        """
        logger.info("GUARDIAN: Checking for stale reports using METADATA_REPORT...")
        conn = get_db_connection()
        if not conn:
            logger.error("GUARDIAN: Could not connect to the database.")
            return []
        
        try:
            peru_tz = pytz.timezone('America/Lima')
            now = datetime.now(peru_tz)
            stale_reports = []

            cursor = conn.cursor()
            cursor.execute("SELECT job_id, id_cia, id_report, name, refresh_time, schedule_date FROM SCHEDULED_JOBS WHERE refresh_time <= 999")
            scheduled_jobs = cursor.fetchall()
            
            logger.info(f"GUARDIAN: Found {len(scheduled_jobs)} jobs in SCHEDULED_JOBS to check.")

            for job in scheduled_jobs:
                job_id = job['job_id']
                refresh_minutes = job['refresh_time']
                staleness_threshold = timedelta(minutes=(refresh_minutes * 2) + 5)

                latest_exec_meta = self.get_latest_report_metadata(job['id_cia'], job['id_report'])

                is_stale = False
                last_successful_exec = None
                staleness_duration = None

                if latest_exec_meta:
                    last_exec_time_str = latest_exec_meta['last_exec']
                    last_successful_exec = datetime.fromisoformat(last_exec_time_str).astimezone(peru_tz)
                    
                    if (now - last_successful_exec) > staleness_threshold:
                        is_stale = True
                        staleness_duration = now - last_successful_exec
                        logger.warning(f"GUARDIAN: Stale job detected! Job ID: {job_id}, Name: {job['name']}. Last successful exec: {last_exec_time_str}. Threshold: {staleness_threshold}.")
                else:
                    schedule_date = datetime.fromisoformat(job['schedule_date']).astimezone(peru_tz)
                    if (now - schedule_date) > staleness_threshold:
                        is_stale = True
                        staleness_duration = now - schedule_date
                        logger.warning(f"GUARDIAN: Stale job detected! Job ID: {job_id}, Name: {job['name']}. Job has never run successfully. Scheduled at: {job['schedule_date']}. Threshold: {staleness_threshold}.")

                if is_stale:
                    all_reports = ReportConfigLoader.get_reports_from_oracle()
                    found_report = next((r for r in all_reports if r.id_cia == job['id_cia'] and r.id_report == job['id_report']), None)
                    
                    if found_report:
                        found_report.last_successful_exec = last_successful_exec
                        found_report.staleness_duration_minutes = int(staleness_duration.total_seconds() / 60)
                        stale_reports.append(found_report)
                    else:
                        logger.error(f"GUARDIAN: Could not find full report configuration for stale job ID {job_id}.")

            return stale_reports

        except sqlite3.Error as e:
            logger.error(f"GUARDIAN: A database error occurred while checking for stale reports: {e}", exc_info=True)
            return []
        finally:
            if conn:
                conn.close()
            logger.info("GUARDIAN: Finished checking for stale reports.")

    def log_stale_job_report(self, stale_reports: list[Any]):
        """
        Logs a list of identified stale jobs into the STALE_JOBS_LOG table for auditing.
        """
        logger.info(f"GUARDIAN: Logging {len(stale_reports)} stale jobs to the database.")
        conn = get_db_connection()
        if not conn:
            logger.critical("GUARDIAN: CRITICAL - Cannot connect to DB to log stale jobs.")
            return

        try:
            peru_tz = pytz.timezone('America/Lima')
            now = datetime.now(peru_tz)
            cursor = conn.cursor()
            
            for report in stale_reports:
                job_id = f"report_{report.id_cia}_{report.id_report}"
                cursor.execute("""
                    INSERT INTO STALE_JOBS_LOG (
                        detection_timestamp, job_id, id_cia, id_report, name, 
                        last_successful_exec, refresh_time, staleness_duration_minutes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    now,
                    job_id,
                    report.id_cia,
                    report.id_report,
                    report.name,
                    report.last_successful_exec,
                    report.refreshtime,
                    report.staleness_duration_minutes
                ))
            
            conn.commit()
            logger.info(f"GUARDIAN: Successfully logged {len(stale_reports)} stale job entries.")
        except sqlite3.Error as e:
            logger.error(f"GUARDIAN: Failed to log stale jobs. Error: {e}", exc_info=True)
            # We do not re-raise the exception to ensure the guardian process can continue.
        finally:
            conn.close()

    def get_stale_job_logs(self) -> list[dict[str, Any]]:
        """Returns the last 500 entries from the stale jobs log."""
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to the database.")
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id, detection_timestamp, job_id, id_cia, id_report, name, 
                    last_successful_exec, refresh_time
                FROM STALE_JOBS_LOG
                ORDER BY detection_timestamp DESC
                LIMIT 500
            """,)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving stale job logs: {e}")
            return []
        finally:
            conn.close()

    def log_guardian_event(self, event_type: str, message: str = None, duration_ms: int = None):
        """Logs an event related to the guardian process itself."""
        conn = get_db_connection()
        if not conn:
            logger.error("GUARDIAN: Failed to connect to the database to log guardian event.")
            return
        try:
            peru_tz = pytz.timezone('America/Lima')
            now_in_peru = datetime.now(peru_tz)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO GUARDIAN_LOG (timestamp, event_type, message, duration_ms)
                VALUES (?, ?, ?, ?)
            """, (now_in_peru, event_type, message, duration_ms))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"GUARDIAN: Error logging guardian event: {e}")
        finally:
            conn.close()