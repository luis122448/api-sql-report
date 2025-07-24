import sqlite3
import logging
from datetime import datetime, timedelta
from configs.sqlite import get_db_connection
from schemas.api_response_schema import ApiResponseList

logger = logging.getLogger(__name__)

class UsageService:
    def log_api_request(self, id_cia: int, id_report: int, requester_ip: str, endpoint: str, user_agent: str, token_coduser: str, processing_time_ms: int):
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get database connection for logging API request.")
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO API_USAGE_LOG (timestamp, id_cia, id_report, requester_ip, endpoint, user_agent, token_coduser, processing_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (datetime.now(), id_cia, id_report, requester_ip, endpoint, user_agent, token_coduser, processing_time_ms))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error logging API usage: {e}")
        finally:
            conn.close()

    def get_top_reports(self, id_cia: int = -1) -> ApiResponseList:
        response = ApiResponseList(status=1, message="Top reports retrieved successfully.")
        conn = get_db_connection()
        if not conn:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = "Failed to connect to the database."
            return response
        try:
            cursor = conn.cursor()
            one_week_ago = datetime.now() - timedelta(weeks=1)
            
            query = """
                SELECT 
                    id_cia, 
                    id_report, 
                    COUNT(*) as request_count,
                    COUNT(DISTINCT requester_ip) as unique_ips,
                    AVG(processing_time_ms) as avg_processing_time_ms
                FROM API_USAGE_LOG
                WHERE timestamp >= ? AND endpoint LIKE '%/reports/last/%'
            """
            params = [one_week_ago]

            if id_cia != -1:
                query += " AND id_cia = ?"
                params.append(id_cia)

            query += """
                GROUP BY id_cia, id_report
                ORDER BY request_count DESC
                LIMIT 20
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            response.list = [dict(row) for row in rows]
        except sqlite3.Error as e:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = f"Error getting top reports: {e}"
        finally:
            conn.close()
            return response

    def get_usage_details(self, id_cia: int, id_report: int) -> ApiResponseList:
        response = ApiResponseList(status=1, message="Usage details retrieved successfully.")
        conn = get_db_connection()
        if not conn:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = "Failed to connect to the database."
            return response
        try:
            cursor = conn.cursor()
            one_week_ago = datetime.now() - timedelta(weeks=1)
            cursor.execute("""
                SELECT timestamp, requester_ip, processing_time_ms
                FROM API_USAGE_LOG
                WHERE id_cia = ? AND id_report = ? AND timestamp >= ? AND endpoint LIKE '%/reports/last/%'
                ORDER BY timestamp DESC
            """, (id_cia, id_report, one_week_ago))
            rows = cursor.fetchall()
            response.list = [dict(row) for row in rows]
        except sqlite3.Error as e:
            response.status = 1.2
            response.message = "ERROR!"
            response.log_message = f"Error getting usage details: {e}"
        finally:
            conn.close()
            return response