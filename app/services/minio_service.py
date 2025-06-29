
import logging
from minio.error import S3Error
from fastapi import Depends
from configs.minio import MinioConfig

logging.basicConfig(level=logging.INFO)

class MinioService:
    def __init__(self, minio_config: MinioConfig = Depends()):
        self.minio_client = minio_config.client

    def create_bucket(self, bucket_name):
        try:
            found = self.minio_client.bucket_exists(bucket_name)
            if not found:
                self.minio_client.make_bucket(bucket_name)
                logging.info(f"Bucket {bucket_name} created.")
            else:
                logging.info(f"Bucket {bucket_name} already exists.")
        except S3Error as exc:
            logging.error(f"Error creating bucket: {exc}")
            raise

    def upload_file(self, bucket_name, object_name, file_path):
        try:
            self.create_bucket(bucket_name)
            self.minio_client.fput_object(
                bucket_name, object_name, file_path,
            )
            logging.info(
                f"'{file_path}' is successfully uploaded as "
                f"object '{object_name}' to bucket '{bucket_name}'."
            )
            return object_name
        except S3Error as exc:
            logging.error(f"Error uploading file: {exc}")
            raise

    def download_file(self, bucket_name: str, object_name: str) -> bytes | None:
        try:
            response = self.minio_client.get_object(bucket_name, object_name)
            return response.read()
        except S3Error as exc:
            logging.error(f"Error downloading file: {exc}")
            return None
        finally:
            if 'response' in locals() and response:
                response.close()
                response.release_conn()
