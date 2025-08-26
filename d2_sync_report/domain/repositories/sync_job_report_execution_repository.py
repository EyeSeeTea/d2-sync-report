from typing import Optional
from d2_sync_report.domain.entities.sync_job_report_execution import SyncJobReportExecution
from abc import ABC, abstractmethod


class SyncJobReportExecutionRepository(ABC):
    @abstractmethod
    def get_last(self) -> Optional[SyncJobReportExecution]:
        pass

    @abstractmethod
    def save_last(self, execution: SyncJobReportExecution) -> None:
        pass
