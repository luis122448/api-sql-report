import time
from datetime import datetime
from fastapi import APIRouter, Depends, Response, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from services.extract_service import ExtractService
from services.metadata_service import MetadataService
from services.usage_service import UsageService
from auth.auth_handler import JWTBearer
from schemas.auth_schema import BasicAnalyticsSchema
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Analytics Reports"])

@router.get("/reports/last/{id_report}", dependencies=[Depends(JWTBearer())])

async def get_last_report(
    request: Request, # Add request: Request
    id_report: int,
    extract_service: ExtractService = Depends(),
    metadata_service: MetadataService = Depends(),
    usage_service: UsageService = Depends(), # Inject UsageService
    token: BasicAnalyticsSchema = Depends(JWTBearer()) # Inject token
):
    start_time = time.time()
    try:
        # Retrieves the latest generated report for a given company and report ID.
        # Get metadata first to check for last_exec and object_name
        metadata_entry = metadata_service.get_latest_report_metadata(token.id_cia, id_report)
        if not metadata_entry:
            error_response = { "status": 1.1, "message": "No metadata found for the given id_cia and id_report.", "log_user": token.coduser }
            return JSONResponse(content=jsonable_encoder(error_response), status_code=status.HTTP_404_NOT_FOUND)

        file_name = metadata_entry["object_name"]

        # Generate a presigned URL for the file
        presigned_url = extract_service.minio_service.generate_presigned_url(
            bucket_name="reports", 
            object_name=file_name
        )

        if not presigned_url:
            error_response = { "status": 1.1, "message": "Could not generate a presigned URL for the report.", "log_user": token.coduser }
            return JSONResponse(content=jsonable_encoder(error_response), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Return the presigned URL in a JSON response
        return JSONResponse(content={"status": 1, "url": presigned_url, "log_user": token.coduser})
    except Exception as e:
        return JSONResponse(content={"status":1.2, "message":f"Endpoint error: {str(e)}", "log_user": token.coduser}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        processing_time_ms = int((time.time() - start_time) * 1000)
        usage_service.log_api_request(
            id_cia=token.id_cia,
            id_report=id_report,
            requester_ip=request.client.host,
            endpoint=request.url.path,
            user_agent=request.headers.get("user-agent"),
            token_coduser=token.coduser,
            processing_time_ms=processing_time_ms
        )

@router.get("/reports/specified/{file_name}", dependencies=[Depends(JWTBearer())])

async def get_specified_report(
    request: Request, # Add request: Request
    file_name: str,
    extract_service: ExtractService = Depends(),
    metadata_service: MetadataService = Depends(),
    usage_service: UsageService = Depends(), # Inject UsageService
    token: BasicAnalyticsSchema = Depends(JWTBearer()) # Inject token
):
    start_time = time.time()
    try:
        # Retrieves a specific report by company ID and file name.
        # Get metadata first to check for last_exec
        metadata_entry = metadata_service.get_report_metadata(token.id_cia, file_name) # Use token.id_cia
        if not metadata_entry:
            error_response = { "status": 1.1, "message": "Metadata not found for the given id_cia and file_name.", "log_user": token.coduser }
            return JSONResponse(content=jsonable_encoder(error_response), status_code=status.HTTP_404_NOT_FOUND)

        # Generate a presigned URL for the file
        presigned_url = extract_service.minio_service.generate_presigned_url(
            bucket_name="reports", 
            object_name=file_name
        )

        if not presigned_url:
            error_response = { "status": 1.1, "message": "Could not generate a presigned URL for the report.", "log_user": token.coduser }
            return JSONResponse(content=jsonable_encoder(error_response), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Return the presigned URL in a JSON response
        return JSONResponse(content={"status": 1, "url": presigned_url, "log_user": token.coduser})
    except Exception as e:
        return JSONResponse(content={"status":1.2, "message":f"Endpoint error: {str(e)}", "log_user": token.coduser}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        processing_time_ms = int((time.time() - start_time) * 1000)
        usage_service.log_api_request(
            id_cia=token.id_cia,
            id_report=None, # No specific report ID in this endpoint
            requester_ip=request.client.host,
            endpoint=request.url.path,
            user_agent=request.headers.get("user-agent"),
            token_coduser=token.coduser,
            processing_time_ms=processing_time_ms
        )
