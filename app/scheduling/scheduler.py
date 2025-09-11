
import logging
import pytz
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from configs.oracle import OracleTransaction, DB_ORACLE_POOL_MAX
from services.extract_service import ExtractService
from services.minio_service import MinioService
from services.metadata_service import MetadataService
from scheduling.report_config_loader import ReportConfigLoader
from core.config_manager import ReportConfigManager
from configs.minio import MinioConfig
from force_stale_jobs import force_reprocess_stale_jobs

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

# MinioService can be a singleton if its methods are thread-safe.
# Assuming Minio client is thread-safe, which is common.
minio_config_instance = MinioConfig()
minio_service = MinioService(minio_config=minio_config_instance)


def job_listener(event):
    """Listens to scheduler events and logs them."""
    if event.exception:
        logger.error(f"SCHEDULER_EVENT: Job {event.job_id} crashed: {event.exception}", exc_info=True)
    elif event.code == EVENT_JOB_MISSED:
        logger.warning(f"SCHEDULER_EVENT: Job {event.job_id} was missed.")
    elif event.code == EVENT_JOB_EXECUTED:
        logger.info(f"SCHEDULER_EVENT: Job {event.job_id} executed successfully.")
    else:
        logger.info(f"SCHEDULER_EVENT: Job {event.job_id} event: {event.code}")


def run_scheduled_extraction(id_cia: int, id_report: int, name: str, query: str, company: str, refreshtime: int):
    """
    Executes the extraction pipeline for a given report.
    This function is called by the scheduler and must be thread-safe.
    """
    job_id = f"report_{id_cia}_{id_report}"
    peru_tz = pytz.timezone('America/Lima')
    start_time = datetime.now(peru_tz)
    logger.info(f"SCHEDULER: Starting job {job_id} for report '{name}'.")

    # Instantiate services locally for thread safety.
    metadata_service = MetadataService()

    schedule_type = ""
    if refreshtime > 999:
        schedule_type = "Daily"
    elif refreshtime >= 60:
        schedule_type = "Hourly"
    else:
        schedule_type = "High-Frequency"

    metadata_service.log_scheduler_event(
        job_id=job_id,
        id_cia=id_cia,
        id_report=id_report,
        name=name,
        company=company,
        event_type='job_started',
        message=f"Starting extraction for Report ID: {id_report}",
        refresh_time=refreshtime,
        schedule_type=schedule_type
    )

    oracle_transaction = None
    try:
        logger.info(f"SCHEDULER: Instantiating dependencies for job {job_id}.")
        oracle_transaction = OracleTransaction()
        logger.debug(f"SCHEDULER: OracleTransaction created for job {job_id}.")

        # Pass the local, thread-safe instance of MetadataService.
        extract_service = ExtractService(
            oracle=oracle_transaction,
            metadata_service=metadata_service
        )
        logger.debug(f"SCHEDULER: ExtractService created for job {job_id}.")

        logger.info(f"SCHEDULER: Running extraction pipeline for job {job_id}.")
        result = extract_service.run_extraction_pipeline(id_cia, id_report, name, query, company)
        logger.debug(f"SCHEDULER: Extraction pipeline finished for job {job_id} with status {result.status}.")

        end_time = datetime.now(peru_tz)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        if result.status == 1:
            metadata_service.log_scheduler_event(
                job_id=job_id,
                id_cia=id_cia,
                id_report=id_report,
                name=name,
                company=company,
                event_type='job_completed',
                message=f"Extraction for Report ID: {id_report} completed successfully.",
                duration_ms=duration_ms,
                status='success'
            )
            logger.info(f"SCHEDULER: Job {job_id} completed successfully.")
        else:
            metadata_service.log_scheduler_event(
                job_id=job_id,
                id_cia=id_cia,
                id_report=id_report,
                name=name,
                company=company,
                event_type='job_failed',
                message=f"Extraction for Report ID: {id_report} failed: {result.log_message}",
                duration_ms=duration_ms,
                status='failed'
            )
            logger.error(f"SCHEDULER: Job {job_id} failed during pipeline execution: {result.log_message}")

    except Exception as e:
        end_time = datetime.now(peru_tz)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        metadata_service.log_scheduler_event(
            job_id=job_id,
            id_cia=id_cia,
            id_report=id_report,
            name=name,
            company=company,
            event_type='job_failed',
            message=f"Unhandled error during scheduled extraction for Report ID: {id_report}: {e}",
            duration_ms=duration_ms,
            status='failed'
        )
        logger.error(f"SCHEDULER: Unhandled exception in job {job_id}. Error: {e}", exc_info=True)

    finally:
        if oracle_transaction and oracle_transaction.connection:
            logger.debug(f"SCHEDULER: Closing Oracle connection for job {job_id}.")
            oracle_transaction.connection.close()
            logger.debug(f"SCHEDULER: Oracle connection closed for job {job_id}.")
        logger.info(f"SCHEDULER: Finished job {job_id}.")


def _clean_old_scheduler_logs_job():
    """Wrapper function to ensure MetadataService is instantiated locally for the job."""
    logger.info("Running scheduled job to clean old scheduler logs.")
    metadata_service = MetadataService()
    metadata_service.clean_old_scheduler_logs()


def update_scheduled_jobs():
    """
    Updates the scheduler's jobs based on the latest configuration from Oracle.
    """
    logger.info("Updating scheduled jobs from Oracle configuration...")
    # Use a local instance of MetadataService for thread safety.
    metadata_service = MetadataService()
    current_reports = ReportConfigLoader.get_reports_from_oracle()
    peru_tz = pytz.timezone('America/Lima')

    # Create Minio buckets for each company based on id_cia
    id_cias = {report.id_cia for report in current_reports if report.id_cia}
    for id_cia in id_cias:
        try:
            bucket_name = f"bucket-{id_cia}"
            minio_service.create_bucket(bucket_name)
        except Exception as e:
            logger.error(f"Error creating bucket for id_cia {id_cia}: {e}")

    grouped_reports = {}
    for report in current_reports:
        if report.company not in grouped_reports:
            grouped_reports[report.company] = []
        grouped_reports[report.company].append(report)

    report_config_manager = ReportConfigManager()
    report_config_manager.set_report_configs(grouped_reports)

    current_job_ids = {job.id for job in scheduler.get_jobs()}
    new_report_ids = set()

    for report in current_reports:
        job_id = f"report_{report.id_cia}_{report.id_report}"
        new_report_ids.add(job_id)

        schedule_type = ""
        if report.refreshtime > 999:
            schedule_type = "Daily"
        elif report.refreshtime >= 60:
            schedule_type = "Hourly"
        else:
            schedule_type = "High-Frequency"

        if job_id in current_job_ids:
            scheduler.remove_job(job_id)
            metadata_service.log_scheduler_event(
                job_id=job_id, id_cia=report.id_cia, id_report=report.id_report,
                name=report.name, company=report.company, event_type='job_updated',
                message=f"Job {job_id} updated due to configuration change.",
                refresh_time=report.refreshtime, schedule_type=schedule_type
            )
            logger.info(f"Removed existing job {job_id} for update.")

        trigger_args = {
            'args': [report.id_cia, report.id_report, report.name, report.query, report.company, report.refreshtime],
            'id': job_id,
            'name': f"Report {report.name}",
            'replace_existing': True
        }
        if report.refreshtime > 999:
            trigger = CronTrigger(hour=3, minute=0, timezone=peru_tz)
            scheduler.add_job(run_scheduled_extraction, trigger, **trigger_args)
            log_message = "Scheduled daily job at 03:00 AM."
        else:
            trigger = IntervalTrigger(minutes=report.refreshtime, timezone=peru_tz)
            scheduler.add_job(run_scheduled_extraction, trigger, **trigger_args)
            log_message = f"Scheduled interval job every {report.refreshtime} minutes."

        metadata_service.log_scheduler_event(
            job_id=job_id, id_cia=report.id_cia, id_report=report.id_report,
            name=report.name, company=report.company, event_type='job_added',
            message=log_message, refresh_time=report.refreshtime, schedule_type=schedule_type
        )
        logger.info(f"Scheduled job for Report ID: {report.id_report} (Name: {report.name}). {log_message}")

        metadata_service.add_scheduled_job(
            job_id=job_id, id_cia=report.id_cia, id_report=report.id_report,
            name=report.name, company=report.company, event_type='job_added',
            refresh_time=report.refreshtime, schedule_type=schedule_type,
            schedule_date=datetime.now(peru_tz)
        )

    jobs_to_remove = current_job_ids - new_report_ids
    for job_id in jobs_to_remove:
        if job_id.startswith("report_"):
            scheduler.remove_job(job_id)
            metadata_service.log_scheduler_event(
                job_id=job_id, event_type='job_removed',
                message=f"Job {job_id} removed as it's no longer in Oracle configuration."
            )
            logger.info(f"Removed job {job_id} as it's no longer in Oracle configuration.")


def start_scheduler():
    """Initializes and starts the APScheduler."""
    logger.info("Starting report scheduler...")
    peru_tz = pytz.timezone('America/Lima')

    # Add event listener
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)
    logger.info("Added scheduler event listener.")

    # Use a local instance of MetadataService for thread safety.
    metadata_service = MetadataService()
    metadata_service.clear_scheduler_logs_on_startup()
    logger.info("Cleared SCHEDULED_JOBS_LOG on startup.")

    logger.info("Starting cleanup and initial parallel execution of URGENT reports...")
    reports_to_run = metadata_service.cleanup_and_get_reports_to_reprocess(urgent_only=True)

    with ThreadPoolExecutor(max_workers=DB_ORACLE_POOL_MAX) as executor:
        futures = [executor.submit(run_scheduled_extraction, r.id_cia, r.id_report, r.name, r.query, r.company, r.refreshtime) for r in reports_to_run]
        for future in futures:
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error during initial report execution: {e}")

    logger.info("Initial parallel execution of URGENT reports finished.")

    scheduler.add_job(
        update_scheduled_jobs,
        IntervalTrigger(minutes=60, timezone=peru_tz),
        id='update_job_config',
        name='Update Report Configurations',
        replace_existing=True
    )
    logger.info("Scheduled job to update report configurations every 60 minutes.")

    scheduler.add_job(
        _clean_old_scheduler_logs_job,
        CronTrigger(hour=4, minute=0),
        id='clean_scheduler_logs',
        name='Clean Old Scheduler Logs',
        replace_existing=True
    )
    logger.info("Scheduled daily cleanup for old scheduler logs at 04:00 AM.")

    scheduler.add_job(
        minio_service.clean_old_minio_objects,
        CronTrigger(hour=5, minute=0),
        id='clean_minio_objects',
        name='Clean Old Minio Objects',
        replace_existing=True
    )
    logger.info("Scheduled daily cleanup for old Minio objects at 05:00 AM.")

    # Add the guardian job to check for and reprocess stale jobs
    scheduler.add_job(
        force_reprocess_stale_jobs,
        IntervalTrigger(minutes=30, timezone=peru_tz),
        id='guardian_stale_job_check',
        name='Guardian: Check for Stale Jobs',
        replace_existing=True
    )
    logger.info("Scheduled guardian job to check for stale reports every 30 minutes.")

    update_scheduled_jobs()

    scheduler.start()
    logger.info("Scheduler started successfully with configured jobs.")


def stop_scheduler():
    """Shuts down the APScheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down.")
    else:
        logger.info("Scheduler is not running.")
