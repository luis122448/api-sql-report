from fastapi import APIRouter, Depends, Response, status, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from services.extract_service import ExtractService
from schemas.api_response_schema import ApiResponseObject
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

class ExtractionRequest(BaseModel):
    id_cia: int
    id_report: int
    name: str
    query: str

router = APIRouter(tags=["Pipeline Extraction"])

@router.post("/extract", response_model=ApiResponseObject)
@limiter.limit("4/minute")
def extract_data(
    request: Request, # Add request: Request
    extraction_request: ExtractionRequest, # Rename request to extraction_request
    extract_service: ExtractService = Depends(),
):
    response = extract_service.run_extraction_pipeline(
        id_cia=extraction_request.id_cia,
        id_report=extraction_request.id_report,
        name=extraction_request.name,
        query=extraction_request.query
    )
    return response



