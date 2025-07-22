from typing import Optional
from datetime import datetime

from d2_sync_report.data.repositories.d2_logs_parser.d2_logs_parser import D2LogsParser
from d2_sync_report.data.repositories.docker_sync_temporal_folder import DockerSyncTemporalFolder
from d2_sync_report.domain.entities.sync_job_report import (
    SyncJobReport,
)
from d2_sync_report.domain.repositories.sync_job_report_repository import (
    SyncJobReportRepository,
)


class SyncJobReportD2Repository(SyncJobReportRepository):
    def __init__(self, logs_folder: str):
        self.logs_folder = logs_folder

    def get(self, since: Optional[datetime] = None) -> SyncJobReport:
        is_docker_path = ":" in self.logs_folder

        if is_docker_path:
            container_name, container_path = self.logs_folder.split(":", 1)
            with DockerSyncTemporalFolder(container_name, container_path) as docker_logs_folder:
                return D2LogsParser(docker_logs_folder).get(since=since)
        else:
            return D2LogsParser(self.logs_folder).get(since=since)
