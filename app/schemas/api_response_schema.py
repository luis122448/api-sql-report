from pydantic import BaseModel
from typing import Optional, Any, List, Dict
from datetime import datetime

class ApiResponseObject(BaseModel):
    status: float
    message: str
    log_message: Optional[str] = None
    log_user: Optional[str] = None
    object: Optional[Any] = None
    last_exec: Optional[datetime] = None

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
    list: Optional[List] = None
    last_exec: Optional[datetime] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "status": 1.2,
                "message": "Error Unauthorized",
                "list": []
            }]
        }
    }


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
