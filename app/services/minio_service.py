import logging
from minio.error import S3Error
from fastapi import Depends
from configs.minio import MinioConfig
from datetime import datetime, timedelta

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

    def download_file(self, bucket_name: str, object_name: str):
        try:
            response = self.minio_client.get_object(bucket_name, object_name)
            yield from response.stream(32 * 1024)
        except S3Error as exc:
            logging.error(f"Error downloading file: {exc}")
            return None
        finally:
            if 'response' in locals() and response:
                response.close()
                response.release_conn()

    def clean_old_minio_objects(self, bucket_name: str = "reports"):
        # Deletes objects from the specified Minio bucket that are older than one week.
        logging.info(f"Starting Minio cleanup for bucket: {bucket_name}")
        try:
            one_week_ago = datetime.now() - timedelta(weeks=1)
            objects_to_delete = []
            for obj in self.minio_client.list_objects(bucket_name, recursive=True):
                if obj.last_modified and obj.last_modified.replace(tzinfo=None) < one_week_ago:
                    objects_to_delete.append(obj.object_name)
            
            if objects_to_delete:
                for obj_name in objects_to_delete:
                    self.minio_client.remove_object(bucket_name, obj_name)
                    logging.info(f"Deleted old object from Minio: {bucket_name}/{obj_name}")
                logging.info(f"Minio cleanup completed. Deleted {len(objects_to_delete)} objects.")
            else:
                logging.info("No old objects found in Minio to delete.")
        except S3Error as exc:
            logging.error(f"Error during Minio cleanup: {exc}")
        except Exception as e:
            logging.error(f"An unexpected error occurred during Minio cleanup: {e}")