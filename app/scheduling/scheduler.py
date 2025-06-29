import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from configs.oracle import OracleTransaction, get_oracle_connection
from services.extract_service import ExtractService
from services.minio_service import MinioService
from services.metadata_service import MetadataService
from scheduling.report_config_loader import ReportConfigLoader, Report
from configs.minio import MinioConfig # Import MinioConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
metadata_service = MetadataService() # Instantiate MetadataService once

# Instantiate MinioConfig and then MinioService
minio_config_instance = MinioConfig()
minio_service = MinioService(minio_config=minio_config_instance) # Pass the instance

def run_scheduled_extraction(id_cia: int, id_report: int, name: str, query: str, company: str):
    # Executes the extraction pipeline for a given report.
    # This function is called by the scheduler.
    job_id = f"report_{id_cia}_{id_report}"
    start_time = datetime.now()
    
    metadata_service.log_scheduler_event(
        job_id=job_id, 
        report_id_cia=id_cia, 
        report_id_report=id_report, 
        report_name=name, 
        report_company=company, # Pass company here
        event_type='job_started',
        message=f"Starting extraction for Report ID: {id_report}"
    )
    logger.info(f"Starting scheduled extraction for Report ID: {id_report}, Name: {name}")
    try:
        # Manually instantiate dependencies for ExtractService
        oracle_connection = get_oracle_connection()
        oracle_transaction = OracleTransaction()
        oracle_transaction.connection = oracle_connection # Set the connection manually
        
        # Use the already instantiated minio_service and metadata_service
        extract_service = ExtractService(
            oracle=oracle_transaction, 
            minio_service=minio_service, 
            metadata_service=metadata_service
        )
        
        result = extract_service.run_extraction_pipeline(id_cia, id_report, name, query, company) # Pass company to pipeline
        
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        if result.status == 1:
            metadata_service.log_scheduler_event(
                job_id=job_id, 
                report_id_cia=id_cia, 
                report_id_report=id_report, 
                report_name=name, 
                report_company=company, # Pass company here
                event_type='job_completed',
                message=f"Extraction for Report ID: {id_report} completed successfully.",
                duration_ms=duration_ms,
                status='success'
            )
            logger.info(f"Scheduled extraction for Report ID: {id_report} completed successfully.")
        else:
            metadata_service.log_scheduler_event(
                job_id=job_id, 
                report_id_cia=id_cia, 
                report_id_report=id_report, 
                report_name=name, 
                report_company=company, # Pass company here
                event_type='job_failed',
                message=f"Extraction for Report ID: {id_report} failed: {result.log_message}",
                duration_ms=duration_ms,
                status='failed'
            )
            logger.error(f"Scheduled extraction for Report ID: {id_report} failed: {result.log_message}")
    except Exception as e:
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        metadata_service.log_scheduler_event(
            job_id=job_id, 
            report_id_cia=id_cia, 
            report_id_report=id_report, 
            report_name=name, 
            report_company=company, # Pass company here
            event_type='job_failed',
            message=f"Unhandled error during scheduled extraction for Report ID: {id_report}: {e}",
            duration_ms=duration_ms,
            status='failed'
        )
        logger.error(f"Unhandled error during scheduled extraction for Report ID: {id_report}: {e}")
    finally:
        if 'oracle_connection' in locals() and oracle_connection:
            oracle_connection.close()

def update_scheduled_jobs():
    # Updates the scheduler's jobs based on the latest configuration from Oracle.
    # This function is called periodically by the scheduler itself.
    logger.info("Updating scheduled jobs from Oracle configuration...")
    current_reports = ReportConfigLoader.get_reports_from_oracle()
    current_job_ids = {job.id for job in scheduler.get_jobs()}
    
    new_report_ids = set()
    for report in current_reports:
        job_id = f"report_{report.id_cia}_{report.id_report}"
        new_report_ids.add(job_id)
        
        if job_id in current_job_ids:
            # Check if job needs to be updated (e.g., refreshtime changed)
            existing_job = scheduler.get_job(job_id)
            # This is a simplified check. A more robust solution would compare all relevant parameters.
            # For now, we'll just re-add it, which will replace the existing one if replace_existing=True.
            scheduler.remove_job(job_id)
            metadata_service.log_scheduler_event(
                job_id=job_id, 
                report_id_cia=report.id_cia, 
                report_id_report=report.id_report, 
                report_name=report.name, 
                report_company=report.company, # Pass company here
                event_type='job_updated',
                message=f"Job {job_id} updated due to configuration change."
            )
            logger.info(f"Removed existing job {job_id} for update.")

        # Add or re-add the job
        if report.refreshtime > 999:
            trigger = CronTrigger(hour=3, minute=0)
            scheduler.add_job(
                run_scheduled_extraction,
                trigger,
                args=[report.id_cia, report.id_report, report.name, report.query, report.company], # Pass company here
                id=job_id,
                name=f"Daily Report {report.name}",
                replace_existing=True
            )
            metadata_service.log_scheduler_event(
                job_id=job_id, 
                report_id_cia=report.id_cia, 
                report_id_report=report.id_report, 
                report_name=report.name, 
                report_company=report.company, # Pass company here
                event_type='job_added',
                message=f"Scheduled daily job at 03:00 AM."
                # next_run_time=added_job.next_run_time # Removed this line
            )
            logger.info(f"Scheduled daily job for Report ID: {report.id_report} (Name: {report.name}) at 03:00 AM.")
        else:
            trigger = IntervalTrigger(minutes=report.refreshtime)
            scheduler.add_job(
                run_scheduled_extraction,
                trigger,
                args=[report.id_cia, report.id_report, report.name, report.query, report.company], # Pass company here
                id=job_id,
                name=f"Interval Report {report.name}",
                replace_existing=True
            )
            metadata_service.log_scheduler_event(
                job_id=job_id, 
                report_id_cia=report.id_cia, 
                report_id_report=report.id_report, 
                report_name=report.name, 
                report_company=report.company, # Pass company here
                event_type='job_added',
                message=f"Scheduled interval job every {report.refreshtime} minutes."
                # next_run_time=added_job.next_run_time # Removed this line
            )
            logger.info(f"Scheduled interval job for Report ID: {report.id_report} (Name: {report.name}) every {report.refreshtime} minutes.")

    # Remove jobs that are no longer in the Oracle configuration
    jobs_to_remove = current_job_ids - new_report_ids
    for job_id in jobs_to_remove:
        if job_id.startswith("report_") : # Ensure we only remove report jobs, not the update_scheduled_jobs job itself
            scheduler.remove_job(job_id)
            metadata_service.log_scheduler_event(
                job_id=job_id, 
                event_type='job_removed',
                message=f"Job {job_id} removed as it's no longer in Oracle configuration."
            )
            logger.info(f"Removed job {job_id} as it's no longer in Oracle configuration.")

def start_scheduler():
    # Initializes and starts the APScheduler, scheduling reports based on Oracle configuration.
    logger.info("Starting report scheduler...")
    
    # Schedule the initial load and subsequent updates
    scheduler.add_job(
        update_scheduled_jobs,
        IntervalTrigger(minutes=60), # Update every 60 minutes
        id='update_job_config',
        name='Update Report Configurations',
        replace_existing=True
    )
    logger.info("Scheduled job to update report configurations every 60 minutes.")

    # Schedule daily cleanup for scheduler logs
    scheduler.add_job(
        metadata_service.clean_old_scheduler_logs,
        CronTrigger(hour=4, minute=0), # Run daily at 4 AM
        id='clean_scheduler_logs',
        name='Clean Old Scheduler Logs',
        replace_existing=True
    )
    logger.info("Scheduled daily cleanup for old scheduler logs at 04:00 AM.")

    # Schedule daily cleanup for Minio objects
    scheduler.add_job(
        minio_service.clean_old_minio_objects,
        CronTrigger(hour=5, minute=0), # Run daily at 5 AM
        id='clean_minio_objects',
        name='Clean Old Minio Objects',
        replace_existing=True
    )
    logger.info("Scheduled daily cleanup for old Minio objects at 05:00 AM.")

    # Run the initial update immediately
    update_scheduled_jobs()

    scheduler.start()
    logger.info("Scheduler started successfully with configured jobs.")

def stop_scheduler():
    # Shuts down the APScheduler.
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down.")
    else:
        logger.info("Scheduler is not running.")
