import logging
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.metadata_service import MetadataService
from app.scheduling.scheduler import run_scheduled_extraction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_reprocess_deprecated_reports_sequentially():
    """
    Forces the reprocessing of reports that are outdated, one by one, to ensure data integrity.
    """
    logger.info("Starting forced sequential reprocessing of deprecated reports.")
    
    metadata_service = MetadataService()
    
    reports_to_reprocess = metadata_service.get_deprecated_reports()
    
    if not reports_to_reprocess:
        logger.info("No deprecated reports found to reprocess.")
        return

    logger.info(f"Found {len(reports_to_reprocess)} deprecated reports to reprocess. Starting sequential execution...")

    # Run extractions sequentially to avoid any concurrency issues.
    for report in reports_to_reprocess:
        try:
            logger.info(f"--- Processing report: {report.name} (ID: {report.id_report}) ---")
            run_scheduled_extraction(
                report.id_cia,
                report.id_report,
                report.name,
                report.query,
                report.company,
                report.refreshtime
            )
            logger.info(f"--- Finished report: {report.name} (ID: {report.id_report}) ---")
        except Exception as e:
            logger.error(f"An error occurred during the reprocessing of report {report.id_report}: {e}", exc_info=True)

    logger.info("Forced sequential reprocessing of deprecated reports has been completed.")

if __name__ == "__main__":
    force_reprocess_deprecated_reports_sequentially()
