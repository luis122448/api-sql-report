from fastapi import APIRouter, Depends
from services.usage_service import UsageService
from schemas.api_response_schema import ApiResponseList

router = APIRouter(tags=["Usage Analytics"])

@router.get("/usage/summary/top-reports", response_model=ApiResponseList)
def get_top_reports(id_cia: int = -1, usage_service: UsageService = Depends()):
    return usage_service.get_top_reports(id_cia)

@router.get("/usage/detail/{id_cia}/{id_report}", response_model=ApiResponseList)
def get_usage_details(id_cia: int, id_report: int, usage_service: UsageService = Depends()):
    return usage_service.get_usage_details(id_cia, id_report)
