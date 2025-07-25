from fastapi import APIRouter, Depends
from services.metadata_service import MetadataService
from schemas.api_response_schema import ApiResponseList
from services.status_service import StatusService
from core.config_manager import ReportConfigManager

router = APIRouter(tags=["Metadata & Dashboard"])

def get_status_service(report_config_manager: ReportConfigManager = Depends(ReportConfigManager)):
    return StatusService(report_config_manager)

@router.get("/dashboard/total_scheduled_reports", response_model=ApiResponseList)
async def get_total_scheduled_reports(metadata_service: MetadataService = Depends()):
    reports = metadata_service.get_total_scheduled_reports_metadata()
    return ApiResponseList(status=1, message="OK", list=reports)

@router.get("/dashboard/last_execution_details", response_model=ApiResponseList)
async def get_weekly_report_execution_details(id_cia: int = -1, metadata_service: MetadataService = Depends()):
    executions = metadata_service.get_weekly_report_execution_details_metadata(id_cia)
    return ApiResponseList(status=1, message="OK", list=executions)

@router.get("/dashboard/status", response_model=ApiResponseList)
async def get_reports_status(report_config_manager: ReportConfigManager = Depends(ReportConfigManager)):
    status_service = StatusService(report_config_manager)
    return status_service.get_report_status()

@router.get("/dashboard/executions_by_report", response_model=ApiResponseList)
async def get_executions_by_report(id_cia: int, id_report: int, metadata_service: MetadataService = Depends()):
    executions = metadata_service.get_executions_by_report(id_cia, id_report)
    return ApiResponseList(status=1, message="OK", list=executions)