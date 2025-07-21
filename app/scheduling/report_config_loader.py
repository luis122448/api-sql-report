import logging

from configs.oracle import OracleTransaction
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Report(BaseModel):
    id_cia: int = Field(alias="ID_CIA")
    company: str = Field(alias="COMPANY") # Added company field
    id_report: int = Field(alias="ID_REPORT")
    name: str = Field(alias="NAME")
    query: str = Field(alias="QUERY")
    swapi: str = Field(alias="SWAPI")
    refreshtime: int = Field(alias="REFRESHTIME")

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
