
import logging
from concurrent.futures import ThreadPoolExecutor
from services.metadata_service import MetadataService
from scheduling.scheduler import run_scheduled_extraction
from configs.oracle import DB_ORACLE_POOL_MAX

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_reprocess_all_reports():
    """
    Forces the reprocessing of all reports by leveraging the existing
    cleanup_and_get_reports_to_reprocess logic from the MetadataService.
    """
    logger.info("Starting forced reprocessing of ALL reports.")
    
    metadata_service = MetadataService()
    
    # Get all reports that need reprocessing, not just urgent ones.
    reports_to_reprocess = metadata_service.cleanup_and_get_reports_to_reprocess(urgent_only=False)
    
    if not reports_to_reprocess:
        logger.info("No reports found to reprocess.")
        return

    logger.info(f"Found {len(reports_to_reprocess)} reports to reprocess. Starting parallel execution...")

    # Use a ThreadPoolExecutor to run extractions in parallel, similar to the scheduler startup.
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
            ) for report in reports_to_reprocess
        ]
        
        # Wait for all futures to complete
        for future in futures:
            try:
                future.result()
            except Exception as e:
                logger.error(f"An error occurred during a report reprocessing task: {e}", exc_info=True)

    logger.info("Forced reprocessing of all reports has been completed.")

if __name__ == "__main__":
    force_reprocess_all_reports()
