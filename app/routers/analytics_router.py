from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from services.extract_service import ExtractService
from services.metadata_service import MetadataService
from typing import Dict, Any
from auth.auth_handler import JWTBearer
from schemas.auth_schema import BasicAnalyticsSchema

router = APIRouter(tags=["Analytics Reports"])

@router.get("/reports/last/{id_report}", dependencies=[Depends(JWTBearer())])
async def get_last_report(
    id_report: int,
    extract_service: ExtractService = Depends(),
    metadata_service: MetadataService = Depends(),
    token: BasicAnalyticsSchema = Depends(JWTBearer()) # Inject token
):
    # Retrieves the latest generated report for a given company and report ID.
    try:
        # Get metadata first to check for last_exec and object_name
        metadata_entry = metadata_service.get_latest_report_metadata(token.id_cia, id_report)
        if not metadata_entry:
            error_response = { "status": 1.1, "message": "No metadata found for the given id_cia and id_report.", "log_user": token.coduser }
            return JSONResponse(content=jsonable_encoder(error_response), status_code=status.HTTP_404_NOT_FOUND)

        file_name = metadata_entry["object_name"]
        last_etl_exec = metadata_entry["last_exec"]

        parquet_data, error_details = extract_service.minio_service.download_file(bucket_name="reports", object_name=file_name)

        if error_details:
            return JSONResponse(content=jsonable_encoder(error_details), status_code=error_details.get("status_code", status.HTTP_400_BAD_REQUEST))
        
        if not parquet_data:
            error_response = { "status": 1.1, "message": "Parquet file not found in Minio or could not be downloaded.", "log_user": token.coduser }
            return JSONResponse(content=jsonable_encoder(error_response), status_code=status.HTTP_404_NOT_FOUND)

        headers = {"X-Log-User": token.coduser, "X-Days-To-Token-Expire": str(token.days_to_token_expire)}
        if last_etl_exec: headers["X-Last-Etl-Exec"] = last_etl_exec.isoformat()

        return Response(content=parquet_data, media_type="application/vnd.apache.parquet", headers=headers)
    except Exception as e:
        return JSONResponse(content={"status":1.2, "message":f"Endpoint error: {str(e)}", "log_user": token.coduser}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/reports/specified/{file_name}", dependencies=[Depends(JWTBearer())])
async def get_specified_report(
    file_name: str,
    extract_service: ExtractService = Depends(),
    metadata_service: MetadataService = Depends(),
    token: BasicAnalyticsSchema = Depends(JWTBearer()) # Inject token
):
    # Retrieves a specific report by company ID and file name.
    try:
        # Get metadata first to check for last_exec
        metadata_entry = metadata_service.get_report_metadata(token.id_cia, file_name) # Use token.id_cia
        if not metadata_entry:
            error_response = { "status": 1.1, "message": "Metadata not found for the given id_cia and file_name.", "log_user": token.coduser }
            return JSONResponse(content=jsonable_encoder(error_response), status_code=status.HTTP_404_NOT_FOUND)

        last_etl_exec = metadata_entry["last_exec"]

        parquet_data, error_details = extract_service.minio_service.download_file(bucket_name="reports", object_name=file_name)

        if error_details:
            return JSONResponse(content=jsonable_encoder(error_details), status_code=error_details.get("status_code", status.HTTP_400_BAD_REQUEST))
        
        if not parquet_data:
            error_response = { "status": 1.1, "message": "Parquet file not found in Minio or could not be downloaded.", "log_user": token.coduser }
            return JSONResponse(content=jsonable_encoder(error_response), status_code=status.HTTP_404_NOT_FOUND)

        headers = {"X-Log-User": token.coduser, "X-Days-To-Token-Expire": str(token.days_to_token_expire)}
        if last_etl_exec: headers["X-Last-Etl-Exec"] = last_etl_exec.isoformat()

        return Response(content=parquet_data, media_type="application/vnd.apache.parquet", headers=headers)
    except Exception as e:
        return JSONResponse(content={"status":1.2, "message":f"Endpoint error: {str(e)}", "log_user": token.coduser}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
