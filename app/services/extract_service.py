import oracledb, time, os, json, re
import pandas as pd
import pyarrow
from datetime import datetime
from schemas.api_response_schema import ApiResponseSchema, ApiResponseList, ApiResponseObject
from configs.oracle import OracleTransaction
from fastapi import Depends
from services.minio_service import MinioService
from services.metadata_service import MetadataService


class ExtractService:

    def __init__(self, 
                 oracle: OracleTransaction = Depends(), 
                 minio_service: MinioService = Depends(),
                 metadata_service: MetadataService = Depends()) -> None:
        self.oracle = oracle
        self.minio_service = minio_service
        self.metadata_service = metadata_service
        self.oracle_connection = oracle.connection
        self.oracle_cursor = oracle.connection.cursor()

    def run_extraction_pipeline(self, id_cia: int, id_report: int, name: str, query: str) -> ApiResponseObject:
        # Step 1: Decode the Oracle query
        decode_response = ExtractService.decode_query(id_cia, query)
        if decode_response.status != 1:
            return decode_response
        decoded_query = decode_response.object
        
        # Step 2: Retrieve data using the decoded query
        data_response = self.get_data(decoded_query)

        if data_response.status != 1:
            return data_response

        # Step 3: If data retrieval was successful, convert to Parquet
        file_path_response = self.to_parquet(data_response.list)
        
        if file_path_response.status != 1:
            return file_path_response

        # Step 4: Upload the Parquet file to Minio
        upload_response = self.upload_to_minio(file_path_response.object)

        if upload_response.status != 1:
            return upload_response

        # Step 5: Log metadata to SQLite
        metadata_response = self.metadata_service.log_report_metadata(
            id_cia=id_cia,
            id_report=id_report,
            name=name,
            cadsql=decoded_query,
            object_name=upload_response.object["file_name"],
            last_exec=data_response.last_exec
        )

        # If metadata logging fails, it's a critical error because the report ID might be reused incorrectly.
        if metadata_response.status != 1:
            return metadata_response

        return upload_response

    @staticmethod
    def decode_query(id_cia: int, query: str) -> ApiResponseObject:
        response = ApiResponseObject(status=1, message="OK!", log_message="Query decoded successfully.")

        # 1. Validate that PID_CIA placeholder exists
        if "PID_CIA" not in query:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = "Validation Error: The query must contain the 'PID_CIA' placeholder."
            return response

        # Replace placeholders
        decoded_query = query.replace("PID_CIA", str(id_cia))
        if ":P02PERIODO" in decoded_query:
            period_value = datetime.now().strftime('%Y')
            decoded_query = decoded_query.replace(":P02PERIODO", f"'{period_value}'")
        if ":P02MES" in decoded_query:
            month_value = "-1"
            decoded_query = decoded_query.replace(":P02MES", f"'{month_value}'")
        if ":P04FECHA_DESDE" in decoded_query:
            start_date_value = (datetime.now() - pd.DateOffset(years=3)).strftime('%Y-%m-%d')
            decoded_query = decoded_query.replace(":P04FECHA_DESDE", f"'{start_date_value}'")
        if ":P04FECHA_HASTA" in decoded_query:
            end_date_value = datetime.now().strftime('%Y-%m-%d')
            decoded_query = decoded_query.replace(":P04FECHA_HASTA", f"'{end_date_value}'")

        # 2. Validate that no placeholders are left undecoded
        remaining_placeholders = re.findall(r'(\{\{.*?\}\}|\:\w+)', decoded_query)
        if remaining_placeholders:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = f"Validation Error: Undecoded placeholders found: {', '.join(remaining_placeholders)}"
            return response

        response.object = decoded_query
        return response

    def get_data(self, query: str) -> ApiResponseList:
        # We now initialize with a fallback time and update it with the precise DB time.
        object_response = ApiResponseList(
            status=1, message="OK!", log_message="OK!", last_exec=datetime.now())
        try:
            # Get current DB time for logging execution using the transactional cursor
            self.oracle_cursor.execute("SELECT CURRENT_TIMESTAMP FROM DUAL")
            db_time_row = self.oracle_cursor.fetchone()
            if db_time_row:
                object_response.last_exec = db_time_row[0]

            # Execute query
            self.oracle_cursor.execute(query)
            rows = self.oracle_cursor.fetchall()

            # Get columns
            columns = [col[0] for col in self.oracle_cursor.description]
            result = [dict(zip(columns, row)) for row in rows]

            object_response.list = result

        except oracledb.Error as e:
            object_response.status = 1.2
            object_response.message = "ERROR!"
            object_response.log_message = f"ERROR (ORACLE) : {e}"
        except Exception as e:
            object_response.status = 1.2
            object_response.message = "ERROR!"
            object_response.log_message = f"ERROR : {e}"
        finally:
            return object_response

    def to_parquet(self, data_list: list) -> ApiResponseObject:
        object_response = ApiResponseObject(
            status=1, message="Data converted to Parquet file successfully.", log_message="OK!")
        try:
            if not data_list:
                object_response.status = 1.1
                object_response.message = "WARNING!"
                object_response.log_message = "The data list is empty. No Parquet file generated."
                return object_response

            # Create a pandas DataFrame
            df = pd.DataFrame(data_list)

            # Generate a unique filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = f"report_{timestamp}.parquet"
            file_path = f"/tmp/{file_name}"

            # Convert the DataFrame to a Parquet file
            df.to_parquet(file_path, engine='pyarrow', index=False)
            object_response.object = file_path

        except Exception as e:
            object_response.status = 1.2
            object_response.message = "ERROR!"
            object_response.log_message = f"ERROR (PARQUET) : {e}"
        finally:
            return object_response

    def upload_to_minio(self, file_path: str) -> ApiResponseObject:
        object_response = ApiResponseObject(
            status=1, message="File uploaded to Minio successfully.", log_message="OK!")
        try:
            bucket_name = "reports"
            object_name = os.path.basename(file_path)
            
            self.minio_service.upload_file(bucket_name, object_name, file_path)
            
            object_response.object = {"bucket": bucket_name, "file_name": object_name}

        except Exception as e:
            object_response.status = 1.2
            object_response.message = "ERROR!"
            object_response.log_message = f"ERROR (MINIO) : {e}"
        finally:
            # Clean up the local file
            if os.path.exists(file_path):
                os.remove(file_path)
            return object_response

    def read_parquet_data(self, id_cia: int, file_name: str) -> tuple[bytes | None, dict | None]:
        try:
            # 1. Verify metadata exists
            metadata_entry = self.metadata_service.get_report_metadata(id_cia, file_name)
            if not metadata_entry:
                return None, {"status": 1.1, "message": "Metadata not found for the given id_cia and file_name.", "log_user": "system", "status_code": 404}

            # 2. Download from Minio
            bucket_name = "reports"
            parquet_data = self.minio_service.download_file(bucket_name, file_name)

            if not parquet_data:
                return None, {"status": 1.2, "message": "Parquet file not found in Minio or could not be downloaded.", "log_user": "system", "status_code": 404}

            return parquet_data, None

        except Exception as e:
            return None, {"status": 1.2, "message": f"Error reading Parquet data: {str(e)}", "log_user": "system", "status_code": 500}

    def read_latest_parquet_data(self, id_cia: int, id_report: int) -> tuple[bytes | None, dict | None]:
        try:
            # 1. Verify metadata exists
            metadata_entry = self.metadata_service.get_latest_report_metadata(id_cia, id_report)
            if not metadata_entry:
                return None, {"status": 1.1, "message": "No metadata found for the given id_cia and id_report.", "log_user": "system", "status_code": 404}

            file_name = metadata_entry["object_name"]

            # 2. Download from Minio
            bucket_name = "reports"
            parquet_data = self.minio_service.download_file(bucket_name, file_name)

            if not parquet_data:
                return None, {"status": 1.2, "message": "Parquet file not found in Minio or could not be downloaded.", "log_user": "system", "status_code": 404}

            return parquet_data, None

        except Exception as e:
            return None, {"status": 1.2, "message": f"Error reading latest Parquet data: {str(e)}", "log_user": "system", "status_code": 500}
