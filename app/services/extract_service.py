import oracledb
import os
import re
import pandas as pd
from datetime import datetime
from schemas.api_response_schema import ApiResponseList, ApiResponseObject
from configs.oracle import OracleTransaction
from fastapi import Depends
from services.minio_service import MinioService
from services.metadata_service import MetadataService
from configs.minio import MinioConfig


class ExtractService:

    def __init__(self, 
                 oracle: OracleTransaction = Depends(), 
                 metadata_service: MetadataService = Depends()) -> None:
        self.oracle = oracle
        self.minio_service = MinioService(minio_config=MinioConfig())
        self.metadata_service = metadata_service
        self.oracle_connection = oracle.connection
        self.oracle_cursor = oracle.connection.cursor()

    def run_extraction_pipeline(self, id_cia: int, id_report: int, name: str, query: str, company: str = None, format: str = 'parquet', execution_type: str = 'AUTO') -> ApiResponseObject:
        start_pipeline_time = datetime.now()
        pipeline_status = 'OK'
        pipeline_error_message = None
        object_name_parquet = None
        object_name_csv = None
        last_exec = None
        decoded_query = None
        processing_time_ms = None

        try:
            # Step 1: Decode the Oracle query
            decode_response = ExtractService.decode_query(id_cia, query)
            if decode_response.status != 1:
                raise Exception(decode_response.log_message)
            decoded_query = decode_response.object
            
            # Step 2: Retrieve data using the decoded query
            data_response = self.get_data(decoded_query)
            if data_response.status != 1:
                last_exec = data_response.last_exec # Still log the time of attempt
                raise Exception(data_response.log_message)
            last_exec = data_response.last_exec

            # Step 3: If data retrieval was successful, convert to Parquet and CSV
            parquet_path_response = self.to_parquet(
                data_rows=data_response.object["rows"], 
                column_names=data_response.object["columns"], 
                columns_description=data_response.object["description"],
                id_cia=id_cia,
                id_report=id_report,
                name_report=name,
                last_exec=last_exec
            )
            if parquet_path_response.status != 1:
                raise Exception(parquet_path_response.log_message)

            csv_path_response = self.to_csv(
                data_rows=data_response.object["rows"],
                column_names=data_response.object["columns"],
                id_cia=id_cia,
                id_report=id_report,
                name_report=name,
                last_exec=last_exec
            )
            if csv_path_response.status != 1:
                raise Exception(csv_path_response.log_message)

            # Step 4: Upload the files to Minio
            upload_parquet_response = self.upload_to_minio(parquet_path_response.object, id_cia)
            if upload_parquet_response.status != 1:
                raise Exception(upload_parquet_response.log_message)
            object_name_parquet = upload_parquet_response.object["file_name"]

            upload_csv_response = self.upload_to_minio(csv_path_response.object, id_cia)
            if upload_csv_response.status != 1:
                raise Exception(upload_csv_response.log_message)
            object_name_csv = upload_csv_response.object["file_name"]

        except Exception as e:
            pipeline_status = 'FAILED'
            pipeline_error_message = f"Unhandled exception during pipeline: {e}"

        finally:
            end_pipeline_time = datetime.now()
            processing_time_ms = int((end_pipeline_time - start_pipeline_time).total_seconds() * 1000)

            # Step 5: Log metadata to SQLite, regardless of success or failure
            self.metadata_service.log_report_metadata(
                id_cia=id_cia,
                id_report=id_report,
                name=name,
                cadsql=decoded_query if decoded_query else query, # Log original query if decode failed
                object_name_parquet=object_name_parquet,
                object_name_csv=object_name_csv,
                last_exec=last_exec if last_exec else datetime.now(), # Log current time if no DB time obtained
                processing_time_ms=processing_time_ms,
                status=pipeline_status,
                error_message=pipeline_error_message,
                execution_type=execution_type
            )
            
            if pipeline_status == 'OK':
                return ApiResponseObject(status=1, message="Pipeline completed successfully.", log_message="OK!")
            else:
                return ApiResponseObject(status=1.2, message="Pipeline failed.", log_message=pipeline_error_message)

    @staticmethod
    def decode_query(id_cia: int, query: str) -> ApiResponseObject:
        response = ApiResponseObject(status=1, message="OK!", log_message="Query decoded successfully.")

        query = query.upper()

        # 1. Validate that PID_CIA placeholder exists
        if "_PID_CIA" not in query:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = "Validation Error: The query must contain the '_PID_CIA' placeholder."
            return response
        # Replace placeholders
        decoded_query = query.replace("_PID_CIA", str(id_cia))
        if ":P01INGSAL" in decoded_query:
            ingsal = '-1'
            decoded_query = decoded_query.replace(":P01INGSAL", f"'{ingsal}'")
        if ":P02MOTIVO" in decoded_query:
            motivo = '-1'
            decoded_query = decoded_query.replace(":P02MOTIVO", f"'{motivo}'")
        if ":P02PERIODO_ANTERIOR" in decoded_query:
            previous_period_value = (datetime.now() - pd.DateOffset(years=1)).strftime('%Y')
            decoded_query = decoded_query.replace(":P02PERIODO_ANTERIOR", f"'{previous_period_value}'")
        if ":P02PERIODO" in decoded_query:
            period_value = datetime.now().strftime('%Y')
            decoded_query = decoded_query.replace(":P02PERIODO", f"'{period_value}'")
        if ":P02MES_STOCK" in decoded_query:
            month_stock_value = datetime.now().strftime('%m')
            decoded_query = decoded_query.replace(":P02MES_STOCK", f"'{month_stock_value}'")
        if ":P02MES_COSTO" in decoded_query:
            month_costs_value = (datetime.now() - pd.DateOffset(months=1)).strftime('%m')
            decoded_query = decoded_query.replace(":P02MES_COSTO", f"'{month_costs_value}'")
        if ":P06MES_STOCK" in decoded_query:
            month_stock_value = datetime.now().strftime('%m')
            decoded_query = decoded_query.replace(":P06MES_STOCK", f"'{month_stock_value}'")
        if ":P06MES_COSTO" in decoded_query:
            month_costs_value = (datetime.now() - pd.DateOffset(months=1)).strftime('%m')
            decoded_query = decoded_query.replace(":P06MES_COSTO", f"'{month_costs_value}'")
        if ":P02MES" in decoded_query:
            month_value = "-1"
            decoded_query = decoded_query.replace(":P02MES", f"'{month_value}'")
        if ":P06MES" in decoded_query:
            month_value = datetime.now().strftime('%m')
            decoded_query = decoded_query.replace(":P06MES", f"'{month_value}'")
        if ":P07MES" in decoded_query:
            month_value = "-1"
            decoded_query = decoded_query.replace(":P07MES", f"'{month_value}'")
        if ":P04FECHA_DESDE" in decoded_query:
            start_date_value = (datetime.now() - pd.DateOffset(years=3)).strftime('%Y-%m-%d')
            decoded_query = decoded_query.replace(":P04FECHA_DESDE", f"TO_DATE('{start_date_value}', 'YYYY-MM-DD')")
        if ":P04FECHA_HASTA" in decoded_query:
            end_date_value = datetime.now().strftime('%Y-%m-%d')
            decoded_query = decoded_query.replace(":P04FECHA_HASTA", f"TO_DATE('{end_date_value}', 'YYYY-MM-DD')")

        # 2. Validate that no placeholders are left undecoded
        remaining_placeholders = re.findall(r'(\{\{.*?\}\}|\:\w+)', decoded_query)
        if remaining_placeholders:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = f"Validation Error: Undecoded placeholders found: {', '.join(remaining_placeholders)}"
            return response

        response.object = decoded_query
        return response

    def get_data(self, query: str) -> ApiResponseObject:
        # We now initialize with a fallback time and update it with the precise DB time.
        object_response = ApiResponseObject(
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

            # Get columns and result
            columns = [col[0] for col in self.oracle_cursor.description]
            
            object_response.object = {
                "rows": rows,
                "columns": columns,
                "description": self.oracle_cursor.description
            }

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

    def to_parquet(self, data_rows: list, column_names: list, columns_description: list, id_cia: int, id_report: int, name_report: str, last_exec: datetime) -> ApiResponseObject:
        object_response = ApiResponseObject(
            status=1, message="Data converted to Parquet file successfully.", log_message="OK!")
        try:
            df = pd.DataFrame(data_rows, columns=column_names)

            # Add traceability columns
            df['ID_CIA'] = id_cia
            df['ID_REPORT'] = id_report
            df['NAME_REPORT'] = name_report
            df['LAST_EXEC'] = last_exec

            type_mapping = {
                oracledb.DB_TYPE_VARCHAR: 'string',
                oracledb.DB_TYPE_CHAR: 'string',
                oracledb.DB_TYPE_LONG: 'string',
                oracledb.DB_TYPE_NVARCHAR: 'string',
                oracledb.DB_TYPE_DATE: 'datetime64[ns]',
                oracledb.DB_TYPE_TIMESTAMP: 'datetime64[ns]',
                oracledb.DB_TYPE_CLOB: 'string',
            }

            # Attempt to apply the ideal data type for each column based on Oracle metadata.
            for i, col_name in enumerate(column_names):
                oracle_type_code = columns_description[i][1]
                target_type = None
                if oracle_type_code == oracledb.DB_TYPE_NUMBER:
                    scale = columns_description[i][5]
                    target_type = 'Int64' if scale is not None and scale == 0 else 'float64'
                else:
                    target_type = type_mapping.get(oracle_type_code)
                
                if target_type:
                    try:
                        # Apply the ideal type.
                        df[col_name] = df[col_name].astype(target_type)
                    except (ValueError, TypeError):
                        # If conversion fails (e.g., mixed data), fallback to string.
                        df[col_name] = df[col_name].astype('string')

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = f"report_{id_cia}_{id_report}_{timestamp}.parquet"
            file_path = f"/tmp/{file_name}"

            df.to_parquet(file_path, engine='pyarrow', index=False)
            object_response.object = file_path

        except Exception as e:
            object_response.status = 1.2
            object_response.message = "ERROR!"
            object_response.log_message = f"ERROR (PARQUET) : {e}"
        finally:
            return object_response

    def to_csv(self, data_rows: list, column_names: list, id_cia: int, id_report: int, name_report: str, last_exec: datetime) -> ApiResponseObject:
        object_response = ApiResponseObject(
            status=1, message="Data converted to CSV file successfully.", log_message="OK!")
        try:
            df = pd.DataFrame(data_rows, columns=column_names)

            # Add traceability columns
            df['ID_CIA'] = id_cia
            df['ID_REPORT'] = id_report
            df['NAME_REPORT'] = name_report
            df['LAST_EXEC'] = last_exec

            # Clean data: remove the '|' character from all columns
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace('|', '', regex=False)

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = f"report_{id_cia}_{id_report}_{timestamp}.csv"
            file_path = f"/tmp/{file_name}"

            df.to_csv(file_path, sep='|', index=False)
            object_response.object = file_path

        except Exception as e:
            object_response.status = 1.2
            object_response.message = "ERROR!"
            object_response.log_message = f"ERROR (CSV) : {e}"
        finally:
            return object_response

    def upload_to_minio(self, file_path: str, id_cia: int) -> ApiResponseObject:
        object_response = ApiResponseObject(
            status=1, message="File uploaded to Minio successfully.", log_message="OK!")
        try:
            bucket_name = f"bucket-{id_cia}"

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
