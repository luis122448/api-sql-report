from fastapi import APIRouter, Depends, HTTPException
from schemas.auth_schema import BasicAuthSchema
from schemas.api_response_schema import ApiResponseAuth
from auth.auth_service import AuthService

router = APIRouter(tags=["Auth"])

@router.post("/login", response_model=ApiResponseAuth)
async def login(auth_credentials: BasicAuthSchema, auth_service: AuthService = Depends(AuthService)):
    response = await auth_service.login(auth_credentials)
    if response.status != 1.0:
        raise HTTPException(status_code=401, detail=response.message)
    return response
