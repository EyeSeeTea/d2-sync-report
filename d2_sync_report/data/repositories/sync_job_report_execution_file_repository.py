from datetime import datetime
from pydantic import BaseModel

from d2_sync_report.data.repositories.file_cache import FileCache
from d2_sync_report.domain.repositories.sync_job_report_execution_repository import (
    SyncJobReportExecutionRepository,
)
from typing import Optional
from d2_sync_report.domain.entities.sync_job_report_execution import SyncJobReportExecution


class SyncJobReportExecutionFileRepository(SyncJobReportExecutionRepository):
    def __init__(self):
        self.cache = FileCache(FileCacheProps, "cache.json")

    def save_last(self, execution: SyncJobReportExecution) -> None:
        props = FileCacheProps(
            last_processed=execution.last_processed,
            last_sync=execution.last_sync,
        )
        self.cache.save(props)

    def get_last(self) -> Optional[SyncJobReportExecution]:
        props = self.cache.load()
        if props is None:
            return None

        return SyncJobReportExecution(
            last_processed=props.last_processed, last_sync=props.last_sync
        )


class FileCacheProps(BaseModel):
    last_processed: datetime
    last_sync: datetime
