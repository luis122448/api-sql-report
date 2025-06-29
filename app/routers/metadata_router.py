from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from services.extract_service import ExtractService

router = APIRouter()

@router.get("/read_parquet/{id_cia}/{file_name}", tags=["ANALYTICS"])
def read_parquet(id_cia: int, file_name: str, extract_service: ExtractService = Depends()):
    try:
        parquet_data, error_details = extract_service.read_parquet_data(id_cia, file_name)

        if error_details:
            return JSONResponse(content=jsonable_encoder(error_details), status_code=error_details.get("status_code", status.HTTP_400_BAD_REQUEST))
        
        if not parquet_data:
            error_response = { "status": 1.1, "message": "No data found or Parquet generation failed.", "log_user": "system", "status_code": status.HTTP_404_NOT_FOUND }
            return JSONResponse(content=jsonable_encoder(error_response), status_code=status.HTTP_404_NOT_FOUND)

        return Response(content=parquet_data, media_type="application/vnd.apache.parquet")
    except Exception as e:
        return JSONResponse(content={"status":1.2, "message":f"Endpoint error: {str(e)}", "log_user": "system"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/read_latest_parquet/{id_cia}/{id_report}", tags=["ANALYTICS"])
def read_latest_parquet(id_cia: int, id_report: int, extract_service: ExtractService = Depends()):
    try:
        parquet_data, error_details = extract_service.read_latest_parquet_data(id_cia, id_report)

        if error_details:
            return JSONResponse(content=jsonable_encoder(error_details), status_code=error_details.get("status_code", status.HTTP_400_BAD_REQUEST))
        
        if not parquet_data:
            error_response = { "status": 1.1, "message": "No data found or Parquet generation failed.", "log_user": "system", "status_code": status.HTTP_404_NOT_FOUND }
            return JSONResponse(content=jsonable_encoder(error_response), status_code=status.HTTP_404_NOT_FOUND)

        return Response(content=parquet_data, media_type="application/vnd.apache.parquet")
    except Exception as e:
        return JSONResponse(content={"status":1.2, "message":f"Endpoint error: {str(e)}", "log_user": "system"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
