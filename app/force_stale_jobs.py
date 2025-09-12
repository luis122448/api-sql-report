
import logging
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the project root to the Python path to allow imports from other modules.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.metadata_service import MetadataService
from app.scheduling.tasks import run_scheduled_extraction
from configs.oracle import DB_ORACLE_POOL_MAX

# Configure logging for the script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def force_reprocess_stale_jobs():
    """
    Identifies and reprocesses stale jobs. A job is considered stale if it hasn't
    run in twice its configured refresh time. This function is designed to be
    resilient and provide a safety net for the main scheduler.
    """
    logger.info("GUARDIAN: Starting check for stale jobs...")
    
    try:
        metadata_service = MetadataService()
        
        # 1. Identify stale reports
        stale_reports = metadata_service.get_stale_reports()
        
        if not stale_reports:
            logger.info("GUARDIAN: No stale jobs found. All scheduled reports are running as expected.")
            return

        logger.warning(f"GUARDIAN: Found {len(stale_reports)} stale reports. Proceeding with logging and reprocessing.")

        # 2. Log the stale reports to the database for tracking
        try:
            metadata_service.log_stale_job_report(stale_reports)
            logger.info("GUARDIAN: Successfully logged stale report details to the database.")
        except Exception as e:
            logger.critical(f"GUARDIAN: CRITICAL FAILURE - Could not log stale jobs to database. Error: {e}", exc_info=True)
            # We continue to reprocessing, as it's the most critical part.

        # 3. Reprocess the stale reports in parallel
        logger.info(f"GUARDIAN: Starting parallel reprocessing of {len(stale_reports)} stale reports...")
        
        with ThreadPoolExecutor(max_workers=DB_ORACLE_POOL_MAX) as executor:
            # Create a future for each report reprocessing
            future_to_report = {
                executor.submit(
                    run_scheduled_extraction,
                    report.id_cia,
                    report.id_report,
                    report.name,
                    report.query,
                    report.company,
                    report.refreshtime,
                    execution_type='FORCE'
                ): report for report in stale_reports
            }
            
            for future in as_completed(future_to_report):
                report = future_to_report[future]
                try:
                    future.result()  # We call result() to raise any exceptions that occurred during execution
                    logger.info(f"GUARDIAN: Successfully reprocessed report: {report.name} (ID: {report.id_report})")
                except Exception as e:
                    logger.error(f"GUARDIAN: An error occurred during the forced reprocessing of report {report.id_report} ('{report.name}'). Error: {e}", exc_info=True)

        logger.info("GUARDIAN: Finished reprocessing all identified stale jobs.")

    except Exception as e:
        # This is a top-level catch to ensure the guardian itself never crashes the scheduler
        logger.critical(f"GUARDIAN: An unexpected critical error occurred in the stale job guardian. Error: {e}", exc_info=True)

if __name__ == "__main__":
    # This allows the script to be run manually for testing or emergency reprocessing.
    logger.info("GUARDIAN: Manual execution started.")
    force_reprocess_stale_jobs()
    logger.info("GUARDIAN: Manual execution finished.")
