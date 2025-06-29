import sqlite3
from datetime import datetime
from configs.sqlite import get_db_connection
from schemas.api_response_schema import ApiResponseObject

class MetadataService:
    def log_report_metadata(self, id_cia: int, id_report: int, name: str, cadsql: str, object_name: str, last_exec: datetime) -> ApiResponseObject:
        """Logs the metadata of a generated report into the SQLite database."""
        response = ApiResponseObject(status=1, message="Metadata logged successfully.")
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO METADATA_REPORT (id_cia, id_report, name, cadsql, object_name, last_exec)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (id_cia, id_report, name, cadsql, object_name, last_exec))
            conn.commit()
            response.object = {"id_cia": id_cia, "id_report": id_report}
        except sqlite3.IntegrityError:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = f"Metadata logging failed: A report with id_cia={id_cia} and id_report={id_report} already exists."
        except sqlite3.Error as e:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = f"Failed to log metadata: {e}"
        finally:
            conn.close()
            return response

    def get_report_metadata(self, id_cia: int, object_name: str):
        """Retrieves metadata for a specific report based on id_cia and object_name."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_cia, id_report, name, cadsql, object_name, last_exec
                FROM METADATA_REPORT
                WHERE id_cia = ? AND object_name = ?
            """, (id_cia, object_name))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            print(f"Error retrieving metadata: {e}")
            return None
        finally:
            conn.close()

    def get_latest_report_metadata(self, id_cia: int, id_report: int):
        """Retrieves the most recent metadata entry for a given id_cia and id_report."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_cia, id_report, name, cadsql, object_name, last_exec
                FROM METADATA_REPORT
                WHERE id_cia = ? AND id_report = ?
                ORDER BY last_exec DESC
                LIMIT 1
            """, (id_cia, id_report))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            print(f"Error retrieving latest metadata: {e}")
            return None
        finally:
            conn.close()
