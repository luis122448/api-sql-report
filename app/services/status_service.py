from core.config_manager import ReportConfigManager
from schemas.api_response_schema import ApiResponseList

class StatusService:
    def __init__(self, report_config_manager: ReportConfigManager):
        self.report_config_manager = report_config_manager

    def get_report_status(self):
        report_configs = self.report_config_manager.get_report_configs()
        company_details = []
        for company_name, reports in report_configs.items():
            if reports:
                # Assuming all reports for a company have the same id_cia
                id_cia = reports[0].id_cia
                company_details.append({
                    "company_name": company_name,
                    "id_cia": id_cia,
                    "num_reports": len(reports)
                })

        return ApiResponseList(
            status=1.0,
            message="Report status retrieved successfully",
            list=company_details
        )
