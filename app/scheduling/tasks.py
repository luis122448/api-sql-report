
import logging
import pytz
from datetime import datetime

from configs.oracle import OracleTransaction
from services.extract_service import ExtractService
from services.metadata_service import MetadataService

logger = logging.getLogger(__name__)

def run_scheduled_extraction(id_cia: int, id_report: int, name: str, query: str, company: str, refreshtime: int, execution_type: str = 'AUTO'):
    """
    Executes the extraction pipeline for a given report.
    This function is designed to be called by the scheduler or other processes and must be thread-safe.
    """
    job_id = f"report_{id_cia}_{id_report}"
    peru_tz = pytz.timezone('America/Lima')
    start_time = datetime.now(peru_tz)
    logger.info(f"TASK: Starting job {job_id} for report '{name}' (Type: {execution_type}).")

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
        logger.info(f"TASK: Instantiating dependencies for job {job_id}.")
        oracle_transaction = OracleTransaction()
        logger.debug(f"TASK: OracleTransaction created for job {job_id}.")

        extract_service = ExtractService(
            oracle=oracle_transaction,
            metadata_service=metadata_service
        )
        logger.debug(f"TASK: ExtractService created for job {job_id}.")

        logger.info(f"TASK: Running extraction pipeline for job {job_id}.")
        result = extract_service.run_extraction_pipeline(id_cia, id_report, name, query, company, execution_type=execution_type)
        logger.debug(f"TASK: Extraction pipeline finished for job {job_id} with status {result.status}.")

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
            logger.info(f"TASK: Job {job_id} completed successfully.")
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
            logger.error(f"TASK: Job {job_id} failed during pipeline execution: {result.log_message}")

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
        logger.error(f"TASK: Unhandled exception in job {job_id}. Error: {e}", exc_info=True)

    finally:
        if oracle_transaction and oracle_transaction.connection:
            logger.debug(f"TASK: Closing Oracle connection for job {job_id}.")
            oracle_transaction.connection.close()
            logger.debug(f"TASK: Oracle connection closed for job {job_id}.")
        logger.info(f"TASK: Finished job {job_id}.")
