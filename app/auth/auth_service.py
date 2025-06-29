import requests, logging, os, base64
from dotenv import load_dotenv
from fastapi import Depends
from schemas.api_response_schema import ApiResponseAuth
from schemas.auth_schema import BasicAuthSchema, BasicAnalyticsSchema
from auth.token_service import TokenService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the environment variables
load_dotenv()


class AuthService:

    def __init__(self, service: TokenService = Depends()):
        self.service = service

    async def login(self, auth: BasicAuthSchema) -> ApiResponseAuth:
        # URL API REST
        url = os.getenv("API_LOGIN_ANALYTICS")

        # Decode Base64
        auth.clave = base64.b64encode(auth.clave.encode()).decode()

        # Request POST
        response = requests.post(url, json=auth.model_dump(), verify=False)

        # Review the response status
        if response.status_code == 200:
            token_response = self.service.create_token(auth, response.json().get('id_cia'))
            return ApiResponseAuth(status=1.0, message="Success", object=token_response)
        else:
            return ApiResponseAuth(status=1.2, message=f"Error al realizar la solicitud POST: {response.status_code}",
                                   object=None)

    async def get_current_user(self, token: str) -> BasicAnalyticsSchema:
        if self.service.validate_token(token):
            return self.service.decode_token(token)
        else:
            return BasicAnalyticsSchema(status=1.1, message="Token no válido")
