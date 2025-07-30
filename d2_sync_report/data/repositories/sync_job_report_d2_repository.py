from typing import Optional
from datetime import datetime
from contextlib import contextmanager
from typing import Iterator

from d2_sync_report.data.dhis2_api import D2Api
from d2_sync_report.data.repositories.d2_logs_parser.d2_logs_parser import D2LogsParser
from d2_sync_report.data.repositories.docker_sync_temporal_folder import DockerSyncTemporalFolder
from d2_sync_report.domain.entities.sync_job_report import (
    SyncJobReport,
)
from d2_sync_report.domain.repositories.sync_job_report_repository import (
    SyncJobReportRepository,
)


class SyncJobReportD2Repository(SyncJobReportRepository):
    def __init__(self, api: D2Api, logs_folder: str):
        self.api = api
        self.logs_folder = logs_folder

    def get(self, since: Optional[datetime] = None) -> SyncJobReport:
        with local_or_docker_folder(self.logs_folder) as logs_folder:
            return D2LogsParser(self.api, logs_folder).get(since=since)


@contextmanager
def local_or_docker_folder(name: str) -> Iterator[str]:
    """
    Context manager that handles local (PATH) or docker (CONTAINER:PATH) paths.
    """
    if ":" in name:
        container_name, container_path = name.split(":", 1)
        with DockerSyncTemporalFolder(container_name, container_path) as docker_logs_folder:
            yield docker_logs_folder
    else:
        yield name
