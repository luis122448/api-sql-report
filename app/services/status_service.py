from core.config_manager import ReportConfigManager

class StatusService:
    def __init__(self, report_config_manager: ReportConfigManager):
        self.report_config_manager = report_config_manager

    def get_report_status(self):
        report_configs = self.report_config_manager.get_report_configs()
        company_details = {}
        for company_name, reports in report_configs.items():
            company_details[company_name] = len(reports)

        num_companies = len(report_configs)
        num_reports = sum(len(reports) for reports in report_configs.values())
        from app.schemas.api_response_schema import ApiResponseObject

        return ApiResponseObject(
            status=1.0,
            message="Report status retrieved successfully",
            object={
                "num_companies_configured": num_companies,
                "num_reports_configured": num_reports,
                "company_details": company_details
            }
        )
