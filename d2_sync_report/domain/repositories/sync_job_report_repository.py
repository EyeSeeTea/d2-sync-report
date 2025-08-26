from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from d2_sync_report.domain.entities.sync_job_report import (
    SyncJobReport,
)


class SyncJobReportRepository(ABC):
    @abstractmethod
    def get(self, since: Optional[datetime] = None) -> SyncJobReport:
        pass
