import logging
from configs.oracle import OracleTransaction
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Report(BaseModel):
    id_cia: int = Field(alias="ID_CIA")
    company: str = Field(alias="COMPANY") # Added company field
    id_report: int = Field(alias="ID_REPORT")
    name: str = Field(alias="NAME")
    query: str = Field(alias="QUERY")
    swapi: str = Field(alias="SWAPI")
    refreshtime: Optional[int] = Field(alias="REFRESHTIME", default=None)
    last_successful_exec: Optional[datetime] = None
    staleness_duration_minutes: Optional[int] = None

class ReportConfigLoader:
    # Handles loading report configurations from the Oracle database.
    @staticmethod
    def get_reports_from_oracle() -> list[Report]:
        # Fetches report configurations from the Oracle database.
        reports = []
        sql_query = "SELECT id_cia, company, id_report, name, query, swapi, refreshtime FROM pack_exceldinamico.sp_buscar_api(-1)" # Updated query
        
        try:
            with OracleTransaction() as connection:
                cursor = connection.cursor()
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                
                for row in rows:
                    report_data = dict(zip(columns, row))
                    reports.append(Report(**report_data))
            logger.info(f"Successfully fetched {len(reports)} reports from Oracle.")
        except Exception as e:
            logger.error(f"Error fetching reports from Oracle: {e}")
        return reports

    @staticmethod
    def get_report_config(id_cia: int, id_report: int) -> Report | None:
        """
        Fetches the configuration for a single report from the Oracle database.
        """
        report = None
        # The procedure likely takes id_cia. The query is parameterized to prevent SQL injection.
        sql_query = "SELECT id_cia, company, id_report, name, query, swapi, refreshtime FROM pack_exceldinamico.sp_buscar_api(:id_cia) WHERE id_cia = :id_cia AND id_report = :id_report"
        
        try:
            with OracleTransaction() as connection:
                cursor = connection.cursor()
                cursor.execute(sql_query, {'id_cia': id_cia, 'id_report': id_report})
                row = cursor.fetchone()
                if row:
                    columns = [col[0] for col in cursor.description]
                    report_data = dict(zip(columns, row))
                    report = Report(**report_data)
                    logger.info(f"Successfully fetched configuration for report ID: {id_report} for company ID: {id_cia}")
        except Exception as e:
            logger.error(f"Error fetching single report config for ID {id_report}: {e}")
            
        return report
