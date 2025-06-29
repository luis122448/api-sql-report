from pydantic import BaseModel
from typing import Optional, Any, List, Dict
from datetime import date, datetime


class ApiResponseSchema(BaseModel):
    # status:
    # 1: "Success"
    # 1.1: "Success but with warnings"
    # 1.2: "Success but with errors"

    status: float
    message: str
    id_cia: Optional[int] = None
    timestamp: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "status": "1",
                "message": "Success",
            }]
        }
    }


class ApiResponseObject(BaseModel):
    status: float
    message: str
    log_message: Optional[str] = None
    log_user: Optional[str] = None
    object: Optional[Any] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "status": 1.2,
                "message": "Error Unauthorized",
                "object": ""
            }]
        }
    }


class ApiResponseList(BaseModel):
    status: float
    message: str
    log_message: Optional[str] = None
    log_user: Optional[str] = None
    last_exec: Optional[datetime] = None
    list: Optional[List[Dict[str, Any]]] = None


class ApiResponseAuth(BaseModel):
    status: float
    message: str
    object: Optional[Any] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "status": 1.2,
                "message": "Error Unauthorized",
                "object": ""
            }]
        }
    }
