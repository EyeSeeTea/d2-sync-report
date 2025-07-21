from typing import Optional
from datetime import datetime

from d2_sync_report.data.repositories.d2_logs_parser import D2LogsParser
from d2_sync_report.domain.entities.sync_job_report import (
    SyncJobReport,
)
from d2_sync_report.domain.repositories.sync_job_report_repository import (
    SyncJobReportRepository,
)


class SyncJobReportD2Repository(SyncJobReportRepository):
    def __init__(self, logs_folder_path: str):
        self.logs_folder_path = logs_folder_path

    def get(self, since: Optional[datetime] = None) -> SyncJobReport:
        return D2LogsParser(self.logs_folder_path).get(since=since)
