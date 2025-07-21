from fastapi import APIRouter, Depends
from services.metadata_service import MetadataService
from schemas.api_response_schema import ApiResponseList
from schemas.api_response_schema import ApiResponseObject
from services.status_service import StatusService
from core.config_manager import ReportConfigManager

router = APIRouter(tags=["Metadata & Dashboard"])

def get_status_service(report_config_manager: ReportConfigManager = Depends(ReportConfigManager)):
    return StatusService(report_config_manager)

@router.get("/dashboard/total_scheduled_reports", response_model=ApiResponseList)
async def get_total_scheduled_reports(metadata_service: MetadataService = Depends()):
    # Returns a list of all currently scheduled reports with their configuration details.
    reports = metadata_service.get_total_scheduled_reports_metadata()
    return ApiResponseList(status=1, message="OK", list=reports)

@router.get("/dashboard/weekly_execution_details", response_model=ApiResponseList)
async def get_weekly_report_execution_details(metadata_service: MetadataService = Depends()):
    # Returns a list of all report executions in the last week with their status and details.
    executions = metadata_service.get_weekly_report_execution_details_metadata()
    return ApiResponseList(status=1, message="OK", list=executions)

@router.get("/dashboard/status", response_model=ApiResponseObject)
async def get_reports_status(report_config_manager: ReportConfigManager = Depends(ReportConfigManager)):
    status_service = StatusService(report_config_manager)
    return status_service.get_report_status()