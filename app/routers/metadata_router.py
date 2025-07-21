from fastapi import APIRouter, Depends
from services.metadata_service import MetadataService
from schemas.api_response_schema import ApiResponseList

router = APIRouter(tags=["Metadata & Dashboard"])

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
