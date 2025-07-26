
import logging
from concurrent.futures import ThreadPoolExecutor
from app.scheduling.report_config_loader import ReportConfigLoader
from app.scheduling.scheduler import run_scheduled_extraction
from app.configs.oracle import DB_ORACLE_POOL_MAX

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_reprocess_all_reports_unconditionally():
    """
    Forces the reprocessing of ALL configured reports, regardless of their current status.
    """
    logger.info("Starting forced reprocessing of ALL configured reports.")
    
    # Get all reports directly from the configuration source.
    all_reports = ReportConfigLoader.get_reports_from_oracle()
    
    if not all_reports:
        logger.info("No reports found in the configuration.")
        return

    logger.info(f"Found {len(all_reports)} total reports. Starting unconditional parallel execution...")

    # Use a ThreadPoolExecutor to run extractions in parallel.
    with ThreadPoolExecutor(max_workers=DB_ORACLE_POOL_MAX) as executor:
        futures = [
            executor.submit(
                run_scheduled_extraction,
                report.id_cia,
                report.id_report,
                report.name,
                report.query,
                report.company,
                report.refreshtime
            ) for report in all_reports
        ]
        
        # Wait for all futures to complete
        for future in futures:
            try:
                future.result()
            except Exception as e:
                logger.error(f"An error occurred during a report reprocessing task: {e}", exc_info=True)

    logger.info("Forced reprocessing of all configured reports has been completed.")

if __name__ == "__main__":
    force_reprocess_all_reports_unconditionally()
