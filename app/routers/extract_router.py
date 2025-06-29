from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from services.extract_service import ExtractService
from schemas.api_response_schema import ApiResponseObject
from pydantic import BaseModel

class ExtractionRequest(BaseModel):
    id_cia: int
    id_report: int
    name: str
    query: str

router = APIRouter()

@router.post("/extract", response_model=ApiResponseObject)
def extract_data(
    request: ExtractionRequest,
    extract_service: ExtractService = Depends(),
):
    response = extract_service.run_extraction_pipeline(
        id_cia=request.id_cia,
        id_report=request.id_report,
        name=request.name,
        query=request.query
    )
    return response



