import os
from minio import Minio
from dotenv import load_dotenv

load_dotenv()

class MinioConfig:
    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_URL"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=False
        )
