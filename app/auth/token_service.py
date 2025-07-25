import logging
from datetime import datetime, timedelta

import os # Import os
from dotenv import load_dotenv # Import load_dotenv

from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
from schemas.auth_schema import BasicAuthSchema, BasicTokenSchema, BasicAnalyticsSchema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TokenService:

    def __init__(self):
        self.SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key") # Load from environment variable
        self.ALGORITHM = 'HS256'
        self.TOKEN_EXPIRATION_TIME = timedelta(days=30)  # 30 days
        pass

    def create_token(self, auth: BasicAuthSchema, id_cia: int) -> BasicTokenSchema:
        data_token = BasicAnalyticsSchema(id_cia=id_cia, ruc=auth.ruc, coduser=auth.coduser, days_to_token_expire=30)
        expiration_time = datetime.now() + self.TOKEN_EXPIRATION_TIME
        data_token.exp = int(expiration_time.timestamp())
        token = encode(payload=data_token.model_dump(), key=self.SECRET_KEY, algorithm=self.ALGORITHM)
        return BasicTokenSchema(ruc=auth.ruc, coduser=auth.coduser, token=token)

    def decode_token(self, token: str) -> BasicAnalyticsSchema:
        try:
            data_token: dict = decode(token, key=self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return BasicAnalyticsSchema(
                id_cia=data_token.get('id_cia'),
                ruc=data_token.get('ruc'),
                coduser=data_token.get('coduser'),
                days_to_token_expire=int((datetime.fromtimestamp(data_token.get('exp')) - datetime.now()).days)
            )
        except ExpiredSignatureError:
            logger.error("Token expired Function")
            raise
        except InvalidTokenError as e:
            logger.error(f"Invalid token Function: {e}")
            raise

    def validate_token(self, token: str) -> bool:
        try:
            decode(token, key=self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return True
        except ExpiredSignatureError:
            logger.error("Token expired Function")
            return False
        except InvalidTokenError as e:
            logger.error(f"Invalid token Function : {e}")
            return False