from typing import Any, Optional
from pydantic import BaseModel


class BasicAuthSchema(BaseModel):
    ruc: str
    coduser: str
    clave: str

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "ruc": "20516612143",
                "coduser": "admin",
                "clave": "TFRWUTIwMjM=.."
            }]
        }
    }


class BasicTokenSchema(BaseModel):
    ruc: str
    coduser: str
    token: Any = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "ruc": "20516612143",
                "coduser": "admin",
                "token": "eyJ0eXAiOi.."  # JWT Token
            }]
        }
    }


class BasicAnalyticsSchema(BaseModel):
    id_cia: int
    ruc: str
    coduser: str
    exp: Optional[int] = None
    days_to_token_expire: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "id_cia": 1,
                "ruc": "9999999999",
                "coduser": "admin",
                "days_to_token_expire": 30
            }]
        }
    }

