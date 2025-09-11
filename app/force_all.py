import logging
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduling.report_config_loader import ReportConfigLoader
from scheduling.scheduler import run_scheduled_extraction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_reprocess_all_reports_sequentially():
    """
    Forces the reprocessing of ALL configured reports, one by one, to ensure data integrity.
    """
    logger.info("Starting forced sequential reprocessing of ALL configured reports.")
    
    all_reports = ReportConfigLoader.get_reports_from_oracle()
    
    if not all_reports:
        logger.info("No reports found in the configuration.")
        return

    logger.info(f"Found {len(all_reports)} total reports. Starting sequential execution...")

    # Run extractions sequentially to avoid any concurrency issues.
    for report in all_reports:
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

    logger.info("Forced sequential reprocessing of all configured reports has been completed.")

if __name__ == "__main__":
    force_reprocess_all_reports_sequentially()