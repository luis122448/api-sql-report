from typing import Dict, List
from scheduling.report_config_loader import Report
import threading

class ReportConfigManager:
    _instance = None
    _lock = threading.Lock()
    report_configs: Dict[str, List[Report]] = {}

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ReportConfigManager, cls).__new__(cls)
        return cls._instance

    def set_report_configs(self, configs: Dict[str, List[Report]]):
        with self._lock:
            self.report_configs = configs

    def get_report_configs(self) -> Dict[str, List[Report]]:
        with self._lock:
            return self.report_configs.copy()
