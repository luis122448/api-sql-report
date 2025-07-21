from fastapi import APIRouter, Depends
from schemas.api_response_schema import ApiResponseObject
from services.status_service import StatusService
from core.config_manager import ReportConfigManager

status_router = APIRouter()

def get_status_service(report_config_manager: ReportConfigManager = Depends(ReportConfigManager)):
    return StatusService(report_config_manager)

@status_router.get("/status/reports", response_model=ApiResponseObject)
async def get_reports_status(status_service: StatusService = Depends(get_status_service)):
    return status_service.get_report_status()
