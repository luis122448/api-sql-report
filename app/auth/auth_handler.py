import logging
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.token_service import TokenService
from starlette.exceptions import HTTPException as StarletteHTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JWTBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request, service: TokenService = Depends()):
        try:
            credentials: HTTPAuthorizationCredentials = await super().__call__(request)
            logger.info(f"jwt_token: {credentials.credentials}")
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if credentials.credentials is None:
                raise HTTPException(status_code=403, detail="Token not found.")
            if not service.validate_token(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return service.decode_token(credentials.credentials)
        except HTTPException as e:
            logger.error(f"HTTPException: {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
            raise e